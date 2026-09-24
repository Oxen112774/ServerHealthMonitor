package servers

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"strings"
	"sync"
	"time"
)

const (
	processAdapterPasswordEnv = "DEPLOY_PASSWORD"
	processAdapterSudoEnv     = "DEPLOY_SUDO_PASSWORD"
	defaultProcessTimeout     = 30 * time.Second
	defaultProcessOutputLimit = 1 << 20
)

// Registry stores deployment extensions by their unique name.
type Registry struct {
	mu         sync.RWMutex
	extensions map[string]Adapter
}

// NewRegistry creates an empty extension registry.
func NewRegistry() *Registry {
	return &Registry{extensions: make(map[string]Adapter)}
}

// Register adds an extension. Names must be non-empty and unique.
func (r *Registry) Register(extension Adapter) error {
	if extension == nil {
		return errors.New("extension must not be nil")
	}
	name := strings.TrimSpace(extension.Name())
	if name == "" {
		return errors.New("extension name must not be empty")
	}
	r.mu.Lock()
	defer r.mu.Unlock()
	if _, exists := r.extensions[name]; exists {
		return fmt.Errorf("extension %q is already registered", name)
	}
	r.extensions[name] = extension
	return nil
}

// List returns registered extension names in sorted order.
func (r *Registry) List() []string {
	r.mu.RLock()
	defer r.mu.RUnlock()
	names := make([]string, 0, len(r.extensions))
	for name := range r.extensions {
		names = append(names, name)
	}
	sortStrings(names)
	return names
}

// Get returns an extension by name.
func (r *Registry) Get(name string) (Adapter, bool) {
	r.mu.RLock()
	defer r.mu.RUnlock()
	extension, ok := r.extensions[name]
	return extension, ok
}

// ExtensionRequest is the JSON request sent to a process extension.
// It deliberately contains no password field; credentials are environment-only.
type ExtensionRequest struct {
	Action  string           `json:"action"`
	Server  Server           `json:"server"`
	Options ExtensionOptions `json:"options"`
}

// ExtensionOptions contains only non-sensitive deployment options.
type ExtensionOptions struct {
	BinaryPath        string `json:"binary_path,omitempty"`
	Adapter           string `json:"adapter,omitempty"`
	RollbackOnFailure bool   `json:"rollback_on_failure,omitempty"`
	MaxConcurrent     int    `json:"max_concurrent,omitempty"`
}

// ExtensionResponse is the single JSON response from a process extension.
type ExtensionResponse struct {
	Output string `json:"output,omitempty"`
	Error  string `json:"error,omitempty"`
}

// ProcessAdapterConfig configures an adapter launched as a direct child process.
type ProcessAdapterConfig struct {
	Name           string
	Executable     string
	Args           []string
	Timeout        time.Duration
	MaxStdoutBytes int
	MaxStderrBytes int
}

// ProcessAdapter implements Adapter using one JSON request/response per process.
type ProcessAdapter struct {
	config ProcessAdapterConfig
}

// NewProcessAdapter validates and creates a process extension.
func NewProcessAdapter(config ProcessAdapterConfig) (*ProcessAdapter, error) {
	if strings.TrimSpace(config.Name) == "" {
		return nil, errors.New("extension name must not be empty")
	}
	if strings.TrimSpace(config.Executable) == "" {
		return nil, errors.New("extension executable must not be empty")
	}
	if config.Timeout <= 0 {
		config.Timeout = defaultProcessTimeout
	}
	if config.MaxStdoutBytes <= 0 {
		config.MaxStdoutBytes = defaultProcessOutputLimit
	}
	if config.MaxStderrBytes <= 0 {
		config.MaxStderrBytes = defaultProcessOutputLimit
	}
	config.Args = append([]string(nil), config.Args...)
	return &ProcessAdapter{config: config}, nil
}

// Name returns the registered extension name.
func (a *ProcessAdapter) Name() string { return a.config.Name }

func (a *ProcessAdapter) run(ctx context.Context, server Server, options DeployOptions, action string) (string, error) {
	server.KeyFile = ""
	request := ExtensionRequest{
		Action: action,
		Server: server,
		Options: ExtensionOptions{
			BinaryPath:        options.BinaryPath,
			Adapter:           options.Adapter,
			RollbackOnFailure: options.RollbackOnFailure,
			MaxConcurrent:     options.MaxConcurrent,
		},
	}
	input, err := json.Marshal(request)
	if err != nil {
		return "", fmt.Errorf("marshal extension request: %w", err)
	}
	runCtx, cancel := context.WithTimeout(ctx, a.config.Timeout)
	defer cancel()
	cmd := exec.CommandContext(runCtx, a.config.Executable, a.config.Args...)
	cmd.Stdin = bytes.NewReader(input)
	env := filteredEnvironment(processAdapterPasswordEnv, processAdapterSudoEnv)
	if options.SSHPassword != "" {
		env = append(env, processAdapterPasswordEnv+"="+options.SSHPassword, processAdapterSudoEnv+"="+options.SSHPassword)
	}
	cmd.Env = env

	var stdout, stderr limitedBuffer
	stdout.limit, stderr.limit = a.config.MaxStdoutBytes, a.config.MaxStderrBytes
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	runErr := cmd.Run()
	if stdout.exceeded {
		return "", fmt.Errorf("extension stdout exceeded %d bytes", stdout.limit)
	}
	if stderr.exceeded {
		return "", fmt.Errorf("extension stderr exceeded %d bytes", stderr.limit)
	}
	safeStderr := redactSensitive(stderr.String(), options.SSHPassword)
	if runCtx.Err() != nil {
		return "", fmt.Errorf("extension %s: %w", action, runCtx.Err())
	}
	if runErr != nil {
		if safeStderr != "" {
			return "", fmt.Errorf("extension %s exited with error: %w: %s", action, runErr, safeStderr)
		}
		return "", fmt.Errorf("extension %s exited with error: %w", action, runErr)
	}

	var response ExtensionResponse
	decoder := json.NewDecoder(bytes.NewReader(stdout.Bytes()))
	if err := decoder.Decode(&response); err != nil {
		return "", fmt.Errorf("invalid extension JSON response: %w", err)
	}
	var extra any
	if err := decoder.Decode(&extra); err != io.EOF {
		if err == nil {
			return "", errors.New("invalid extension response: multiple JSON values")
		}
		return "", fmt.Errorf("invalid extension JSON response: %w", err)
	}
	safeOutput := redactSensitive(response.Output, options.SSHPassword)
	if response.Error != "" {
		return safeOutput, fmt.Errorf("extension %s failed: %s", action, redactSensitive(response.Error, options.SSHPassword))
	}
	return safeOutput, nil
}

func (a *ProcessAdapter) Preflight(ctx context.Context, s Server, o DeployOptions) error {
	_, err := a.run(ctx, s, o, "preflight")
	return err
}

func (a *ProcessAdapter) Install(ctx context.Context, s Server, o DeployOptions) (string, error) {
	return a.run(ctx, s, o, "install")
}

func (a *ProcessAdapter) Rollback(ctx context.Context, s Server, o DeployOptions) error {
	_, err := a.run(ctx, s, o, "rollback")
	return err
}

func (a *ProcessAdapter) HealthCheck(ctx context.Context, s Server, o DeployOptions) error {
	_, err := a.run(ctx, s, o, "health_check")
	return err
}

type limitedBuffer struct {
	bytes.Buffer
	limit    int
	exceeded bool
}

func (b *limitedBuffer) Write(p []byte) (int, error) {
	if b.Len()+len(p) > b.limit {
		remaining := b.limit - b.Len()
		if remaining > 0 {
			_, _ = b.Buffer.Write(p[:remaining])
		}
		b.exceeded = true
		return len(p), nil
	}
	return b.Buffer.Write(p)
}

func filteredEnvironment(removed ...string) []string {
	blocked := make(map[string]struct{}, len(removed))
	for _, name := range removed {
		blocked[name] = struct{}{}
	}
	result := make([]string, 0)
	for _, entry := range os.Environ() {
		name, _, ok := strings.Cut(entry, "=")
		if ok {
			if _, remove := blocked[name]; remove {
				continue
			}
		}
		result = append(result, entry)
	}
	return result
}

func redactSensitive(value, password string) string {
	if password == "" {
		return value
	}
	return strings.ReplaceAll(value, password, "[REDACTED]")
}

func sortStrings(values []string) {
	for i := 1; i < len(values); i++ {
		for j := i; j > 0 && values[j] < values[j-1]; j-- {
			values[j], values[j-1] = values[j-1], values[j]
		}
	}
}
