#!/usr/bin/env python3
"""
Server Health Monitor - Local Dashboard Client
Standalone Python 3 application. Zero external dependencies.

Runs locally on your computer (Windows/Mac/Linux) and connects
to the remote server's monitor-agent to display real-time metrics.

Usage:
  python dashboard-client.py
  python dashboard-client.py --server <server-address> --port 8080
  python dashboard-client.py --mode direct --server <server-address> --port 8080
  python dashboard-client.py --mode tunnel --server 127.0.0.1 --port 18080
  python dashboard-client.py --local-port 8090

Config file: dashboard-client.conf (auto-created on first run)
"""

import http.server
import json
import os
import sys
import socket
import urllib.request
import urllib.error
import ssl
from datetime import datetime
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DEFAULTS = {
  # direct = HTTPS/reachable Agent, tunnel = local SSH forward, proxy = internal gateway.
  'mode': 'direct',
    'server_ip': '',
    'server_port': 8080,
    'local_port': 8090,
    # The desktop client must not unintentionally publish an authenticated
    # proxy to every device on the LAN. Set 0.0.0.0 only when phone access is
    # deliberately required on a trusted network.
    'local_bind': '127.0.0.1',
    'auth_user': '',
    'auth_pass': '',
}

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dashboard-client.conf')


def load_config():
    cfg = dict(DEFAULTS)
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    k, v = line.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k in cfg:
                        old = cfg[k]
                        if isinstance(old, int):
                            cfg[k] = int(v) if v.isdigit() else old
                        else:
                            cfg[k] = v
    # Parse command-line args
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == '--server' and i + 1 < len(args):
            cfg['server_ip'] = args[i + 1]
            i += 2
        elif args[i] == '--mode' and i + 1 < len(args):
          cfg['mode'] = args[i + 1].lower()
          i += 2
        elif args[i] == '--port' and i + 1 < len(args):
            cfg['server_port'] = int(args[i + 1])
            i += 2
        elif args[i] == '--local-port' and i + 1 < len(args):
            cfg['local_port'] = int(args[i + 1])
            i += 2
        elif args[i] == '--auth-user' and i + 1 < len(args):
            cfg['auth_user'] = args[i + 1]
            i += 2
        elif args[i] == '--auth-pass' and i + 1 < len(args):
            cfg['auth_pass'] = args[i + 1]
            i += 2
        else:
            i += 1
    return cfg


def save_config(cfg):
    with open(CONFIG_FILE, 'w', encoding='utf-8', newline='\n') as f:
        f.write('# SCP:SL Dashboard Client Configuration\n')
        f.write(f'mode = {cfg.get("mode", "direct")}\n')
        f.write(f'server_ip = {cfg["server_ip"]}\n')
        f.write(f'server_port = {cfg["server_port"]}\n')
        f.write(f'local_port = {cfg["local_port"]}\n')
        f.write(f'local_bind = {cfg.get("local_bind", "127.0.0.1")}\n')
        f.write(f'auth_user = {cfg.get("auth_user", "")}\n')
        f.write(f'auth_pass = {cfg.get("auth_pass", "")}\n')


# ---------------------------------------------------------------------------
# Dashboard HTML
# ---------------------------------------------------------------------------
DASHBOARD_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no">
<meta name="theme-color" content="#4a90d9">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="Server Health Monitor">
<title>服务器运维监控</title>
<style>
:root{
--bg:#070b14;--card:#121b2e;--primary:#6c8cff;--primary-dark:#5b7cf0;--primary-light:rgba(108,140,255,0.12);
--success:#4ade80;--success-light:rgba(74,222,128,0.1);--warning:#fbbf24;--warning-light:rgba(251,191,36,0.1);
--error:#f87171;--error-light:rgba(248,113,113,0.1);--info:#38d9f5;--info-light:rgba(56,217,245,0.1);
--text:#e8eef9;--text2:#a8b8d0;--text3:#6b7c96;--border:rgba(120,150,200,0.14);--border-light:rgba(120,150,200,0.08);
--radius:16px;--radius-sm:10px;
--shadow:0 4px 20px rgba(0,0,0,.3);--shadow-h:0 12px 40px rgba(0,0,0,.5);
--ts:.35s cubic-bezier(.4,0,.2,1);
--font:-apple-system,"PingFang SC","Microsoft YaHei","Segoe UI",sans-serif;
}
[data-theme="dark"]{
--bg:#070b14;--card:#121b2e;--primary:#6c8cff;--primary-dark:#5b7cf0;--primary-light:rgba(108,140,255,0.12);
--success:#4ade80;--success-light:rgba(74,222,128,0.1);--warning:#fbbf24;--warning-light:rgba(251,191,36,0.1);
--error:#f87171;--error-light:rgba(248,113,113,0.1);--info:#38d9f5;--info-light:rgba(56,217,245,0.1);
--text:#e8eef9;--text2:#a8b8d0;--text3:#6b7c96;--border:rgba(120,150,200,0.14);--border-light:rgba(120,150,200,0.08);
--shadow:0 4px 20px rgba(0,0,0,.3);--shadow-h:0 12px 40px rgba(0,0,0,.5);
}
[data-theme="light"]{
--bg:#f0f2f5;--card:#fff;--primary:#4a90d9;--primary-dark:#357abd;--primary-light:#e8f1fb;
--success:#52c41a;--success-light:#f6ffed;--warning:#faad14;--warning-light:#fffbe6;
--error:#ff4d4f;--error-light:#fff2f0;--info:#1890ff;--info-light:#e6f7ff;
--text:#1a1a2e;--text2:#8c8c8c;--text3:#bfbfbf;--border:#e8e8e8;--border-light:#f0f0f0;
--shadow:0 2px 12px rgba(0,0,0,.06);--shadow-h:0 8px 28px rgba(0,0,0,.12);
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:var(--font);background:var(--bg);color:var(--text);min-height:100vh;transition:background var(--ts),color var(--ts);-webkit-font-smoothing:antialiased;
background-image:radial-gradient(ellipse 800px 400px at 50% -10%, rgba(108,140,255,0.08), transparent 60%);}

/* Scrollbar */
::-webkit-scrollbar{width:6px;height:6px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--text3)}

/* Header */
.header{background:linear-gradient(135deg,#6c8cff 0%,#5b7cf0 40%,#38d9f5 100%);color:#fff;padding:0;position:sticky;top:0;z-index:100;box-shadow:0 4px 24px rgba(108,140,255,0.3)}
.header-inner{max-width:1280px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px}
.header-left{display:flex;align-items:center;gap:14px;min-width:0}
.header-logo{width:44px;height:44px;background:rgba(255,255,255,.18);border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0;backdrop-filter:blur(10px)}
.header-title{font-size:17px;font-weight:700;letter-spacing:.3px;white-space:nowrap}
.header-sub{font-size:11px;opacity:.8;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.header-right{display:flex;align-items:center;gap:8px;flex-shrink:0}
.conn-pill{display:inline-flex;align-items:center;gap:6px;font-size:11px;background:rgba(255,255,255,.15);padding:5px 12px;border-radius:20px;backdrop-filter:blur(10px);white-space:nowrap}
.conn-dot{width:8px;height:8px;border-radius:50%;background:#52c41a;box-shadow:0 0 6px rgba(82,196,26,.6);animation:pulse 2s infinite}
.conn-dot.off{background:#ff4d4f;box-shadow:0 0 6px rgba(255,77,79,.6);animation:none}
.conn-dot.connecting{background:#faad14;box-shadow:0 0 6px rgba(250,173,20,.6)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.btn-icon{width:38px;height:38px;border:none;background:rgba(255,255,255,.15);color:#fff;border-radius:10px;cursor:pointer;font-size:17px;transition:all var(--ts);display:flex;align-items:center;justify-content:center;backdrop-filter:blur(10px)}
.btn-icon:hover{background:rgba(255,255,255,.28);transform:translateY(-1px)}
.btn-icon:active{transform:translateY(0)}

/* Layout */
.container{max-width:1280px;margin:0 auto;padding:20px;padding-bottom:80px}
.section-title{font-size:13px;font-weight:700;color:var(--text2);margin:24px 0 12px;text-transform:uppercase;letter-spacing:.8px;display:flex;align-items:center;gap:8px}
.section-title .bar{width:3px;height:16px;background:var(--primary);border-radius:2px}
.section-title:first-child{margin-top:0}

/* Metric Cards */
.metrics-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px}
.metric-card{background:var(--card);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow);border:1px solid var(--border);transition:all var(--ts);position:relative;overflow:hidden}
.metric-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:var(--metric-color,var(--primary));opacity:.9}
.metric-card::after{content:'';position:absolute;top:-40px;right:-40px;width:120px;height:120px;border-radius:50%;background:var(--metric-color,var(--primary));opacity:.06;filter:blur(20px)}
.metric-card:hover{box-shadow:var(--shadow-h);transform:translateY(-3px);border-color:var(--metric-color,var(--primary))}
.metric-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}
.metric-label{font-size:13px;color:var(--text2);font-weight:600;letter-spacing:.3px}
.metric-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;background:var(--metric-bg,var(--primary-light));color:var(--metric-color,var(--primary))}
.metric-body{display:flex;align-items:baseline;gap:4px;margin-bottom:12px}
.metric-value{font-size:34px;font-weight:800;line-height:1;letter-spacing:-.5px}
.metric-unit{font-size:15px;font-weight:500;color:var(--text2)}
.metric-sub{font-size:12px;color:var(--text3);margin-left:8px;font-weight:400}
.progress-bar{height:8px;background:var(--border-light);border-radius:4px;overflow:hidden;margin-bottom:8px}
.progress-fill{height:100%;border-radius:4px;transition:width .8s cubic-bezier(.4,0,.2,1),background-color .3s;width:0}
.progress-fill.ok{background:linear-gradient(90deg,#52c41a,#73d13d)}
.progress-fill.warn{background:linear-gradient(90deg,#faad14,#ffc53d)}
.progress-fill.crit{background:linear-gradient(90deg,#ff4d4f,#ff7875)}
.sparkline{width:100%;height:36px;margin-top:4px}
.metric-detail{font-size:11px;color:var(--text3);margin-top:6px;display:flex;justify-content:space-between}

/* Instance Cards */
.instances{display:flex;flex-direction:column;gap:12px}
.inst-card{background:var(--card);border-radius:var(--radius);padding:16px 20px;box-shadow:var(--shadow);border:1px solid var(--border);transition:all var(--ts);display:flex;align-items:center;gap:16px}
.inst-card:hover{box-shadow:var(--shadow-h)}
.inst-card:hover .inst-dot{transform:scale(1.2)}
.inst-dot{width:12px;height:12px;border-radius:50%;flex-shrink:0;transition:transform var(--ts)}
.inst-dot.active{background:var(--success);box-shadow:0 0 10px rgba(82,196,26,.5)}
.inst-dot.inactive{background:var(--error);box-shadow:0 0 10px rgba(255,77,79,.5)}
.inst-dot.unknown{background:var(--text3)}
.inst-info{flex:1;min-width:0}
.inst-name{font-weight:700;font-size:15px}
.inst-detail{font-size:12px;color:var(--text2);margin-top:3px}
.inst-badges{display:flex;gap:6px;flex-wrap:wrap;justify-content:flex-end}
.badge{font-size:11px;padding:3px 10px;border-radius:6px;font-weight:600;letter-spacing:.3px}
.badge.green{background:var(--success-light);color:var(--success);border:1px solid var(--success)}
.badge.red{background:var(--error-light);color:var(--error);border:1px solid var(--error)}
.badge.gray{background:var(--border-light);color:var(--text2);border:1px solid var(--border)}

/* Alerts Panel */
.alerts-panel{background:var(--card);border-radius:var(--radius);box-shadow:var(--shadow);border:1px solid var(--border);overflow:hidden}
.alerts-head{padding:16px 20px;border-bottom:1px solid var(--border);font-weight:700;font-size:14px;display:flex;align-items:center;justify-content:space-between}
.alerts-list{max-height:340px;overflow-y:auto}
.alert-item{padding:14px 20px;border-bottom:1px solid var(--border-light);display:flex;gap:12px;align-items:flex-start;transition:background var(--ts)}
.alert-item:hover{background:var(--border-light)}
.alert-item:last-child{border-bottom:none}
.alert-icon{width:28px;height:28px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0}
.alert-icon.warning{background:var(--warning-light);color:var(--warning)}
.alert-icon.critical{background:var(--error-light);color:var(--error)}
.alert-icon.recovery{background:var(--success-light);color:var(--success)}
.alert-body{flex:1;min-width:0}
.alert-title{font-size:13px;font-weight:700;margin-bottom:3px}
.alert-msg{font-size:12px;color:var(--text2);line-height:1.5}
.alert-time{font-size:11px;color:var(--text3);white-space:nowrap;margin-top:2px}
.no-data{padding:48px 20px;text-align:center;color:var(--text3);font-size:14px}
.no-data .emoji{font-size:32px;display:block;margin-bottom:8px;opacity:.5}

/* Toasts */
.toasts{position:fixed;top:80px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:10px;max-width:380px;pointer-events:none}
.toast{background:var(--card);border-radius:var(--radius);padding:14px 16px;box-shadow:0 8px 32px rgba(0,0,0,.15);display:flex;gap:10px;align-items:flex-start;animation:slideIn .4s cubic-bezier(.4,0,.2,1);border-left:4px solid var(--warning);pointer-events:auto}
[data-theme="dark"] .toast{box-shadow:0 8px 32px rgba(0,0,0,.4)}
.toast.critical{border-left-color:var(--error)}
.toast.recovery{border-left-color:var(--success)}
.toast.removing{animation:slideOut .3s cubic-bezier(.4,0,.2,1) forwards}
.toast-body{flex:1;min-width:0}
.toast-title{font-size:13px;font-weight:700;margin-bottom:3px}
.toast-msg{font-size:12px;color:var(--text2);line-height:1.4}
.toast-close{background:none;border:none;color:var(--text3);cursor:pointer;font-size:18px;padding:0;line-height:1;opacity:.5;transition:opacity var(--ts)}
.toast-close:hover{opacity:1}
@keyframes slideIn{from{transform:translateX(120%);opacity:0}to{transform:translateX(0);opacity:1}}
@keyframes slideOut{to{transform:translateX(120%);opacity:0}}

/* Modal */
.modal-overlay{position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:5000;display:none;align-items:center;justify-content:center;animation:fadeIn .2s;backdrop-filter:blur(4px)}
.modal-overlay.show{display:flex}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
.modal{background:var(--card);border-radius:20px;padding:28px;width:90%;max-width:440px;box-shadow:0 16px 48px rgba(0,0,0,.25);animation:modalIn .35s cubic-bezier(.4,0,.2,1);max-height:90vh;overflow-y:auto}
@keyframes modalIn{from{transform:translateY(30px) scale(.95);opacity:0}to{transform:translateY(0) scale(1);opacity:1}}
.modal-title{font-size:18px;font-weight:700;margin-bottom:6px;display:flex;align-items:center;gap:8px}
.modal-desc{font-size:12px;color:var(--text2);margin-bottom:20px}
.setting-row{margin-bottom:18px}
.setting-label{font-size:12px;color:var(--text2);margin-bottom:8px;display:flex;justify-content:space-between;font-weight:600}
.setting-input{width:100%;padding:10px 14px;border:1px solid var(--border);border-radius:10px;font-size:14px;font-family:var(--font);background:var(--card);color:var(--text);transition:border-color var(--ts)}
.setting-input:focus{outline:none;border-color:var(--primary);box-shadow:0 0 0 3px rgba(74,144,217,.12)}
.setting-slider{width:100%;-webkit-appearance:none;height:6px;background:var(--border-light);border-radius:3px;outline:none}
.setting-slider::-webkit-slider-thumb{-webkit-appearance:none;width:20px;height:20px;border-radius:50%;background:var(--primary);cursor:pointer;box-shadow:0 2px 6px rgba(0,0,0,.2);transition:transform var(--ts)}
.setting-slider::-webkit-slider-thumb:hover{transform:scale(1.15)}
.toggle{position:relative;width:46px;height:26px;background:var(--border);border-radius:13px;cursor:pointer;transition:background var(--ts);flex-shrink:0}
.toggle.on{background:var(--primary)}
.toggle::after{content:'';position:absolute;top:3px;left:3px;width:20px;height:20px;background:#fff;border-radius:50%;transition:transform var(--ts);box-shadow:0 2px 4px rgba(0,0,0,.15)}
.toggle.on::after{transform:translateX(20px)}
.toggle-row{display:flex;align-items:center;justify-content:space-between}
.modal-actions{display:flex;gap:10px;justify-content:flex-end;margin-top:24px;padding-top:20px;border-top:1px solid var(--border-light)}
.btn{padding:10px 24px;border:none;border-radius:10px;font-size:14px;font-family:var(--font);cursor:pointer;transition:all var(--ts);font-weight:600}
.btn-primary{background:var(--primary);color:#fff}
.btn-primary:hover{background:var(--primary-dark);transform:translateY(-1px)}
.btn-secondary{background:var(--border-light);color:var(--text)}
.btn-secondary:hover{background:var(--border)}

/* Server Config Modal */
.server-config-row{display:flex;gap:8px;align-items:center}
.server-config-row .setting-input{flex:1}
.server-config-row select{padding:10px 14px;border:1px solid var(--border);border-radius:10px;font-size:14px;background:var(--card);color:var(--text);cursor:pointer}

/* Loading */
.loading{display:flex;flex-direction:column;align-items:center;justify-content:center;min-height:200px;color:var(--text2);gap:12px}
.spinner{width:36px;height:36px;border:3px solid var(--border-light);border-top-color:var(--primary);border-radius:50%;animation:spin .8s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}

/* Footer */
.footer{text-align:center;padding:20px;color:var(--text3);font-size:11px;line-height:1.6}
.footer a{color:var(--primary);text-decoration:none}

/* Mobile Bottom Nav */
.bottom-nav{display:none;position:fixed;bottom:0;left:0;right:0;background:var(--card);border-top:1px solid var(--border);padding:6px 0;z-index:100;box-shadow:0 -2px 12px rgba(0,0,0,.06)}
.bottom-nav-inner{display:flex;justify-content:space-around;max-width:480px;margin:0 auto}
.nav-item{display:flex;flex-direction:column;align-items:center;gap:2px;padding:6px 16px;border:none;background:none;cursor:pointer;color:var(--text3);font-size:10px;transition:color var(--ts)}
.nav-item.active{color:var(--primary)}
.nav-item .nav-icon{font-size:20px}

/* Connection Error Banner */
.error-banner{background:var(--error-light);border:1px solid var(--error);border-radius:var(--radius);padding:16px 20px;margin-bottom:20px;display:flex;align-items:center;gap:12px;animation:fadeIn .3s}
.error-banner .icon{font-size:24px}
.error-banner .body{flex:1}
.error-banner .title{font-weight:700;font-size:14px;color:var(--error)}
.error-banner .msg{font-size:12px;color:var(--text2);margin-top:2px}
.retry-btn{padding:6px 16px;background:var(--error);color:#fff;border:none;border-radius:8px;cursor:pointer;font-size:12px;font-weight:600;transition:opacity var(--ts)}
.retry-btn:hover{opacity:.85}

/* Responsive */
@media(max-width:768px){
.header-inner{padding:12px 14px}
.header-logo{width:38px;height:38px;font-size:20px}
.header-title{font-size:15px}
.header-sub{font-size:10px}
.conn-pill{font-size:10px;padding:4px 8px}
.container{padding:14px;padding-bottom:70px}
.metrics-grid{grid-template-columns:1fr;gap:12px}
.metric-card{padding:16px}
.metric-value{font-size:28px}
.section-title{font-size:12px;margin:18px 0 10px}
.inst-card{padding:14px;gap:12px}
.inst-badges{flex-direction:column;align-items:flex-end}
.toasts{right:10px;left:10px;max-width:none;top:70px}
.bottom-nav{display:block}
.modal{padding:22px;border-radius:16px}
}

@media(max-width:380px){
.header-title{font-size:13px}
.conn-pill .pill-text{display:none}
.metric-value{font-size:24px}
}
</style>
</head>
<body>

<!-- Header -->
<div class="header">
  <div class="header-inner">
    <div class="header-left">
      <div class="header-logo">&#x1F6E0;</div>
      <div style="min-width:0">
        <div class="header-title">服务器运维监控</div>
        <div class="header-sub" id="serverInfo">正在连接服务器...</div>
      </div>
    </div>
    <div class="header-right">
      <div class="conn-pill">
        <span class="conn-dot connecting" id="connDot"></span>
        <span class="pill-text" id="connText">连接中</span>
      </div>
      <button class="btn-icon" onclick="toggleTheme()" id="themeBtn" title="切换主题">&#x1F313;</button>
      <button class="btn-icon" onclick="toggleSettings()" title="设置">&#x2699;</button>
    </div>
  </div>
</div>

<!-- Main Container -->
<div class="container">

  <!-- Error Banner (hidden by default) -->
  <div class="error-banner" id="errorBanner" style="display:none">
    <div class="icon">&#x26A0;</div>
    <div class="body">
      <div class="title">无法连接到服务器</div>
      <div class="msg" id="errorMsg">请检查服务器地址和网络连接</div>
    </div>
    <button class="retry-btn" onclick="fetchData()">重试</button>
  </div>

  <!-- System Resources -->
  <div class="section-title"><span class="bar"></span>系统资源</div>
  <div class="metrics-grid" id="metricsGrid">
    <div class="loading"><div class="spinner"></div><span>加载中...</span></div>
  </div>

  <!-- SCP:SL Instances -->
  <div class="section-title"><span class="bar"></span>服务实例</div>
  <div class="instances" id="instancesList">
    <div class="loading"><div class="spinner"></div><span>加载中...</span></div>
  </div>

  <!-- Alerts -->
  <div class="section-title"><span class="bar"></span>告警记录</div>
  <div class="alerts-panel">
    <div class="alerts-head">
      <span>&#x1F514; 告警历史</span>
      <span id="alertCount" style="font-weight:400;font-size:12px;color:var(--text2)">0 条</span>
    </div>
    <div class="alerts-list" id="alertsList">
      <div class="no-data"><span class="emoji">&#x2705;</span>暂无告警记录</div>
    </div>
  </div>

  <!-- Footer -->
  <div class="footer">
    Server Health Monitor &mdash; Local Client<br>
    本地客户端 v1.0 &mdash; <a href="https://gitee.com/hanbeimuren/server-health-monitor-v2" target="_blank">Gitee</a>
  </div>
</div>

<!-- Toast Container -->
<div class="toasts" id="toasts"></div>

<!-- Settings Modal -->
<div class="modal-overlay" id="settingsModal">
  <div class="modal">
    <div class="modal-title">&#x2699; 监控设置</div>
    <div class="modal-desc">调整刷新频率和告警阈值，设置会自动保存</div>

    <div class="setting-row">
      <div class="setting-label"><span>刷新间隔</span><span id="intervalVal">3 秒</span></div>
      <input type="range" class="setting-slider" id="intervalSlider" min="1" max="15" value="3">
    </div>

    <div class="setting-row">
      <div class="setting-label"><span>CPU 告警阈值</span><span id="thrCpuVal">90%</span></div>
      <input type="range" class="setting-slider" id="thrCpu" min="50" max="100" value="90">
    </div>

    <div class="setting-row">
      <div class="setting-label"><span>内存告警阈值</span><span id="thrMemVal">90%</span></div>
      <input type="range" class="setting-slider" id="thrMem" min="50" max="100" value="90">
    </div>

    <div class="setting-row">
      <div class="setting-label"><span>磁盘告警阈值</span><span id="thrDiskVal">85%</span></div>
      <input type="range" class="setting-slider" id="thrDisk" min="50" max="100" value="85">
    </div>

    <div class="setting-row toggle-row">
      <div class="setting-label" style="margin:0"><span>浏览器推送通知</span></div>
      <div class="toggle" id="toggleNotif" onclick="this.classList.toggle('on')"></div>
    </div>

    <div class="setting-row toggle-row">
      <div class="setting-label" style="margin:0"><span>声音提醒</span></div>
      <div class="toggle" id="toggleSound" onclick="this.classList.toggle('on')"></div>
    </div>

    <div class="modal-actions">
      <button class="btn btn-secondary" onclick="toggleSettings()">关闭</button>
      <button class="btn btn-primary" onclick="saveSettings()">保存并应用</button>
    </div>
  </div>
</div>

<!-- Mobile Bottom Nav -->
<div class="bottom-nav">
  <div class="bottom-nav-inner">
    <button class="nav-item active" onclick="scrollToSection('metricsGrid')">
      <span class="nav-icon">&#x1F4CA;</span>资源
    </button>
    <button class="nav-item" onclick="scrollToSection('instancesList')">
      <span class="nav-icon">&#x1F3AE;</span>实例
    </button>
    <button class="nav-item" onclick="scrollToSection('alertsList')">
      <span class="nav-icon">&#x1F514;</span>告警
    </button>
    <button class="nav-item" onclick="toggleSettings()">
      <span class="nav-icon">&#x2699;</span>设置
    </button>
  </div>
</div>

<script>
// ==================== State ====================
let refreshTimer = null;
let lastAlerts = [];
let seenAlertIds = new Set();
let settings = {};
let reconnectAttempts = 0;

// ==================== Settings ====================
function loadSettings() {
  try { settings = JSON.parse(localStorage.getItem('scpsl_monitor_settings') || '{}'); } catch(e) { settings = {}; }
  settings = Object.assign({
    interval: 3, cpu: 90, mem: 90, disk: 85, load: 4,
    notif: false, sound: false,
    theme: 'dark'
  }, settings);
  applyTheme();
}

function saveSettingsL() {
  localStorage.setItem('scpsl_monitor_settings', JSON.stringify(settings));
}

function applySettings() {
  if (refreshTimer) clearInterval(refreshTimer);
  refreshTimer = setInterval(fetchData, settings.interval * 1000);
}

function applyTheme() {
  document.documentElement.setAttribute('data-theme', settings.theme);
  document.getElementById('themeBtn').innerHTML = settings.theme === 'dark' ? '&#x1F315;' : '&#x1F313;';
}

function toggleTheme() {
  settings.theme = settings.theme === 'dark' ? 'light' : 'dark';
  saveSettingsL();
  applyTheme();
}

function toggleSettings() {
  const m = document.getElementById('settingsModal');
  m.classList.toggle('show');
  if (m.classList.contains('show')) {
    document.getElementById('intervalSlider').value = settings.interval;
    document.getElementById('intervalVal').textContent = settings.interval + ' 秒';
    document.getElementById('thrCpu').value = settings.cpu;
    document.getElementById('thrCpuVal').textContent = settings.cpu + '%';
    document.getElementById('thrMem').value = settings.mem;
    document.getElementById('thrMemVal').textContent = settings.mem + '%';
    document.getElementById('thrDisk').value = settings.disk;
    document.getElementById('thrDiskVal').textContent = settings.disk + '%';
    document.getElementById('toggleNotif').classList.toggle('on', settings.notif);
    document.getElementById('toggleSound').classList.toggle('on', settings.sound);
  }
}

function saveSettings() {
  settings.interval = parseInt(document.getElementById('intervalSlider').value);
  settings.cpu = parseInt(document.getElementById('thrCpu').value);
  settings.mem = parseInt(document.getElementById('thrMem').value);
  settings.disk = parseInt(document.getElementById('thrDisk').value);
  settings.notif = document.getElementById('toggleNotif').classList.contains('on');
  settings.sound = document.getElementById('toggleSound').classList.contains('on');

  saveSettingsL();
  applySettings();
  document.getElementById('settingsModal').classList.remove('show');
}

// Slider value displays
document.getElementById('intervalSlider').addEventListener('input', function() {
  document.getElementById('intervalVal').textContent = this.value + ' 秒';
});
document.getElementById('thrCpu').addEventListener('input', function() {
  document.getElementById('thrCpuVal').textContent = this.value + '%';
});
document.getElementById('thrMem').addEventListener('input', function() {
  document.getElementById('thrMemVal').textContent = this.value + '%';
});
document.getElementById('thrDisk').addEventListener('input', function() {
  document.getElementById('thrDiskVal').textContent = this.value + '%';
});

// ==================== Utilities ====================
function fmtBytes(n) {
  if (!n || n < 0) return '0 B';
  const u = ['B','KB','MB','GB','TB'];
  let i = 0;
  while (n >= 1024 && i < u.length - 1) { n /= 1024; i++; }
  return n.toFixed(1) + ' ' + u[i];
}

function fmtUptime(s) {
  if (!s || s < 0) return '0 秒';
  if (s < 60) return Math.floor(s) + ' 秒';
  if (s < 3600) return Math.floor(s / 60) + ' 分' + Math.floor(s % 60) + ' 秒';
  if (s < 86400) return Math.floor(s / 3600) + ' 小时' + Math.floor((s % 3600) / 60) + ' 分';
  return Math.floor(s / 86400) + ' 天' + Math.floor((s % 86400) / 3600) + ' 小时';
}

function levelClass(val, threshold) {
  if (val >= threshold) return 'crit';
  if (val >= threshold * 0.8) return 'warn';
  return 'ok';
}

function sparkline(data, color) {
  if (!data || data.length < 2) return '<svg class="sparkline" viewBox="0 0 100 36"></svg>';
  const w = 100, h = 36, pad = 2;
  const max = Math.max.apply(null, data);
  const min = Math.min.apply(null, data);
  const range = (max - min) || 1;
  const pts = data.map(function(v, i) {
    const x = pad + (i / (data.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return x.toFixed(1) + ',' + y.toFixed(1);
  }).join(' ');
  const areaPts = pad + ',' + (h - pad) + ' ' + pts + ' ' + (w - pad) + ',' + (h - pad);
  return '<svg class="sparkline" viewBox="0 0 100 36" preserveAspectRatio="none">' +
    '<polygon points="' + areaPts + '" fill="' + color + '" opacity="0.12"/>' +
    '<polyline points="' + pts + '" fill="none" stroke="' + color + '" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/></svg>';
}

function scrollToSection(id) {
  document.querySelectorAll('.nav-item').forEach(function(el) { el.classList.remove('active'); });
  event.currentTarget.classList.add('active');
  document.getElementById(id).scrollIntoView({ behavior: 'smooth', block: 'start' });
}

// ==================== Data Fetching ====================
async function fetchData() {
  try {
    const url = '/api/status';
    const res = await fetch(url, { mode: 'cors', signal: AbortSignal.timeout(8000) });
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    updateUI(data);
    setConn(true);
    reconnectAttempts = 0;
  } catch(e) {
    setConn(false);
    reconnectAttempts++;
    if (reconnectAttempts <= 3) {
      setTimeout(fetchData, 2000 * reconnectAttempts);
    }
  }
}

function setConn(online) {
  const dot = document.getElementById('connDot');
  const txt = document.getElementById('connText');
  const banner = document.getElementById('errorBanner');
  if (online) {
    dot.className = 'conn-dot';
    txt.textContent = '已连接';
    banner.style.display = 'none';
  } else {
    dot.className = 'conn-dot off';
    txt.textContent = '已断开';
    banner.style.display = 'flex';
  }
}

// ==================== UI Update ====================
function updateUI(data) {
  const srv = data.server || {};
  const m = data.metrics || {};

  document.getElementById('serverInfo').textContent =
    (srv.hostname || 'server') + ' | 运行 ' + fmtUptime(srv.uptime || 0) + ' | CPU x' + (srv.cpu_count || 1);

  const grid = document.getElementById('metricsGrid');
  const cpuVal = m.cpu ? m.cpu.percent : 0;
  const memVal = m.memory ? m.memory.percent : 0;
  const memUsed = m.memory ? m.memory.used : 0;
  const memTotal = m.memory ? m.memory.total : 0;
  const diskVal = m.disk ? m.disk.percent : 0;
  const diskUsed = m.disk ? m.disk.used : 0;
  const diskTotal = m.disk ? m.disk.total : 0;
  const loadVal = m.load ? m.load['1min'] : 0;
  const load5 = m.load ? m.load['5min'] : 0;
  const load15 = m.load ? m.load['15min'] : 0;
  const loadNorm = srv.cpu_count ? loadVal / srv.cpu_count : 0;
  const netVal = m.network || 'disabled';

  const hist = data.history || { cpu: [], memory: [], disk: [] };

  grid.innerHTML =
    card('CPU', '&#x2697;', cpuVal, '%', settings.cpu, hist.cpu || [], '#4a90d9', '') +
    card('内存', '&#x1F4BE;', memVal, '%', settings.mem, hist.memory || [], '#722ed1', fmtBytes(memUsed) + ' / ' + fmtBytes(memTotal)) +
    card('磁盘', '&#x1F4BF;', diskVal, '%', settings.disk, hist.disk || [], '#fa8c16', fmtBytes(diskUsed) + ' / ' + fmtBytes(diskTotal)) +
    card('系统负载', '&#x26A1;', loadNorm, '', settings.load || 4, [], '#13c2c2', '1m:' + loadVal.toFixed(2) + ' 5m:' + load5.toFixed(2) + ' 15m:' + load15.toFixed(2)) +
    cardNet('网络连通', '&#x1F310;', netVal);

  const insts = data.instances || [];
  const il = document.getElementById('instancesList');
  if (!insts.length) {
    il.innerHTML = '<div class="no-data"><span class="emoji">&#x1F50D;</span>未检测到 SCP:SL 服务实例</div>';
  } else {
    il.innerHTML = insts.map(function(i) {
      const cls = i.state === 'active' ? 'active' : (i.state === 'inactive' || i.state === 'failed' ? 'inactive' : 'unknown');
      const udpBadge = i.udp === 'listening' ? '<span class="badge green">UDP \u2713</span>' :
        i.udp === 'not-listening' ? '<span class="badge red">UDP \u2717</span>' : '<span class="badge gray">' + i.udp + '</span>';
      const stateBadge = i.state === 'active' ? '<span class="badge green">' + i.state + '</span>' :
        '<span class="badge red">' + i.state + '</span>';
      return '<div class="inst-card"><div class="inst-dot ' + cls + '"></div><div class="inst-info">' +
        '<div class="inst-name">' + i.service + '</div>' +
        '<div class="inst-detail">端口 ' + i.port + ' | 进程数: ' + i.processes + '</div></div>' +
        '<div class="inst-badges">' + stateBadge + udpBadge + '</div></div>';
    }).join('');
  }

  const alerts = data.alerts || [];
  document.getElementById('alertCount').textContent = alerts.length + ' 条';
  const al = document.getElementById('alertsList');
  if (!alerts.length) {
    al.innerHTML = '<div class="no-data"><span class="emoji">&#x2705;</span>暂无告警记录</div>';
  } else {
    al.innerHTML = alerts.map(function(a) {
      const icon = a.type === 'critical' ? '\uD83D\uDD34' : (a.type === 'recovery' ? '\u2705' : '\u26A0');
      const iconBg = a.type === 'critical' ? 'critical' : (a.type === 'recovery' ? 'recovery' : 'warning');
      return '<div class="alert-item"><div class="alert-icon ' + iconBg + '">' + icon + '</div>' +
        '<div class="alert-body"><div class="alert-title">' + a.title + '</div>' +
        '<div class="alert-msg">' + a.message + '</div>' +
        '<div class="alert-time">' + (a.time || '') + '</div></div></div>';
    }).join('');
  }

  for (let i = 0; i < alerts.length; i++) {
    const a = alerts[i];
    const aid = a.time + '|' + a.title;
    if (!seenAlertIds.has(aid)) {
      seenAlertIds.add(aid);
      showToast(a);
      if (settings.notif && 'Notification' in window && Notification.permission === 'granted') {
        new Notification(a.title, { body: a.message });
      }
    }
  }
}

function card(label, icon, val, unit, threshold, hist, color, sub) {
  const cls = levelClass(val, threshold);
  const pct = Math.min(val, 100);
  return '<div class="metric-card" style="--metric-color:' + color + ';--metric-bg:' + color + '22">' +
    '<div class="metric-head"><span class="metric-label">' + label + '</span>' +
    '<span class="metric-icon">' + icon + '</span></div>' +
    '<div class="metric-body"><span class="metric-value">' + (typeof val === 'number' ? val.toFixed(1) : val) +
    '</span><span class="metric-unit">' + unit + '</span>' +
    (sub ? '<span class="metric-sub">' + sub + '</span>' : '') + '</div>' +
    '<div class="progress-bar"><div class="progress-fill ' + cls + '" style="width:' + pct + '%"></div></div>' +
    sparkline(hist, color) +
    '<div class="metric-detail"><span>实时</span><span>阈值 ' + threshold + '</span></div></div>';
}

function cardNet(label, icon, val) {
  const color = val === 'reachable' ? '#52c41a' : (val === 'unreachable' ? '#ff4d4f' : '#8c8c8c');
  const text = val === 'reachable' ? '正常' : (val === 'unreachable' ? '不可达' : '未启用');
  return '<div class="metric-card" style="--metric-color:' + color + ';--metric-bg:' + color + '22">' +
    '<div class="metric-head"><span class="metric-label">' + label + '</span>' +
    '<span class="metric-icon">' + icon + '</span></div>' +
    '<div class="metric-body"><span class="metric-value" style="color:' + color + '">' + text + '</span></div>' +
    '<div class="metric-detail"><span>' + val + '</span><span>&nbsp;</span></div></div>';
}

function showToast(a) {
  const tc = document.getElementById('toasts');
  const div = document.createElement('div');
  div.className = 'toast ' + (a.type || 'warning');
  div.innerHTML = '<div class="toast-body"><div class="toast-title">' + a.title + '</div>' +
    '<div class="toast-msg">' + a.message + '</div></div>' +
    '<button class="toast-close" onclick="this.parentElement.remove()">&times;</button>';
  tc.appendChild(div);
  if (settings.sound) {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      osc.connect(ctx.destination);
      osc.frequency.value = 800;
      osc.start();
      setTimeout(function() { osc.stop(); }, 200);
    } catch(e) {}
  }
  setTimeout(function() {
    div.classList.add('removing');
    setTimeout(function() { div.remove(); }, 300);
  }, 10000);
}

// ==================== Init ====================
loadSettings();
applySettings();
fetchData();
if ('Notification' in window && Notification.permission !== 'granted') {
  setTimeout(function() { Notification.requestPermission(); }, 3000);
}

// Close modal on overlay click
document.getElementById('settingsModal').addEventListener('click', function(e) {
  if (e.target === this) this.classList.remove('show');
});
</script>
</body>
</html>
'''


# ---------------------------------------------------------------------------
# HTTP Handler (Local Proxy Server)
# ---------------------------------------------------------------------------
class ClientHandler(http.server.BaseHTTPRequestHandler):
    config = None

    def _agent_url(self, path):
        endpoint = self.config['server_ip'].strip().rstrip('/')
        if not endpoint.startswith(('http://', 'https://')):
            endpoint = f'http://{endpoint}:{self.config["server_port"]}'
        return endpoint + path

    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/' or path == '/index.html':
            self._serve_dashboard()
        elif path == '/api/status':
            self._proxy_api()
        elif path == '/api/health':
            self._proxy_health()
        elif path == '/api/client-config':
            self._serve_client_config()
        elif path == '/manifest.json':
            self._serve_manifest()
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_dashboard(self):
        bootstrap = json.dumps({
            'server_ip': self.config['server_ip'],
            'server_port': self.config['server_port'],
        }).replace('</', '<\\/')
        html = DASHBOARD_HTML.replace(
            '</head>', f'<script>window.MONITOR_BOOTSTRAP={bootstrap};</script></head>', 1)
        body = html.encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_client_config(self):
        body = json.dumps({
            'server_ip': self.config['server_ip'],
            'server_port': self.config['server_port'],
        }).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy_api(self):
        cfg = self.config
        if not cfg.get('server_ip'):
            self._send_json_error('未配置服务器地址', 424)
            return
        url = self._agent_url('/api/status')
        try:
            req = urllib.request.Request(url)
            if cfg.get('auth_user'):
                import base64
                cred = f'{cfg["auth_user"]}:{cfg["auth_pass"]}'
                req.add_header('Authorization', f'Basic {base64.b64encode(cred.encode()).decode()}')
            with urllib.request.urlopen(req, timeout=8) as resp:
                body = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except urllib.error.URLError as e:
            err = json.dumps({'error': 'connection_failed', 'detail': str(e)}).encode()
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(err)))
            self.end_headers()
            self.wfile.write(err)
        except Exception as e:
            err = json.dumps({'error': 'internal_error', 'detail': str(e)}).encode()
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(err)))
            self.end_headers()
            self.wfile.write(err)

    def _proxy_health(self):
        cfg = self.config
        if not cfg.get('server_ip'):
            self._send_json_error('未配置服务器地址', 424)
            return
        url = self._agent_url('/api/health')
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                body = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
        except Exception:
            err = json.dumps({'status': 'offline'}).encode()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(err)))
            self.end_headers()
            self.wfile.write(err)

    def _send_json_error(self, detail, status):
        body = json.dumps({'error': 'configuration_required', 'detail': detail}).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_manifest(self):
        manifest = json.dumps({
            'name': 'SCP:SL Server Monitor',
            'short_name': 'SCPSL Monitor',
            'description': 'SCP:SL 服务器健康监控面板',
            'start_url': '/',
            'display': 'standalone',
            'background_color': '#4a90d9',
            'theme_color': '#4a90d9',
            'icons': []
        }).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(manifest)))
        self.end_headers()
        self.wfile.write(manifest)

    def log_message(self, fmt, *args):
        ts = datetime.now().strftime('%H:%M:%S')
        sys.stderr.write(f'[{ts}] {fmt % args}\n')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    cfg = load_config()

    if cfg.get('mode') not in ('direct', 'tunnel', 'proxy'):
        print('连接模式必须是 direct、tunnel 或 proxy', file=sys.stderr)
        sys.exit(2)
    if not cfg.get('server_ip'):
        print('未配置服务器地址。请使用 --server <地址>，或编辑 dashboard-client.conf。', file=sys.stderr)
        sys.exit(2)

    # Save config if it doesn't exist
    if not os.path.isfile(CONFIG_FILE):
        save_config(cfg)

    ClientHandler.config = cfg

    local_port = cfg.get('local_port', 8090)

    # Listen on 0.0.0.0 so phones on same WiFi can access
    local_bind = cfg.get('local_bind', '127.0.0.1')
    try:
        server = http.server.ThreadingHTTPServer((local_bind, local_port), ClientHandler)
    except OSError as exc:
        print(f'Unable to start local dashboard on {local_bind}:{local_port}: {exc}', file=sys.stderr)
        sys.exit(1)

    # Get local IP for display
    local_ip = '127.0.0.1'
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    print('=' * 60)
    print('  Server Health Monitor - Local Dashboard Client')
    print('=' * 60)
    mode_names = {'direct': '安全直连/HTTPS', 'tunnel': 'SSH 隧道', 'proxy': '内网反向代理'}
    print(f'  连接模式:     {mode_names[cfg["mode"]]}')
    print(f'  远程入口:     {cfg["server_ip"]}:{cfg["server_port"]}')
    print(f'  本地端口:     {local_port}')
    print(f'  电脑访问:     http://127.0.0.1:{local_port}/')
    if local_bind in ('0.0.0.0', '::'):
        print(f'  手机访问:     http://{local_ip}:{local_port}/')
    else:
        print('  手机访问:     已关闭（将 local_bind 改为 0.0.0.0 后启用）')
    print(f'  配置文件:     {CONFIG_FILE}')
    if cfg.get('auth_user'):
        print(f'  认证用户:     {cfg["auth_user"]}')
    print('=' * 60)
    print('  浏览器会自动打开，手机请用上面第二个地址')
    print('  按 Ctrl+C 停止')
    print('=' * 60)
    print()

    # Auto-open browser
    import webbrowser
    webbrowser.open(f'http://127.0.0.1:{local_port}/')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n正在关闭...')
        server.shutdown()


if __name__ == '__main__':
    main()
