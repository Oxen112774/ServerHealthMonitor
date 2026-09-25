package runbook

import (
	"fmt"

	"github.com/Oxen112774/ServerHealthMonitor/internal/incident"
)

// Symptom keywords are defined once in the incident package so detection and
// remediation can never drift apart. These aliases keep runbook code readable.
const (
	SymptomServiceDown  = incident.SymptomServiceDown
	SymptomUDPNotListen = incident.SymptomUDPNotListen
	SymptomCircuitOpen  = incident.SymptomCircuitOpen
	SymptomResourceHigh = incident.SymptomResourceHigh
)

// Builtins returns the shipped remediation catalog. Every entry starts in
// recommend-only mode; read-only diagnostics run without approval, anything
// with a side effect requires an operator to approve it first.
func Builtins() []Runbook {
	return []Runbook{
		{
			ID:          "rb-diagnose-service",
			Name:        "服务异常只读诊断",
			Description: "收集 systemd 状态、最近日志与 UDP 监听情况，用于快速定位服务异常原因。全部为只读操作，可直接执行。",
			Trigger:     SymptomServiceDown,
			Steps: []Step{
				{Name: "查询 systemd 状态", Action: ActionServiceStatus, Args: map[string]string{"service": "${service}"}, TimeoutSeconds: 15, ReadOnly: true},
				{Name: "读取最近日志", Action: ActionServiceLogs, Args: map[string]string{"service": "${service}", "lines": "50"}, TimeoutSeconds: 20, ReadOnly: true},
				{Name: "校验 UDP 端口", Action: ActionUDPCheck, Args: map[string]string{"port": "${port}"}, TimeoutSeconds: 15, ReadOnly: true},
			},
			Autonomy:    AutonomyRecommend,
			Risk:        "low",
			Reversible:  true,
			BlastRadius: 1,
		},
		{
			ID:          "rb-restart-service",
			Name:        "服务重启并校验端口",
			Description: "先取证（状态+日志），再执行 systemctl restart，最后轮询确认 UDP 端口恢复监听。重启可逆，但会短暂中断在线玩家。",
			Trigger:     SymptomServiceDown,
			Steps: []Step{
				{Name: "重启前取证", Action: ActionServiceLogs, Args: map[string]string{"service": "${service}", "lines": "30"}, TimeoutSeconds: 20, ReadOnly: true},
				{Name: "重启服务", Action: ActionServiceRestart, Args: map[string]string{"service": "${service}", "port": "${port}"}, TimeoutSeconds: 90},
				{Name: "校验 UDP 端口", Action: ActionUDPCheck, Args: map[string]string{"port": "${port}", "expect": "listening"}, TimeoutSeconds: 15, ReadOnly: true},
			},
			Autonomy:    AutonomyRecommend,
			Risk:        "medium",
			Reversible:  true,
			BlastRadius: 1,
		},
		{
			ID:          "rb-recover-udp",
			Name:        "UDP 未监听恢复",
			Description: "针对进程存活但 UDP 端口未监听的场景：先确认端口状态，再重启服务并复检。",
			Trigger:     SymptomUDPNotListen,
			Steps: []Step{
				{Name: "确认端口状态", Action: ActionUDPCheck, Args: map[string]string{"port": "${port}"}, TimeoutSeconds: 15, ReadOnly: true},
				{Name: "重启服务", Action: ActionServiceRestart, Args: map[string]string{"service": "${service}", "port": "${port}"}, TimeoutSeconds: 90},
				{Name: "复检端口", Action: ActionUDPCheck, Args: map[string]string{"port": "${port}", "expect": "listening"}, TimeoutSeconds: 15, ReadOnly: true},
			},
			Autonomy:    AutonomyRecommend,
			Risk:        "medium",
			Reversible:  true,
			BlastRadius: 1,
		},
		{
			ID:          "rb-clear-circuit",
			Name:        "重置自动处置熔断",
			Description: "自动重启达到上限后熔断会暂停一切自动修复。本 Runbook 先取证再清除该实例的熔断与重启记录，并发出通知。清除熔断会解除安全制动，属于不可逆操作，执行前请确认服务已人工恢复。",
			Trigger:     SymptomCircuitOpen,
			Steps: []Step{
				{Name: "取证服务状态", Action: ActionServiceStatus, Args: map[string]string{"service": "${service}"}, TimeoutSeconds: 15, ReadOnly: true},
				{Name: "清除熔断记录", Action: ActionCircuitClear, Args: map[string]string{"service": "${service}"}, TimeoutSeconds: 10},
				{Name: "通知处理结果", Action: ActionAlertNotify, Args: map[string]string{
					"title":   "熔断已重置",
					"message": "实例 ${service} 的自动处置熔断已由 Runbook 重置，自动重启能力已恢复。",
				}, TimeoutSeconds: 10},
			},
			Autonomy:    AutonomyRecommend,
			Risk:        "medium",
			Reversible:  false,
			BlastRadius: 1,
		},
		{
			ID:          "rb-triage-resource",
			Name:        "资源压力只读排查",
			Description: "CPU/内存/磁盘/负载超过阈值或异常检测触发时使用：采集服务状态、日志与端口信息，供人工判断根因。全部为只读操作。",
			Trigger:     SymptomResourceHigh,
			Steps: []Step{
				{Name: "查询服务状态", Action: ActionServiceStatus, Args: map[string]string{"service": "${service}"}, TimeoutSeconds: 15, ReadOnly: true},
				{Name: "读取最近日志", Action: ActionServiceLogs, Args: map[string]string{"service": "${service}", "lines": "100"}, TimeoutSeconds: 20, ReadOnly: true},
				{Name: "校验 UDP 端口", Action: ActionUDPCheck, Args: map[string]string{"port": "${port}"}, TimeoutSeconds: 15, ReadOnly: true},
			},
			Autonomy:    AutonomyRecommend,
			Risk:        "low",
			Reversible:  true,
			BlastRadius: 1,
		},
		{
			ID:          "rb-full-recovery",
			Name:        "熔断后完整恢复（重置+重启+复检）",
			Description: "服务处于熔断状态且需要立即恢复时使用：先取证，再清除熔断，随后重启服务并复检端口，最后通知结果。影响面较大，建议在维护窗口内执行。",
			Trigger:     SymptomCircuitOpen,
			Steps: []Step{
				{Name: "取证服务状态", Action: ActionServiceStatus, Args: map[string]string{"service": "${service}"}, TimeoutSeconds: 15, ReadOnly: true},
				{Name: "读取最近日志", Action: ActionServiceLogs, Args: map[string]string{"service": "${service}", "lines": "100"}, TimeoutSeconds: 20, ReadOnly: true},
				{Name: "清除熔断记录", Action: ActionCircuitClear, Args: map[string]string{"service": "${service}"}, TimeoutSeconds: 10},
				{Name: "重启服务", Action: ActionServiceRestart, Args: map[string]string{"service": "${service}", "port": "${port}"}, TimeoutSeconds: 90},
				{Name: "复检端口", Action: ActionUDPCheck, Args: map[string]string{"port": "${port}", "expect": "listening"}, TimeoutSeconds: 15, ReadOnly: true},
				{Name: "通知处理结果", Action: ActionAlertNotify, Args: map[string]string{
					"title":   "完整恢复流程已执行",
					"message": "实例 ${service} 已执行熔断重置与服务重启，请确认玩家可正常连入。",
				}, TimeoutSeconds: 10},
			},
			Autonomy:    AutonomyRecommend,
			Risk:        "medium",
			Reversible:  false,
			BlastRadius: 2,
		},
	}
}

// init performs a self-check of the shipped catalog so a malformed built-in
// definition fails loudly at process start rather than during an outage.
func init() {
	if err := ValidateCatalog(Builtins()); err != nil {
		panic(fmt.Sprintf("内置 Runbook 目录校验失败: %v", err))
	}
}