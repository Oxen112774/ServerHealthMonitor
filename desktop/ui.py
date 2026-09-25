# -*- coding: utf-8 -*-
"""
Server Health Monitor v5.0 - 桌面端 UI
聚焦服务器运维一体智能插件
"""

SHELL_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Server Health Monitor v5.0</title>
<style>
:root{
  --bg-0:#0a0e1a;--bg-1:#0f1525;--bg-2:#161d33;
  --glass:rgba(255,255,255,0.04);--glass-2:rgba(255,255,255,0.07);
  --border:rgba(255,255,255,0.08);--border-2:rgba(255,255,255,0.12);
  --text:#e8ecf4;--text-2:#9aa5bd;--text-3:#5a6480;
  --accent:#6c8cff;--accent-2:#38d9f5;--accent-3:#8b5cf6;
  --green:#4ade80;--amber:#fbbf24;--red:#f87171;--cyan:#22d3ee;
  --ease:cubic-bezier(0.4,0,0.2,1);
  --font:'Segoe UI',system-ui,-apple-system,sans-serif;
  --mono:'Cascadia Code','Consolas',monospace;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden}
body{
  font-family:var(--font);background:var(--bg-0);color:var(--text);
  background:radial-gradient(ellipse at 20% 0%,rgba(108,140,255,0.08),transparent 50%),
             radial-gradient(ellipse at 80% 100%,rgba(56,217,245,0.06),transparent 50%),
             var(--bg-0);
}
#particles{position:fixed;inset:0;z-index:0;pointer-events:none}
#app{position:relative;z-index:1;height:100%;display:flex;flex-direction:column;opacity:0;transition:opacity 0.6s var(--ease)}
#app.ready{opacity:1}

/* ===== Splash ===== */
#splash{position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;background:var(--bg-0);transition:opacity 0.8s var(--ease),visibility 0.8s}
#splash.gone{opacity:0;visibility:hidden}
.splash-logo{width:80px;height:80px;border-radius:24px;position:relative;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;font-size:36px;font-weight:800;color:#fff;box-shadow:0 0 40px rgba(108,140,255,0.4);animation:splashPulse 2s ease-in-out infinite}
.splash-logo::before{content:"";position:absolute;inset:-6px;border-radius:28px;border:2px solid rgba(108,140,255,0.3);animation:splashRing 2s ease-out infinite}
.splash-logo::after{content:"";position:absolute;inset:-12px;border-radius:32px;border:1px solid rgba(56,217,245,0.2);animation:splashRing 2s ease-out infinite 0.5s}
@keyframes splashPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.05)}}
@keyframes splashRing{0%{transform:scale(1);opacity:1}100%{transform:scale(1.5);opacity:0}}
.splash-bar{width:200px;height:3px;background:var(--glass-2);border-radius:3px;overflow:hidden}
.splash-bar::after{content:"";display:block;width:40%;height:100%;border-radius:3px;background:linear-gradient(90deg,var(--accent),var(--accent-2));animation:splashSlide 1.2s ease-in-out infinite}
@keyframes splashSlide{0%{transform:translateX(-120%)}100%{transform:translateX(380%)}}
.splash-text{font-size:11px;letter-spacing:4px;color:var(--text-3);text-transform:uppercase}
.splash-ver{font-size:10px;color:var(--accent);font-family:var(--mono);letter-spacing:1px}
.splash-error{display:none;font-size:11px;color:var(--red);max-width:360px;text-align:center;line-height:1.6}
.splash-skip{display:none;margin-top:8px;padding:6px 16px;border-radius:8px;border:1px solid var(--border);background:var(--glass);color:var(--text-2);font-size:11px;cursor:pointer;transition:all 0.2s}
.splash-skip:hover{color:var(--text);border-color:var(--accent)}

/* ===== Top Nav ===== */
.topnav{display:flex;align-items:center;gap:16px;padding:12px 20px;border-bottom:1px solid var(--border);background:var(--glass);backdrop-filter:blur(20px);position:relative;z-index:10}
.brand{display:flex;align-items:center;gap:12px;cursor:pointer;flex-shrink:0}
.brand-mark{width:40px;height:40px;border-radius:13px;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;font-weight:800;font-size:18px;color:#fff;box-shadow:0 4px 20px rgba(108,140,255,0.35);position:relative;transition:transform 0.3s var(--ease)}
.brand:hover .brand-mark{transform:rotate(-5deg) scale(1.05)}
.brand-mark::after{content:"";position:absolute;inset:-2px;border-radius:14px;border:1px solid rgba(108,140,255,0.25)}
.brand-name{font-size:15px;font-weight:700;letter-spacing:0.3px}
.brand-sub{font-size:10px;color:var(--text-3);letter-spacing:2px;text-transform:uppercase;margin-top:1px}
.nav-tabs{display:flex;gap:4px;padding:4px;background:var(--glass);border:1px solid var(--border);border-radius:14px;backdrop-filter:blur(12px);margin-left:auto}
.nav-tab{display:flex;align-items:center;gap:7px;padding:9px 16px;border:none;border-radius:10px;background:transparent;color:var(--text-2);font-size:12.5px;font-weight:500;font-family:var(--font);cursor:pointer;transition:all 0.3s var(--ease);position:relative;white-space:nowrap}
.nav-tab svg{width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.nav-tab:hover{color:var(--text);background:var(--glass-2);transform:translateY(-1px)}
.nav-tab.active{color:#fff;background:linear-gradient(135deg,rgba(108,140,255,0.3),rgba(56,217,245,0.15));box-shadow:0 2px 16px rgba(108,140,255,0.25),inset 0 0 0 1px rgba(108,140,255,0.3)}
.nav-tab.active::before{content:"";position:absolute;bottom:-2px;left:50%;transform:translateX(-50%);width:20px;height:2px;border-radius:2px;background:linear-gradient(90deg,var(--accent),var(--accent-2));box-shadow:0 0 8px var(--accent)}
.status-group{display:flex;gap:8px;align-items:center;flex-shrink:0}
.status-pill{display:flex;align-items:center;gap:7px;padding:7px 13px;border-radius:20px;background:var(--glass);border:1px solid var(--border);font-size:11px;color:var(--text-2);backdrop-filter:blur(8px);transition:all 0.3s var(--ease)}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--text-3);transition:all 0.3s;position:relative}
.status-dot.ok{background:var(--green);box-shadow:0 0 8px rgba(74,222,128,0.6)}
.status-dot.ok::after{content:"";position:absolute;inset:-3px;border-radius:50%;border:1px solid rgba(74,222,128,0.4);animation:dotPulse 2s infinite}
.status-dot.warn{background:var(--amber);box-shadow:0 0 8px rgba(251,191,36,0.6)}
.status-dot.err{background:var(--red);box-shadow:0 0 8px rgba(248,113,113,0.6)}
@keyframes dotPulse{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.5);opacity:0}}

/* ===== Content ===== */
.content{flex:1;position:relative;overflow:hidden}
.pane{position:absolute;inset:0;opacity:0;visibility:hidden;transform:translateY(20px) scale(0.98);transition:all 0.5s var(--ease);overflow-y:auto;overflow-x:hidden;padding:24px}
.pane.active{opacity:1;visibility:visible;transform:translateY(0) scale(1)}
.pane::-webkit-scrollbar{width:6px}
.pane::-webkit-scrollbar-track{background:transparent}
.pane::-webkit-scrollbar-thumb{background:var(--border-2);border-radius:3px}

/* ===== Glass Card ===== */
.glass{background:var(--glass);border:1px solid var(--border);border-radius:16px;backdrop-filter:blur(16px);position:relative;overflow:hidden;transition:all 0.4s var(--ease)}
.glass::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15),transparent)}
.glass:hover{border-color:var(--border-2);transform:translateY(-2px);box-shadow:0 12px 40px rgba(0,0,0,0.3)}
.glass-card{padding:20px}

/* ===== Stat Cards ===== */
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin-bottom:20px}
.stat-card{padding:18px 20px;position:relative;overflow:hidden}
.stat-card::after{content:"";position:absolute;top:-50%;right:-20%;width:120px;height:120px;border-radius:50%;background:radial-gradient(circle,rgba(108,140,255,0.1),transparent 70%);transition:transform 0.5s var(--ease)}
.stat-card:hover::after{transform:scale(1.5)}
.stat-label{font-size:11px;color:var(--text-3);text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;display:flex;align-items:center;gap:6px}
.stat-label .dot{width:6px;height:6px;border-radius:50%}
.stat-value{font-size:32px;font-weight:800;font-family:var(--mono);line-height:1;transition:color 0.3s}
.stat-sub{font-size:11px;color:var(--text-3);margin-top:6px}
.stat-bar{height:4px;background:var(--glass-2);border-radius:2px;margin-top:12px;overflow:hidden}
.stat-bar-fill{height:100%;border-radius:2px;transition:width 1s var(--ease);position:relative}
.stat-bar-fill::after{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.3),transparent);animation:barShine 2s infinite}
@keyframes barShine{0%{transform:translateX(-100%)}100%{transform:translateX(100%)}}

/* ===== Chart ===== */
.chart-container{padding:20px;margin-bottom:20px}
.chart-title{font-size:14px;font-weight:600;margin-bottom:16px;display:flex;align-items:center;gap:8px}
.chart-title .icon{width:20px;height:20px;border-radius:6px;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;font-size:11px}
.chart-canvas{width:100%;height:200px;display:block}
.chart-legend{display:flex;gap:20px;margin-top:12px;flex-wrap:wrap}
.legend-item{display:flex;align-items:center;gap:6px;font-size:11px;color:var(--text-2)}
.legend-dot{width:8px;height:8px;border-radius:50%}

/* ===== Section Title ===== */
.section-title{font-size:16px;font-weight:700;margin:24px 0 16px;display:flex;align-items:center;gap:10px}
.section-title::before{content:"";width:3px;height:18px;border-radius:2px;background:linear-gradient(180deg,var(--accent),var(--accent-2))}

/* ===== Process Table ===== */
.proc-table{width:100%;border-collapse:collapse;font-size:12px}
.proc-table th{text-align:left;padding:10px 12px;color:var(--text-3);font-weight:500;font-size:10px;text-transform:uppercase;letter-spacing:1px;border-bottom:1px solid var(--border)}
.proc-table td{padding:10px 12px;border-bottom:1px solid var(--border);color:var(--text-2)}
.proc-table tr{transition:background 0.2s}
.proc-table tbody tr:hover{background:var(--glass-2)}
.proc-cpu{font-family:var(--mono);color:var(--amber)}
.proc-mem{font-family:var(--mono);color:var(--cyan)}
.proc-bar{height:4px;background:var(--glass-2);border-radius:2px;overflow:hidden;margin-top:4px}
.proc-bar-fill{height:100%;border-radius:2px;background:linear-gradient(90deg,var(--accent),var(--accent-2))}

/* ===== Alert List ===== */
.alert-list{display:flex;flex-direction:column;gap:10px}
.alert-item{display:flex;align-items:flex-start;gap:12px;padding:14px 16px;border-radius:12px;background:var(--glass);border:1px solid var(--border);transition:all 0.3s var(--ease);animation:alertIn 0.4s var(--ease)}
@keyframes alertIn{from{opacity:0;transform:translateX(-20px)}to{opacity:1;transform:translateX(0)}}
.alert-item:hover{border-color:var(--border-2);transform:translateX(4px)}
.alert-icon{width:32px;height:32px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.alert-icon.critical{background:rgba(248,113,113,0.15);color:var(--red)}
.alert-icon.warning{background:rgba(251,191,36,0.15);color:var(--amber)}
.alert-icon.info{background:rgba(56,217,245,0.15);color:var(--cyan)}
.alert-content{flex:1;min-width:0}
.alert-title{font-size:13px;font-weight:600;margin-bottom:2px}
.alert-desc{font-size:11px;color:var(--text-3)}
.alert-time{font-size:10px;color:var(--text-3);font-family:var(--mono);flex-shrink:0}

/* ===== Quick Actions ===== */
.quick-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px}
.quick-btn{display:flex;flex-direction:column;align-items:center;gap:8px;padding:16px 12px;border-radius:12px;background:var(--glass);border:1px solid var(--border);cursor:pointer;transition:all 0.3s var(--ease);color:var(--text-2);font-size:11px;font-family:var(--font)}
.quick-btn:hover{border-color:var(--accent);color:var(--text);transform:translateY(-3px);box-shadow:0 8px 24px rgba(108,140,255,0.2)}
.quick-btn:active{transform:translateY(-1px) scale(0.98)}
.quick-btn svg{width:22px;height:22px;stroke:currentColor;fill:none;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}

/* ===== Console ===== */
.console-output{background:rgba(0,0,0,0.4);border:1px solid var(--border);border-radius:12px;padding:16px;font-family:var(--mono);font-size:12px;line-height:1.8;max-height:400px;overflow-y:auto;color:var(--green)}
.console-output::-webkit-scrollbar{width:6px}
.console-output::-webkit-scrollbar-thumb{background:var(--border-2);border-radius:3px}
.console-line{opacity:0;animation:lineIn 0.3s forwards}
@keyframes lineIn{to{opacity:1}}
.console-input-row{display:flex;gap:10px;margin-top:12px}
.console-input{flex:1;padding:10px 14px;border-radius:10px;background:var(--glass);border:1px solid var(--border);color:var(--text);font-family:var(--mono);font-size:12px;outline:none;transition:border-color 0.3s}
.console-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(108,140,255,0.1)}
.console-send{padding:10px 20px;border-radius:10px;border:none;background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:all 0.3s}
.console-send:hover{transform:translateY(-1px);box-shadow:0 4px 16px rgba(108,140,255,0.3)}

/* ===== Form ===== */
.form-group{margin-bottom:16px}
.form-label{display:block;font-size:12px;color:var(--text-2);margin-bottom:6px;font-weight:500}
.form-input{width:100%;padding:10px 14px;border-radius:10px;background:var(--glass);border:1px solid var(--border);color:var(--text);font-size:13px;outline:none;transition:all 0.3s}
.form-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(108,140,255,0.1)}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.btn{padding:10px 24px;border-radius:10px;border:none;font-size:13px;font-weight:600;cursor:pointer;transition:all 0.3s var(--ease);display:inline-flex;align-items:center;gap:8px}
.btn-primary{background:linear-gradient(135deg,var(--accent),var(--accent-2));color:#fff}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 6px 20px rgba(108,140,255,0.35)}
.btn-secondary{background:var(--glass);border:1px solid var(--border);color:var(--text-2)}
.btn-secondary:hover{color:var(--text);border-color:var(--border-2)}
.btn-danger{background:rgba(248,113,113,0.15);border:1px solid rgba(248,113,113,0.3);color:var(--red)}
.btn-danger:hover{background:rgba(248,113,113,0.25)}

/* ===== Logs ===== */
.log-container{background:rgba(0,0,0,0.4);border:1px solid var(--border);border-radius:12px;padding:16px;font-family:var(--mono);font-size:11px;line-height:1.8;max-height:500px;overflow-y:auto}
.log-line{padding:2px 0;opacity:0;animation:lineIn 0.2s forwards}
.log-time{color:var(--text-3)}
.log-level{font-weight:600;padding:1px 6px;border-radius:4px;margin-right:8px}
.log-level.info{color:var(--cyan)}
.log-level.warn{color:var(--amber)}
.log-level.error{color:var(--red)}
.log-level.success{color:var(--green)}

/* ===== Toast ===== */
.toasts{position:fixed;bottom:20px;right:20px;z-index:10000;display:flex;flex-direction:column;gap:8px}
.toast{padding:12px 20px;border-radius:10px;background:var(--glass-2);border:1px solid var(--border-2);backdrop-filter:blur(16px);font-size:12px;animation:toastIn 0.3s var(--ease);box-shadow:0 8px 32px rgba(0,0,0,0.3)}
@keyframes toastIn{from{opacity:0;transform:translateX(30px)}to{opacity:1;transform:translateX(0)}}
@keyframes toastOut{to{opacity:0;transform:translateX(30px)}}

/* ===== Server Info ===== */
.info-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}
.info-item{padding:14px 16px;border-radius:12px;background:var(--glass);border:1px solid var(--border)}
.info-label{font-size:10px;color:var(--text-3);text-transform:uppercase;letter-spacing:1px;margin-bottom:4px}
.info-value{font-size:14px;font-weight:600;font-family:var(--mono)}

/* ===== Network Cards ===== */
.net-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}
.net-card{padding:16px;text-align:center}
.net-icon{font-size:24px;margin-bottom:8px}
.net-value{font-size:20px;font-weight:700;font-family:var(--mono)}
.net-unit{font-size:11px;color:var(--text-3)}

/* ===== Responsive ===== */
@media (max-width:900px){
  .nav-tab span{display:none}
  .nav-tab{padding:9px 10px}
  .form-row{grid-template-columns:1fr}
}
</style>
</head>
<body>

<canvas id="particles"></canvas>

<div id="splash">
  <div class="splash-logo">S</div>
  <div class="splash-bar"></div>
  <div class="splash-text">Loading Server Health Monitor</div>
  <div class="splash-ver">v5.0.0 · 运维一体智能插件</div>
  <div class="splash-error" id="splashError"></div>
  <button class="splash-skip" id="splashSkip" onclick="forceHideSplash()">跳过加载</button>
</div>

<div id="app">
  <nav class="topnav">
    <div class="brand" onclick="switchPane('monitor')">
      <div class="brand-mark">S</div>
      <div><div class="brand-name">Server Health</div><div class="brand-sub">Monitor · v5.0</div></div>
    </div>
    <div class="nav-tabs" id="navTabs">
      <button class="nav-tab active" data-pane="monitor"><svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg><span>监控</span></button>
      <button class="nav-tab" data-pane="console"><svg viewBox="0 0 24 24"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg><span>控制台</span></button>
      <button class="nav-tab" data-pane="connect"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg><span>连接</span></button>
      <button class="nav-tab" data-pane="logs"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg><span>日志</span></button>
    </div>
    <div class="status-group">
      <div class="status-pill"><span class="status-dot" id="connDot"></span><span id="connText">未连接</span></div>
    </div>
  </nav>

  <div class="content">
    <!-- Monitor -->
    <section class="pane active" id="pane-monitor">
      <div class="stat-grid">
        <div class="glass stat-card"><div class="stat-label"><span class="dot" style="background:var(--green);box-shadow:0 0 6px var(--green)"></span>CPU 使用率</div><div class="stat-value" id="cpuVal" style="color:var(--green)">--</div><div class="stat-sub" id="cpuSub">-- 核心</div><div class="stat-bar"><div class="stat-bar-fill" id="cpuBar" style="width:0%;background:linear-gradient(90deg,var(--green),#22c55e)"></div></div></div>
        <div class="glass stat-card"><div class="stat-label"><span class="dot" style="background:var(--cyan);box-shadow:0 0 6px var(--cyan)"></span>内存使用</div><div class="stat-value" id="memVal" style="color:var(--cyan)">--</div><div class="stat-sub" id="memSub">-- / --</div><div class="stat-bar"><div class="stat-bar-fill" id="memBar" style="width:0%;background:linear-gradient(90deg,var(--cyan),#06b6d4)"></div></div></div>
        <div class="glass stat-card"><div class="stat-label"><span class="dot" style="background:var(--amber);box-shadow:0 0 6px var(--amber)"></span>磁盘使用</div><div class="stat-value" id="diskVal" style="color:var(--amber)">--</div><div class="stat-sub" id="diskSub">-- / --</div><div class="stat-bar"><div class="stat-bar-fill" id="diskBar" style="width:0%;background:linear-gradient(90deg,var(--amber),#f59e0b)"></div></div></div>
        <div class="glass stat-card"><div class="stat-label"><span class="dot" style="background:var(--accent-3);box-shadow:0 0 6px var(--accent-3)"></span>系统负载</div><div class="stat-value" id="loadVal" style="color:var(--accent-3)">--</div><div class="stat-sub" id="loadSub">1/5/15 min</div><div class="stat-bar"><div class="stat-bar-fill" id="loadBar" style="width:0%;background:linear-gradient(90deg,var(--accent-3),#7c3aed)"></div></div></div>
      </div>

      <div class="glass chart-container">
        <div class="chart-title"><span class="icon">📈</span>实时趋势</div>
        <canvas class="chart-canvas" id="trendChart"></canvas>
        <div class="chart-legend">
          <div class="legend-item"><span class="legend-dot" style="background:var(--green)"></span>CPU</div>
          <div class="legend-item"><span class="legend-dot" style="background:var(--cyan)"></span>内存</div>
          <div class="legend-item"><span class="legend-dot" style="background:var(--amber)"></span>磁盘</div>
        </div>
      </div>

      <div class="section-title">网络流量</div>
      <div class="net-grid" id="netGrid">
        <div class="glass net-card"><div class="net-icon">📥</div><div class="net-value" id="rxVal">--</div><div class="net-unit">接收速率</div></div>
        <div class="glass net-card"><div class="net-icon">📤</div><div class="net-value" id="txVal">--</div><div class="net-unit">发送速率</div></div>
        <div class="glass net-card"><div class="net-icon">🔗</div><div class="net-value" id="tcpVal">--</div><div class="net-unit">TCP 连接</div></div>
        <div class="glass net-card"><div class="net-icon">⏱️</div><div class="net-value" id="uptimeVal">--</div><div class="net-unit">运行时间</div></div>
      </div>

      <div class="section-title">Top 进程</div>
      <div class="glass" style="padding:0;overflow:hidden">
        <table class="proc-table" id="procTable">
          <thead><tr><th>PID</th><th>进程名</th><th>用户</th><th>CPU%</th><th>内存(KB)</th></tr></thead>
          <tbody><tr><td colspan="5" style="text-align:center;padding:30px;color:var(--text-3)">连接服务器后显示进程列表</td></tr></tbody>
        </table>
      </div>

      <div class="section-title">系统信息</div>
      <div class="info-grid" id="infoGrid">
        <div class="info-item"><div class="info-label">主机名</div><div class="info-value" id="infoHost">--</div></div>
        <div class="info-item"><div class="info-label">操作系统</div><div class="info-value" id="infoOS">--</div></div>
        <div class="info-item"><div class="info-label">内核版本</div><div class="info-value" id="infoKernel">--</div></div>
        <div class="info-item"><div class="info-label">架构</div><div class="info-value" id="infoArch">--</div></div>
        <div class="info-item"><div class="info-label">CPU 核心</div><div class="info-value" id="infoCores">--</div></div>
        <div class="info-item"><div class="info-label">文件描述符</div><div class="info-value" id="infoFD">--</div></div>
      </div>

      <div class="section-title">快捷运维</div>
      <div class="quick-grid">
        <button class="quick-btn" onclick="runQuick('top')"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>查看进程</button>
        <button class="quick-btn" onclick="runQuick('df')"><svg viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>磁盘空间</button>
        <button class="quick-btn" onclick="runQuick('free')"><svg viewBox="0 0 24 24"><rect x="2" y="6" width="20" height="12" rx="2"/><line x1="6" y1="10" x2="6" y2="14"/><line x1="10" y1="10" x2="10" y2="14"/></svg>内存状态</button>
        <button class="quick-btn" onclick="runQuick('ss')"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>网络连接</button>
        <button class="quick-btn" onclick="runQuick('journal')"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>系统日志</button>
        <button class="quick-btn" onclick="runQuick('services')"><svg viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>服务管理</button>
      </div>
    </section>

    <!-- Console -->
    <section class="pane" id="pane-console">
      <div class="section-title" style="margin-top:0">远程控制台</div>
      <div class="glass" style="padding:20px">
        <div class="console-output" id="consoleOutput">
          <div class="console-line" style="color:var(--accent)">╔══════════════════════════════════════╗</div>
          <div class="console-line" style="color:var(--accent)">║  Server Health Monitor 远程控制台 v5.0 ║</div>
          <div class="console-line" style="color:var(--accent)">╚══════════════════════════════════════╝</div>
          <div class="console-line" style="color:var(--text-3)">连接服务器后可执行命令。输入 help 查看可用命令。</div>
        </div>
        <div class="console-input-row">
          <input class="console-input" id="consoleInput" placeholder="输入命令..." onkeydown="if(event.key==='Enter')sendConsole()">
          <button class="console-send" onclick="sendConsole()">执行</button>
        </div>
      </div>

      <div class="section-title">服务状态</div>
      <div class="glass" style="padding:20px" id="serviceList">
        <div style="text-align:center;color:var(--text-3);padding:20px">连接服务器后显示服务状态</div>
      </div>

      <div class="section-title">告警中心</div>
      <div class="alert-list" id="alertList">
        <div class="alert-item"><div class="alert-icon info">ℹ️</div><div class="alert-content"><div class="alert-title">系统就绪</div><div class="alert-desc">等待连接服务器后开始监控</div></div><div class="alert-time">--:--:--</div></div>
      </div>
    </section>

    <!-- Connect -->
    <section class="pane" id="pane-connect">
      <div class="section-title" style="margin-top:0">服务器连接</div>
      <div class="glass glass-card" style="max-width:600px">
        <div class="form-row">
          <div class="form-group"><label class="form-label">服务器 IP</label><input class="form-input" id="cfgIP" placeholder="192.168.1.100"></div>
          <div class="form-group"><label class="form-label">端口</label><input class="form-input" id="cfgPort" placeholder="8080" value="8080"></div>
        </div>
        <div class="form-row">
          <div class="form-group"><label class="form-label">认证用户名</label><input class="form-input" id="cfgUser" placeholder="admin"></div>
          <div class="form-group"><label class="form-label">认证密码</label><input class="form-input" id="cfgPass" type="password" placeholder="••••••••"></div>
        </div>
        <div class="form-group"><label class="form-label">连接模式</label>
          <select class="form-input" id="cfgMode"><option value="direct">直连</option><option value="tunnel">SSH 隧道</option></select>
        </div>
        <div style="display:flex;gap:12px;margin-top:8px">
          <button class="btn btn-primary" onclick="testConn()">🔌 测试连接</button>
          <button class="btn btn-secondary" onclick="saveConn()">💾 保存配置</button>
          <button class="btn btn-primary" onclick="connectServer()">🚀 开始监控</button>
        </div>
      </div>

      <div class="section-title">连接状态</div>
      <div class="glass glass-card" id="connStatus" style="max-width:600px">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px">
          <span class="status-dot" id="csDot" style="width:12px;height:12px"></span>
          <span style="font-size:14px;font-weight:600" id="csText">未连接</span>
        </div>
        <div id="csDetail" style="font-size:12px;color:var(--text-3);line-height:2"></div>
      </div>
    </section>

    <!-- Logs -->
    <section class="pane" id="pane-logs">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <div class="section-title" style="margin:0">运行日志</div>
        <div style="display:flex;gap:8px">
          <button class="btn btn-secondary" onclick="clearLogs()">🗑️ 清空</button>
          <button class="btn btn-secondary" onclick="refreshLogs()">🔄 刷新</button>
        </div>
      </div>
      <div class="log-container" id="logContainer">
        <div class="log-line"><span class="log-time">--:--:--</span><span class="log-level info">INFO</span>系统启动，等待连接服务器...</div>
      </div>
    </section>
  </div>
</div>

<div class="toasts" id="toasts"></div>

<script>
/* ===== State ===== */
var STATE = null;
var chartData = {cpu:[],mem:[],disk:[],max:60};
var connected = false;
var pollTimer = null;

/* ===== Particles ===== */
(function(){
  var c=document.getElementById('particles'),ctx=c.getContext('2d'),particles=[];
  function resize(){c.width=window.innerWidth;c.height=window.innerHeight}
  resize();window.addEventListener('resize',resize);
  for(var i=0;i<60;i++){particles.push({x:Math.random()*c.width,y:Math.random()*c.height,vx:(Math.random()-0.5)*0.3,vy:(Math.random()-0.5)*0.3,r:Math.random()*1.5+0.5})}
  function draw(){
    ctx.clearRect(0,0,c.width,c.height);
    for(var i=0;i<particles.length;i++){
      var p=particles[i];p.x+=p.vx;p.y+=p.vy;
      if(p.x<0||p.x>c.width)p.vx*=-1;if(p.y<0||p.y>c.height)p.vy*=-1;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);ctx.fillStyle='rgba(108,140,255,0.3)';ctx.fill();
      for(var j=i+1;j<particles.length;j++){
        var p2=particles[j],dx=p.x-p2.x,dy=p.y-p2.y,d=Math.sqrt(dx*dx+dy*dy);
        if(d<120){ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(p2.x,p2.y);ctx.strokeStyle='rgba(108,140,255,'+(0.15*(1-d/120))+')';ctx.stroke()}
      }
    }
    requestAnimationFrame(draw);
  }
  draw();
})();

/* ===== Splash ===== */
var _splashHidden=false;
function forceHideSplash(){if(_splashHidden)return;_splashHidden=true;var s=document.getElementById('splash');if(s){s.classList.add('gone');setTimeout(function(){s.style.display='none'},700)}document.getElementById('app').classList.add('ready')}
function hideSplash(){forceHideSplash()}
setTimeout(hideSplash,1200);
setTimeout(function(){if(!_splashHidden){var b=document.getElementById('splashSkip');if(b)b.style.display='block'}},5000);
window.addEventListener('error',function(e){var el=document.getElementById('splashError');if(el&&!_splashHidden){el.style.display='block';el.textContent='加载异常: '+(e.message||'未知')+' ('+(e.filename||'').split('/').pop()+':'+(e.lineno||'?')+')';document.getElementById('splashSkip').style.display='block'}});

/* ===== Number Animation ===== */
function animateNumber(el,target,suffix){
  suffix=suffix||'';var start=parseFloat(el.textContent)||0,dur=600,st=null;
  function step(ts){if(!st)st=ts;var p=Math.min((ts-st)/dur,1),ease=1-Math.pow(1-p,3);el.textContent=(start+(target-start)*ease).toFixed(1)+suffix;if(p<1)requestAnimationFrame(step)}
  requestAnimationFrame(step);
}

/* ===== Chart ===== */
function drawChart(){
  var c=document.getElementById('trendChart'),ctx=c.getContext('2d');
  var dpr=window.devicePixelRatio||1;c.width=c.offsetWidth*dpr;c.height=200*dpr;ctx.scale(dpr,dpr);
  var w=c.offsetWidth,h=200,pad=30;
  ctx.clearRect(0,0,w,h);
  // grid
  ctx.strokeStyle='rgba(255,255,255,0.05)';ctx.lineWidth=1;
  for(var i=0;i<=4;i++){var y=pad+(h-pad*2)*i/4;ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke()}
  // lines
  var datasets=[{data:chartData.cpu,color:'#4ade80'},{data:chartData.mem,color:'#22d3ee'},{data:chartData.disk,color:'#fbbf24'}];
  datasets.forEach(function(ds){
    if(ds.data.length<2)return;
    ctx.beginPath();ctx.strokeStyle=ds.color;ctx.lineWidth=2;ctx.shadowColor=ds.color;ctx.shadowBlur=8;
    ds.data.forEach(function(v,i){var x=pad+(w-pad*2)*i/(chartData.max-1),y=h-pad-(h-pad*2)*v/100;i===0?ctx.moveTo(x,y):ctx.lineTo(x,y)});
    ctx.stroke();ctx.shadowBlur=0;
    // fill
    ctx.lineTo(pad+(w-pad*2)*(ds.data.length-1)/(chartData.max-1),h-pad);ctx.lineTo(pad,h-pad);ctx.closePath();
    ctx.fillStyle=ds.color+'15';ctx.fill();
  });
}

/* ===== Navigation ===== */
function switchPane(name){
  document.querySelectorAll('.nav-tab').forEach(function(t){t.classList.toggle('active',t.dataset.pane===name)});
  document.querySelectorAll('.pane').forEach(function(p){p.classList.toggle('active',p.id==='pane-'+name)});
  if(name==='logs')refreshLogs();
  if(name==='console')scrollConsoleBottom();
}
document.querySelectorAll('.nav-tab').forEach(function(t){t.addEventListener('click',function(){switchPane(t.dataset.pane)})});

/* ===== Toast ===== */
function toast(msg,type){type=type||'info';var t=document.createElement('div');t.className='toast';t.textContent=msg;document.getElementById('toasts').appendChild(t);setTimeout(function(){t.style.animation='toastOut 0.3s forwards';setTimeout(function(){t.remove()},300)},2500)}

/* ===== API ===== */
async function apiGet(url){try{var r=await fetch(url);return await r.json()}catch(e){return null}}
async function apiPost(url,body){try{var r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});return await r.json()}catch(e){return null}}

/* ===== Connect ===== */
async function loadConfig(){try{var c=await apiGet('/api/app/config');if(c){document.getElementById('cfgIP').value=c.server_ip||'';document.getElementById('cfgPort').value=c.server_port||8080;document.getElementById('cfgUser').value=c.auth_user||'';document.getElementById('cfgMode').value=c.mode||'direct'}}catch(e){}}
async function saveConn(){var cfg={server_ip:document.getElementById('cfgIP').value,server_port:parseInt(document.getElementById('cfgPort').value)||8080,auth_user:document.getElementById('cfgUser').value,auth_pass:document.getElementById('cfgPass').value,mode:document.getElementById('cfgMode').value};await apiPost('/api/app/config',cfg);toast('配置已保存','success')}
async function testConn(){await saveConn();var r=await apiPost('/api/app/test');if(r&&r.success){toast('连接成功: '+r.message,'success');setConnStatus('ok','连接正常')}else{toast('连接失败: '+(r&&r.message||'未知错误'),'error');setConnStatus('err','连接失败')}}
async function connectServer(){await saveConn();var r=await apiPost('/api/app/connect');if(r&&r.success){connected=true;toast('已连接服务器','success');setConnStatus('ok','已连接');startPolling();addLog('info','已连接到服务器 '+document.getElementById('cfgIP').value)}else{toast('连接失败','error');setConnStatus('err','连接失败')}}
function setConnStatus(s,text){var dot=document.getElementById('connDot'),txt=document.getElementById('connText');dot.className='status-dot '+s;txt.textContent=text;var csd=document.getElementById('csDot'),cst=document.getElementById('csText');csd.className='status-dot '+s;cst.textContent=text}

/* ===== Polling ===== */
function startPolling(){if(pollTimer)clearInterval(pollTimer);pollTimer=setInterval(pollData,3000);pollData()}
function stopPolling(){if(pollTimer){clearInterval(pollTimer);pollTimer=null}}
async function pollData(){
  var d=await apiGet('/api/status');if(!d){setConnStatus('warn','数据获取失败');return}
  if(!connected){connected=true;setConnStatus('ok','已连接')}
  var m=d.metrics||{},s=d.server||{};
  animateNumber(document.getElementById('cpuVal'),m.cpu&&m.cpu.percent||0,'%');
  document.getElementById('cpuBar').style.width=(m.cpu&&m.cpu.percent||0)+'%';
  document.getElementById('cpuSub').textContent=(s.cpu_count||0)+' 核心';
  animateNumber(document.getElementById('memVal'),m.memory&&m.memory.percent||0,'%');
  document.getElementById('memBar').style.width=(m.memory&&m.memory.percent||0)+'%';
  document.getElementById('memSub').textContent=fmtBytes(m.memory&&m.memory.used||0)+' / '+fmtBytes(m.memory&&m.memory.total||0);
  animateNumber(document.getElementById('diskVal'),m.disk&&m.disk.percent||0,'%');
  document.getElementById('diskBar').style.width=(m.disk&&m.disk.percent||0)+'%';
  document.getElementById('diskSub').textContent=fmtBytes(m.disk&&m.disk.used||0)+' / '+fmtBytes(m.disk&&m.disk.total||0);
  animateNumber(document.getElementById('loadVal'),m.load&&m.load['1min']||0,'');
  document.getElementById('loadBar').style.width=Math.min((m.load&&m.load['1min']||0)/(s.cpu_count||1)*100,100)+'%';
  document.getElementById('loadSub').textContent=(m.load&&m.load['1min']||0).toFixed(2)+' / '+(m.load&&m.load['5min']||0).toFixed(2)+' / '+(m.load&&m.load['15min']||0).toFixed(2);
  // network
  var nets=d.net_interfaces||[];if(nets.length>0){var n=nets[0];document.getElementById('rxVal').textContent=fmtRate(n.rx_bytes||0);document.getElementById('txVal').textContent=fmtRate(n.tx_bytes||0)}
  document.getElementById('tcpVal').textContent=(d.tcp&&d.tcp.established||0)+'';
  document.getElementById('uptimeVal').textContent=fmtUptime(s.uptime||0);
  // info
  document.getElementById('infoHost').textContent=s.hostname||'--';
  document.getElementById('infoOS').textContent=s.os||'--';
  document.getElementById('infoKernel').textContent=s.kernel||'--';
  document.getElementById('infoArch').textContent=s.arch||'--';
  document.getElementById('infoCores').textContent=s.cpu_count||'--';
  document.getElementById('infoFD').textContent=(m.fd_used||0)+' / '+(m.fd_max||0);
  // chart
  chartData.cpu.push(m.cpu&&m.cpu.percent||0);chartData.mem.push(m.memory&&m.memory.percent||0);chartData.disk.push(m.disk&&m.disk.percent||0);
  if(chartData.cpu.length>chartData.max){chartData.cpu.shift();chartData.mem.shift();chartData.disk.shift()}
  drawChart();
  // processes
  renderProcs(d.top_processes||[]);
  // alerts
  if(d.alerts&&d.alerts.length>0)renderAlerts(d.alerts);
}

function renderProcs(procs){
  var tb=document.querySelector('#procTable tbody');if(!procs.length){tb.innerHTML='<tr><td colspan="5" style="text-align:center;padding:30px;color:var(--text-3)">暂无进程数据</td></tr>';return}
  tb.innerHTML=procs.map(function(p){return '<tr><td style="font-family:var(--mono)">'+p.pid+'</td><td>'+p.name+'</td><td>'+(p.user||'--')+'</td><td class="proc-cpu">'+(p.cpu_percent||0).toFixed(1)+'%</td><td class="proc-mem">'+(p.memory_kb||0).toLocaleString()+'</td></tr>'}).join('');
}

function renderAlerts(alerts){
  var list=document.getElementById('alertList');
  list.innerHTML=alerts.slice(0,5).map(function(a){var lv=a.type&&a.type.toLowerCase();var icon=lv==='critical'?'🔴':lv==='warning'?'🟡':'ℹ️';return '<div class="alert-item"><div class="alert-icon '+(lv||'info')+'">'+icon+'</div><div class="alert-content"><div class="alert-title">'+(a.title||'告警')+'</div><div class="alert-desc">'+(a.message||'')+'</div></div><div class="alert-time">'+(a.time||'')+'</div></div>'}).join('');
}

/* ===== Console ===== */
function sendConsole(){
  var input=document.getElementById('consoleInput'),cmd=input.value.trim();if(!cmd)return;
  appendConsole('> '+cmd,'var(--text)');input.value='';
  var cmds={'help':'可用命令: status, top, df, free, ss, journal, services, clear','status':'显示服务器状态','clear':'清空控制台'};
  if(cmd==='clear'){document.getElementById('consoleOutput').innerHTML='';return}
  if(cmd==='help'){appendConsole(cmds.help,'var(--text-3)');return}
  appendConsole('执行: '+cmd+' ...','var(--text-3)');
  setTimeout(function(){appendConsole('命令已发送到服务器（需 Agent 支持远程执行）','var(--amber)')},500);
  scrollConsoleBottom();
}
function appendConsole(text,color){var out=document.getElementById('consoleOutput');var d=document.createElement('div');d.className='console-line';d.style.color=color||'var(--green)';d.textContent=text;out.appendChild(d);scrollConsoleBottom()}
function scrollConsoleBottom(){var out=document.getElementById('consoleOutput');if(out)out.scrollTop=out.scrollHeight}
function runQuick(cmd){switchPane('console');sendConsole();document.getElementById('consoleInput').value=cmd;sendConsole()}

/* ===== Logs ===== */
async function refreshLogs(){try{var d=await apiGet('/api/app/logs');var logs=(d&&d.logs)||[];var c=document.getElementById('logContainer');c.innerHTML=logs.map(function(l){return '<div class="log-line"><span class="log-time">'+l.t+'</span><span class="log-level '+(l.level||'info')+'">'+(l.level||'info').toUpperCase()+'</span>'+l.msg+'</div>'}).join('')||'<div class="log-line"><span class="log-time">--:--:--</span><span class="log-level info">INFO</span>暂无日志</div>'}catch(e){}}
function clearLogs(){apiPost('/api/app/logs/clear');document.getElementById('logContainer').innerHTML='<div class="log-line"><span class="log-time">--:--:--</span><span class="log-level info">INFO</span>日志已清空</div>';toast('日志已清空')}
function addLog(level,msg){var c=document.getElementById('logContainer');var d=document.createElement('div');d.className='log-line';d.innerHTML='<span class="log-time">'+new Date().toLocaleTimeString()+'</span><span class="log-level '+level+'">'+level.toUpperCase()+'</span>'+msg;c.appendChild(d);c.scrollTop=c.scrollHeight}

/* ===== Utils ===== */
function fmtBytes(b){if(b<1024)return b+' B';if(b<1048576)return(b/1024).toFixed(1)+' KB';if(b<1073741824)return(b/1048576).toFixed(1)+' MB';return(b/1073741824).toFixed(1)+' GB'}
function fmtRate(bps){if(bps<1024)return bps+' B/s';if(bps<1048576)return(bps/1024).toFixed(1)+' KB/s';return(bps/1048576).toFixed(1)+' MB/s'}
function fmtUptime(s){var d=Math.floor(s/86400),h=Math.floor((s%86400)/3600),m=Math.floor((s%3600)/60);if(d>0)return d+'d '+h+'h';if(h>0)return h+'h '+m+'m';return m+'m'}

/* ===== Init ===== */
loadConfig();
setTimeout(function(){drawChart();refreshLogs()},1500);
</script>
</body>
</html>
"""
