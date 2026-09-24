package servers

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"testing"
	"time"
)

func TestRegistryRejectsEmptyAndDuplicateNames(t *testing.T) {
	registry := NewRegistry()
	empty, err := NewProcessAdapter(ProcessAdapterConfig{Name: " ", Executable: os.Args[0]})
	if err == nil || empty != nil {
		t.Fatal("expected empty process extension name to fail")
	}
	first := &recordingAdapter{}
	if err := registry.Register(first); err != nil {
		t.Fatal(err)
	}
	if err := registry.Register(first); err == nil {
		t.Fatal("expected duplicate registration to fail")
	}
	if got := registry.List(); len(got) != 1 || got[0] != "test" {
		t.Fatalf("unexpected registry names: %v", got)
	}
}

func TestProcessAdapterProtocolSuccessAndSensitiveOutputRedaction(t *testing.T) {
	t.Setenv("EXTENSION_HELPER_MODE", "success")
	adapter, err := NewProcessAdapter(ProcessAdapterConfig{
		Name:       "helper",
		Executable: os.Args[0],
		Args:       []string{"-test.run=TestProcessAdapterHelper"},
	})
	if err != nil {
		t.Fatal(err)
	}
	output, err := adapter.Install(context.Background(), Server{Name: "server", Host: "host"}, DeployOptions{SSHPassword: "secret"})
	if err != nil {
		t.Fatal(err)
	}
	if output != "safe [REDACTED]" {
		t.Fatalf("unexpected output: %q", output)
	}
}

func TestProcessAdapterTimeout(t *testing.T) {
	t.Setenv("EXTENSION_HELPER_MODE", "timeout")
	adapter, err := NewProcessAdapter(ProcessAdapterConfig{
		Name: "helper", Executable: os.Args[0], Args: []string{"-test.run=TestProcessAdapterHelper"},
		Timeout: 20 * time.Millisecond,
	})
	if err != nil {
		t.Fatal(err)
	}
	_, err = adapter.Install(context.Background(), Server{}, DeployOptions{})
	if err == nil || !contains(err.Error(), "deadline exceeded") {
		t.Fatalf("expected timeout error, got %v", err)
	}
}

func TestProcessAdapterRejectsInvalidJSONAndNonZeroExit(t *testing.T) {
	for _, mode := range []string{"bad-json", "exit"} {
		t.Run(mode, func(t *testing.T) {
			adapter, err := NewProcessAdapter(ProcessAdapterConfig{
				Name: "helper", Executable: os.Args[0],
				Args: []string{"-test.run=TestProcessAdapterHelper"},
			})
			if err != nil {
				t.Fatal(err)
			}
			t.Setenv("EXTENSION_HELPER_MODE", mode)
			_, err = adapter.Install(context.Background(), Server{}, DeployOptions{})
			if err == nil {
				t.Fatal("expected process extension failure")
			}
			if mode == "bad-json" && !contains(err.Error(), "invalid extension JSON") {
				t.Fatalf("unexpected JSON error: %v", err)
			}
			if mode == "exit" && !contains(err.Error(), "exited with error") {
				t.Fatalf("unexpected exit error: %v", err)
			}
		})
	}
}

func TestProcessAdapterHelper(t *testing.T) {
	mode := os.Getenv("EXTENSION_HELPER_MODE")
	if mode == "" {
		return
	}
	switch mode {
	case "timeout":
		time.Sleep(time.Second)
	case "bad-json":
		fmt.Print("{not-json")
		os.Exit(0)
	case "exit":
		fmt.Fprint(os.Stderr, "child failure")
		os.Exit(3)
	default:
		password := os.Getenv(processAdapterPasswordEnv)
		response, _ := json.Marshal(ExtensionResponse{Output: "safe " + password})
		fmt.Print(string(response))
		os.Exit(0)
	}
}
