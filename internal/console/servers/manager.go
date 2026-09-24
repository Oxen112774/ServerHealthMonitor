package servers

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"log"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

const (
	StatusQueued             = "queued"
	StatusRunning            = "running"
	StatusSucceeded          = "succeeded"
	StatusFailed             = "failed"
	StatusRolledBack         = "rolled_back"
	StatusCancelled          = "cancelled"
	defaultConcurrency       = 4
	deploymentWatchInterval  = 10 * time.Second
	deploymentHeartbeatLimit = 90 * time.Second
)

type Server struct {
	ID        string    `json:"id"`
	Name      string    `json:"name"`
	Host      string    `json:"host"`
	Port      int       `json:"port"`
	User      string    `json:"user"`
	KeyFile   string    `json:"key_file"`
	AgentPort int       `json:"agent_port"`
	Status    string    `json:"status"`
	GroupIDs  []string  `json:"group_ids,omitempty"`
	LastCheck time.Time `json:"last_check"`
	CreatedAt time.Time `json:"created_at"`
}

type ServerGroup struct {
	ID          string    `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description,omitempty"`
	CreatedAt   time.Time `json:"created_at"`
}

type DeploymentLog struct {
	ID           string    `json:"id"`
	ServerID     string    `json:"server_id"`
	ServerIDs    []string  `json:"server_ids,omitempty"`
	User         string    `json:"user"`
	Status       string    `json:"status"`
	Adapter      string    `json:"adapter"`
	Binary       string    `json:"binary,omitempty"`
	Output       string    `json:"output,omitempty"`
	Error        string    `json:"error,omitempty"`
	Rollback     bool      `json:"rollback"`
	StartedAt    time.Time `json:"started_at"`
	EndedAt      time.Time `json:"ended_at"`
	HeartbeatAt  time.Time `json:"heartbeat_at,omitempty"`
	LastOutputAt time.Time `json:"last_output_at,omitempty"`
}

type DeployOptions struct {
	BinaryPath        string
	SSHPassword       string
	Adapter           string
	RollbackOnFailure bool
	MaxConcurrent     int
}

// Adapter is the extension point for remote deployment implementations.
// Implementations must not persist or log credentials.
type Adapter interface {
	Name() string
	Preflight(context.Context, Server, DeployOptions) error
	Install(context.Context, Server, DeployOptions) (string, error)
	Rollback(context.Context, Server, DeployOptions) error
	HealthCheck(context.Context, Server, DeployOptions) error
}

type scriptAdapter struct{ name string }

func (a scriptAdapter) Name() string { return a.name }
func (a scriptAdapter) run(ctx context.Context, srv Server, opts DeployOptions, action string) (string, error) {
	script := filepath.Join("deploy", "deploy.py")
	if _, err := os.Stat(script); err != nil {
		if exe, e := os.Executable(); e == nil {
			script = filepath.Join(filepath.Dir(exe), "deploy", "deploy.py")
		}
	}
	if _, err := os.Stat(script); err != nil {
		return "", fmt.Errorf("部署脚本不存在: %s", script)
	}
	args := []string{script, "--host", srv.Host, "--port", fmt.Sprintf("%d", srv.Port), "--user", srv.User, "--" + action}
	if opts.BinaryPath != "" {
		args = append(args, "--binary", opts.BinaryPath)
	}
	if srv.KeyFile != "" {
		args = append(args, "--key", srv.KeyFile)
	}
	cmd := exec.CommandContext(ctx, "python", args...)
	if opts.SSHPassword != "" {
		cmd.Env = append(os.Environ(), "DEPLOY_PASSWORD="+opts.SSHPassword, "DEPLOY_SUDO_PASSWORD="+opts.SSHPassword)
	}
	var out, errOut bytes.Buffer
	cmd.Stdout, cmd.Stderr = &out, &errOut
	err := cmd.Run()
	result := out.String()
	if errOut.Len() > 0 {
		result += "\n" + errOut.String()
	}
	if err != nil {
		return result, err
	}
	return result, nil
}
func (a scriptAdapter) Preflight(ctx context.Context, s Server, o DeployOptions) error {
	_, err := a.run(ctx, s, o, "preflight")
	return err
}
func (a scriptAdapter) Install(ctx context.Context, s Server, o DeployOptions) (string, error) {
	return a.run(ctx, s, o, "install")
}
func (a scriptAdapter) Rollback(ctx context.Context, s Server, o DeployOptions) error {
	_, err := a.run(ctx, s, o, "rollback")
	return err
}
func (a scriptAdapter) HealthCheck(ctx context.Context, s Server, o DeployOptions) error {
	_, err := a.run(ctx, s, o, "health-check")
	return err
}

func GenericAdapter() Adapter { return scriptAdapter{name: "generic"} }
func SystemdAdapter() Adapter { return scriptAdapter{name: "systemd"} }

type Manager struct {
	mu       sync.RWMutex
	servers  map[string]*Server
	groups   map[string]*ServerGroup
	deploys  []*DeploymentLog
	dataPath string
	registry *Registry
	active   map[string]string
	cancels  map[string]context.CancelFunc
}

func NewManager(dataPath string) *Manager {
	m := &Manager{servers: map[string]*Server{}, groups: map[string]*ServerGroup{}, registry: NewRegistry(), dataPath: dataPath, active: map[string]string{}, cancels: map[string]context.CancelFunc{}}
	m.RegisterAdapter(GenericAdapter())
	m.RegisterAdapter(SystemdAdapter())
	m.load()
	return m
}

func (m *Manager) RegisterAdapter(adapter Adapter) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	return m.registry.Register(adapter)
}
func (m *Manager) AdapterNames() []string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.registry.List()
}

func (m *Manager) AddServer(s Server) (*Server, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	if s.Name == "" || s.Host == "" {
		return nil, errors.New("服务器名称和地址不能为空")
	}
	if s.Port == 0 {
		s.Port = 22
	}
	if s.AgentPort == 0 {
		s.AgentPort = 8080
	}
	s.ID, s.Status, s.CreatedAt = generateID(), "unknown", time.Now()
	m.servers[s.ID] = &s
	m.save()
	c := s
	return &c, nil
}
func (m *Manager) UpdateServer(id string, u Server) (*Server, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	s, ok := m.servers[id]
	if !ok {
		return nil, errors.New("服务器不存在")
	}
	if u.Name != "" {
		s.Name = u.Name
	}
	if u.Host != "" {
		s.Host = u.Host
	}
	if u.Port > 0 {
		s.Port = u.Port
	}
	if u.User != "" {
		s.User = u.User
	}
	if u.KeyFile != "" {
		s.KeyFile = u.KeyFile
	}
	if u.AgentPort > 0 {
		s.AgentPort = u.AgentPort
	}
	if u.GroupIDs != nil {
		s.GroupIDs = append([]string(nil), u.GroupIDs...)
	}
	m.save()
	c := *s
	return &c, nil
}
func (m *Manager) DeleteServer(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if _, ok := m.servers[id]; !ok {
		return errors.New("服务器不存在")
	}
	delete(m.servers, id)
	m.save()
	return nil
}
func (m *Manager) GetServer(id string) (*Server, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	s, ok := m.servers[id]
	if !ok {
		return nil, false
	}
	c := *s
	c.GroupIDs = append([]string(nil), s.GroupIDs...)
	return &c, true
}
func (m *Manager) ListServers() []Server {
	m.mu.RLock()
	defer m.mu.RUnlock()
	r := make([]Server, 0, len(m.servers))
	for _, s := range m.servers {
		c := *s
		c.GroupIDs = append([]string(nil), s.GroupIDs...)
		r = append(r, c)
	}
	return r
}

func (m *Manager) AddGroup(name, description string) (*ServerGroup, error) {
	m.mu.Lock()
	defer m.mu.Unlock()
	name = strings.TrimSpace(name)
	if name == "" {
		return nil, errors.New("分组名称不能为空")
	}
	g := &ServerGroup{ID: generateID(), Name: name, Description: description, CreatedAt: time.Now()}
	m.groups[g.ID] = g
	m.save()
	c := *g
	return &c, nil
}
func (m *Manager) ListGroups() []ServerGroup {
	m.mu.RLock()
	defer m.mu.RUnlock()
	r := make([]ServerGroup, 0, len(m.groups))
	for _, g := range m.groups {
		r = append(r, *g)
	}
	return r
}
func (m *Manager) DeleteGroup(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	if _, ok := m.groups[id]; !ok {
		return errors.New("分组不存在")
	}
	delete(m.groups, id)
	for _, s := range m.servers {
		s.GroupIDs = removeString(s.GroupIDs, id)
	}
	m.save()
	return nil
}
func (m *Manager) AssignGroup(serverID, groupID string, assigned bool) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	s, ok := m.servers[serverID]
	if !ok {
		return errors.New("服务器不存在")
	}
	if _, ok = m.groups[groupID]; !ok {
		return errors.New("分组不存在")
	}
	if assigned {
		for _, id := range s.GroupIDs {
			if id == groupID {
				return nil
			}
		}
		s.GroupIDs = append(s.GroupIDs, groupID)
	} else {
		s.GroupIDs = removeString(s.GroupIDs, groupID)
	}
	m.save()
	return nil
}

func (m *Manager) DeployToServer(serverID, username, binaryPath, password string) (*DeployResult, error) {
	job, err := m.StartDeployment([]string{serverID}, username, DeployOptions{BinaryPath: binaryPath, SSHPassword: password, Adapter: "systemd", RollbackOnFailure: true, MaxConcurrent: 1})
	if err != nil {
		return nil, err
	}
	for {
		d, _ := m.GetDeployment(job.ID)
		if d.Status != StatusQueued && d.Status != StatusRunning {
			return &DeployResult{Success: d.Status == StatusSucceeded, Output: d.Output, LogID: d.ID}, nil
		}
		time.Sleep(25 * time.Millisecond)
	}
}

type DeployResult struct {
	Success bool
	Output  string
	LogID   string
}

func (m *Manager) StartDeployment(ids []string, user string, opts DeployOptions) (*DeploymentLog, error) {
	if len(ids) == 0 {
		return nil, errors.New("请选择服务器")
	}
	if opts.Adapter == "" {
		opts.Adapter = "systemd"
	}
	if opts.MaxConcurrent <= 0 || opts.MaxConcurrent > 32 {
		opts.MaxConcurrent = defaultConcurrency
	}
	if opts.BinaryPath != "" {
		if err := validateBinaryPath(opts.BinaryPath); err != nil {
			return nil, err
		}
	}
	m.mu.Lock()
	adapter, ok := m.registry.Get(opts.Adapter)
	if !ok {
		m.mu.Unlock()
		return nil, errors.New("未知部署适配器")
	}
	seen := make(map[string]bool, len(ids))
	for _, id := range ids {
		if seen[id] {
			m.mu.Unlock()
			return nil, errors.New("服务器列表包含重复项")
		}
		seen[id] = true
		if _, ok := m.servers[id]; !ok {
			m.mu.Unlock()
			return nil, errors.New("服务器不存在: " + id)
		}
		if existing, ok := m.active[id]; ok {
			m.mu.Unlock()
			return nil, fmt.Errorf("服务器已有活动部署任务: %s", existing)
		}
	}
	now := time.Now()
	j := &DeploymentLog{ID: generateID(), ServerID: ids[0], ServerIDs: append([]string(nil), ids...), User: user, Adapter: opts.Adapter, Binary: opts.BinaryPath, Rollback: opts.RollbackOnFailure, Status: StatusQueued, StartedAt: now, HeartbeatAt: now, LastOutputAt: now}
	m.deploys = append(m.deploys, j)
	for _, id := range ids {
		m.active[id] = j.ID
	}
	ctx, cancel := context.WithCancel(context.Background())
	m.cancels[j.ID] = cancel
	m.save()
	result := cloneDeployment(j)
	m.mu.Unlock()
	go m.watchDeployment(ctx, j.ID)
	go m.runDeployment(ctx, j.ID, ids, opts, adapter)
	return result, nil
}

func (m *Manager) watchDeployment(parent context.Context, jobID string) {
	ticker := time.NewTicker(deploymentWatchInterval)
	defer ticker.Stop()
	for {
		select {
		case <-parent.Done():
			return
		case <-ticker.C:
			m.mu.Lock()
			var job *DeploymentLog
			for _, candidate := range m.deploys {
				if candidate.ID == jobID {
					job = candidate
					break
				}
			}
			if job == nil || job.Status == StatusSucceeded || job.Status == StatusFailed || job.Status == StatusRolledBack || job.Status == StatusCancelled {
				m.mu.Unlock()
				return
			}
			if time.Since(job.HeartbeatAt) > deploymentHeartbeatLimit {
				if cancel := m.cancels[jobID]; cancel != nil {
					cancel()
				}
				job.Status = StatusFailed
				job.Error = "部署任务心跳超时，适配器可能已停止或无响应"
				job.EndedAt = time.Now()
				m.save()
				m.mu.Unlock()
				return
			}
			m.mu.Unlock()
		}
	}
}

func (m *Manager) touchHeartbeat(jobID string, output bool) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, job := range m.deploys {
		if job.ID == jobID {
			now := time.Now()
			job.HeartbeatAt = now
			if output {
				job.LastOutputAt = now
			}
			return
		}
	}
}

func (m *Manager) runDeployment(parent context.Context, jobID string, ids []string, opts DeployOptions, adapter Adapter) {
	defer func() {
		if recovered := recover(); recovered != nil {
			m.updateStatusIf(jobID, StatusFailed, fmt.Sprintf("适配器异常退出: %v", recovered), "")
		}
		m.mu.Lock()
		delete(m.cancels, jobID)
		for _, id := range ids {
			if m.active[id] == jobID {
				delete(m.active, id)
			}
		}
		m.mu.Unlock()
	}()
	if !m.updateStatusIf(jobID, StatusRunning, "", "") {
		return
	}
	sem := make(chan struct{}, opts.MaxConcurrent)
	var wg sync.WaitGroup
	var mu sync.Mutex
	failed := false
	for _, id := range ids {
		id := id
		wg.Add(1)
		go func() {
			defer wg.Done()
			select {
			case sem <- struct{}{}:
			case <-parent.Done():
				return
			}
			defer func() { <-sem }()
			if parent.Err() != nil {
				return
			}
			s, ok := m.GetServer(id)
			if !ok {
				mu.Lock()
				failed = true
				mu.Unlock()
				return
			}
			ctx, cancel := context.WithTimeout(parent, 5*time.Minute)
			defer cancel()
			if ctx.Err() != nil {
				return
			}
			m.touchHeartbeat(jobID, false)
			if err := adapter.Preflight(ctx, *s, opts); err != nil {
				mu.Lock()
				failed = true
				mu.Unlock()
				m.appendOutput(jobID, id+": preflight failed: "+err.Error(), opts.SSHPassword)
				return
			}
			m.touchHeartbeat(jobID, false)
			out, err := adapter.Install(ctx, *s, opts)
			m.appendOutput(jobID, id+": "+out, opts.SSHPassword)
			if ctx.Err() != nil {
				return
			}
			if err != nil {
				mu.Lock()
				failed = true
				mu.Unlock()
				if opts.RollbackOnFailure {
					m.touchHeartbeat(jobID, false)
					rollbackCtx, rollbackCancel := context.WithTimeout(context.Background(), 2*time.Minute)
					rollbackErr := adapter.Rollback(rollbackCtx, *s, opts)
					rollbackCancel()
					if rollbackErr == nil {
						m.appendOutput(jobID, id+": rollback completed", opts.SSHPassword)
					}
				}
			}
			if err == nil {
				if ctx.Err() != nil {
					return
				}
				m.touchHeartbeat(jobID, false)
				if healthErr := adapter.HealthCheck(ctx, *s, opts); healthErr != nil {
					mu.Lock()
					failed = true
					mu.Unlock()
					if opts.RollbackOnFailure {
						m.touchHeartbeat(jobID, false)
						rollbackCtx, rollbackCancel := context.WithTimeout(context.Background(), 2*time.Minute)
						rollbackErr := adapter.Rollback(rollbackCtx, *s, opts)
						rollbackCancel()
						if rollbackErr == nil {
							m.appendOutput(jobID, id+": rollback completed", opts.SSHPassword)
						}
					}
				}
			}
		}()
	}
	wg.Wait()
	if parent.Err() != nil {
		return
	}
	if failed {
		status := StatusFailed
		m.mu.RLock()
		for _, d := range m.deploys {
			if d.ID == jobID && strings.Contains(d.Output, "rollback completed") {
				status = StatusRolledBack
			}
		}
		m.mu.RUnlock()
		m.updateStatusIf(jobID, status, "one or more servers failed", "")
	} else {
		m.updateStatusIf(jobID, StatusSucceeded, "", "")
	}
}
func (m *Manager) CancelDeployment(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, d := range m.deploys {
		if d.ID == id && (d.Status == StatusQueued || d.Status == StatusRunning) {
			if cancel := m.cancels[id]; cancel != nil {
				cancel()
			}
			d.Status = StatusCancelled
			d.EndedAt = time.Now()
			m.save()
			return nil
		}
	}
	return errors.New("任务不可取消")
}
func (m *Manager) GetDeployment(id string) (*DeploymentLog, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	for _, d := range m.deploys {
		if d.ID == id {
			return cloneDeployment(d), true
		}
	}
	return nil, false
}
func (m *Manager) ListDeployments(limit int) []DeploymentLog {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if limit <= 0 || limit > len(m.deploys) {
		limit = len(m.deploys)
	}
	r := make([]DeploymentLog, limit)
	for i := range r {
		r[i] = *cloneDeployment(m.deploys[len(m.deploys)-1-i])
	}
	return r
}
func (m *Manager) updateStatus(id, status, errMsg, output string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, d := range m.deploys {
		if d.ID == id {
			d.Status = status
			if errMsg != "" {
				d.Error = errMsg
			}

			if output != "" {
				d.Output += output
			}
			if status != StatusRunning {
				d.EndedAt = time.Now()
			}
			m.save()
			return
		}
	}
}

func (m *Manager) updateStatusIf(id, status, errMsg, output string) bool {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, d := range m.deploys {
		if d.ID == id {
			if d.Status != StatusQueued && d.Status != StatusRunning {
				return false
			}
			d.Status = status
			if errMsg != "" {
				d.Error = errMsg
			}
			if output != "" {
				d.Output += output
			}
			if status != StatusRunning {
				d.EndedAt = time.Now()
			}
			m.save()
			return true
		}
	}
	return false
}
func (m *Manager) appendOutput(id, output, password string) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, d := range m.deploys {
		if d.ID == id {
			if d.Status == StatusSucceeded || d.Status == StatusFailed || d.Status == StatusRolledBack || d.Status == StatusCancelled {
				return
			}
			now := time.Now()
			d.HeartbeatAt = now
			d.LastOutputAt = now
			d.Output += redactOutput(output, password) + "\n"
			m.save()
			return
		}
	}
}

func redactOutput(output, password string) string {
	if password == "" {
		return output
	}
	return strings.ReplaceAll(output, password, "[REDACTED]")
}

type DeployOptionsJSON struct{}
type persistenceData struct {
	Servers map[string]*Server      `json:"servers"`
	Groups  map[string]*ServerGroup `json:"groups,omitempty"`
	Deploys []*DeploymentLog        `json:"deploys"`
}

func (m *Manager) load() {
	f, err := os.ReadFile(filepath.Join(m.dataPath, "servers.json"))
	if err != nil {
		if !os.IsNotExist(err) {
			log.Printf("加载服务器数据失败: %v", err)
		}
		return
	}
	var d persistenceData
	if err := json.Unmarshal(f, &d); err == nil {
		if d.Servers != nil {
			m.servers = d.Servers
		}
		if d.Groups != nil {
			m.groups = d.Groups
		}
		if d.Deploys != nil {
			m.deploys = d.Deploys
		}
		for _, job := range m.deploys {
			if job.Status == StatusQueued || job.Status == StatusRunning {
				job.Status = StatusFailed
				job.Error = "进程重启，任务被中断"
				job.EndedAt = time.Now()
			}
		}
	} else {
		log.Printf("服务器数据文件损坏，未加载: %v", err)
	}
}
func (m *Manager) save() {
	if err := os.MkdirAll(m.dataPath, 0750); err != nil {
		log.Printf("创建数据目录失败: %v", err)
		return
	}
	b, err := json.MarshalIndent(persistenceData{Servers: m.servers, Groups: m.groups, Deploys: m.deploys}, "", "  ")
	if err != nil {
		log.Printf("序列化服务器数据失败: %v", err)
		return
	}
	tmp := filepath.Join(m.dataPath, "servers.json.tmp")
	if err := os.WriteFile(tmp, b, 0600); err != nil {
		log.Printf("写入服务器数据失败: %v", err)
		return
	}
	if err := os.Rename(tmp, filepath.Join(m.dataPath, "servers.json")); err != nil {
		target := filepath.Join(m.dataPath, "servers.json")
		if removeErr := os.Remove(target); removeErr == nil {
			if retryErr := os.Rename(tmp, target); retryErr == nil {
				return
			} else {
				log.Printf("替换服务器数据失败: %v", retryErr)
			}
		} else {
			log.Printf("替换服务器数据失败: %v", err)
		}
		_ = os.Remove(tmp)
	}
}

func validateBinaryPath(path string) error {
	if filepath.IsAbs(path) {
		return errors.New("binary_path 必须是构建目录下的相对路径")
	}
	root, err := filepath.Abs(".")
	if err != nil {
		return err
	}
	clean := filepath.Clean(path)
	full := filepath.Join(root, clean)
	buildRoot := filepath.Join(root, "build")
	rel, err := filepath.Rel(buildRoot, full)
	if err != nil || rel == ".." || strings.HasPrefix(rel, ".."+string(filepath.Separator)) || filepath.IsAbs(rel) {
		return errors.New("binary_path 必须位于 build 目录")
	}
	info, err := os.Stat(full)
	if err != nil {
		return fmt.Errorf("binary_path 无法读取: %w", err)
	}
	if !info.Mode().IsRegular() {
		return errors.New("binary_path 不是普通文件")
	}
	return nil
}
func cloneDeployment(d *DeploymentLog) *DeploymentLog {
	c := *d
	c.ServerIDs = append([]string(nil), d.ServerIDs...)
	return &c
}
func removeString(values []string, target string) []string {
	r := values[:0]
	for _, v := range values {
		if v != target {
			r = append(r, v)
		}
	}
	return r
}
func generateID() string { return fmt.Sprintf("srv-%d", time.Now().UnixNano()) }
