# Server Health Monitor v4.0.0

> 🚀 **v4.0 重大更新**：桌面端全面重写（液态玻璃 UI + 鼠标跟随），新增命令词典（120+ 命令）、模拟实战实验室（6 场景 21 题）、运维工具箱（8 工具）；服务器端扩展采集（Swap/TCP/网络速率/Top进程）+ 4 个新 API。

> ⚠️ **仓库迁移声明**
> 本项目原存放于 GitHub，因上传限制无法继续迭代，现已完整迁移至 Gitee 作为主仓库。
> 🔗 **主仓库地址：https://gitee.com/hanbeimuren/server-health-monitor-v2**
> 旧 GitHub 仓库仅做历史备份，不再接收新功能与修复。
>
> SCP:SL 服务端适配仅为内置示例模块；本项目是通用服务器健康监控与自动修复平台，并非 SCP:SL 专用工具。

面向生产环境的通用服务器健康监控与自动修复平台。项目包含 Go 监控 Agent、Web 管理控制台，以及 Prometheus/Grafana 集成。SCP:SL 作为一个可选应用适配器保留。

## ⚠️ 首次初始化（必读）

**管理控制台首次启动时必须创建管理员账户。**

### 初始管理员设置

#### 命令行初始化（推荐）

```bash
# 服务器端
server-health-monitor-console --admin-user <username> --admin-pass '<password>'
```

密码必须满足以下要求：
- **最少 12 个字符**
- 包含**大写字母** (A-Z)
- 包含**小写字母** (a-z)
- 包含**数字** (0-9)
- 包含**特殊字符** (!@#$%^&*._-~)

#### 示例（生成强随机密码）

```bash
# Linux / macOS
python3 -c "import secrets; print('P@ssw0rd' + secrets.token_hex(8))"

# PowerShell
$p = -join ((65..90) + (97..122) + (48..57) + (33,64,35,36,37,94,38,42,46,95,45,126) | Get-Random -Count 12 | % {[char]$_}); Write-Host $p
```

### 首次登录提示

⚠️ **重要**：首次使用初始管理员账户登录后，**必须立即修改密码**。系统会强制拦截：修改密码前无法访问控制台其他页面（仅可退出登录或完成改密）。API 密钥只显示一次，请妥善保存。

### CLI 兜底（锁定 / 遗失密钥）

当唯一管理员被锁或遗失 API 密钥、无法通过 Web 登录时，可在服务器上用命令行兜底：

```bash
# 解锁被锁定的账户
server-health-monitor-console --unlock-user <用户名>

# 重置密码（下次登录强制修改密码），需配合 --new-pass
server-health-monitor-console --reset-user-password <用户名> --new-pass '<新密码>'

# 轮换 API 密钥（只打印一次，请妥善保存）
server-health-monitor-console --rotate-user-key <用户名>
```

### 登录方式

Web 控制台使用**双重验证**：
- **第一因素**：用户名 + 密码
- **第二因素**：API 密钥（初始化时生成，仅显示一次）

如果遗失 API 密钥，管理员可通过 Web 界面重新生成。

## 功能

### 服务器端 Agent（Go）
- 监控 CPU、内存、Swap、磁盘、负载、进程数、文件描述符。
- 采集网络接口速率、TCP 连接统计、Top 5 进程、系统信息。
- 自动发现并监控服务实例（支持 systemd）。
- 异常达到阈值后自动重启，支持冷却、验证和熔断。
- 自适应异常检测（滑动窗口 Z-score + EWMA）。
- 告警管理：分组、抑制、升级、静默。
- Prometheus /metrics 端点 + Grafana 集成。
- 邮件 / ServerChan / Webhook 通知。
- API：`/api/status`、`/api/top`、`/api/network`、`/api/info`、`/api/services`、`/api/health`、`/api/ready`。

### 桌面客户端（Windows）
- 液态玻璃 UI，鼠标跟随光晕，流畅动画。
- 实时监控面板：CPU / 内存 / 磁盘 / 网络 / 告警。
- 管理控制台：服务状态、远程操作、熔断重置。
- **命令词典**：120+ 命令，覆盖 Linux / PowerShell / CMD / 网络 / 安全 / Docker / Git / 数据库，支持搜索、收藏、复制。
- **模拟实战实验室**：6 个交互式故障排查场景（CPU 飙高 / 网站宕机 / 磁盘满 / SSH 失败 / 内存泄漏 / DB 超时），21 道题带解析和评分。
- **运维工具箱**：Base64 / URL / JSON 格式化 / 时间戳 / 密码生成 / 哈希计算 / 进制转换 / 正则测试。
- 连接管理：多服务器配置，Basic Auth 支持。
- 运行日志查看。

### Web 管理控制台
- 多用户认证（密码 + API 密钥双重验证）。
- 服务器注册与分组管理。
- 实时仪表盘与历史趋势。
- 插件化适配器架构（generic / systemd / 自定义）。

## Extension Point

控制台部署支持通过 `internal/console/servers.Registry` 注册 Go `Adapter`，也支持独立进程扩展。扩展名称必须非空且唯一，可通过注册表列出或按名称获取。现有 `generic` 和 `systemd` 适配器仍然可用。

独立进程扩展由控制台直接启动（不经过 shell），通过 stdin 接收一条 JSON 请求，并通过 stdout 返回一条 JSON 响应：

```json
{"action":"preflight|install|health_check|rollback","server":{...},"options":{"binary_path":"...","adapter":"..."}}
```

响应格式为 `{"output":"..."}`，失败时为 `{"error":"..."}`。扩展进程必须支持上述四个动作。请求只包含服务器和非敏感选项；密码不会进入命令行、JSON、输出或持久化部署日志，而是仅通过 `DEPLOY_PASSWORD` 和 `DEPLOY_SUDO_PASSWORD` 环境变量提供。进程受 context 超时和 stdout/stderr 大小限制约束，超时、非零退出码及无效 JSON 都会使部署失败。扩展实现应避免输出凭据，控制台也会对已知密码进行脱敏。

## 快速安装

```bash
git clone https://gitee.com/hanbeimuren/server-health-monitor-v2.git
cd server-health-monitor-v2
sudo bash install.sh
```

安装脚本会自动：
- 检测 Linux 发行版和包管理器
- 检查依赖命令（iproute2、procps、util-linux 等）
- 安装 Go Agent、systemd unit 和配置文件
- 启用并启动 Agent

安装脚本需要 root 权限和 systemd。没有检测到游戏服务适配器时仍可安装通用 Agent；它不会安装任何业务应用本身。

Go Agent 默认仅监听 `127.0.0.1:8080`。如需远程访问，优先使用 SSH 隧道；若改为公网监听，必须同时启用认证或 TLS，并配置防火墙白名单。程序会拒绝无认证、无 TLS 的公网监听。

## 手动安装

```bash
sudo install -o root -g root -m 0755 build/server-health-monitor-agent /usr/local/sbin/server-health-monitor-agent
sudo install -o root -g root -m 0644 deploy/systemd/server-health-monitor-agent.service /etc/systemd/system/
sudo install -o root -g root -m 0640 server-health-monitor-agent.conf.example /etc/server-health-monitor-agent.conf
sudo systemctl daemon-reload
sudo systemctl enable --now server-health-monitor-agent.service
```

## 配置

编辑配置文件：

```bash
sudo vi /etc/server-health-monitor-agent.conf
```

### 关键参数

| 参数 | 默认值 | 说明 |
|---|---:|---|
| `service` | 空 | 自动发现 `scpsl-*.service` |
| `service_port` | 空 | 指定 UDP 端口 |
| `failure_threshold` | 3 | 连续异常后触发修复 |
| `restart_cooldown` | 300 秒 | 两次重启的最小间隔 |
| `max_restarts` | 3 | 1 小时内最多自动重启次数 |
| `restart_window` | 3600 秒 | 自动重启限制窗口 |
| `socket_wait_timeout` | 30 秒 | 重启后等待端口恢复 |
| `webhook_url` | 空 | Discord / Slack Webhook |
| `notify_cooldown` | 600 秒 | 通知冷却时间 |

`SERVICE` 留空时自动发现 `scpsl-*.service`；只监控一个实例时填写服务名和端口。通知通过 `WEBHOOK_URL` 配置 Discord 或 Slack 兼容 Webhook。

## 查看状态

```bash
systemctl status server-health-monitor-agent.service
journalctl -u server-health-monitor-agent.service -n 100 --no-pager
curl -fsS http://127.0.0.1:8080/api/health
```

## 运维操作

### Go Agent

```bash
sudo systemctl status server-health-monitor-agent.service
sudo journalctl -u server-health-monitor-agent.service -n 100 --no-pager
curl -fsS http://127.0.0.1:8080/api/health
curl -fsS http://127.0.0.1:8080/metrics
```

### 升级与卸载

升级前备份 `/etc/server-health-monitor-agent.conf` 和控制台数据目录。替换二进制或重新运行安装脚本后执行：

```bash
sudo systemctl daemon-reload
sudo systemctl restart server-health-monitor-agent.service
```

项目目前没有自动卸载脚本。确认不再需要后，先停止服务，再手动删除对应 unit、二进制、配置和状态目录；删除前请备份配置与审计数据。

## Prometheus + Grafana

```bash
cd deploy
set -a; . ./.env; set +a
docker compose up -d
```

创建 `deploy/.env`（不要提交）并设置强随机密码：

```dotenv
GRAFANA_ADMIN_PASSWORD=replace-with-a-long-random-password
```

- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000

启动前请编辑 [prometheus.yml](deploy/prometheus/prometheus.yml) 中的 Agent 地址。模板中的 target 只是本机示例，不适用于所有环境；如果 Agent 开启认证，还需要配置 Prometheus 的 `basic_auth`。Grafana 初始账号由 [docker-compose.yml](deploy/docker-compose.yml) 设置，首次登录后必须立即修改密码。

Go Agent 默认仅监听 `127.0.0.1:8080`。如需远程访问，优先使用 SSH 隧道；若改为公网监听，必须同时启用认证或 TLS，并配置防火墙白名单。程序会拒绝无认证、无 TLS 的公网监听。

### Go Agent 配置

配置模板见 [server-health-monitor-agent.conf.example](server-health-monitor-agent.conf.example)。常用配置如下：

```ini
# 仅本机访问，推荐配合 SSH 隧道
host = "127.0.0.1"
port = 8080

# 远程访问时至少启用认证，并通过 HTTPS 反向代理保护传输
auth_user = "admin"
auth_pass = "change-this-password"

collect_interval = 3
check_interval = 5
failure_threshold = 3
restart_cooldown = 300
max_restarts = 3
restart_window = 3600
socket_wait_timeout = 30
service = ""
service_port = ""
```

修改后执行：

```bash
sudo systemctl restart server-health-monitor-agent.service
sudo journalctl -u server-health-monitor-agent.service -n 100 --no-pager
```

### 端口与访问方式

| 组件 | 默认地址 | 用途 |
|------|----------|------|
| Go Agent | `127.0.0.1:8080` | 面板、`/api/status`、`/metrics` |
| 管理控制台 | `127.0.0.1:8081` | 用户、服务器和部署管理 |
| Prometheus | `0.0.0.0:9090` | 指标查询 |
| Grafana | `0.0.0.0:3000` | 可视化面板 |

推荐让 Agent 监听 `127.0.0.1`，再使用 SSH 隧道或 HTTPS 反向代理。若必须监听公网地址，请配置认证、防火墙白名单和 TLS；不要把管理控制台、Prometheus 或 Grafana 直接暴露给互联网。

### Windows 桌面版

Windows 用户不需要先打开浏览器或手动运行 Go 命令：

1. 双击 `启动服务器监控.cmd`，脚本会自动构建缺失的组件并启动桌面窗口。
2. 需要发布 EXE 时，在 PowerShell 执行 `powershell -ExecutionPolicy Bypass -File .\build-desktop.ps1`。
3. 构建完成后直接双击 `dist\ServerHealthMonitor.exe`。

桌面窗口内包含监控面板、管理控制台、服务器连接设置和运行日志。首次使用管理控制台时，在窗口的“管理控制台”页面创建管理员，不需要手动打开 `localhost`。

### 客户端连接路径

本地运行时有三种路径：

1. **SSH 隧道**：在桌面窗口的“连接设置”中填写服务器地址；这是公网服务器的默认推荐方式。
2. **HTTPS 直连**：选择“直接连接”，填写 Agent 的 HTTPS 地址和认证信息。
3. **内网反向代理**：选择“内网反向代理”，填写企业网关地址。

桌面客户端会把 Agent API 代理到本机，并在同一窗口中显示监控和日志；SSH 私钥、网关凭据和生产地址应放在本机私有配置或密钥管理系统中。

### 控制台

控制台提供用户、服务器、部署、诊断、审计和工单功能。权限由后端校验，前端隐藏按钮不是安全边界；高风险修复应先预览、确认，再执行和验证。服务器部署支持 root 或普通 SSH 用户 + sudo；部署窗口中的密码仅用于本次请求，不写入服务器清单、审计记录或部署日志。生产环境建议使用 SSH 密钥，并通过跳板机或密钥管理系统接入。

首次部署控制台时必须通过命令行安全初始化管理员：

```bash
server-health-monitor-console --admin-user <username> --admin-pass '<strong-password>'
```

登录需要密码和一次性 API 密钥。连续失败会临时锁定账户；遗失密钥时使用 `--rotate-user-key`，生产环境请设置 `CONSOLE_TOKEN_SECRET`，并通过 HTTPS、VPN 或 SSH 隧道访问 8081。

## 工作原理（简版）

Agent 定期采集指标并检查服务；连续异常达到阈值后执行受控重启，等待服务恢复并发送通知。超过自动重启上限后进入熔断，需要人工恢复。

<!-- diagram removed
每 15 秒触发一次（开机约 90 秒后开始）
     │
     ▼
┌─────────────────────┐
│  自动发现 SCP:SL     │  ← systemctl list-units + 磁盘扫描
│  systemd 服务实例     │
└─────────┬───────────┘
          │
          ▼ (对每个实例)
┌─────────────────────┐
│  收集指标            │  服务状态 / UDP 端口 / 进程数
│                     │  磁盘 / 内存 / CPU / 负载 / 错误日志
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  健康评估            │  healthy / socket-missing / service-inactive
└─────────┬───────────┘
          │
     ┌────┴────┐
     │         │
  healthy    unhealthy
     │         │
     │         ▼
     │    ┌──────────────────┐
     │    │ 连续 N 次异常?   │── No → 记录状态，等待下次检查
     │    └────────┬─────────┘
     │             │ Yes
     │             ▼
     │    ┌──────────────────┐
     │    │ 冷却时间已过?     │── No → 记录 suppressed，等待
     │    └────────┬─────────┘
     │             │ Yes
     │             ▼
     │    ┌──────────────────┐
     │    │ systemctl restart │── webhook 通知
     │    └────────┬─────────┘
     │             │
     │             ▼
     │    ┌──────────────────┐
     │    │ 等待 UDP 恢复     │  最长 SOCKET_WAIT_TIMEOUT 秒
     │    └────────┬─────────┘
     │             │
     ▼             ▼
┌──────────────────────────┐
│  运行状态与指标           │  Agent 内存、Prometheus 与中心平台存储
│  webhook 恢复通知         │
└──────────────────────────┘
```
-->

## 安全说明

- 脚本需要 root 权限运行（读取 systemd/journal 状态，可能执行 `systemctl restart`）
- systemd unit 已做安全加固：NoNewPrivileges、ProtectSystem=full、ProtectHome、ProtectKernelTunables/Modules/Logs 等
- 状态文件权限 0640，目录 0750
- Webhook 通知使用 curl 发送，超时 10 秒，失败不影响主流程
- Agent 和控制台当前使用 HTTP，不提供内置 TLS；生产环境应通过 SSH 隧道或 HTTPS 反向代理访问
- 双凭据登录是密码加 API key，不等同于 TOTP 或硬件密钥；API key 只在创建或轮换时显示一次
- 控制台默认不信任 `X-Forwarded-For`（防伪造 IP 绕过限流）；仅在反向代理之后设置 `CONSOLE_TRUST_PROXY=1`
- HTTPS 之后请设置 `CONSOLE_COOKIE_SECURE=1`，让登录 Cookie 携带 Secure 标志

## 兼容性

| 发行版 | 支持状态 | 备注 |
|--------|---------|------|
| Debian / Ubuntu | ✅ 完全支持 | 需要 iproute2、procps、util-linux |
| RHEL / CentOS / Rocky / Alma | ✅ 完全支持 | 需要 iproute、procps-ng |
| openSUSE | ✅ 完全支持 | 需要 iproute2 |
| Arch Linux | ✅ 完全支持 | 需要 iproute2、procps-ng |
| Alpine Linux | ⚠️ 需额外配置 | 默认不是 systemd，需先提供 systemd 环境 |
| 其他 systemd 发行版 | ⚠️ 通常可运行 | 需要 bash 4+、systemd 和系统工具 |

安装脚本会自动检测发行版和包管理器，在缺少依赖时给出安装提示。Go Agent 是唯一的监控与自动修复入口，避免多套实现同时操作同一实例。

## 常见问题

- **没有发现实例**：确认服务名称符合 `scpsl-<数字>.service`，并运行 `systemctl list-units --type=service --all` 检查。
- **面板打不开**：检查 `systemctl status server-health-monitor-agent.service`、监听地址、防火墙和 `ss -lntp | grep 8080`。
- **自动重启未触发**：确认服务状态或 UDP 端口确实异常，并检查 `failure_threshold` 与 `restart_cooldown`。
- **Prometheus 无数据**：检查 target 地址、容器到 Agent 的网络连通性、防火墙以及 `/metrics` 是否可访问。
- **控制台无法登录**：首次运行必须用 `--admin-user` 和 `--admin-pass` 创建管理员；API key 使用创建时输出的值。账户被锁或遗失密钥时，在服务器上用 `--unlock-user`、`--reset-user-password`、`--rotate-user-key` 兜底（见上文）。

## 开发

```bash
go test ./...
```

Windows 桌面版构建：

```powershell
powershell -ExecutionPolicy Bypass -File .\build-desktop.ps1
```

##676767676767 寒碑墓人出品 持续更新ING

## 许可证

[MIT](LICENSE)
