package servers

import (
	"context"
	"os"
	"path/filepath"
	"sync"
	"testing"
	"time"
)

type recordingAdapter struct {
	mu     sync.Mutex
	events []string
}

type blockingAdapter struct {
	started chan struct{}
}

func (a *blockingAdapter) Name() string                                           { return "blocking" }
func (a *blockingAdapter) Preflight(context.Context, Server, DeployOptions) error { return nil }
func (a *blockingAdapter) Install(ctx context.Context, server Server, opts DeployOptions) (string, error) {
	close(a.started)
	<-ctx.Done()
	return "", ctx.Err()
}
func (a *blockingAdapter) Rollback(context.Context, Server, DeployOptions) error    { return nil }
func (a *blockingAdapter) HealthCheck(context.Context, Server, DeployOptions) error { return nil }

func (a *recordingAdapter) Name() string { return "test" }
func (a *recordingAdapter) Preflight(context.Context, Server, DeployOptions) error {
	a.mu.Lock()
	a.events = append(a.events, "preflight")
	a.mu.Unlock()
	return nil
}
func (a *recordingAdapter) Install(context.Context, Server, DeployOptions) (string, error) {
	a.mu.Lock()
	a.events = append(a.events, "install")
	a.mu.Unlock()
	return "ok", nil
}
func (a *recordingAdapter) Rollback(context.Context, Server, DeployOptions) error    { return nil }
func (a *recordingAdapter) HealthCheck(context.Context, Server, DeployOptions) error { return nil }

func waitForDeployment(t *testing.T, m *Manager, id string) *DeploymentLog {
	t.Helper()
	deadline := time.Now().Add(2 * time.Second)
	for time.Now().Before(deadline) {
		job, ok := m.GetDeployment(id)
		if ok && job.Status != StatusQueued && job.Status != StatusRunning {
			return job
		}
		time.Sleep(time.Millisecond)
	}
	t.Fatal("deployment did not finish")
	return nil
}

func TestDeploymentPreflightRunsBeforeInstallAndPersistsStatus(t *testing.T) {
	m := NewManager(t.TempDir())
	adapter := &recordingAdapter{}
	m.RegisterAdapter(adapter)
	server, err := m.AddServer(Server{Name: "one", Host: "127.0.0.1"})
	if err != nil {
		t.Fatal(err)
	}
	job, err := m.StartDeployment([]string{server.ID}, "operator", DeployOptions{Adapter: "test", RollbackOnFailure: true})
	if err != nil {
		t.Fatal(err)
	}
	result := waitForDeployment(t, m, job.ID)
	if result.Status != StatusSucceeded {
		t.Fatalf("status = %s", result.Status)
	}
	if len(adapter.events) != 2 || adapter.events[0] != "preflight" || adapter.events[1] != "install" {
		t.Fatalf("unexpected adapter sequence: %v", adapter.events)
	}
	data, err := os.ReadFile(filepath.Join(m.dataPath, "servers.json"))
	if err != nil {
		t.Fatal(err)
	}
	if string(data) == "" {
		t.Fatal("expected persisted JSON")
	}
}

func TestGroupsPersistAndPasswordIsNotWritten(t *testing.T) {
	dir := t.TempDir()
	m := NewManager(dir)
	server, _ := m.AddServer(Server{Name: "one", Host: "host"})
	group, err := m.AddGroup("production", "prod")
	if err != nil {
		t.Fatal(err)
	}

	if err := m.AssignGroup(server.ID, group.ID, true); err != nil {
		t.Fatal(err)
	}

	if _, err := m.StartDeployment([]string{server.ID}, "operator", DeployOptions{Adapter: "test", SSHPassword: "never-write-this"}); err == nil {
		// The adapter is intentionally absent; the validation must still never persist credentials.
		t.Fatal("expected unknown adapter error")
	}
	data, _ := os.ReadFile(filepath.Join(dir, "servers.json"))
	if string(data) == "" || contains(string(data), "never-write-this") {
		t.Fatal("credential was persisted")
	}
	reloaded := NewManager(dir)
	if len(reloaded.ListGroups()) != 1 {
		t.Fatal("group was not persisted")
	}
}

func TestDeploymentRejectsConcurrentServerAndCancelsRunningJob(t *testing.T) {
	m := NewManager(t.TempDir())
	adapter := &blockingAdapter{started: make(chan struct{})}
	m.RegisterAdapter(adapter)
	server, err := m.AddServer(Server{Name: "one", Host: "host"})
	if err != nil {
		t.Fatal(err)
	}
	job, err := m.StartDeployment([]string{server.ID}, "operator", DeployOptions{Adapter: "blocking"})
	if err != nil {
		t.Fatal(err)
	}
	<-adapter.started
	if _, err := m.StartDeployment([]string{server.ID}, "operator", DeployOptions{Adapter: "blocking"}); err == nil {
		t.Fatal("expected duplicate deployment to be rejected")
	}
	if err := m.CancelDeployment(job.ID); err != nil {
		t.Fatal(err)
	}
	result := waitForDeployment(t, m, job.ID)
	if result.Status != StatusCancelled {
		t.Fatalf("status = %s, want cancelled", result.Status)
	}
}

func TestBinaryPathMustBeRegularFileUnderBuild(t *testing.T) {
	m := NewManager(t.TempDir())
	server, _ := m.AddServer(Server{Name: "one", Host: "host"})
	if _, err := m.StartDeployment([]string{server.ID}, "operator", DeployOptions{BinaryPath: "..\\server-health-monitor-agent"}); err == nil {
		t.Fatal("expected path traversal to be rejected")
	}
}

func contains(s, part string) bool {
	for i := 0; i+len(part) <= len(s); i++ {
		if s[i:i+len(part)] == part {
			return true
		}
	}
	return false
}
