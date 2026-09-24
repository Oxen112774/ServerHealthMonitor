package web

import "net/http"

// --- Page handlers ---

func (h *Handler) handleLoginPage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write([]byte(loginPageHTML))
}

func (h *Handler) handleChangePasswordPage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.Write([]byte(changePasswordPageHTML))
}

func (h *Handler) handleConsolePage(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, "/console/dashboard", http.StatusSeeOther)
}

func (h *Handler) handleDashboardPage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	content := `
		<div class="page-header dashboard-header">
			<div>
				<div class="page-kicker">OPERATIONS COMMAND CENTER</div>
				<h2>运维中枢</h2>
				<p class="page-desc">实时监控、故障感知与一键响应</p>
			</div>
			<div class="header-actions">
				<button class="btn btn-secondary" type="button">⟳ 刷新</button>
				<button class="btn btn-primary" type="button">⚡ 诊断</button>
			</div>
		</div>

		<div class="stats-grid">
			<div class="stat-card">
				<div class="stat-icon">🖥️</div>
				<div class="stat-info">
					<div class="stat-value" id="stat-servers">0</div>
					<div class="stat-label">服务器总数</div>
				</div>
			</div>
			<div class="stat-card stat-online">
				<div class="stat-icon">✅</div>
				<div class="stat-info">
					<div class="stat-value" id="stat-online">0</div>
					<div class="stat-label">在线</div>
				</div>
			</div>
			<div class="stat-card stat-offline">
				<div class="stat-icon">⚠️</div>
				<div class="stat-info">
					<div class="stat-value" id="stat-offline">0</div>
					<div class="stat-label">离线/异常</div>
				</div>
			</div>
			<div class="stat-card stat-alerts">
				<div class="stat-icon">🔔</div>
				<div class="stat-info">
					<div class="stat-value" id="stat-alerts">0</div>
					<div class="stat-label">告警</div>
				</div>
			</div>
		</div>

		<div class="dashboard-grid">
			<div class="section hero-panel">
				<div class="hero-panel-head">
					<div>
						<div class="panel-kicker">SYSTEM HEALTH</div>
						<h3>运行状态概览</h3>
					</div>
					<span class="live-pill"><span class="pulse-dot"></span> 实时</span>
				</div>
				<div class="health-visual">
					<div class="ring-wrap">
						<div class="ring ring-good">
							<div class="ring-core">99.2%</div>
						</div>
					</div>
					<div class="health-metrics">
						<div class="mini-metric">
							<span>响应延迟</span>
							<strong>42 ms</strong>
						</div>
						<div class="mini-metric">
							<span>恢复效率</span>
							<strong>96.4%</strong>
						</div>
						<div class="mini-metric">
							<span>执行窗口</span>
							<strong>24 h</strong>
						</div>
					</div>
				</div>
			</div>

			<div class="section compact-panel">
				<div class="panel-kicker">SERVICE STATUS</div>
				<h3>安全状态</h3>
				<div class="data-strip">
					<div><span>SSH</span><strong>正常</strong></div>
					<div><span>进程</span><strong>稳定</strong></div>
					<div><span>日志</span><strong>已采集</strong></div>
				</div>
				<div class="alert-list">
					<div class="alert-item warning">
						<span>⚠</span>
						<div><strong>磁盘占用</strong><small>本周上升趋势</small></div>
					</div>
					<div class="alert-item ok">
						<span>✓</span>
						<div><strong>端口连通性</strong><small>无阻断事件</small></div>
					</div>
				</div>
			</div>
		</div>

		<div class="section">
			<div class="panel-kicker">RESOURCE MAP</div>
			<h3>服务器列表</h3>
			<div class="server-list" id="server-list">
				<div class="empty-state">
					<div class="empty-icon">📡</div>
					<p>暂无服务器</p>
					<p class="empty-hint">去 <a href="/console/servers">服务器管理</a> 添加你的第一台服务器</p>
				</div>
			</div>
		</div>
	` + dashboardScript
	w.Write([]byte(consoleLayoutHTML(content, "dashboard")))
}

func (h *Handler) handleServersPage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	content := `
		<div class="page-header">
			<div>
				<h2>🖥️ 服务器管理</h2>
				<p class="page-desc">管理你的监控服务器，一键部署 Agent</p>
			</div>
			<button class="btn btn-primary" onclick="openAddServer()">➕ 添加服务器</button>
		</div>

		<div class="section">
			<div class="toolbar">
				<input type="text" id="search-server" placeholder="搜索服务器..." oninput="filterServers()" class="search-input">
			</div>
			<div class="server-table-wrap">
				<table class="data-table">
					<thead>
						<tr>
							<th>名称</th>
							<th>地址</th>
							<th>SSH端口</th>
							<th>用户</th>
							<th>Agent端口</th>
							<th>状态</th>
							<th>操作</th>
						</tr>
					</thead>
					<tbody id="servers-tbody">
						<tr><td colspan="7" class="empty-cell">加载中...</td></tr>
					</tbody>
				</table>
			</div>
		</div>

		<!-- Add Server Modal -->
		<div class="modal" id="add-server-modal">
			<div class="modal-content">
				<div class="modal-header">
					<h3>添加服务器</h3>
					<button class="modal-close" onclick="closeModal('add-server-modal')">✕</button>
				</div>
				<div class="modal-body">
					<div class="form-group">
						<label>服务器名称 *</label>
						<input type="text" id="srv-name" placeholder="例如：生产节点 / web-prod">
					</div>
					<div class="form-group">
						<label>IP / 主机名 *</label>
						<input type="text" id="srv-host" placeholder="例如：server.example.com">
					</div>
					<div class="form-row">
						<div class="form-group">
							<label>SSH 端口</label>
							<input type="number" id="srv-port" value="22">
						</div>
						<div class="form-group">
							<label>SSH 用户名</label>
							<input type="text" id="srv-user" value="root">
						</div>
					</div>
					<div class="form-row">
						<div class="form-group">
							<label>Agent 端口</label>
							<input type="number" id="srv-agent-port" value="8080">
						</div>
						<div class="form-group">
							<label>SSH 密钥路径</label>
							<input type="text" id="srv-keyfile" placeholder="/path/to/key.pem（可选）">
						</div>
					</div>
				</div>
				<div class="modal-footer">
					<button class="btn btn-secondary" onclick="closeModal('add-server-modal')">取消</button>
					<button class="btn btn-primary" onclick="addServer()">确认添加</button>
				</div>
			</div>
		</div>

		<!-- Deploy Modal -->
		<div class="modal" id="deploy-modal">
			<div class="modal-content">
				<div class="modal-header">
					<h3>🚀 一键部署</h3>
					<button class="modal-close" onclick="closeModal('deploy-modal')">✕</button>
				</div>
				<div class="modal-body">
					<div class="deploy-info" id="deploy-info"></div>
					<div class="form-group">
						<label>二进制文件路径</label>
						<input type="text" id="deploy-binary" value="build/server-health-monitor-agent">
					</div>
					<div class="form-group">
						<label>SSH / sudo 密码（仅本次部署使用）</label>
						<input type="password" id="deploy-ssh-password" autocomplete="new-password" placeholder="普通用户请输入 SSH 密码">
					</div>
					<div class="form-row">
						<div class="form-group"><label>服务器分组 ID（可选，批量部署）</label><input type="text" id="deploy-group-id" placeholder="从分组 API 获取"></div>
						<div class="form-group"><label>并发上限</label><input type="number" id="deploy-concurrency" value="4" min="1" max="32"></div>
					</div>
					<div class="deploy-output" id="deploy-output"></div>
				</div>
				<div class="modal-footer">
					<button class="btn btn-secondary" onclick="closeModal('deploy-modal')">关闭</button>
					<button class="btn btn-primary" id="deploy-btn" onclick="doDeploy()">开始部署</button>
				</div>
			</div>
		</div>
	` + serversPageScript
	w.Write([]byte(consoleLayoutHTML(content, "servers")))
}

func (h *Handler) handleTicketsPage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	content := `
		<div class="page-header"><div><h2>🎫 工单中心</h2><p class="page-desc">提交问题、跟踪处理进度和协作记录</p></div></div>
		<div class="section">
			<h3>提交工单</h3>
			<div class="form-group"><label>标题</label><input id="ticket-title" maxlength="120" placeholder="简要描述需要处理的问题"></div>
			<div class="form-group"><label>详细描述</label><textarea id="ticket-description" maxlength="10000" rows="5" placeholder="请提供现象、时间、影响范围和可复现信息"></textarea></div>
			<div class="form-row"><div class="form-group"><label>优先级</label><select id="ticket-priority"><option value="low">低</option><option value="normal" selected>普通</option><option value="high">高</option></select></div><div class="form-group"><label>&nbsp;</label><button class="btn btn-primary" onclick="createTicket()">提交工单</button></div></div>
		</div>
		<div class="section"><h3>工单列表</h3><div id="tickets-list" class="server-list">加载中...</div></div>
		<script>
		async function loadTickets(){const res=await apiCall('/console/api/tickets');if(!res.ok||!res.data.success)return;const list=res.data.data;document.getElementById('tickets-list').innerHTML=list.length?list.map(function(t){return '<div class="server-item"><div class="server-item-icon">🎫</div><div class="server-item-info"><div class="server-item-name">'+escapeHtml(t.title)+'</div><div class="server-item-host">'+escapeHtml(t.reporter)+' · '+escapeHtml(t.priority)+' · '+escapeHtml(t.status)+'</div></div></div>';}).join(''):'暂无工单';}
		async function createTicket(){const title=document.getElementById('ticket-title').value.trim(),description=document.getElementById('ticket-description').value.trim();if(!title||!description){toast('请填写标题和描述','error');return;}const res=await apiCall('/console/api/tickets','POST',{title:title,description:description,priority:document.getElementById('ticket-priority').value});if(res.ok&&res.data.success){toast('工单已提交','success');document.getElementById('ticket-title').value='';document.getElementById('ticket-description').value='';loadTickets();}else{toast(res.data.error||'提交失败','error');}}
		loadTickets();
		</script>`
	w.Write([]byte(consoleLayoutHTML(content, "tickets")))
}

func (h *Handler) handleUsersPage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	content := `
		<div class="page-header">
			<div>
				<h2>👥 用户管理</h2>
				<p class="page-desc">管理控制台用户、角色和权限</p>
			</div>
			<button class="btn btn-primary" onclick="openAddUser()">➕ 添加用户</button>
		</div>

		<div class="section">
			<div class="security-notice">
				<strong>🔒 安全策略：</strong>
				密码连续错误 3 次后账户将被永久锁定，需管理员手动解锁。
				登录需要 <strong>密码 + API 密钥</strong> 双重验证。
			</div>
		</div>

		<div class="section">
			<table class="data-table">
				<thead>
					<tr>
						<th>用户名</th>
						<th>角色</th>
						<th>状态</th>
						<th>错误次数</th>
						<th>最后登录</th>
						<th>创建时间</th>
						<th>操作</th>
					</tr>
				</thead>
				<tbody id="users-tbody">
					<tr><td colspan="7" class="empty-cell">加载中...</td></tr>
				</tbody>
			</table>
		</div>

		<!-- Add User Modal -->
		<div class="modal" id="add-user-modal">
			<div class="modal-content">
				<div class="modal-header">
					<h3>添加用户</h3>
					<button class="modal-close" onclick="closeModal('add-user-modal')">✕</button>
				</div>
				<div class="modal-body">
					<div class="form-group">
						<label>用户名 *</label>
						<input type="text" id="new-username" placeholder="用户名">
					</div>
					<div class="form-group">
						<label>密码 *</label>
						<input type="password" id="new-password" placeholder="至少 12 位，含大小写字母、数字和特殊字符">
					</div>
					<div class="form-group">
						<label>角色</label>
						<select id="new-role">
							<option value="owner">服主（全部权限，可管理权限组）</option>
							<option value="director">技术总监（运维与权限组）</option>
							<option value="viewer">查看者（只读）</option>
							<option value="reporter">报告提交者（工单）</option>
							<option value="operator">运维人员（服务操作）</option>
							<option value="custom">自定义权限组（仅服主/技术总监管理）</option>
							<option value="admin">管理员</option>
						</select>
					</div>
						<div class="form-group" id="custom-permissions-group" style="display:none">
							<label>自定义权限（仅服主/技术总监可设置）</label>
							<select id="custom-permissions" multiple size="5">
								<option value="dashboard:view">查看仪表盘</option>
								<option value="servers:view">查看服务器</option>
								<option value="servers:manage">管理服务器</option>
								<option value="tickets:create">提交工单</option>
								<option value="tickets:manage">处理工单</option>
								<option value="diagnostics:view">查看诊断</option>
							</select>
						</div>
					<div class="notice-box">
						<strong>⚠️ 注意：</strong>API 密钥创建后只会显示一次，请妥善保存。
					</div>
				</div>
				<div class="modal-footer">
					<button class="btn btn-secondary" onclick="closeModal('add-user-modal')">取消</button>
					<button class="btn btn-primary" onclick="addUser()">创建用户</button>
				</div>
			</div>
		</div>

		<!-- API Key Result Modal -->
		<div class="modal" id="apikey-modal">
			<div class="modal-content">
				<div class="modal-header">
					<h3>🔑 API 密钥</h3>
				</div>
				<div class="modal-body">
					<p>请妥善保存以下 API 密钥，<strong>只显示这一次！</strong></p>
					<div class="apikey-box" id="apikey-display"></div>
					<p class="apikey-hint">登录时需要输入此密钥作为第二验证因素。</p>
				</div>
				<div class="modal-footer">
					<button class="btn btn-primary" onclick="closeModal('apikey-modal')">我已保存</button>
				</div>
			</div>
		</div>
	` + usersPageScript
	w.Write([]byte(consoleLayoutHTML(content, "users")))
}

func (h *Handler) handleAuditPage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	content := `
		<div class="page-header">
			<div>
				<h2>📋 审计日志</h2>
				<p class="page-desc">所有操作记录，可追溯可审计</p>
			</div>
			<button class="btn btn-secondary" onclick="refreshAudit()">🔄 刷新</button>
		</div>

		<div class="section">
			<div class="toolbar">
				<input type="text" id="audit-user" placeholder="筛选用户..." oninput="refreshAudit()" class="search-input">
				<select id="audit-action" onchange="refreshAudit()" class="select-input">
					<option value="">全部操作</option>
					<option value="login">登录</option>
					<option value="login_failed">登录失败</option>
					<option value="user_create">创建用户</option>
					<option value="user_delete">删除用户</option>
					<option value="user_unlock">解锁用户</option>
					<option value="server_add">添加服务器</option>
					<option value="server_delete">删除服务器</option>
					<option value="deploy">部署</option>
				</select>
			</div>
			<table class="data-table">
				<thead>
					<tr>
						<th>时间</th>
						<th>用户</th>
						<th>操作</th>
						<th>目标</th>
						<th>详情</th>
						<th>IP</th>
						<th>结果</th>
					</tr>
				</thead>
				<tbody id="audit-tbody">
					<tr><td colspan="7" class="empty-cell">加载中...</td></tr>
				</tbody>
			</table>
		</div>
	` + auditPageScript
	w.Write([]byte(consoleLayoutHTML(content, "audit")))
}

func (h *Handler) handleToolsPage(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	content := toolsExtraStyles + toolsPageHTML + serversPageScript
	w.Write([]byte(consoleLayoutHTML(content, "tools")))
}

// dashboardScript is a lighter version of servers script for the dashboard
var dashboardScript = `
<script>
let allServers = [];
async function loadServers() {
	const res = await fetch('/console/api/servers').then(r => r.json());
	if (res.success) {
		allServers = res.data;
		updateDashboardStats(allServers);
	}
}
function updateDashboardStats(servers) {
	const onlineEl = document.getElementById('stat-online');
	const totalEl = document.getElementById('stat-servers');
	const offlineEl = document.getElementById('stat-offline');
	const listEl = document.getElementById('server-list');
	if (totalEl) totalEl.textContent = servers.length;
	let online = 0, offline = 0;
	servers.forEach(s => {
		if (s.status === 'online') online++;
		else offline++;
	});
	if (onlineEl) onlineEl.textContent = online;
	if (offlineEl) offlineEl.textContent = offline;
	if (listEl && servers.length > 0) {
		listEl.innerHTML = servers.map(s => {
			const cls = s.status === 'online' ? 'success' : 'danger';
			const txt = s.status === 'online' ? '在线' : '离线';
			return '<div class="server-item"><div class="server-item-icon">🖥️</div><div class="server-item-info"><div class="server-item-name">' + (s.name||'') + '</div><div class="server-item-host">' + (s.host||'') + ':' + s.agent_port + '</div></div><div class="server-item-status"><span class="badge badge-' + cls + '">' + txt + '</span></div></div>';
		}).join('');
	}
}
if (document.getElementById('server-list')) {
	loadServers();
	setInterval(loadServers, 30000);
}
</script>
`
