package monitor

import (
	"testing"

	"github.com/Oxen112774/ServerHealthMonitor/internal/collector"
	"github.com/Oxen112774/ServerHealthMonitor/internal/notifier"
)

func newTestMonitor() *Monitor {
	m := New(collector.NewCollector("", 0, 1),
		notifier.NewNotifier(20, "", "", 0, notifier.SMTPConfig{}), 1, 0, 1)
	m.restartFunc = func(collector.Instance) {}
	return m
}

func unhealthy(service string) collector.Instance {
	return collector.Instance{Service: service, Port: 7777, State: "failed", UDP: "unknown"}
}

func TestRestartLimitAllowsRestartsWithinWindow(t *testing.T) {
	m := newTestMonitor()
	m.SetRestartPolicy(3, 3600)
	restarts := make(chan struct{}, 3)
	m.restartFunc = func(collector.Instance) { restarts <- struct{}{} }

	for i := int64(0); i < 3; i++ {
		m.checkInstance(unhealthy("svc"), 100+i)
	}

	for i := 0; i < 3; i++ {
		<-restarts
	}
	if m.states["svc"].CircuitOpen {
		t.Fatal("circuit opened before restart limit was exceeded")
	}
}

func TestRestartLimitOpensCircuit(t *testing.T) {
	m := newTestMonitor()
	m.SetRestartPolicy(2, 3600)
	restarts := make(chan struct{}, 2)
	m.restartFunc = func(collector.Instance) { restarts <- struct{}{} }

	for i := int64(0); i < 3; i++ {
		m.checkInstance(unhealthy("svc"), 100+i)
	}

	state := m.states["svc"]
	for i := 0; i < 2; i++ {
		<-restarts
	}
	if !state.CircuitOpen || state.CircuitOpenedAt != 102 {
		t.Fatalf("circuit = %#v, want open at 102", state)
	}
}

func TestRestartCooldownAndWindowBoundaries(t *testing.T) {
	m := newTestMonitor()
	m.SetRestartPolicy(2, 10)
	m.restartCooldown = 5
	restarts := make(chan struct{}, 3)
	m.restartFunc = func(collector.Instance) { restarts <- struct{}{} }

	m.checkInstance(unhealthy("svc"), 100)
	m.checkInstance(unhealthy("svc"), 104) // still inside cooldown
	<-restarts
	select {
	case <-restarts:
		t.Fatal("restart was attempted during cooldown")
	default:
	}
	m.checkInstance(unhealthy("svc"), 105)
	<-restarts

	// At exactly the window boundary, the first timestamp expires.
	m.checkInstance(unhealthy("svc"), 110)
	<-restarts
	if m.states["svc"].CircuitOpen {
		t.Fatal("circuit opened after the oldest restart expired")
	}
}

func TestClearCircuit(t *testing.T) {
	m := newTestMonitor()
	m.SetRestartPolicy(1, 3600)
	m.checkInstance(unhealthy("svc"), 100)
	m.checkInstance(unhealthy("svc"), 101)
	if !m.states["svc"].CircuitOpen {
		t.Fatal("expected circuit to open")
	}
	if !m.ClearCircuit("svc") || m.states["svc"].CircuitOpen {
		t.Fatal("ClearCircuit did not clear the circuit")
	}
}
