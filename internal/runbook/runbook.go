// Package runbook implements an auditable remediation engine for the
// monitoring agent.
//
// Design constraints (deliberate, security-driven):
//
//  1. Steps never carry a shell string. Each step names a whitelisted action
//     and passes structured arguments; the engine only runs actions that were
//     registered at construction time. There is no way to express "run
//     arbitrary command" through a runbook, so a compromised control plane
//     cannot turn this into remote code execution.
//  2. Autonomy defaults to recommend-only. A runbook must be explicitly
//     approved by an operator before Execute will accept it, mirroring the
//     graduated-autonomy model used by AIOps remediation platforms: suggest
//     first, automate only after the suggestion has proven reliable.
//  3. Every execution is gated on risk/blast-radius policy and is reported to
//     an audit hook so the incident timeline records who ran what and when.
package runbook

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Autonomy is the trust level granted to a runbook.
type Autonomy string

const (
	// AutonomyRecommend means the runbook may only be proposed, never executed
	// automatically. This is the default for every runbook.
	AutonomyRecommend Autonomy = "recommend"
	// AutonomyApproved means an operator has explicitly authorised execution.
	AutonomyApproved Autonomy = "approved"
)

// Action is a whitelisted remediation primitive.
type Action string

const (
	// ActionServiceRestart restarts one monitored systemd unit.
	ActionServiceRestart Action = "service.restart"
	// ActionServiceStatus reads `systemctl status` for one unit (read-only).
	ActionServiceStatus Action = "service.status"
	// ActionServiceLogs reads the last N journal lines for one unit (read-only).
	ActionServiceLogs Action = "service.logs"
	// ActionUDPCheck verifies that a UDP port is listening (read-only).
	ActionUDPCheck Action = "udp.check"
	// ActionCircuitClear resets the auto-remediation circuit breaker.
	ActionCircuitClear Action = "circuit.clear"
	// ActionAlertNotify pushes an operator-facing notification.
	ActionAlertNotify Action = "alert.notify"
)

// readOnlyActions is the authoritative classification of which primitives are
// side-effect free. A step cannot claim ReadOnly for a mutating action.
var readOnlyActions = map[Action]bool{
	ActionServiceStatus: true,
	ActionServiceLogs:   true,
	ActionUDPCheck:      true,
}

// requiredArgs lists the mandatory arguments per action. Validated before any
// step runs so a malformed runbook fails fast instead of half-executing.
var requiredArgs = map[Action][]string{
	ActionServiceRestart: {"service"},
	ActionServiceStatus:  {"service"},
	ActionServiceLogs:    {"service"},
	ActionUDPCheck:       {"port"},
	ActionCircuitClear:   {},
	ActionAlertNotify:    {"message"},
}

// validAction reports whether an action name is a known primitive.
func validAction(a Action) bool {
	_, ok := requiredArgs[a]
	return ok
}

// Step is one action invocation inside a runbook.
type Step struct {
	Name           string            `json:"name"`
	Action         Action            `json:"action"`
	Args           map[string]string `json:"args,omitempty"`
	TimeoutSeconds int               `json:"timeout_seconds,omitempty"`
	ReadOnly       bool              `json:"read_only"`
}

// Runbook is a named remediation procedure.
type Runbook struct {
	ID          string     `json:"id"`
	Name        string     `json:"name"`
	Description string     `json:"description"`
	// Trigger matches the symptom keyword reported by the monitor
	// (e.g. "service_down", "udp_not_listening", "circuit_open").
	Trigger string `json:"trigger"`
	// Services restricts the runbook to specific instances. Empty = any.
	Services    []string   `json:"services,omitempty"`
	Steps       []Step     `json:"steps"`
	Autonomy    Autonomy   `json:"autonomy"`
	ApprovedBy  string     `json:"approved_by,omitempty"`
	ApprovedAt  *time.Time `json:"approved_at,omitempty"`
	Risk        string     `json:"risk"`         // low / medium / high
	Reversible  bool       `json:"reversible"`   // can the effect be undone?
	BlastRadius int        `json:"blast_radius"` // max instances affected
}

// Approved reports whether the runbook may be executed.
func (r *Runbook) Approved() bool {
	return r.Autonomy == AutonomyApproved && r.ApprovedBy != ""
}

// AppliesTo reports whether this runbook targets the given service.
func (r *Runbook) AppliesTo(service string) bool {
	if len(r.Services) == 0 {
		return true
	}
	for _, s := range r.Services {
		if s == service {
			return true
		}
	}
	return false
}

// Proposal is a runbook suggested for an active symptom.
type Proposal struct {
	RunbookID   string   `json:"runbook_id"`
	Name        string   `json:"name"`
	Description string   `json:"description"`
	Service     string   `json:"service"`
	Trigger     string   `json:"trigger"`
	Autonomy    Autonomy `json:"autonomy"`
	Executable  bool     `json:"executable"`
	Reason      string   `json:"reason,omitempty"`
	Risk        string   `json:"risk"`
	Reversible  bool     `json:"reversible"`
	BlastRadius int      `json:"blast_radius"`
	Steps       []string `json:"steps"`
}

// ActionFunc executes one whitelisted primitive.
type ActionFunc func(ctx context.Context, args map[string]string) (string, error)

// AuditFunc records a runbook execution in the incident timeline. It is
// injected by the caller so this package stays independent of the incident
// store.
type AuditFunc func(runbookID, incidentID, actor, kind, note string)

// Request describes one execution request. Service and Port are substituted
// into step arguments that use the ${service} / ${port} placeholders, so a
// single runbook definition can be applied to any instance.
type Request struct {
	RunbookID  string `json:"runbook_id"`
	IncidentID string `json:"incident_id,omitempty"`
	Actor      string `json:"actor"`
	Service    string `json:"service,omitempty"`
	Port       int    `json:"port,omitempty"`
}

// StepResult is the outcome of one executed step.
type StepResult struct {
	Name       string `json:"name"`
	Action     Action `json:"action"`
	Output     string `json:"output,omitempty"`
	Error      string `json:"error,omitempty"`
	DurationMs int64  `json:"duration_ms"`
}

// Result is the outcome of a full runbook execution.
type Result struct {
	RunbookID  string       `json:"runbook_id"`
	IncidentID string       `json:"incident_id,omitempty"`
	Actor      string       `json:"actor"`
	OK         bool         `json:"ok"`
	Steps      []StepResult `json:"steps"`
	StartedAt  time.Time    `json:"started_at"`
	FinishedAt time.Time    `json:"finished_at"`
	Error      string       `json:"error,omitempty"`
}

// Policy bounds what the engine will accept.
type Policy struct {
	// MaxBlastRadius is the largest BlastRadius value the engine will execute.
	MaxBlastRadius int
	// AllowHighRisk permits executing runbooks marked risk=high.
	AllowHighRisk bool
}

// DefaultPolicy is intentionally conservative: at most 2 instances, no
// high-risk automation.
func DefaultPolicy() Policy {
	return Policy{MaxBlastRadius: 2, AllowHighRisk: false}
}

// Engine holds the runbook catalog and executes approved procedures.
type Engine struct {
	mu       sync.RWMutex
	books    map[string]*Runbook
	order    []string // stable listing order
	actions  map[Action]ActionFunc
	policy   Policy
	dataPath string
	audit    AuditFunc
}

// NewEngine builds an engine seeded with the built-in catalog and backed by
// <dataPath>/runbook_approvals.json for persisted approvals. Pass an empty
// dataPath to keep approvals in memory only.
func NewEngine(dataPath string, builtins []Runbook, actions map[Action]ActionFunc) *Engine {
	e := &Engine{
		books:    make(map[string]*Runbook, len(builtins)),
		actions:  actions,
		policy:   DefaultPolicy(),
		dataPath: dataPath,
	}
	for _, rb := range builtins {
		rb.Autonomy = AutonomyRecommend
		rb.ApprovedBy = ""
		rb.ApprovedAt = nil
		e.books[rb.ID] = &rb
		e.order = append(e.order, rb.ID)
	}
	e.loadApprovals()
	return e
}

// SetPolicy overrides the execution policy.
func (e *Engine) SetPolicy(p Policy) {
	e.mu.Lock()
	defer e.mu.Unlock()
	if p.MaxBlastRadius > 0 {
		e.policy.MaxBlastRadius = p.MaxBlastRadius
	}
	e.policy.AllowHighRisk = p.AllowHighRisk
}

// SetAuditHook installs the incident-timeline recorder.
func (e *Engine) SetAuditHook(fn AuditFunc) {
	e.mu.Lock()
	defer e.mu.Unlock()
	e.audit = fn
}

// List returns the catalog in registration order.
func (e *Engine) List() []Runbook {
	e.mu.RLock()
	defer e.mu.RUnlock()
	out := make([]Runbook, 0, len(e.order))
	for _, id := range e.order {
		if rb, ok := e.books[id]; ok {
			out = append(out, *rb.clone())
		}
	}
	return out
}

// Get returns one runbook.
func (e *Engine) Get(id string) (*Runbook, error) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	rb, ok := e.books[id]
	if !ok {
		return nil, fmt.Errorf("Runbook 不存在: %s", id)
	}
	return rb.clone(), nil
}

// Approve upgrades a runbook to approved autonomy, recording the operator.
// This is the single point where automation authority is granted, which is why
// it is deliberately a separate, explicit call.
func (e *Engine) Approve(id, actor string) (*Runbook, error) {
	actor = strings.TrimSpace(actor)
	if actor == "" {
		return nil, errors.New("批准人不能为空")
	}
	e.mu.Lock()
	defer e.mu.Unlock()
	rb, ok := e.books[id]
	if !ok {
		return nil, fmt.Errorf("Runbook 不存在: %s", id)
	}
	if !e.policy.AllowHighRisk && rb.Risk == "high" {
		return nil, fmt.Errorf("策略禁止批准高风险 Runbook（%s）；请先在配置中显式放开", id)
	}
	now := time.Now().UTC()
	rb.Autonomy = AutonomyApproved
	rb.ApprovedBy = actor
	rb.ApprovedAt = &now
	e.saveApprovals()
	return rb.clone(), nil
}

// Revoke returns a runbook to recommend-only.
func (e *Engine) Revoke(id, actor string) (*Runbook, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	rb, ok := e.books[id]
	if !ok {
		return nil, fmt.Errorf("Runbook 不存在: %s", id)
	}
	if actor == "" {
		actor = "unknown"
	}
	rb.Autonomy = AutonomyRecommend
	rb.ApprovedBy = ""
	rb.ApprovedAt = nil
	e.saveApprovals()
	if e.audit != nil {
		e.audit(id, "", actor, "runbook", "撤销执行授权，恢复为仅建议")
	}
	return rb.clone(), nil
}

// Propose returns the runbooks that match a symptom for a service, ordered so
// executable (approved) suggestions come first. Read-only runbooks are always
// reported as executable because gathering diagnostics carries no risk.
func (e *Engine) Propose(service, symptom string) []Proposal {
	e.mu.RLock()
	defer e.mu.RUnlock()

	var out []Proposal
	for _, id := range e.order {
		rb := e.books[id]
		if rb == nil || !rb.AppliesTo(service) {
			continue
		}
		if rb.Trigger != "" && symptom != "" && !strings.EqualFold(rb.Trigger, symptom) {
			continue
		}
		p := Proposal{
			RunbookID:   rb.ID,
			Name:        rb.Name,
			Description: rb.Description,
			Service:     service,
			Trigger:     rb.Trigger,
			Autonomy:    rb.Autonomy,
			Risk:        rb.Risk,
			Reversible:  rb.Reversible,
			BlastRadius: rb.BlastRadius,
		}
		for _, s := range rb.Steps {
			p.Steps = append(p.Steps, string(s.Action)+"("+s.Name+")")
		}
		p.Executable, p.Reason = e.evaluateLocked(rb, service)
		out = append(out, p)
	}
	sort.SliceStable(out, func(i, j int) bool { return out[i].Executable && !out[j].Executable })
	return out
}

// evaluateLocked applies every gate and returns the first blocking reason.
func (e *Engine) evaluateLocked(rb *Runbook, service string) (bool, string) {
	if service != "" && !rb.AppliesTo(service) {
		return false, "该 Runbook 未覆盖此服务"
	}
	for _, s := range rb.Steps {
		if !validAction(s.Action) {
			return false, fmt.Sprintf("步骤 %s 使用了非白名单动作 %s", s.Name, s.Action)
		}
		if _, ok := e.actions[s.Action]; !ok {
			return false, fmt.Sprintf("动作 %s 未在本机注册", s.Action)
		}
	}
	mutating := false
	for _, s := range rb.Steps {
		if !readOnlyActions[s.Action] {
			mutating = true
		}
	}
	if !mutating {
		return true, "" // diagnostics-only, always safe to run
	}
	if !rb.Approved() {
		return false, "仅建议模式：需管理员批准该 Runbook 后才能执行"
	}
	if rb.BlastRadius > e.policy.MaxBlastRadius {
		return false, fmt.Sprintf("影响半径 %d 超出策略上限 %d", rb.BlastRadius, e.policy.MaxBlastRadius)
	}
	if rb.Risk == "high" && !e.policy.AllowHighRisk {
		return false, "策略禁止执行高风险 Runbook"
	}
	return true, ""
}

// Execute runs an approved runbook. It refuses, with an explicit error, when
// the runbook is still in recommend-only mode or violates the policy — a
// silent no-op would hide that the automation brake is engaged.
func (e *Engine) Execute(ctx context.Context, req Request) (Result, error) {
	id := req.RunbookID
	e.mu.RLock()
	rb, ok := e.books[id]
	var snapshot *Runbook
	if ok {
		snapshot = rb.clone()
	}
	actions := e.actions
	audit := e.audit
	if ok {
		if allowed, reason := e.evaluateLocked(rb, req.Service); !allowed {
			e.mu.RUnlock()
			return Result{}, errors.New(reason)
		}
	}
	e.mu.RUnlock()

	if !ok {
		return Result{}, fmt.Errorf("Runbook 不存在: %s", id)
	}
	if req.Actor == "" {
		return Result{}, errors.New("执行人不能为空")
	}

	for i := range snapshot.Steps {
		snapshot.Steps[i].Args = substitute(snapshot.Steps[i].Args, req)
	}

	result := Result{
		RunbookID:  snapshot.ID,
		IncidentID: req.IncidentID,
		Actor:      req.Actor,
		StartedAt:  time.Now().UTC(),
	}
	// Record intent before the first side effect so an interrupted execution
	// still leaves a trace in the incident timeline.
	if audit != nil {
		audit(snapshot.ID, req.IncidentID, req.Actor, "runbook",
			fmt.Sprintf("开始执行 Runbook %s（对象 %s:%d，风险 %s，可逆 %v，影响半径 %d），共 %d 步",
				snapshot.Name, req.Service, req.Port, snapshot.Risk, snapshot.Reversible, snapshot.BlastRadius, len(snapshot.Steps)))
	}

	for _, step := range snapshot.Steps {
		if err := ctx.Err(); err != nil {
			result.Error = "执行被取消: " + err.Error()
			result.OK = false
			break
		}
		if miss := missingArgs(step); miss != "" {
			result.Error = fmt.Sprintf("步骤 %s 缺少必需参数 %s", step.Name, miss)
			result.OK = false
			break
		}
		fn, ok := actions[step.Action]
		if !ok {
			result.Error = fmt.Sprintf("动作未注册: %s", step.Action)
			result.OK = false
			break
		}
		timeout := step.TimeoutSeconds
		if timeout <= 0 {
			timeout = 60
		}
		if timeout > 300 {
			timeout = 300
		}
		stepCtx, cancel := context.WithTimeout(ctx, time.Duration(timeout)*time.Second)
		started := time.Now()
		out, err := fn(stepCtx, step.Args)
		cancel()

		sr := StepResult{
			Name:       step.Name,
			Action:     step.Action,
			Output:     truncate(out, 4000),
			DurationMs: time.Since(started).Milliseconds(),
		}
		if err != nil {
			sr.Error = err.Error()
			result.Steps = append(result.Steps, sr)
			result.OK = false
			result.Error = fmt.Sprintf("步骤 %s 失败: %v", step.Name, err)
			break
		}
		result.Steps = append(result.Steps, sr)
	}

	if result.Error == "" {
		result.OK = true
	}
	result.FinishedAt = time.Now().UTC()

	if audit != nil {
		note := "Runbook " + snapshot.Name + " 执行完成，结果: "
		if result.OK {
			note += "成功"
		} else {
			note += "失败: " + result.Error
		}
		audit(snapshot.ID, req.IncidentID, req.Actor, "runbook", note)
	}
	return result, nil
}

// substitute expands ${service} and ${port} in step arguments. Unknown
// placeholders are left untouched so a typo is visible in the output rather
// than silently becoming an empty string.
func substitute(args map[string]string, req Request) map[string]string {
	if args == nil {
		return nil
	}
	out := make(map[string]string, len(args))
	for k, v := range args {
		v = strings.ReplaceAll(v, "${service}", req.Service)
		v = strings.ReplaceAll(v, "${port}", strconv.Itoa(req.Port))
		out[k] = v
	}
	return out
}

// ValidateCatalog rejects runbooks that reference unknown actions or declare
// inconsistent read-only flags. Called on the built-in catalog as a self-check
// so a coding mistake surfaces at construction instead of at 3am.
func ValidateCatalog(books []Runbook) error {
	for _, rb := range books {
		if strings.TrimSpace(rb.ID) == "" || strings.TrimSpace(rb.Name) == "" {
			return errors.New("Runbook 必须包含 id 与 name")
		}
		if len(rb.Steps) == 0 {
			return fmt.Errorf("Runbook %s 未定义任何步骤", rb.ID)
		}
		for _, s := range rb.Steps {
			if !validAction(s.Action) {
				return fmt.Errorf("Runbook %s 步骤 %s 使用了非白名单动作 %s", rb.ID, s.Name, s.Action)
			}
			if s.ReadOnly && !readOnlyActions[s.Action] {
				return fmt.Errorf("Runbook %s 步骤 %s 将写操作标记为只读", rb.ID, s.Name)
			}
			if miss := missingArgs(s); miss != "" {
				return fmt.Errorf("Runbook %s 步骤 %s 缺少参数 %s", rb.ID, s.Name, miss)
			}
		}
		if rb.Risk != "low" && rb.Risk != "medium" && rb.Risk != "high" {
			return fmt.Errorf("Runbook %s 的 risk 必须是 low/medium/high", rb.ID)
		}
	}
	return nil
}

func missingArgs(step Step) string {
	for _, key := range requiredArgs[step.Action] {
		if strings.TrimSpace(step.Args[key]) == "" {
			return key
		}
	}
	return ""
}

// ArgInt reads an integer argument with a default.
func ArgInt(args map[string]string, key string, def int) int {
	raw, ok := args[key]
	if !ok {
		return def
	}
	n, err := strconv.Atoi(strings.TrimSpace(raw))
	if err != nil {
		return def
	}
	return n
}

func truncate(s string, max int) string {
	s = strings.TrimSpace(s)
	if len(s) <= max {
		return s
	}
	return s[:max] + "…(截断)"
}

func (r *Runbook) clone() *Runbook {
	copied := *r
	copied.Services = append([]string(nil), r.Services...)
	copied.Steps = make([]Step, len(r.Steps))
	for i, s := range r.Steps {
		step := s
		if s.Args != nil {
			args := make(map[string]string, len(s.Args))
			for k, v := range s.Args {
				args[k] = v
			}
			step.Args = args
		}
		copied.Steps[i] = step
	}
	return &copied
}

type approval struct {
	ID         string     `json:"id"`
	Autonomy   Autonomy   `json:"autonomy"`
	ApprovedBy string     `json:"approved_by"`
	ApprovedAt *time.Time `json:"approved_at,omitempty"`
}

type approvalsFile struct {
	Approvals []approval `json:"approvals"`
}

func (e *Engine) loadApprovals() {
	if e.dataPath == "" {
		return
	}
	content, err := os.ReadFile(filepath.Join(e.dataPath, "runbook_approvals.json"))
	if err != nil {
		return
	}
	var saved approvalsFile
	if json.Unmarshal(content, &saved) != nil {
		return
	}
	for _, a := range saved.Approvals {
		rb, ok := e.books[a.ID]
		if !ok {
			continue
		}
		rb.Autonomy = a.Autonomy
		rb.ApprovedBy = a.ApprovedBy
		rb.ApprovedAt = a.ApprovedAt
	}
}

func (e *Engine) saveApprovals() {
	if e.dataPath == "" {
		return
	}
	var out approvalsFile
	for _, id := range e.order {
		rb := e.books[id]
		if rb == nil {
			continue
		}
		out.Approvals = append(out.Approvals, approval{
			ID:         rb.ID,
			Autonomy:   rb.Autonomy,
			ApprovedBy: rb.ApprovedBy,
			ApprovedAt: rb.ApprovedAt,
		})
	}
	_ = os.MkdirAll(e.dataPath, 0750)
	content, err := json.MarshalIndent(out, "", "  ")
	if err == nil {
		_ = os.WriteFile(filepath.Join(e.dataPath, "runbook_approvals.json"), content, 0600)
	}
}