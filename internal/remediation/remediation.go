// Package remediation provides the concrete implementations behind the
// runbook action whitelist.
//
// Every action is a fixed argv invocation — never a shell string — and every
// argument that names a systemd unit is validated twice: against a strict
// character allow-list (so it cannot be reinterpreted as a flag) and against
// the set of instances the monitor actually watches (so a runbook cannot be
// pointed at an unrelated unit by a compromised control plane).
package remediation

import (
	"context"
	"fmt"
	"os/exec"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/Oxen112774/ServerHealthMonitor/internal/collector"
	"github.com/Oxen112774/ServerHealthMonitor/internal/monitor"
	"github.com/Oxen112774/ServerHealthMonitor/internal/notifier"
	"github.com/Oxen112774/ServerHealthMonitor/internal/runbook"
)

// Deps are the live agent components the actions operate on.
type Deps struct {
	Monitor  *monitor.Monitor
	Notifier *notifier.Notifier
}

// unitNameRe matches valid systemd unit names. The leading character class
// deliberately excludes '-', so an argument can never be read as a CLI flag.
var unitNameRe = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9_.@:-]{0,127}$`)

// Providers builds the action table handed to runbook.NewEngine. Only the
// actions present here can ever be executed.
func Providers(d Deps) map[runbook.Action]runbook.ActionFunc {
	return map[runbook.Action]runbook.ActionFunc{
		runbook.ActionServiceStatus:  d.serviceStatus,
		runbook.ActionServiceLogs:    d.serviceLogs,
		runbook.ActionServiceRestart: d.serviceRestart,
		runbook.ActionUDPCheck:       d.udpCheck,
		runbook.ActionCircuitClear:   d.circuitClear,
		runbook.ActionAlertNotify:    d.alertNotify,
	}
}

// resolveUnit validates a unit argument and returns it, or an error explaining
// which guard rejected it.
func (d Deps) resolveUnit(args map[string]string) (string, error) {
	service := strings.TrimSpace(args["service"])
	if service == "" {
		return "", fmt.Errorf("缺少 service 参数")
	}
	if !unitNameRe.MatchString(service) {
		return "", fmt.Errorf("服务名包含非法字符，已拒绝: %q", service)
	}
	if d.Monitor == nil {
		return "", fmt.Errorf("监控组件不可用")
	}
	if !d.Monitor.HasService(service) {
		return "", fmt.Errorf("未监控的服务，拒绝操作: %s", service)
	}
	return service, nil
}

func (d Deps) serviceStatus(ctx context.Context, args map[string]string) (string, error) {
	service, err := d.resolveUnit(args)
	if err != nil {
		return "", err
	}
	out, runErr := exec.CommandContext(ctx, "systemctl", "status", service, "--no-pager", "--lines=0").CombinedOutput()
	text := strings.TrimSpace(string(out))
	if text == "" {
		if runErr != nil {
			return "", fmt.Errorf("systemctl status 执行失败: %w", runErr)
		}
		return "systemctl status 无输出", nil
	}
	// `systemctl status` exits non-zero for an inactive unit while still
	// printing the information we want, so a non-zero exit is reported as
	// context rather than treated as a failed step.
	if runErr != nil {
		text += fmt.Sprintf("\n[退出码非零: %v]", runErr)
	}
	return text, nil
}

func (d Deps) serviceLogs(ctx context.Context, args map[string]string) (string, error) {
	service, err := d.resolveUnit(args)
	if err != nil {
		return "", err
	}
	lines := runbook.ArgInt(args, "lines", 50)
	if lines < 1 {
		lines = 1
	}
	if lines > 200 {
		lines = 200
	}
	out, runErr := exec.CommandContext(ctx, "journalctl", "-u", service,
		"-n", strconv.Itoa(lines), "--no-pager").CombinedOutput()
	text := strings.TrimSpace(string(out))
	if runErr != nil {
		if text == "" {
			return "", fmt.Errorf("journalctl 执行失败: %w", runErr)
		}
		text += fmt.Sprintf("\n[journalctl 退出码非零: %v]", runErr)
	}
	if text == "" {
		return "最近日志为空", nil
	}
	return text, nil
}

func (d Deps) serviceRestart(ctx context.Context, args map[string]string) (string, error) {
	service, err := d.resolveUnit(args)
	if err != nil {
		return "", err
	}
	// Reuse the monitor's restart path so manual and automatic remediation
	// behave identically (same timeout, same socket verification).
	return d.Monitor.RestartInstance(service, runbook.ArgInt(args, "port", 0))
}

func (d Deps) udpCheck(ctx context.Context, args map[string]string) (string, error) {
	port := runbook.ArgInt(args, "port", 0)
	if port < 1 || port > 65535 {
		return "", fmt.Errorf("非法端口: %q", args["port"])
	}
	out, err := exec.CommandContext(ctx, "ss", "-H", "-lun").Output()
	if err != nil {
		return "", fmt.Errorf("ss 执行失败: %w", err)
	}
	listening := collector.UDPPortListening(string(out), port)
	state := "not-listening"
	if listening {
		state = "listening"
	}
	text := fmt.Sprintf("UDP 端口 %d 当前状态: %s", port, state)

	// Optional verification semantics: a step may assert the expected state,
	// which lets a runbook fail loudly when the fix did not work.
	if expect := strings.TrimSpace(args["expect"]); expect != "" && expect != state {
		return text, fmt.Errorf("端口期望状态为 %s，实际为 %s", expect, state)
	}
	return text, nil
}

func (d Deps) circuitClear(ctx context.Context, args map[string]string) (string, error) {
	service, err := d.resolveUnit(args)
	if err != nil {
		return "", err
	}
	changed := d.Monitor.ClearCircuit(service)
	if changed {
		return fmt.Sprintf("已清除 %s 的熔断与重启记录", service), nil
	}
	return fmt.Sprintf("%s 当前没有熔断或重启记录，无需清除", service), nil
}

func (d Deps) alertNotify(ctx context.Context, args map[string]string) (string, error) {
	if d.Notifier == nil {
		return "", fmt.Errorf("通知组件不可用")
	}
	message := strings.TrimSpace(args["message"])
	if message == "" {
		return "", fmt.Errorf("缺少 message 参数")
	}
	title := strings.TrimSpace(args["title"])
	if title == "" {
		title = "Runbook 通知"
	}
	sev := notifier.SeverityWarning
	switch strings.ToLower(strings.TrimSpace(args["severity"])) {
	case "critical":
		sev = notifier.SeverityCritical
	case "recovery":
		sev = notifier.SeverityRecovery
	case "warning", "":
		sev = notifier.SeverityWarning
	default:
		return "", fmt.Errorf("未知的 severity: %q", args["severity"])
	}
	d.Notifier.Push(notifier.Alert{
		Time:    time.Now().Format("2006-01-02 15:04:05"),
		Type:    sev,
		Title:   "[Runbook] " + title,
		Message: message,
	})
	return "通知已发送", nil
}