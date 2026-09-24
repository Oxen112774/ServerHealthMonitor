package web

// Landing page for the open-source project
var landingPageHTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Server Health Monitor — 运营中枢</title>
<meta name="description" content="专业运维中枢：多服务器健康监控、告警、自动修复和安全管理。">
<style>
:root {
  --bg: #06111d;
  --bg-soft: #0b1627;
  --panel: rgba(17, 25, 38, 0.76);
  --panel-strong: rgba(10, 18, 29, 0.96);
  --line: rgba(148, 163, 184, 0.18);
  --text: #edf5ff;
  --muted: #9db0c8;
  --primary: #7c9bff;
  --primary-2: #8be9ff;
  --green: #67f0b7;
  --amber: #f5c777;
  --red: #ff7e8d;
  --purple: #9a8cff;
  --shadow: 0 36px 80px rgba(2, 6, 18, 0.52);
}

* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  margin: 0;
  font-family: Inter, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(124, 155, 255, 0.22), transparent 28%),
    radial-gradient(circle at top right, rgba(139, 233, 255, 0.16), transparent 26%),
    linear-gradient(180deg, #030b14 0%, #091725 40%, #07131f 100%);
  color: var(--text);
  min-height: 100vh;
}
a { color: inherit; text-decoration: none; }
img { max-width: 100%; }

.topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  backdrop-filter: blur(18px);
  background: rgba(6, 17, 29, 0.72);
  border-bottom: 1px solid var(--line);
}
.topbar-inner {
  max-width: 1280px;
  margin: 0 auto;
  height: 76px;
  padding: 0 26px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
}
.brand-mark {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  background: linear-gradient(135deg, rgba(124,155,255,0.3), rgba(154,140,255,0.1));
  border: 1px solid rgba(124,155,255,0.35);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.18);
}
.brand-name {
  font-size: 1.02rem;
}
.nav {
  display: flex;
  align-items: center;
  gap: 26px;
  color: var(--muted);
  font-size: 0.93rem;
}
.nav a:hover { color: var(--text); }
.nav-cta {
  padding: 10px 18px;
  border-radius: 12px;
  border: 1px solid rgba(124,155,255,0.4);
  background: linear-gradient(135deg, rgba(124,155,255,0.18), rgba(139,233,255,0.08));
  color: var(--text) !important;
  box-shadow: 0 14px 28px rgba(124,155,255,0.16);
}

.hero {
  max-width: 1280px;
  margin: 0 auto;
  padding: 76px 26px 24px;
}
.hero-shell {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  gap: 32px;
  align-items: center;
  min-height: 680px;
}
.hero-copy {
  position: relative;
  z-index: 1;
}
.badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  border-radius: 999px;
  padding: 9px 18px;
  font-size: 0.74rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  background: rgba(124, 155, 255, 0.1);
  border: 1px solid rgba(124, 155, 255, 0.2);
  color: #afc1ff;
}
.badge-dot {
  width: 9px;
  height: 9px;
  border-radius: 50%;
  background: var(--green);
  box-shadow: 0 0 0 0 rgba(103, 240, 183, 0.7);
  animation: pulse 2s infinite;
}
@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(103, 240, 183, 0.5); }
  70% { box-shadow: 0 0 0 12px rgba(103, 240, 183, 0); }
  100% { box-shadow: 0 0 0 0 rgba(103, 240, 183, 0); }
}
.hero h1 {
  margin: 26px 0 18px;
  font-size: clamp(2.8rem, 5vw, 5rem);
  line-height: 0.96;
  letter-spacing: -0.06em;
}
.hero h1 .gradient {
  display: inline-block;
  background: linear-gradient(135deg, #fbfdff 0%, #a4c0ff 35%, #8be9ff 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero-sub {
  max-width: 620px;
  font-size: 1.08rem;
  line-height: 1.85;
  color: var(--muted);
}
.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  margin-top: 32px;
}
.primary-btn, .secondary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 52px;
  padding: 0 22px;
  border-radius: 14px;
  font-weight: 700;
  letter-spacing: 0.01em;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.primary-btn {
  background: linear-gradient(135deg, var(--primary), var(--primary-2));
  color: #07131f;
  box-shadow: 0 25px 40px rgba(124,155,255,0.28);
}
.secondary-btn {
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--line);
  color: var(--text);
}
.primary-btn:hover, .secondary-btn:hover {
  transform: translateY(-2px);
}
.stats-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(110px, 1fr));
  gap: 14px;
  margin-top: 36px;
}
.stat-box {
  background: rgba(13, 25, 38, 0.8);
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 18px 16px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}
.stat-box strong {
  display: block;
  font-size: 1.7rem;
  letter-spacing: -0.04em;
  margin-bottom: 4px;
}
.stat-box span {
  color: var(--muted);
  font-size: 0.78rem;
}

.visual-panel {
  position: relative;
  min-height: 560px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.panel-3d {
  position: relative;
  width: min(100%, 540px);
  min-height: 520px;
  border-radius: 30px;
  padding: 24px;
  background: linear-gradient(180deg, rgba(17, 25, 38, 0.88), rgba(8, 14, 24, 0.95));
  border: 1px solid rgba(148, 163, 184, 0.2);
  box-shadow: var(--shadow);
}
.panel-3d::before {
  content: "";
  position: absolute;
  inset: 12px;
  border-radius: 24px;
  border: 1px solid rgba(124,155,255,0.12);
  pointer-events: none;
}
.monitor-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 8px 18px;
}
.dot-group {
  display: flex;
  gap: 8px;
}
.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}
.dot.red { background: var(--red); }
.dot.amber { background: var(--amber); }
.dot.green { background: var(--green); }
.browser-pill {
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 999px;
  padding: 7px 12px;
  background: rgba(255,255,255,0.018);
  color: var(--muted);
  font-size: 0.72rem;
}
.board {
  margin-top: 10px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.card {
  position: relative;
  background: linear-gradient(180deg, rgba(16, 26, 38, 0.96), rgba(10, 16, 24, 0.96));
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 18px;
  padding: 18px 16px;
}
.card h3 {
  margin: 0 0 14px;
  font-size: 0.8rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  font-weight: 700;
}
.score {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: -0.05em;
  color: var(--text);
}
.score-sub {
  color: var(--green);
  font-size: 0.75rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
.mini-bars {
  display: flex;
  align-items: end;
  height: 120px;
  gap: 10px;
  margin-top: 18px;
}
.mini-bars span {
  display: block;
  flex: 1;
  border-radius: 999px 999px 0 0;
  background: linear-gradient(180deg, var(--primary-2), var(--primary));
  opacity: 0.85;
}
.mini-bars span:nth-child(1) { height: 32%; }
.mini-bars span:nth-child(2) { height: 54%; }
.mini-bars span:nth-child(3) { height: 76%; }
.mini-bars span:nth-child(4) { height: 68%; }
.mini-bars span:nth-child(5) { height: 94%; }
.list {
  margin-top: 18px;
  display: grid;
  gap: 8px;
}
.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(148,163,184,0.08);
  color: var(--muted);
  font-size: 0.8rem;
}
.row strong {
  color: var(--text);
  font-size: 0.82rem;
}
.badge-live {
  padding: 5px 8px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  background: rgba(103,240,183,0.08);
  border: 1px solid rgba(103,240,183,0.18);
  color: var(--green);
}
.floating-panel {
  position: absolute;
  right: -8px;
  bottom: 42px;
  width: 200px;
  padding: 18px 16px;
  border-radius: 18px;
  border: 1px solid rgba(124,155,255,0.28);
  background: rgba(8,18,30,0.92);
  box-shadow: var(--shadow);
}
.floating-panel small {
  display: block;
  color: var(--muted);
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 8px;
}
.floating-panel strong {
  display: block;
  font-size: 1.9rem;
  letter-spacing: -0.04em;
  margin-bottom: 8px;
}
.floating-panel span {
  color: var(--green);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.section {
  max-width: 1280px;
  margin: 0 auto;
  padding: 36px 26px 18px;
}
.section-head {
  text-align: center;
  margin-bottom: 34px;
}
.kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  font-size: 0.72rem;
  color: #b6c9ff;
  background: rgba(124,155,255,0.08);
  border: 1px solid rgba(124,155,255,0.16);
}
.section-head h2 {
  margin: 18px 0 12px;
  font-size: clamp(2rem, 3vw, 3rem);
  line-height: 1.1;
  letter-spacing: -0.05em;
}
.section-head p {
  margin: 0 auto;
  max-width: 720px;
  color: var(--muted);
  font-size: 1.02rem;
  line-height: 1.8;
}
.feature-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18px;
}
.feature-card {
  background: rgba(12, 21, 31, 0.78);
  border: 1px solid var(--line);
  border-radius: 24px;
  padding: 22px 20px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
  transition: transform 0.2s ease, border-color 0.2s ease;
}
.feature-card:hover {
  transform: translateY(-2px);
  border-color: rgba(124,155,255,0.44);
}
.feature-icon {
  width: 52px;
  height: 52px;
  border-radius: 16px;
  display: grid;
  place-items: center;
  font-size: 1.5rem;
  background: linear-gradient(135deg, rgba(124,155,255,0.18), rgba(139,233,255,0.1));
  border: 1px solid rgba(124,155,255,0.2);
}
.feature-card h3 {
  margin: 16px 0 10px;
  font-size: 1.15rem;
}
.feature-card p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
  font-size: 0.96rem;
}

.arch-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 18px;
  margin-top: 26px;
}
.arch-node {
  background: rgba(11, 22, 32, 0.82);
  border: 1px solid var(--line);
  border-radius: 22px;
  padding: 20px 16px 18px;
  text-align: center;
  min-height: 180px;
}
.arch-node .node-icon {
  width: 58px;
  height: 58px;
  border-radius: 18px;
  margin: 0 auto 14px;
  display: grid;
  place-items: center;
  font-size: 1.7rem;
  background: linear-gradient(135deg, rgba(124,155,255,0.18), rgba(154,140,255,0.12));
  border: 1px solid rgba(124,155,255,0.2);
}
.arch-node h4 {
  margin: 0 0 8px;
  font-size: 1rem;
}
.arch-node p {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
  font-size: 0.83rem;
}

.cta-wrap {
  max-width: 1280px;
  margin: 30px auto 80px;
  padding: 0 26px;
}
.cta-box {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22px;
  padding: 30px 28px;
  border-radius: 26px;
  background: linear-gradient(135deg, rgba(124,155,255,0.12), rgba(154,140,255,0.08), rgba(139,233,255,0.06));
  border: 1px solid rgba(124,155,255,0.22);
  box-shadow: var(--shadow);
}
.cta-box:before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 20%, rgba(255,255,255,0.04) 50%, transparent 80%);
  transform: translateX(-100%);
  animation: sheen 7s linear infinite;
}
@keyframes sheen {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}
.cta-copy {
  position: relative;
  z-index: 1;
}
.cta-copy h3 {
  margin: 0 0 10px;
  font-size: clamp(1.8rem, 2.5vw, 2.6rem);
  letter-spacing: -0.05em;
}
.cta-copy p {
  margin: 0;
  color: var(--muted);
  line-height: 1.8;
}
.cta-actions {
  position: relative;
  z-index: 1;
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

footer {
  max-width: 1280px;
  margin: 0 auto 32px;
  padding: 0 26px;
  color: var(--muted);
  border-top: 1px solid var(--line);
}
.footer-inner {
  padding-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  font-size: 0.86rem;
}
.footer-links {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
}

@media (max-width: 980px) {
  .hero-shell { grid-template-columns: 1fr; }
  .feature-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .arch-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .cta-box { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 720px) {
  .nav { display: none; }
  .topbar-inner { padding: 0 16px; }
  .hero { padding-left: 16px; padding-right: 16px; }
  .stats-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .feature-grid, .arch-grid { grid-template-columns: 1fr; }
  .footer-inner { flex-direction: column; align-items: flex-start; }
}
</style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-inner">
      <div class="brand">
        <div class="brand-mark">🛡️</div>
        <div class="brand-name">Server Health Monitor</div>
      </div>
      <nav class="nav">
        <a href="#overview">概览</a>
        <a href="#features">功能</a>
        <a href="#architecture">架构</a>
        <a href="#start">开始</a>
        <a href="/console/login" class="nav-cta">进入控制台</a>
      </nav>
    </div>
  </header>

  <main>
    <section class="hero" id="overview">
      <div class="hero-shell">
        <div class="hero-copy">
          <div class="badge"><span class="badge-dot"></span> 运维中枢</div>
          <h1>多服务器 <span class="gradient">运行状态</span> 监控平台</h1>
          <p class="hero-sub">
            面向高可用运维与个人服务器场景设计的统一控制台，实时感知健康状态、检测异常、自动恢复服务，并把风险变成可执行行动。
          </p>
          <div class="hero-actions">
            <a class="primary-btn" href="/console/login">🚀 进入控制台</a>
            <a class="secondary-btn" href="#features">了解功能</a>
          </div>
          <div class="stats-row">
            <div class="stat-box">
              <strong>24/7</strong>
              <span>持续监控</span>
            </div>
            <div class="stat-box">
              <strong>&lt;20MB</strong>
              <span>轻量占用</span>
            </div>
            <div class="stat-box">
              <strong>5s</strong>
              <span>检测周期</span>
            </div>
            <div class="stat-box">
              <strong>100%</strong>
              <span>开源免费</span>
            </div>
          </div>
        </div>

        <div class="visual-panel">
          <div class="panel-3d">
            <div class="monitor-header">
              <div class="dot-group">
                <span class="dot red"></span>
                <span class="dot amber"></span>
                <span class="dot green"></span>
              </div>
              <div class="browser-pill">Server Health Monitor</div>
            </div>

            <div class="board">
              <div class="card">
                <h3>整体健康</h3>
                <div class="score">99.2%</div>
                <div class="score-sub">稳定</div>
              </div>

              <div class="card">
                <h3>延迟</h3>
                <div class="score">42ms</div>
                <div class="score-sub">正常</div>
              </div>
            </div>

            <div class="card" style="margin-top: 16px;">
              <h3>服务趋势</h3>
              <div class="mini-bars">
                <span></span>
                <span></span>
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>

            <div class="list">
              <div class="row">
                <strong>web-prod-01</strong>
                <span class="badge-live">在线</span>
              </div>
              <div class="row">
                <strong>game-asia-02</strong>
                <span class="badge-live">在线</span>
              </div>
              <div class="row">
                <strong>db-backup-03</strong>
                <span class="badge-live">稳定</span>
              </div>
            </div>
          </div>

          <div class="floating-panel">
            <small>自动恢复</small>
            <strong>12</strong>
            <span>次已恢复</span>
          </div>
        </div>
      </div>
    </section>

    <section class="section" id="features">
      <div class="section-head">
        <div class="kicker">功能</div>
        <h2>从“监控”到“协同修复”</h2>
        <p>把系统状态、事件与动作收敛到一个统一界面，让服务器健康管理从被动观测变成主动运营。</p>
      </div>

      <div class="feature-grid">
        <article class="feature-card">
          <div class="feature-icon">📡</div>
          <h3>实时探测</h3>
          <p>通过端口、进程和服务状态持续检测，及时发现异常波动与宕机风险。</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">🧠</div>
          <h3>智能判断</h3>
          <p>分析 CPU、内存、磁盘、网络等维度，快速识别问题类型并判断异常严重程度。</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">🔧</div>
          <h3>自动修复</h3>
          <p>在安全阈值下自动执行服务重启、清理动作，减少人工介入，提高恢复效率。</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">🔔</div>
          <h3>多渠道告警</h3>
          <p>支持消息通知、Webhook 与自定义告警渠道，把风险推送到你最关心的终端。</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">📊</div>
          <h3>可视化分析</h3>
          <p>从趋势图到关键指标，业务状态一目了然，帮助你快速定位根因与演化轨迹。</p>
        </article>
        <article class="feature-card">
          <div class="feature-icon">🛡️</div>
          <h3>安全管理</h3>
          <p>认证、审计、权限控制与部署保护配套完善，适合团队协作和生产环境使用。</p>
        </article>
      </div>
    </section>

    <section class="section" id="architecture">
      <div class="section-head">
        <div class="kicker">架构</div>
        <h2>统一、扩展、可维护</h2>
        <p>采用清晰分层设计，覆盖监控、控制、部署、告警和安全四大核心能力。</p>
      </div>

      <div class="arch-grid">
        <div class="arch-node">
          <div class="node-icon">💻</div>
          <h4>控制台</h4>
          <p>统一管理服务器、用户与权限，提供直观管理入口。</p>
        </div>
        <div class="arch-node">
          <div class="node-icon">🧩</div>
          <h4>Agent</h4>
          <p>在目标服务器端持续采集状态，进行健康检测与恢复动作。</p>
        </div>
        <div class="arch-node">
          <div class="node-icon">📈</div>
          <h4>指标</h4>
          <p>通过标准化指标输出为观察、告警和大屏分析提供统一数据源。</p>
        </div>
        <div class="arch-node">
          <div class="node-icon">🛟</div>
          <h4>修复</h4>
          <p>结合策略与手动干预，做到快速恢复、风险控制与流程闭环。</p>
        </div>
      </div>
    </section>

    <section class="cta-wrap" id="start">
      <div class="cta-box">
        <div class="cta-copy">
          <div class="kicker" style="margin-bottom: 14px;">开始使用</div>
          <h3>从今天开始，把运维变成可视化、可操作、可学习</h3>
          <p>面向新手友好，适合团队协作与个人服务器管理，不再只是“看日志”。</p>
        </div>
        <div class="cta-actions">
          <a class="primary-btn" href="/console/login">进入控制台</a>
          <a class="secondary-btn" href="https://github.com/Oxen112774/ServerHealthMonitor">GitHub</a>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <div class="footer-inner">
      <div>© 2026 Server Health Monitor</div>
      <div class="footer-links">
        <a href="#overview">概览</a>
        <a href="#features">功能</a>
        <a href="#architecture">架构</a>
        <a href="/console/login">控制台</a>
      </div>
    </div>
  </footer>
</body>
</html>`
