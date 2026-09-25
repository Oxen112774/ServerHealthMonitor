package web

import (
	"encoding/json"
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"

	"github.com/Oxen112774/ServerHealthMonitor/internal/incident"
	"github.com/Oxen112774/ServerHealthMonitor/internal/notifier"
	"github.com/Oxen112774/ServerHealthMonitor/internal/runbook"
)

// actor resolves who performed an action. The authenticated Basic Auth user is
// authoritative; an unauthenticated deployment (auth disabled) degrades to a
// literal marker rather than an empty audit field.
func (h *Handler) actor(r *http.Request) string {
	if user, _, ok := r.BasicAuth(); ok && strings.TrimSpace(user) != "" {
		return user
	}
	if h.authUser != "" {
		return h.authUser
	}
	return "operator"
}

func writeJSON(w http.ResponseWriter, status int, payload interface{}) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(payload)
}

func (h *Handler) requireIncidents(w http.ResponseWriter) bool {
	if h.incidents == nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]interface{}{
			"status":  "unavailable",
			"message": "事件存储未启用",
		})
		return false
	}
	return true
}

// handleIncidentList returns incidents, optionally filtered by
// ?status=open&service=scpsl-1 and limited by ?limit=N.
func (h *Handler) handleIncidentList(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, map[string]interface{}{"status": "error", "message": "method must be GET"})
		return
	}
	if !h.requireIncidents(w) {
		return
	}
	status := incident.Status(strings.TrimSpace(r.URL.Query().Get("status")))
	service := strings.TrimSpace(r.URL.Query().Get("service"))
	items := h.incidents.List(status, service)

	limit := 50
	if raw := strings.TrimSpace(r.URL.Query().Get("limit")); raw != "" {
		if n, err := strconv.Atoi(raw); err == nil && n > 0 && n <= 500 {
			limit = n
		}
	}
	truncated := false
	if len(items) > limit {
		items = items[:limit]
		truncated = true
	}
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"count":       len(items),
		"truncated":   truncated,
		"incidents":   items,
		"server_time": time.Now().Format(time.RFC3339),
	})
}

// handleIncidentStats returns MTTR aggregates.
func (h *Handler) handleIncidentStats(w http.ResponseWriter, r *http.Request) {
	if !h.requireIncidents(w) {
		return
	}
	writeJSON(w, http.StatusOK, h.incidents.Stats())
}

// handleIncidentItem dispatches /api/incidents/<id>[/<action>].
func (h *Handler) handleIncidentItem(w http.ResponseWriter, r *http.Request) {
	if !h.requireIncidents(w) {
		return
	}
	rest := strings.Trim(strings.TrimPrefix(r.URL.Path, "/api/incidents/"), "/")
	if rest == "" {
		writeJSON(w, http.StatusNotFound, map[string]interface{}{"status": "error", "message": "缺少事件 ID"})
		return
	}
	parts := strings.SplitN(rest, "/", 2)
	id := parts[0]
	action := ""
	if len(parts) == 2 {
		action = parts[1]
	}

	switch {
	case action == "" && r.Method == http.MethodGet:
		inc, err := h.incidents.Get(id)
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]interface{}{"status": "error", "message": err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, inc)
	case action == "runbooks" && r.Method == http.MethodGet:
		h.handleIncidentProposals(w, id)
	case r.Method == http.MethodPost && (action == "ack" || action == "triage" || action == "mitigate" ||
		action == "resolve" || action == "postmortem" || action == "note" || action == "rootcause"):
		h.handleIncidentTransition(w, r, id, action)
	default:
		writeJSON(w, http.StatusMethodNotAllowed, map[string]interface{}{
			"status":  "error",
			"message": "不支持的方法或动作",
		})
	}
}

func (h *Handler) handleIncidentProposals(w http.ResponseWriter, id string) {
	inc, err := h.incidents.Get(id)
	if err != nil {
		writeJSON(w, http.StatusNotFound, map[string]interface{}{"status": "error", "message": err.Error()})
		return
	}
	if h.runbooks == nil {
		writeJSON(w, http.StatusOK, map[string]interface{}{
			"incident_id": id,
			"proposals":   []runbook.Proposal{},
			"message":     "Runbook 引擎未启用",
		})
		return
	}
	proposals := h.runbooks.Propose(inc.Service, inc.Symptom)
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"incident_id": id,
		"service":     inc.Service,
		"symptom":     inc.Symptom,
		"proposals":   proposals,
	})
}

type incidentTransitionBody struct {
	Note      string `json:"note"`
	Actor     string `json:"actor"`
	RootCause string `json:"root_cause"`
}

func (h *Handler) handleIncidentTransition(w http.ResponseWriter, r *http.Request, id, action string) {
	var body incidentTransitionBody
	if r.Body != nil {
		_ = json.NewDecoder(r.Body).Decode(&body)
	}
	actor := strings.TrimSpace(body.Actor)
	if actor == "" {
		actor = h.actor(r)
	}

	if action == "note" {
		inc, err := h.incidents.AppendEvent(id, actor, "note", strings.TrimSpace(body.Note))
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]interface{}{"status": "error", "message": err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, inc)
		return
	}

	if action == "rootcause" {
		inc, err := h.incidents.SetRootCause(id, actor, body.RootCause)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]interface{}{"status": "error", "message": err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, inc)
		return
	}

	target := incident.Status(action)
	inc, err := h.incidents.Transition(id, target, actor, strings.TrimSpace(body.Note))
	if err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]interface{}{"status": "error", "message": err.Error()})
		return
	}
	writeJSON(w, http.StatusOK, inc)
}

// handleRunbookList returns the catalog with its current autonomy state.
func (h *Handler) handleRunbookList(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		writeJSON(w, http.StatusMethodNotAllowed, map[string]interface{}{"status": "error", "message": "method must be GET"})
		return
	}
	if h.runbooks == nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]interface{}{"status": "unavailable", "message": "Runbook 引擎未启用"})
		return
	}
	books := h.runbooks.List()
	writeJSON(w, http.StatusOK, map[string]interface{}{
		"count":    len(books),
		"runbooks": books,
		"policy_note": "所有 Runbook 默认仅建议（recommend）；只有被显式批准（approved）的 Runbook 才能执行，且需通过风险与影响半径校验。",
	})
}

type runbookActionBody struct {
	Actor      string `json:"actor"`
	IncidentID string `json:"incident_id"`
	Service    string `json:"service"`
	Port       int    `json:"port"`
	Confirm    string `json:"confirm"`
}

// handleRunbookItem dispatches /api/runbooks/<id>[/approve|revoke|execute].
func (h *Handler) handleRunbookItem(w http.ResponseWriter, r *http.Request) {
	if h.runbooks == nil {
		writeJSON(w, http.StatusServiceUnavailable, map[string]interface{}{"status": "unavailable", "message": "Runbook 引擎未启用"})
		return
	}
	rest := strings.Trim(strings.TrimPrefix(r.URL.Path, "/api/runbooks/"), "/")
	if rest == "" {
		writeJSON(w, http.StatusNotFound, map[string]interface{}{"status": "error", "message": "缺少 Runbook ID"})
		return
	}
	parts := strings.SplitN(rest, "/", 2)
	id := parts[0]
	action := ""
	if len(parts) == 2 {
		action = parts[1]
	}

	if action == "" && r.Method == http.MethodGet {
		rb, err := h.runbooks.Get(id)
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]interface{}{"status": "error", "message": err.Error()})
			return
		}
		writeJSON(w, http.StatusOK, rb)
		return
	}
	if r.Method != http.MethodPost {
		writeJSON(w, http.StatusMethodNotAllowed, map[string]interface{}{"status": "error", "message": "method must be POST"})
		return
	}

	var body runbookActionBody
	if r.Body != nil {
		_ = json.NewDecoder(r.Body).Decode(&body)
	}
	actor := strings.TrimSpace(body.Actor)
	if actor == "" {
		actor = h.actor(r)
	}

	switch action {
	case "approve":
		rb, err := h.runbooks.Approve(id, actor)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]interface{}{"status": "error", "message": err.Error()})
			return
		}
		if h.notifier != nil {
			h.pushRunbookNotice("Runbook 授权变更",
				fmt.Sprintf("%s 已批准 Runbook「%s」为可执行（批准人 %s）", actor, rb.Name, rb.ApprovedBy))
		}
		writeJSON(w, http.StatusOK, rb)
	case "revoke":
		rb, err := h.runbooks.Revoke(id, actor)
		if err != nil {
			writeJSON(w, http.StatusBadRequest, map[string]interface{}{"status": "error", "message": err.Error()})
			return
		}
		if h.notifier != nil {
			h.pushRunbookNotice("Runbook 授权变更",
				fmt.Sprintf("%s 已撤销 Runbook「%s」的执行授权，恢复为仅建议", actor, rb.Name))
		}
		writeJSON(w, http.StatusOK, rb)
	case "execute":
		h.handleRunbookExecute(w, r, id, actor, body)
	default:
		writeJSON(w, http.StatusNotFound, map[string]interface{}{"status": "error", "message": "不支持的动作: " + action})
	}
}

func (h *Handler) handleRunbookExecute(w http.ResponseWriter, r *http.Request, id, actor string, body runbookActionBody) {
	req := runbook.Request{
		RunbookID:  id,
		IncidentID: strings.TrimSpace(body.IncidentID),
		Actor:      actor,
		Service:    strings.TrimSpace(body.Service),
		Port:       body.Port,
	}

	// When an incident is referenced, the target instance is taken from the
	// incident itself so the operator cannot silently retarget remediation.
	if req.IncidentID != "" {
		if h.incidents == nil {
			writeJSON(w, http.StatusBadRequest, map[string]interface{}{"status": "error", "message": "事件存储未启用，无法按事件执行"})
			return
		}
		inc, err := h.incidents.Get(req.IncidentID)
		if err != nil {
			writeJSON(w, http.StatusNotFound, map[string]interface{}{"status": "error", "message": err.Error()})
			return
		}
		if req.Service == "" {
			req.Service = inc.Service
		}
		if req.Port == 0 {
			req.Port = h.portForService(inc.Service)
		}
		if inc.Service != "" && req.Service != inc.Service {
			writeJSON(w, http.StatusBadRequest, map[string]interface{}{
				"status":  "error",
				"message": fmt.Sprintf("目标服务 %s 与事件所属服务 %s 不一致", req.Service, inc.Service),
			})
			return
		}
		// An incident in a closed state should not be quietly re-remediated.
		if !inc.Active() {
			writeJSON(w, http.StatusBadRequest, map[string]interface{}{
				"status":  "error",
				"message": "该事件已结束，如需再次处置请先重新打开或新建事件",
			})
			return
		}
	}
	if req.Service != "" && req.Port == 0 {
		req.Port = h.portForService(req.Service)
	}

	// Irreversible runbooks require an explicit acknowledgement, mirroring the
	// confirm="ALL" guard used for bulk circuit resets.
	if rb, err := h.runbooks.Get(id); err == nil && !rb.Reversible {
		if !strings.EqualFold(strings.TrimSpace(body.Confirm), "EXECUTE") {
			writeJSON(w, http.StatusBadRequest, map[string]interface{}{
				"status":  "confirmation_required",
				"message": "该 Runbook 标记为不可逆操作：请在请求体提交 confirm=\"EXECUTE\" 后重试。",
			})
			return
		}
	}

	result, err := h.runbooks.Execute(r.Context(), req)
	if err != nil {
		// A refused execution is not a server fault: it means the autonomy
		// brake is engaged, which the operator must see explicitly.
		writeJSON(w, http.StatusForbidden, map[string]interface{}{
			"status":  "refused",
			"message": err.Error(),
		})
		return
	}

	if h.notifier != nil && req.IncidentID != "" {
		sev := notifier.SeverityRecovery
		outcome := "成功"
		if !result.OK {
			sev = notifier.SeverityCritical
			outcome = "失败: " + result.Error
		}
		h.notifier.Push(notifier.Alert{
			Time:  time.Now().Format("2006-01-02 15:04:05"),
			Type:  sev,
			Title: "Runbook 执行结果",
			Message: fmt.Sprintf("%s 执行 Runbook %s（事件 %s），结果: %s",
				actor, id, req.IncidentID, outcome),
		})
	}
	writeJSON(w, http.StatusOK, result)
}

// portForService resolves the UDP port of a monitored instance, so a runbook
// step does not need the caller to know it.
func (h *Handler) portForService(service string) int {
	_, instances := h.collector.Get()
	for _, inst := range instances {
		if inst.Service == service {
			return inst.Port
		}
	}
	return 0
}

// pushRunbookNotice records an authorization or policy change on the alert
// channels so a granted or revoked automation authority is never a silent
// event.
func (h *Handler) pushRunbookNotice(title, message string) {
	if h.notifier == nil {
		return
	}
	h.notifier.Push(notifier.Alert{
		Time:    time.Now().Format("2006-01-02 15:04:05"),
		Type:    notifier.SeverityWarning,
		Title:   title,
		Message: message,
	})
}