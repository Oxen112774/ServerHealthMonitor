// Package incident implements the operational event lifecycle used by the
// monitoring agent: detection -> triage -> mitigation -> resolution ->
// postmortem, together with MTTR accounting.
//
// The lifecycle model follows the incident-management practice described in
// Google SRE Workbook (chapter 9, "Incident Response") and ITIL 4 incident
// management: every alert that matters becomes a tracked record with an
// explicit owner, a timestamped timeline, and a measurable time-to-repair.
// Persistence mirrors internal/console/tickets so operators get the same
// behaviour from both the desktop app and the server-side console.
package incident

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

// Status is a position in the incident lifecycle.
type Status string

const (
	// StatusOpen is the state right after automatic detection.
	StatusOpen Status = "open"
	// StatusTriage means a human has accepted the incident and is assessing it.
	StatusTriage Status = "triage"
	// StatusMitigating means remediation is in progress.
	StatusMitigating Status = "mitigating"
	// StatusResolved means service was restored (MTTR stops counting here).
	StatusResolved Status = "resolved"
	// StatusPostmortem means the review is closed; a root cause is mandatory.
	StatusPostmortem Status = "postmortem"
)

// Severity mirrors the notifier severities, plus an informational level.
type Severity string

const (
	SeverityInfo     Severity = "info"
	SeverityWarning  Severity = "warning"
	SeverityCritical Severity = "critical"
)

// Symptom keywords form the shared vocabulary between detection and
// remediation: the monitor stamps a symptom on an incident, and the runbook
// engine matches its Trigger against the same string. Defining them once here
// is what keeps "propose a fix" deterministic instead of fuzzy matching.
const (
	SymptomServiceDown  = "service_down"
	SymptomUDPNotListen = "udp_not_listening"
	SymptomCircuitOpen  = "circuit_open"
	SymptomResourceHigh = "resource_pressure"
)

// Event kinds recorded on the timeline.
const (
	KindDetected   = "detected"
	KindAck        = "ack"
	KindTriage     = "triage"
	KindMitigate   = "mitigate"
	KindResolve    = "resolve"
	KindPostmortem = "postmortem"
	KindRunbook    = "runbook"
	KindNote       = "note"
	KindEscalated  = "escalated"
)

// allTransitions is the allowed lifecycle graph. Forward movement is always
// permitted; resolved incidents may be reopened (regression) or closed with a
// postmortem. Postmortem is terminal.
var allTransitions = map[Status][]Status{
	StatusOpen:       {StatusTriage, StatusMitigating, StatusResolved},
	StatusTriage:     {StatusMitigating, StatusResolved},
	StatusMitigating: {StatusResolved, StatusTriage},
	StatusResolved:   {StatusPostmortem, StatusOpen},
	StatusPostmortem: {},
}

// Event is one entry on an incident timeline.
type Event struct {
	Time  time.Time `json:"time"`
	Actor string    `json:"actor"`
	Kind  string    `json:"kind"`
	Note  string    `json:"note"`
}

// Incident is one tracked operational event.
type Incident struct {
	ID          string            `json:"id"`
	Title       string            `json:"title"`
	Service     string            `json:"service"`
	Symptom     string            `json:"symptom,omitempty"`
	Severity    Severity          `json:"severity"`
	Status      Status            `json:"status"`
	DetectedAt  time.Time         `json:"detected_at"`
	AckedAt     *time.Time        `json:"acked_at,omitempty"`
	MitigatedAt *time.Time        `json:"mitigated_at,omitempty"`
	ResolvedAt  *time.Time        `json:"resolved_at,omitempty"`
	MTTRSeconds int64             `json:"mttr_seconds"`
	RunbookID   string            `json:"runbook_id,omitempty"`
	RootCause   string            `json:"root_cause,omitempty"`
	Timeline    []Event           `json:"timeline"`
	Labels      map[string]string `json:"labels,omitempty"`
	UpdatedAt   time.Time         `json:"updated_at"`
}

// Active reports whether the incident is still consuming operator attention.
func (i *Incident) Active() bool {
	return i.Status != StatusResolved && i.Status != StatusPostmortem
}

// Store persists incidents on disk. It is safe for concurrent use.
type Store struct {
	mu        sync.RWMutex
	incidents map[string]*Incident
	dataPath  string
	// maxKeep bounds the number of retained incidents so a noisy service
	// cannot grow the file without bound.
	maxKeep int
}

// NewStore creates a store backed by <dataPath>/incidents.json.
func NewStore(dataPath string) *Store {
	s := &Store{
		incidents: make(map[string]*Incident),
		dataPath:  dataPath,
		maxKeep:   500,
	}
	s.load()
	return s
}

// Trigger describes the detection that opens an incident.
type Trigger struct {
	Title    string
	Service  string
	Symptom  string
	Severity Severity
	Labels   map[string]string
}

// Open creates a new incident in StatusOpen.
func (s *Store) Open(t Trigger) (*Incident, error) {
	title := strings.TrimSpace(t.Title)
	if title == "" {
		return nil, errors.New("事件标题不能为空")
	}
	if len([]rune(title)) > 200 {
		return nil, errors.New("事件标题超出长度限制")
	}
	severity := t.Severity
	if severity != SeverityInfo && severity != SeverityWarning && severity != SeverityCritical {
		severity = SeverityWarning
	}

	now := time.Now().UTC()
	inc := &Incident{
		ID:         "inc-" + now.Format("20060102150405.000000000"),
		Title:      title,
		Service:    strings.TrimSpace(t.Service),
		Symptom:    t.Symptom,
		Severity:   severity,
		Status:     StatusOpen,
		DetectedAt: now,
		Timeline: []Event{{
			Time:  now,
			Actor: "monitor",
			Kind:  KindDetected,
			Note:  title,
		}},
		Labels:    t.Labels,
		UpdatedAt: now,
	}

	s.mu.Lock()
	s.incidents[inc.ID] = inc
	s.pruneLocked()
	s.save()
	copied := inc.clone()
	s.mu.Unlock()
	return copied, nil
}

// OpenForService returns the existing active incident for a service, creating
// one when none exists. Automatic detection runs on every check tick, so this
// de-duplication is what keeps a flapping service from producing hundreds of
// incidents: the first failure opens the record, later failures are recorded
// as an updated symptom instead of a new incident.
func (s *Store) OpenForService(t Trigger) (*Incident, bool, error) {
	service := strings.TrimSpace(t.Service)
	if service != "" {
		s.mu.Lock()
		for _, inc := range s.incidents {
			if inc.Service == service && inc.Active() {
				now := time.Now().UTC()
				if t.Symptom != "" && inc.Symptom != t.Symptom {
					inc.Symptom = t.Symptom
					inc.Timeline = append(inc.Timeline, Event{
						Time: now, Actor: "monitor", Kind: KindDetected, Note: t.Title,
					})
					inc.UpdatedAt = now
					s.save()
				}
				existing := inc.clone()
				s.mu.Unlock()
				return existing, false, nil
			}
		}
		s.mu.Unlock()
	}
	inc, err := s.Open(t)
	return inc, true, err
}

// Get returns a copy of one incident.
func (s *Store) Get(id string) (*Incident, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	inc, ok := s.incidents[id]
	if !ok {
		return nil, fmt.Errorf("事件不存在: %s", id)
	}
	return inc.clone(), nil
}

// List returns incidents filtered by status and service. Both filters are
// optional ("" = no filter). Results are ordered newest first.
func (s *Store) List(status Status, service string) []Incident {
	s.mu.RLock()
	defer s.mu.RUnlock()
	out := make([]Incident, 0, len(s.incidents))
	for _, inc := range s.incidents {
		if status != "" && inc.Status != status {
			continue
		}
		if service != "" && inc.Service != service {
			continue
		}
		out = append(out, *inc.clone())
	}
	sort.Slice(out, func(i, j int) bool { return out[i].DetectedAt.After(out[j].DetectedAt) })
	return out
}

// Transition moves an incident to a new lifecycle status and records who did
// it. Illegal transitions are rejected so the timeline cannot become
// inconsistent (e.g. jumping straight from postmortem back to mitigating).
func (s *Store) Transition(id string, to Status, actor, note string) (*Incident, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	inc, ok := s.incidents[id]
	if !ok {
		return nil, fmt.Errorf("事件不存在: %s", id)
	}
	if inc.Status == to {
		return nil, fmt.Errorf("事件已处于 %s 状态", to)
	}
	if !canTransition(inc.Status, to) {
		return nil, fmt.Errorf("非法状态流转: %s → %s", inc.Status, to)
	}
	if to == StatusPostmortem && strings.TrimSpace(inc.RootCause) == "" {
		return nil, errors.New("关闭复盘前必须填写根因（RootCause）")
	}

	now := time.Now().UTC()
	kind := string(to)
	event := Event{Time: now, Actor: actor, Kind: kind, Note: note}

	switch to {
	case StatusTriage:
		if inc.AckedAt == nil {
			inc.AckedAt = &now
		}
		event.Kind = KindTriage
	case StatusMitigating:
		if inc.AckedAt == nil {
			inc.AckedAt = &now
		}
		if inc.MitigatedAt == nil {
			inc.MitigatedAt = &now
		}
		event.Kind = KindMitigate
	case StatusResolved:
		inc.ResolvedAt = &now
		// MTTR is measured from detection to mitigation when a distinct
		// mitigation timestamp exists, otherwise to resolution.
		end := now
		if inc.MitigatedAt != nil {
			end = *inc.MitigatedAt
		}
		inc.MTTRSeconds = int64(end.Sub(inc.DetectedAt).Seconds())
		if inc.MTTRSeconds < 0 {
			inc.MTTRSeconds = 0
		}
		event.Kind = KindResolve
	case StatusPostmortem:
		event.Kind = KindPostmortem
	case StatusOpen:
		// Reopened after a regression: clear the resolution bookkeeping.
		inc.ResolvedAt = nil
		inc.MTTRSeconds = 0
		event.Kind = KindNote
	}

	inc.Status = to
	inc.UpdatedAt = now
	inc.Timeline = append(inc.Timeline, event)
	s.save()
	return inc.clone(), nil
}

// AppendEvent adds a free-form timeline entry without changing status. Used
// for runbook executions and operator notes so the record stays auditable.
func (s *Store) AppendEvent(id, actor, kind, note string) (*Incident, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	inc, ok := s.incidents[id]
	if !ok {
		return nil, fmt.Errorf("事件不存在: %s", id)
	}
	if kind == "" {
		kind = KindNote
	}
	now := time.Now().UTC()
	inc.Timeline = append(inc.Timeline, Event{Time: now, Actor: actor, Kind: kind, Note: note})
	inc.UpdatedAt = now
	s.save()
	return inc.clone(), nil
}

// SetRootCause records the root cause. This is a prerequisite for closing the
// postmortem, which is why it is a separate call from Transition.
func (s *Store) SetRootCause(id, actor, rootCause string) (*Incident, error) {
	rootCause = strings.TrimSpace(rootCause)
	if rootCause == "" {
		return nil, errors.New("根因不能为空")
	}
	if len([]rune(rootCause)) > 5000 {
		return nil, errors.New("根因内容超出长度限制")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	inc, ok := s.incidents[id]
	if !ok {
		return nil, fmt.Errorf("事件不存在: %s", id)
	}
	now := time.Now().UTC()
	inc.RootCause = rootCause
	inc.UpdatedAt = now
	inc.Timeline = append(inc.Timeline, Event{Time: now, Actor: actor, Kind: KindPostmortem, Note: "根因记录: " + rootCause})
	s.save()
	return inc.clone(), nil
}

// SetRunbook records which runbook was applied to the incident.
func (s *Store) SetRunbook(id, runbookID string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	inc, ok := s.incidents[id]
	if !ok {
		return fmt.Errorf("事件不存在: %s", id)
	}
	inc.RunbookID = runbookID
	inc.UpdatedAt = time.Now().UTC()
	s.save()
	return nil
}

// ServiceStats aggregates incident outcomes for one service.
type ServiceStats struct {
	Service       string  `json:"service"`
	Total         int     `json:"total"`
	Active        int     `json:"active"`
	Resolved      int     `json:"resolved"`
	MTTRAvgSecond float64 `json:"mttr_avg_seconds"`
	MTTRMaxSecond int64   `json:"mttr_max_seconds"`
}

// Stats is the aggregate reliability view of the incident store.
type Stats struct {
	Total          int            `json:"total"`
	Active         int            `json:"active"`
	Resolved       int            `json:"resolved"`
	Critical       int            `json:"critical_active"`
	MTTRAvgSecond  float64        `json:"mttr_avg_seconds"`
	MTTRMedianSec  float64        `json:"mttr_median_seconds"`
	MTTRP90Second  float64        `json:"mttr_p90_seconds"`
	MTTRMaxSecond  int64          `json:"mttr_max_seconds"`
	ByStatus       map[string]int `json:"by_status"`
	BySeverity     map[string]int `json:"by_severity"`
	ByService      []ServiceStats `json:"by_service"`
	MeanTimeToAck  float64        `json:"mtta_seconds"`
}

// Stats computes MTTR aggregates. MTTR (mean time to repair) is the industry
// standard reliability KPI; the median and P90 are reported alongside the mean
// because a single long outage skews the average badly.
func (s *Store) Stats() Stats {
	s.mu.RLock()
	defer s.mu.RUnlock()

	st := Stats{
		ByStatus:   make(map[string]int),
		BySeverity: make(map[string]int),
	}
	var repairs []int64
	var acks []int64
	perService := make(map[string]*ServiceStats)
	perServiceRepairs := make(map[string][]int64)

	for _, inc := range s.incidents {
		st.Total++
		st.ByStatus[string(inc.Status)]++
		st.BySeverity[string(inc.Severity)]++
		svc := perService[inc.Service]
		if svc == nil {
			svc = &ServiceStats{Service: inc.Service}
			perService[inc.Service] = svc
		}
		svc.Total++

		if inc.Active() {
			st.Active++
			svc.Active++
			if inc.Severity == SeverityCritical {
				st.Critical++
			}
			continue
		}
		st.Resolved++
		svc.Resolved++
		if inc.ResolvedAt != nil {
			repairs = append(repairs, inc.MTTRSeconds)
			perServiceRepairs[inc.Service] = append(perServiceRepairs[inc.Service], inc.MTTRSeconds)
			if inc.MTTRSeconds > svc.MTTRMaxSecond {
				svc.MTTRMaxSecond = inc.MTTRSeconds
			}
		}
		if inc.AckedAt != nil {
			acks = append(acks, int64(inc.AckedAt.Sub(inc.DetectedAt).Seconds()))
		}
	}

	if len(repairs) > 0 {
		st.MTTRMaxSecond = maxInt64(repairs)
		st.MTTRAvgSecond = meanInt64(repairs)
		st.MTTRMedianSec = percentile(repairs, 0.50)
		st.MTTRP90Second = percentile(repairs, 0.90)
	}
	if len(acks) > 0 {
		st.MeanTimeToAck = meanInt64(acks)
	}

	services := make([]ServiceStats, 0, len(perService))
	for name, svc := range perService {
		if svcRepairs := perServiceRepairs[name]; len(svcRepairs) > 0 {
			svc.MTTRAvgSecond = meanInt64(svcRepairs)
		}
		services = append(services, *svc)
	}
	sort.Slice(services, func(i, j int) bool { return services[i].Total > services[j].Total })
	st.ByService = services

	return st
}

// ActiveForService reports the open incident for a service, if any.
func (s *Store) ActiveForService(service string) (*Incident, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	var best *Incident
	for _, inc := range s.incidents {
		if inc.Service != service || !inc.Active() {
			continue
		}
		if best == nil || inc.DetectedAt.After(best.DetectedAt) {
			best = inc
		}
	}
	if best == nil {
		return nil, false
	}
	return best.clone(), true
}

func canTransition(from, to Status) bool {
	for _, allowed := range allTransitions[from] {
		if allowed == to {
			return true
		}
	}
	return false
}

// pruneLocked drops the oldest closed incidents once maxKeep is exceeded.
// Active incidents are never dropped.
func (s *Store) pruneLocked() {
	if len(s.incidents) <= s.maxKeep {
		return
	}
	type pair struct {
		id string
		at time.Time
	}
	closed := make([]pair, 0, len(s.incidents))
	for id, inc := range s.incidents {
		if !inc.Active() {
			closed = append(closed, pair{id: id, at: inc.DetectedAt})
		}
	}
	sort.Slice(closed, func(i, j int) bool { return closed[i].at.Before(closed[j].at) })
	excess := len(s.incidents) - s.maxKeep
	for i := 0; i < excess && i < len(closed); i++ {
		delete(s.incidents, closed[i].id)
	}
}

func (i *Incident) clone() *Incident {
	copied := *i
	copied.Timeline = append([]Event(nil), i.Timeline...)
	if i.Labels != nil {
		labels := make(map[string]string, len(i.Labels))
		for k, v := range i.Labels {
			labels[k] = v
		}
		copied.Labels = labels
	}
	return &copied
}

type persisted struct {
	Incidents map[string]*Incident `json:"incidents"`
}

func (s *Store) load() {
	content, err := os.ReadFile(filepath.Join(s.dataPath, "incidents.json"))
	if err != nil {
		return
	}
	var saved persisted
	if json.Unmarshal(content, &saved) == nil && saved.Incidents != nil {
		s.incidents = saved.Incidents
	}
}

func (s *Store) save() {
	if s.dataPath == "" {
		return
	}
	_ = os.MkdirAll(s.dataPath, 0750)
	content, err := json.MarshalIndent(persisted{Incidents: s.incidents}, "", "  ")
	if err == nil {
		_ = os.WriteFile(filepath.Join(s.dataPath, "incidents.json"), content, 0600)
	}
}

func percentile(values []int64, p float64) float64 {
	if len(values) == 0 {
		return 0
	}
	sorted := append([]int64(nil), values...)
	sort.Slice(sorted, func(i, j int) bool { return sorted[i] < sorted[j] })
	if len(sorted) == 1 {
		return float64(sorted[0])
	}
	idx := p * float64(len(sorted)-1)
	lower := int(idx)
	upper := lower + 1
	if upper >= len(sorted) {
		return float64(sorted[len(sorted)-1])
	}
	frac := idx - float64(lower)
	return float64(sorted[lower])*(1-frac) + float64(sorted[upper])*frac
}

func meanInt64(values []int64) float64 {
	if len(values) == 0 {
		return 0
	}
	var sum int64
	for _, v := range values {
		sum += v
	}
	return float64(sum) / float64(len(values))
}

func maxInt64(values []int64) int64 {
	var best int64
	for _, v := range values {
		if v > best {
			best = v
		}
	}
	return best
}