package web

func consoleLayoutHTML(content, active string) string {
	return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>服务器运维控制台</title>
<style>
:root {
  --bg-0: #070b14;
  --bg-1: #0d1524;
  --bg-2: #141f31;
  --panel: rgba(17, 25, 39, 0.8);
  --panel-strong: rgba(20, 31, 49, 0.94);
  --panel-soft: rgba(255, 255, 255, 0.04);
  --line: rgba(148, 163, 184, 0.18);
  --text: #edf3ff;
  --muted: #9aa8bd;
  --accent: #a78bfa;
  --accent-2: #7dd3fc;
  --gold: #d4af7a;
  --success: #5ee7a1;
  --danger: #ff7a7a;
  --warning: #f5c979;
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html { scroll-behavior: smooth; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans CJK SC", sans-serif;
  background:
    radial-gradient(circle at top left, rgba(167, 139, 250, 0.14), transparent 28%),
    radial-gradient(circle at bottom right, rgba(125, 211, 252, 0.12), transparent 28%),
    linear-gradient(135deg, var(--bg-0) 0%, var(--bg-1) 28%, var(--bg-2) 100%);
  color: var(--text);
  min-height: 100vh;
  display: flex;
  position: relative;
  overflow-x: hidden;
}
body::before,
body::after {
  content: "";
  position: fixed;
  width: 380px;
  height: 380px;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
  z-index: 0;
  opacity: 0.35;
  animation: floatOrb 16s ease-in-out infinite alternate;
}
body::before {
  background: rgba(167, 139, 250, 0.26);
  top: -120px;
  left: -60px;
}
body::after {
  background: rgba(125, 211, 252, 0.18);
  bottom: -140px;
  right: -40px;
  animation-delay: 2s;
}

@keyframes floatOrb {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(20px, 28px, 0) scale(1.08); }
}

/* Sidebar */
.sidebar {
  width: 248px;
  background: rgba(12, 18, 29, 0.82);
  border-right: 1px solid var(--line);
  backdrop-filter: blur(18px);
  display: flex;
  flex-direction: column;
  position: fixed;
  height: 100vh;
  z-index: 20;
  box-shadow: 18px 0 40px rgba(3, 7, 18, 0.22);
}
.sidebar-logo {
  padding: 24px 20px 18px;
  border-bottom: 1px solid var(--line);
  display: flex;
  align-items: center;
  gap: 12px;
  background: linear-gradient(180deg, rgba(167, 139, 250, 0.06), transparent);
}
.sidebar-logo .icon {
  font-size: 30px;
  width: 42px;
  height: 42px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(212, 175, 122, 0.18), rgba(167, 139, 250, 0.22));
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.2), 0 10px 22px rgba(167, 139, 250, 0.2);
}
.sidebar-logo h1 { font-size: 15px; font-weight: 700; letter-spacing: 0.05em; color: #fff; }
.sidebar-logo p { font-size: 11px; color: var(--muted); letter-spacing: 0.08em; text-transform: uppercase; }

.sidebar-nav { flex: 1; padding: 18px 12px; }
.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 12px;
  color: var(--muted);
  text-decoration: none;
  font-size: 14px;
  margin-bottom: 5px;
  transition: transform 0.2s ease, background 0.2s ease, box-shadow 0.2s ease, color 0.2s ease;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.nav-item::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(167,139,250,0.14), rgba(125,211,252,0.08));
  opacity: 0;
  transition: opacity 0.2s ease;
}
.nav-item:hover::before,
.nav-item.active::before { opacity: 1; }
.nav-item:hover {
  background: rgba(255,255,255,0.03);
  color: var(--text);
  transform: translateX(2px);
}
.nav-item.active {
  background: linear-gradient(135deg, rgba(167,139,250,0.18), rgba(125,211,252,0.12));
  border: 1px solid rgba(167,139,250,0.2);
  color: #fff;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.12), 0 12px 20px rgba(123, 97, 255, 0.12);
}
.nav-item .nav-icon {
  position: relative;
  z-index: 1;
  font-size: 18px;
  width: 24px;
  text-align: center;
}
.nav-item span:last-child { position: relative; z-index: 1; }

.sidebar-footer {
  padding: 16px 16px 18px;
  border-top: 1px solid var(--line);
  background: linear-gradient(180deg, rgba(255,255,255,0.015), rgba(255,255,255,0.02));
}
.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.user-avatar {
  width: 38px; height: 38px;
  background: linear-gradient(135deg, #d4af7a, #8b5cf6);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  box-shadow: 0 8px 18px rgba(167,139,250,0.28);
}
.user-meta .user-name { font-size: 13px; font-weight: 600; color: var(--text); }
.user-meta .user-role { font-size: 11px; color: var(--muted); }
.logout-btn {
  width: 100%;
  padding: 9px 12px;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 10px;
  color: var(--muted);
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.logout-btn:hover { background: rgba(255,122,122,0.12); border-color: rgba(255,122,122,0.3); color: #fff; }
.logout-btn + .logout-btn { margin-top: 8px; }
.change-pass-btn:hover { background: rgba(167,139,250,0.12); border-color: rgba(167,139,250,0.3); color: #fff; }

/* Main content */
.main-content {
  position: relative;
  z-index: 1;
  flex: 1;
  margin-left: 248px;
  padding: 28px 30px 40px;
}
.main-content::before {
  content: "";
  position: absolute;
  inset: 18px 18px auto auto;
  width: 220px;
  height: 220px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(167,139,250,0.15), transparent 62%);
  pointer-events: none;
  filter: blur(26px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
}
.page-kicker,
.panel-kicker {
  color: #9cc8ff;
  letter-spacing: 0.12em;
  font-size: 11px;
  text-transform: uppercase;
  font-weight: 700;
  opacity: 0.82;
}
.dashboard-header {
  padding: 18px 18px 10px;
  border-bottom: 1px solid var(--line);
  margin-bottom: 20px;
}
.page-header h2 {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: #fff;
}
.page-desc {
  color: var(--muted);
  font-size: 14px;
  margin-top: 6px;
}
.header-actions {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-top: 10px;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: 1.7fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}
.hero-panel {
  position: relative;
  overflow: hidden;
  min-height: 240px;
}
.hero-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(167,139,250,0.08), rgba(125,211,252,0.05), transparent);
}
.hero-panel-head {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.live-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 999px;
  background: rgba(94,231,161,0.1);
  border: 1px solid rgba(94,231,161,0.18);
  color: #69ebad;
  font-size: 12px;
  font-weight: 700;
}
.pulse-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #69ebad;
  box-shadow: 0 0 0 0 rgba(105, 235, 173, 0.6);
  animation: pulseDot 1.8s infinite;
}
@keyframes pulseDot {
  0% { box-shadow: 0 0 0 0 rgba(105, 235, 173, 0.6); }
  70% { box-shadow: 0 0 0 12px rgba(105, 235, 173, 0); }
  100% { box-shadow: 0 0 0 0 rgba(105, 235, 173, 0); }
}
.health-visual {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  min-height: 150px;
}
.ring-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 150px;
}
.ring {
  width: 128px;
  height: 128px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  position: relative;
  background: conic-gradient(#a78bfa 0 86%, rgba(255,255,255,0.06) 86% 100%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.14), 0 18px 28px rgba(167,139,250,0.15);
  animation: rotateGlow 8s linear infinite;
}
.ring::before {
  content: "";
  position: absolute;
  inset: 12px;
  border-radius: 50%;
  background: rgba(10, 15, 24, 0.96);
  border: 1px solid rgba(148,163,184,0.12);
}
.ring-good {
  background: conic-gradient(#5ee7a1 0 88%, rgba(255,255,255,0.06) 88% 100%);
}
.ring-core {
  position: relative;
  z-index: 1;
  font-size: 24px;
  font-weight: 700;
  color: #fff;
}
.health-metrics {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.mini-metric {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(148,163,184,0.14);
  border-radius: 14px;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 88px;
}
.mini-metric span {
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.mini-metric strong {
  margin-top: 8px;
  font-size: 22px;
  color: #fff;
}
.compact-panel {
  display: flex;
  flex-direction: column;
}
.data-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 10px 0 14px;
}
.data-strip > div {
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(148,163,184,0.14);
  border-radius: 12px;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.data-strip span {
  color: var(--muted);
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}
.data-strip strong {
  font-size: 18px;
  color: #fff;
}
.alert-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 8px;
}
.alert-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 10px;
  border-radius: 12px;
  border: 1px solid rgba(148,163,184,0.12);
  background: rgba(255,255,255,0.015);
}
.alert-item span {
  width: 28px;
  height: 28px;
  display: grid;
  place-items: center;
  border-radius: 10px;
  font-weight: 700;
}
.alert-item.warning {
  border-color: rgba(245,201,121,0.22);
  background: rgba(245,201,121,0.06);
}
.alert-item.warning span { background: rgba(245,201,121,0.12); color: #f7d69a; }
.alert-item.ok {
  border-color: rgba(94,231,161,0.18);
  background: rgba(94,231,161,0.06);
}
.alert-item.ok span { background: rgba(94,231,161,0.12); color: #69ebad; }
.alert-item strong {
  font-size: 13px;
  display: block;
  color: #f3f7ff;
}
.alert-item small {
  color: var(--muted);
  display: block;
  margin-top: 2px;
}
@keyframes rotateGlow {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Stats grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}
.stat-card {
  background: linear-gradient(180deg, rgba(17,25,39,0.85), rgba(15,23,42,0.8));
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
  backdrop-filter: blur(12px);
  box-shadow: 0 18px 26px rgba(2, 6, 23, 0.18);
  position: relative;
  overflow: hidden;
}
.stat-card::before {
  content: "";
  position: absolute;
  inset: 0 auto auto 0;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, rgba(212,175,122,0.8), transparent 45%);
}
.stat-card:hover {
  transform: translateY(-3px);
  border-color: rgba(167,139,250,0.35);
  box-shadow: 0 22px 32px rgba(58, 46, 101, 0.25);
}
.stat-icon {
  width: 52px;
  height: 52px;
  background: linear-gradient(135deg, rgba(167,139,250,0.2), rgba(125,211,252,0.14));
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.18);
}
.stat-online .stat-icon { background: linear-gradient(135deg, rgba(94,231,161,0.18), rgba(34,197,94,0.1)); }
.stat-offline .stat-icon { background: linear-gradient(135deg, rgba(255,122,122,0.18), rgba(239,68,68,0.13)); }
.stat-alerts .stat-icon { background: linear-gradient(135deg, rgba(245,201,121,0.18), rgba(251,191,36,0.12)); }
.stat-value { font-size: 28px; font-weight: 700; color: #fff; }
.stat-label { font-size: 13px; color: var(--muted); margin-top: 2px; }

/* Sections */
.section {
  background: linear-gradient(180deg, rgba(17,25,39,0.84), rgba(15,23,42,0.9));
  border: 1px solid var(--line);
  border-radius: 18px;
  padding: 20px;
  margin-bottom: 20px;
  backdrop-filter: blur(12px);
  box-shadow: 0 16px 26px rgba(2, 6, 23, 0.14);
}
.section h3 {
  font-size: 16px;
  font-weight: 700;
  color: #f8fbff;
  margin-bottom: 16px;
  letter-spacing: 0.02em;
}

/* Buttons */
.btn {
  padding: 9px 16px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  letter-spacing: 0.02em;
}
.btn-primary {
  background: linear-gradient(135deg, #a78bfa 0%, #7dd3fc 100%);
  color: #0b1020;
  box-shadow: 0 12px 20px rgba(167, 139, 250, 0.22);
}
.btn-primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 22px rgba(167, 139, 250, 0.28);
}
.btn-secondary {
  background: rgba(255,255,255,0.03);
  color: var(--text);
  border: 1px solid rgba(148,163,184,0.2);
}
.btn-secondary:hover { background: rgba(255,255,255,0.06); }
.btn-danger {
  background: linear-gradient(135deg, #ff7a7a 0%, #ef4444 100%);
  color: #fff;
}
.btn-danger:hover { background: #dc2626; }
.btn-sm { padding: 5px 10px; font-size: 12px; }
.btn-success {
  background: linear-gradient(135deg, #5ee7a1 0%, #2ac76d 100%);
  color: #07130d;
}
.btn-success:hover { background: #16a34a; }
.btn-warning {
  background: linear-gradient(135deg, #f5c979, #f59e0b);
  color: #18120a;
}
.btn-warning:hover { background: #d97706; }

/* Table */
.data-table {
  width: 100%;
  border-collapse: collapse;
}
.data-table th {
  text-align: left;
  padding: 12px 14px;
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  border-bottom: 1px solid var(--line);
}
.data-table td {
  padding: 12px 14px;
  font-size: 13px;
  color: #dfe9ff;
  border-bottom: 1px solid var(--line);
}
.data-table tr:hover td { background: rgba(255,255,255,0.02); }
.empty-cell {
  text-align: center;
  color: var(--muted) !important;
  padding: 40px !important;
}

/* Status badges */
.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.02em;
}
.badge-success { background: rgba(94,231,161,0.12); color: var(--success); }
.badge-danger { background: rgba(255,122,122,0.12); color: var(--danger); }
.badge-warning { background: rgba(245,201,121,0.12); color: var(--warning); }
.badge-info { background: rgba(125,211,252,0.12); color: var(--accent-2); }
.badge-secondary { background: rgba(148,163,184,0.12); color: #dfe7f6; }

.action-btns { display: flex; gap: 6px; }
.action-btns .btn { padding: 4px 10px; font-size: 12px; }

/* Modal */
.modal {
  display: none;
  position: fixed;
  inset: 0;
  background: rgba(5, 9, 18, 0.72);
  backdrop-filter: blur(6px);
  z-index: 1000;
  align-items: center;
  justify-content: center;
}
.modal.show { display: flex; }
.modal-content {
  background: linear-gradient(180deg, rgba(17,25,39,0.95), rgba(11,18,30,0.95));
  border: 1px solid rgba(167,139,250,0.2);
  border-radius: 20px;
  width: min(520px, 92vw);
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 32px 60px rgba(3, 7, 18, 0.45);
}
.modal-header {
  padding: 20px 22px;
  border-bottom: 1px solid var(--line);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.modal-header h3 { font-size: 18px; font-weight: 700; color: #fff; }
.modal-close {
  background: transparent;
  border: none;
  color: var(--muted);
  font-size: 22px;
  cursor: pointer;
  padding: 4px;
}
.modal-close:hover { color: #fff; }
.modal-body { padding: 20px 22px; }
.modal-footer {
  padding: 16px 22px 20px;
  border-top: 1px solid var(--line);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* Forms */
.form-group { margin-bottom: 16px; }
.form-group label {
  display: block;
  margin-bottom: 7px;
  font-size: 13px;
  font-weight: 600;
  color: #d9e5ff;
}
.form-group input, .form-group select {
  width: 100%;
  padding: 10px 12px;
  background: rgba(15, 23, 42, 0.82);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 10px;
  color: #edf3ff;
  font-size: 13px;
  transition: all 0.2s ease;
}
.form-group input:focus, .form-group select:focus {
  outline: none;
  border-color: rgba(167,139,250,0.5);
  box-shadow: 0 0 0 3px rgba(167,139,250,0.12);
}
.form-row { display: flex; gap: 12px; }
.form-row .form-group { flex: 1; }

.security-notice,
.notice-box {
  background: rgba(212,175,122,0.08);
  border: 1px solid rgba(212,175,122,0.3);
  border-radius: 10px;
  padding: 14px 16px;
  font-size: 13px;
  color: #f7d69a;
}
.notice-box { margin-top: 8px; }

.apikey-box {
  background: rgba(11, 16, 24, 0.9);
  border: 1px dashed rgba(167,139,250,0.5);
  border-radius: 10px;
  padding: 16px;
  font-family: monospace;
  font-size: 13px;
  color: #c8c4ff;
  word-break: break-all;
  margin: 12px 0;
  user-select: all;
}
.apikey-hint { font-size: 12px; color: var(--muted); }

.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.search-input, .select-input {
  padding: 9px 12px;
  background: rgba(11, 16, 24, 0.85);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 10px;
  color: #edf3ff;
  font-size: 13px;
}
.search-input { flex: 1; max-width: 300px; }
.search-input:focus, .select-input:focus {
  outline: none;
  border-color: rgba(125,211,252,0.5);
}

.deploy-output {
  background: rgba(11,16,24,0.85);
  border: 1px solid rgba(148,163,184,0.18);
  border-radius: 10px;
  padding: 12px;
  font-family: monospace;
  font-size: 12px;
  color: #c5d3eb;
  max-height: 200px;
  overflow-y: auto;
  margin-top: 12px;
  white-space: pre-wrap;
}
.deploy-info {
  background: rgba(167,139,250,0.08);
  border: 1px solid rgba(167,139,250,0.28);
  border-radius: 10px;
  padding: 12px 14px;
  font-size: 13px;
  color: #daceff;
  margin-bottom: 16px;
}

.empty-state {
  text-align: center;
  padding: 40px 20px;
  color: var(--muted);
}
.empty-icon { font-size: 48px; margin-bottom: 12px; }
.empty-hint { font-size: 13px; margin-top: 8px; }
.empty-hint a { color: #bca7ff; text-decoration: none; }
.empty-hint a:hover { text-decoration: underline; }

.server-list { display: flex; flex-direction: column; gap: 10px; }
.server-item {
  display: flex;
  align-items: center;
  padding: 14px 16px;
  background: rgba(11,16,24,0.82);
  border: 1px solid rgba(148,163,184,0.16);
  border-radius: 12px;
  transition: all 0.2s ease;
}
.server-item:hover { border-color: rgba(167,139,250,0.36); transform: translateY(-1px); }
.server-item-icon {
  width: 42px; height: 42px;
  background: linear-gradient(135deg, rgba(167,139,250,0.18), rgba(125,211,252,0.12));
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-right: 14px;
}
.server-item-info { flex: 1; }
.server-item-name { font-size: 14px; font-weight: 600; color: #edf3ff; }
.server-item-host { font-size: 12px; color: var(--muted); margin-top: 2px; }
.server-item-status { display: flex; align-items: center; gap: 8px; }

/* Responsive */
@media (max-width: 768px) {
  .sidebar { width: 60px; }
  .sidebar-logo h1, .sidebar-logo p, .nav-item span, .user-meta, .logout-btn span { display: none; }
  .main-content { margin-left: 60px; padding: 16px; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .form-row { flex-direction: column; gap: 0; }
}
</style>
</head>
<body>
<aside class="sidebar">
	<div class="sidebar-logo">
		<div class="icon">🛡️</div>
		<div>
			<h1>监控控制台</h1>
			<p>Server Health Monitor</p>
		</div>
	</div>
	<nav class="sidebar-nav">
		<a href="/console/dashboard" class="nav-item ` + activeClass(active, "dashboard") + `">
			<span class="nav-icon">📊</span><span>仪表盘</span>
		</a>
		<a href="/console/servers" class="nav-item ` + activeClass(active, "servers") + `">
			<span class="nav-icon">🖥️</span><span>服务器管理</span>
		</a>
		<a href="/console/tickets" class="nav-item ` + activeClass(active, "tickets") + `">
			<span class="nav-icon">🎫</span><span>工单中心</span>
		</a>
		<a href="/console/users" class="nav-item ` + activeClass(active, "users") + `">
			<span class="nav-icon">👥</span><span>用户管理</span>
		</a>
		<a href="/console/audit" class="nav-item ` + activeClass(active, "audit") + `">
			<span class="nav-icon">📋</span><span>审计日志</span>
		</a>
		<a href="/console/tools" class="nav-item ` + activeClass(active, "tools") + `">
			<span class="nav-icon">🧰</span><span>工具箱</span>
		</a>
	</nav>
	<div class="sidebar-footer">
		<div class="user-info">
			<div class="user-avatar" id="user-avatar">A</div>
			<div class="user-meta">
				<div class="user-name" id="user-name">加载中...</div>
				<div class="user-role" id="user-role">-</div>
			</div>
		</div>
		<button class="logout-btn change-pass-btn" onclick="window.location.href='/console/change-password'">🔑 修改密码</button>
		<button class="logout-btn" onclick="doLogout()">🚪 退出登录</button>
	</div>
</aside>

<main class="main-content">
` + content + `
</main>

<script>
let currentUser = null;
let currentRole = null;

// Load user info
async function loadUser() {
	try {
		const res = await fetch('/console/api/me');
		const data = await res.json();
		if (data.success) {
			currentUser = data.data.username;
			currentRole = data.data.role;
			document.getElementById('user-name').textContent = currentUser;
			document.getElementById('user-role').textContent = currentRole === 'admin' ? '管理员' : '查看者';
			document.getElementById('user-avatar').textContent = currentUser.charAt(0).toUpperCase();
		}
	} catch(e) { console.error(e); }
}

async function doLogout() {
	if (!confirm('确定要退出登录吗？')) return;
	await fetch('/console/api/logout', { method: 'POST' });
	window.location.href = '/console/login';
}

// Modal helpers
function openModal(id) { document.getElementById(id).classList.add('show'); }
function closeModal(id) { document.getElementById(id).classList.remove('show'); }

// Close modal on background click
document.addEventListener('click', (e) => {
	if (e.target.classList.contains('modal')) {
		e.target.classList.remove('show');
	}
});

// API helper
async function apiCall(url, method, body) {
	const opts = { method: method || 'GET', headers: {} };
	if (body) {
		opts.headers['Content-Type'] = 'application/json';
		opts.body = JSON.stringify(body);
	}
	const res = await fetch(url, opts);
	const data = await res.json();
	return { ok: res.ok, data, status: res.status };
}

// Show toast notification
function toast(msg, type) {
	const t = document.createElement('div');
	t.style.cssText = 'position:fixed;top:20px;right:20px;padding:12px 20px;border-radius:8px;z-index:9999;font-size:14px;box-shadow:0 4px 12px rgba(0,0,0,0.3);';
	if (type === 'error') {
		t.style.background = '#ef4444';
		t.style.color = '#fff';
	} else if (type === 'success') {
		t.style.background = '#22c55e';
		t.style.color = '#fff';
	} else {
		t.style.background = '#6366f1';
		t.style.color = '#fff';
	}
	t.textContent = msg;
	document.body.appendChild(t);
	setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity 0.3s'; }, 2500);
	setTimeout(() => t.remove(), 3000);
}

loadUser();
</script>
</body>
</html>`
}

func activeClass(current, target string) string {
	if current == target {
		return "active"
	}
	return ""
}
