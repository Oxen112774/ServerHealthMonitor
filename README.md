# Server Health Monitor v5.0

> 面向生产环境的**服务器运维一体智能插件**。Go 高性能 Agent + Windows 桌面客户端 + Web 管理控制台，三位一体覆盖监控、告警、自愈、远程运维全流程。

[![Gitee](https://img.shields.io/badge/Gitee-主仓库-red?logo=gitee)](https://gitee.com/hanbeimuren/server-health-monitor-v2)
[![GitHub](https://img.shields.io/badge/GitHub-镜像-181717?logo=github)](https://github.com/Oxen112774/ServerHealthMonitor)
[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8?logo=go)](https://go.dev/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](#)

## ⚠️ 仓库说明

本项目同时托管于 **Gitee（主仓库）** 和 **GitHub（镜像）**，双仓库同步更新。

🔗 **Gitee 主仓库：https://gitee.com/hanbeimuren/server-health-monitor-v2**
🔗 **GitHub 镜像：https://github.com/Oxen112774/ServerHealthMonitor**

> SCP:SL 服务端适配仅为内置示例模块；本项目是通用服务器健康监控与自动修复平台，并非 SCP:SL 专用工具。

## ✨ 项目亮点

### 🎯 监控即插即用
- **零依赖单二进制**：Go 编译的 Agent 拷贝到服务器直接运行，无需安装运行时
- **自动发现服务**：systemd 服务自动识别，支持自定义服务名和端口
- **全维度指标**：CPU / 内存 / Swap / 磁盘 / 负载 / 网络速率 / TCP连接 / 文件描述符 / Top进程 / 系统信息

### 🛡️ 自动修复闭环
- 故障检测 → 自动重启 → 冷却验证 → 熔断保护，完整自愈链路
- 自适应异常检测（滑动窗口 Z-score + EWMA），捕捉慢泄漏和突发尖峰
- 告警分组 / 抑制 / 升级 / 静默，减少 60%+ 重复告警

### 🖥️ 桌面端 v5.0 全新改版
- **粒子背景动画**：Canvas 粒子网络 + 连线，科技感拉满
- **数字滚动动画**：指标变化时平滑过渡，实时趋势图带发光效果
- **液态玻璃 UI**：毛玻璃卡片 + 3D 悬浮 + 渐变光效
- **4 核心页签**：监控面板 / 远程控制台 / 连接设置 / 运行日志，聚焦运维
- **快捷运维**：一键查看进程、磁盘、内存、网络、日志、服务状态
- **实时图表**：CPU/内存/磁盘 60 秒趋势图，带渐变填充和发光线条

### 🔌 开放集成
- Prometheus `/metrics` 端点 + Grafana 仪表盘开箱即用
- 邮件 / ServerChan(微信) / Webhook 三种通知渠道
- 插件化适配器架构，支持自定义服务类型
- RESTful API，方便二次开发

## 🏗️ 技术架构

```
┌─────────────────────────────────────────────────┐
│              Windows 桌面客户端 v5.0              │
│   监控面板 │ 远程控制台 │ 连接设置 │ 运行日志      │
│  (Python + PyWebView, 粒子动画+液态玻璃UI)        │
└────────────────────┬────────────────────────────┘
                     │ HTTP/HTTPS (Basic Auth)
┌────────────────────▼────────────────────────────┐
│            Go Agent (服务器端)                    │
│  采集器 │ 监控器 │ 异常检测 │ 告警管理 │ 自动修复   │
│  API: /api/status /top /network /info /services  │
└────────────────────┬────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────┐
│         Web 控制台 (多用户 + 插件扩展)             │
│  用户认证 │ 服务器管理 │ 仪表盘 │ 工单系统          │
└─────────────────────────────────────────────────┘
```

## 📦 功能清单

### 服务器端 Agent（Go）
- 监控 CPU、内存、Swap、磁盘、负载、进程数、文件描述符
- 采集网络接口速率、TCP 连接统计、Top 5 进程、系统信息
- 自动发现并监控服务实例（支持 systemd）
- 异常达到阈值后自动重启，支持冷却、验证和熔断
- 自适应异常检测（滑动窗口 Z-score + EWMA）
- 告警管理：分组、抑制、升级、静默
- Prometheus /metrics 端点 + Grafana 集成
- 邮件 / ServerChan / Webhook 通知

### 桌面客户端（Windows）
- 液态玻璃 UI，鼠标跟随光晕，流畅动画
- 实时监控面板：CPU / 内存 / 磁盘 / 网络 / 告警
- 管理控制台：服务状态、远程操作、熔断重置
- **命令词典**：120+ 命令，12 大分类，支持搜索、收藏、复制
- **模拟实战实验室**：12 场景 43 题，交互式评分和解析
- **运维工具箱**：8 个实用工具，全部本地运行
- 连接管理：多服务器配置，Basic Auth 支持
- 运行日志查看

### Web 管理控制台
- 多用户认证（密码 + API 密钥双重验证）
- 服务器注册与分组管理
- 实时仪表盘与历史趋势
- 插件化适配器架构（generic / systemd / 自定义）

## 🚀 快速开始

### 服务器端（Linux）

```bash
# 克隆仓库
git clone https://gitee.com/hanbeimuren/ServerHealthMonitor.git
cd ServerHealthMonitor

# 编译 Agent
go build -o server-health-monitor-agent ./cmd/agent

# 复制配置并修改
cp server-health-monitor-agent.conf.example /etc/server-health-monitor-agent.conf
vim /etc/server-health-monitor-agent.conf

# 安装为 systemd 服务
cp deploy/systemd/server-health-monitor-agent.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now server-health-monitor-agent

# 验证
curl http://localhost:8080/api/health
```

### 桌面端（Windows）

1. 下载 `ServerHealthMonitor.exe`（或自行用 PyInstaller 打包）
2. 双击运行，首次打开自动初始化
3. 进入「连接」页面，填写服务器地址和端口
4. 开始监控

### 桌面端自行打包

```bash
pip install -r desktop-requirements.txt
pyinstaller --clean --noconfirm ServerHealthMonitor.spec
```

## 📡 API 一览

| 端点 | 方法 | 说明 | 认证 |
|------|------|------|------|
| `/api/status` | GET | 全量指标 + 实例状态 + 告警 + 历史趋势 | Basic Auth |
| `/api/top` | GET | Top 5 进程（CPU/内存/PID/用户） | Basic Auth |
| `/api/network` | GET | 网卡速率 + TCP连接统计 + 连通性 | Basic Auth |
| `/api/info` | GET | 系统信息（OS/内核/架构/运行时间） | Basic Auth |
| `/api/services` | GET | systemd 服务列表（支持 ?filter=running） | Basic Auth |
| `/api/remediation/reset` | POST | 重置熔断状态 | Basic Auth |
| `/api/health` | GET | 健康检查 | 无需认证 |
| `/api/ready` | GET | 就绪探针（优雅关闭时返回 503） | 无需认证 |
| `/metrics` | GET | Prometheus 指标 | 可配置认证 |

## 🎮 模拟实战场景

| # | 场景 | 难度 | 题数 | 核心知识点 |
|---|------|------|------|-----------|
| 1 | 🔥 CPU 飙高排查 | 入门 | 4 | top定位 → 确认身份 → 清除后门 → 修复Redis未授权 |
| 2 | 🌐 网站无法访问 | 入门 | 3 | 502排查 → 日志找崩溃原因 → OOM处理 |
| 3 | 💾 磁盘空间爆满 | 入门 | 3 | du定位 → logrotate轮转 → deleted but open文件 |
| 4 | 🔑 SSH登录失败 | 进阶 | 3 | refused vs timeout → 防火墙 → 密钥权限 |
| 5 | 📈 内存泄漏排查 | 进阶 | 3 | top观察RES → jmap堆快照 → 缓存LRU |
| 6 | 🗄️ 数据库连接超时 | 高级 | 3 | 连通性确认 → 连接数满处理 → 慢查询优化 |
| 7 | 🔴 Nginx 502排查 | 入门 | 4 | 502 vs 504 → 后端状态 → Connection refused → 超时配置 |
| 8 | 🟡 Redis连接超时 | 进阶 | 4 | maxmemory满 → 淘汰策略 → 大key阻塞 → 主从同步 |
| 9 | 🟠 MySQL慢查询 | 进阶 | 4 | 慢查询日志 → EXPLAIN全表扫描 → 索引失效 → 连接数满 |
| 10 | 🔵 Docker容器退出 | 入门 | 3 | docker logs → 退出码137(OOM) → 启动命令错误 |
| 11 | 🟣 K8s Pod崩溃 | 进阶 | 4 | describe events → OOMKilled → ConfigMap挂载 → liveness探针 |
| 12 | 🟢 DNS解析失败 | 入门 | 3 | resolv.conf → 53端口拦截 → 部分域名解析失败 |

## 📖 命令词典分类

| 分类 | 命令数 | 代表命令 |
|------|--------|----------|
| 🐧 Linux | 18 | top, htop, ps, df, free, systemctl, journalctl |
| 🔵 PowerShell | 10 | Get-Process, Get-Service, Restart-Service, Invoke-WebRequest |
| ⚫ CMD | 8 | tasklist, taskkill, netstat, ipconfig, sfc |
| 🌐 网络 | 12 | ping, traceroute, dig, nslookup, ss, netcat, curl |
| 🔒 安全 | 10 | iptables, ufw, fail2ban, ssh-keygen, openssl |
| 🐳 Docker | 10 | docker ps, logs, exec, compose, build, system prune |
| 📦 Git | 8 | git status, log, reflog, reset, cherry-pick, stash |
| 🗄️ 数据库 | 10 | mysql, redis-cli, mongosh, pg_dump, EXPLAIN |
| 📊 监控 | 8 | vmstat, iostat, sar, dstat, glances, prometheus |
| 📝 文本处理 | 8 | grep, awk, sed, cut, sort, uniq, wc, less |
| 💾 磁盘/文件 | 8 | du, df, mount, fsck, rsync, tar, dd, lsof |
| ⚙️ 系统管理 | 10 | systemctl, crontab, nice, renice, ulimit, sysctl |

## ⚠️ 首次初始化（必读）

**管理控制台首次启动时必须创建管理员账户。**

### 命令行初始化（推荐）

```bash
server-health-monitor-console --admin-user <username> --admin-pass '<password>'
```

密码要求：最少 12 字符，包含大写字母、小写字母、数字、特殊字符。

### 登录方式

Web 控制台使用**双重验证**：
- **第一因素**：用户名 + 密码
- **第二因素**：API 密钥（初始化时生成，仅显示一次）

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

- 发现 Bug？请提 Issue 并附上复现步骤和环境信息
- 有新功能想法？欢迎讨论，先提 Issue 再写代码
- 想加命令词典条目或模拟实战场景？直接 PR
- 代码提交前请运行 `go vet ./...` 和相关测试

## 📄 许可证

MIT License

---

##676767676767 寒碑墓人出品 持续更新ING
