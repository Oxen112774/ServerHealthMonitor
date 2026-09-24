"""
Server Health Monitor - 桌面应用外壳（全面重构版 v2）
顶部导航 + 液态玻璃 + 命令词典 + 模拟实战 + 运维工具箱 + 鼠标跟随动效
"""

SHELL_HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Server Health Monitor</title>
<style>
:root{
  --bg-0:#060912;--bg-1:#0a0f1c;--bg-2:#0e1525;
  --glass:rgba(255,255,255,0.045);--glass-2:rgba(255,255,255,0.07);--glass-3:rgba(255,255,255,0.1);
  --border:rgba(255,255,255,0.08);--border-2:rgba(255,255,255,0.14);--border-3:rgba(255,255,255,0.2);
  --text:#eef2fa;--text-2:#9aa8c0;--text-3:#5c6a82;
  --accent:#6c8cff;--accent-2:#38d9f5;--accent-3:#a78bfa;
  --green:#4ade80;--amber:#fbbf24;--red:#f87171;--cyan:#22d3ee;
  --radius:18px;--radius-sm:12px;--radius-xs:8px;
  --shadow:0 8px 32px rgba(0,0,0,0.35);--shadow-lg:0 24px 64px rgba(0,0,0,0.5);
  --ease:cubic-bezier(0.4,0,0.2,1);--ease-spring:cubic-bezier(0.34,1.56,0.64,1);
  --font:"Segoe UI","PingFang SC","Microsoft YaHei",system-ui,sans-serif;
  --mono:"Cascadia Code","Fira Code","JetBrains Mono",Consolas,monospace;
  --mx:50%;--my:30%;
}
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;overflow:hidden}
body{font-family:var(--font);background:var(--bg-0);color:var(--text);-webkit-font-smoothing:antialiased;position:relative}
body::before{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;background:radial-gradient(ellipse 900px 600px at var(--mx) var(--my),rgba(108,140,255,0.10),transparent 55%),radial-gradient(ellipse 700px 500px at 85% 100%,rgba(56,217,245,0.07),transparent 55%),radial-gradient(ellipse 500px 400px at 10% 90%,rgba(167,139,250,0.06),transparent 55%),linear-gradient(180deg,#060912 0%,#080d18 50%,#060912 100%);transition:background 0.3s var(--ease)}
body::after{content:"";position:fixed;inset:0;z-index:0;pointer-events:none;background-image:linear-gradient(rgba(255,255,255,0.018) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,0.018) 1px,transparent 1px);background-size:56px 56px;mask-image:radial-gradient(ellipse at center,black 20%,transparent 75%)}
::-webkit-scrollbar{width:5px;height:5px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border-2);border-radius:3px}
::-webkit-scrollbar-thumb:hover{background:var(--border-3)}

/* Splash */
#splash{position:fixed;inset:0;z-index:9999;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px;background:var(--bg-0);transition:opacity 0.6s var(--ease),visibility 0.6s}
#splash.gone{opacity:0;visibility:hidden}
.splash-logo{width:72px;height:72px;border-radius:22px;position:relative;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;font-size:32px;font-weight:800;color:#fff;box-shadow:0 0 50px rgba(108,140,255,0.4),0 0 100px rgba(56,217,245,0.2);animation:splashPulse 2s var(--ease) infinite}
.splash-logo::after{content:"";position:absolute;inset:-4px;border-radius:24px;border:1.5px solid rgba(108,140,255,0.3);animation:splashRing 2s var(--ease) infinite}
@keyframes splashPulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes splashRing{0%{transform:scale(1);opacity:1}100%{transform:scale(1.4);opacity:0}}
.splash-bar{width:180px;height:3px;background:var(--glass-2);border-radius:3px;overflow:hidden}
.splash-bar::after{content:"";display:block;width:35%;height:100%;border-radius:3px;background:linear-gradient(90deg,var(--accent),var(--accent-2));animation:splashSlide 1.1s var(--ease) infinite}
@keyframes splashSlide{0%{transform:translateX(-120%)}100%{transform:translateX(380%)}}
.splash-text{font-size:11px;letter-spacing:3px;color:var(--text-3);text-transform:uppercase}

/* App Shell */
#app{position:relative;z-index:1;display:flex;flex-direction:column;height:100vh;opacity:0;transform:translateY(12px);transition:all 0.6s var(--ease)}
#app.ready{opacity:1;transform:translateY(0)}

/* Top Nav */
.topnav{height:64px;flex-shrink:0;display:flex;align-items:center;justify-content:space-between;padding:0 20px;gap:16px;background:rgba(10,15,28,0.6);backdrop-filter:blur(24px) saturate(1.4);border-bottom:1px solid var(--border);position:relative;z-index:10}
.brand{display:flex;align-items:center;gap:12px;cursor:pointer;user-select:none;flex-shrink:0}
.brand-mark{width:38px;height:38px;border-radius:12px;flex-shrink:0;background:linear-gradient(135deg,var(--accent),var(--accent-2));display:flex;align-items:center;justify-content:center;font-weight:800;font-size:17px;color:#fff;box-shadow:0 4px 16px rgba(108,140,255,0.35);position:relative}
.brand-mark::after{content:"";position:absolute;inset:-2px;border-radius:13px;border:1px solid rgba(108,140,255,0.25)}
.brand-name{font-size:15px;font-weight:700;letter-spacing:0.3px}
.brand-sub{font-size:10px;color:var(--text-3);letter-spacing:2px;text-transform:uppercase;margin-top:1px}
.nav-tabs{display:flex;gap:3px;padding:4px;background:var(--glass);border:1px solid var(--border);border-radius:14px;backdrop-filter:blur(12px);overflow-x:auto;scrollbar-width:none;scroll-behavior:smooth;flex:1;min-width:0}
.nav-tabs::-webkit-scrollbar{display:none}
.nav-wrapper{display:flex;align-items:center;gap:4px;flex:1;min-width:0;position:relative}
.nav-arrow{width:28px;height:28px;border-radius:9px;border:1px solid var(--border);background:var(--glass);backdrop-filter:blur(8px);color:var(--text-2);cursor:pointer;display:flex;align-items:center;justify-content:center;transition:all 0.25s var(--ease);flex-shrink:0;opacity:0;pointer-events:none}
.nav-arrow.show{opacity:1;pointer-events:auto}
.nav-arrow:hover{color:var(--text);background:var(--glass-2);border-color:rgba(108,140,255,0.3)}
.nav-arrow svg{width:14px;height:14px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.nav-fade-left,.nav-fade-right{position:absolute;top:4px;bottom:4px;width:24px;pointer-events:none;z-index:2;opacity:0;transition:opacity 0.3s}
.nav-fade-left{left:4px;background:linear-gradient(90deg,var(--glass),transparent);border-radius:14px 0 0 14px}
.nav-fade-right{right:4px;background:linear-gradient(-90deg,var(--glass),transparent);border-radius:0 14px 14px 0}
.nav-fade-left.show,.nav-fade-right.show{opacity:1}
.nav-tab{display:flex;align-items:center;gap:6px;padding:8px 14px;border:none;border-radius:10px;background:transparent;color:var(--text-2);font-size:12.5px;font-weight:500;font-family:var(--font);cursor:pointer;transition:all 0.25s var(--ease);position:relative;white-space:nowrap;flex-shrink:0}
.nav-tab svg{width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
.nav-tab:hover{color:var(--text);background:var(--glass-2)}
.nav-tab.active{color:#fff;background:linear-gradient(135deg,rgba(108,140,255,0.25),rgba(56,217,245,0.15));box-shadow:0 2px 12px rgba(108,140,255,0.2),inset 0 0 0 1px rgba(108,140,255,0.3)}
.status-group{display:flex;gap:8px;align-items:center;flex-shrink:0}
.status-pill{display:flex;align-items:center;gap:7px;padding:6px 12px;border-radius:20px;background:var(--glass);border:1px solid var(--border);font-size:11px;color:var(--text-2);backdrop-filter:blur(8px);transition:all 0.3s var(--ease)}
.status-dot{width:7px;height:7px;border-radius:50%;background:var(--text-3);transition:all 0.3s}
.status-dot.ok{background:var(--green);box-shadow:0 0 8px rgba(74,222,128,0.5)}
.status-dot.warn{background:var(--amber);box-shadow:0 0 8px rgba(251,191,36,0.5)}
.status-dot.err{background:var(--red);box-shadow:0 0 8px rgba(248,113,113,0.5)}

/* Content */
.content{flex:1;position:relative;overflow:hidden}
.pane{position:absolute;inset:0;opacity:0;visibility:hidden;transform:translateY(16px) scale(0.99);transition:all 0.4s var(--ease);overflow-y:auto;overflow-x:hidden}
.pane.active{opacity:1;visibility:visible;transform:translateY(0) scale(1)}
.pane-inner{padding:28px 32px;max-width:1200px;margin:0 auto}

/* Glass Card */
.glass{background:var(--glass);border:1px solid var(--border);border-radius:var(--radius);backdrop-filter:blur(20px) saturate(1.3);position:relative;overflow:hidden;transition:all 0.3s var(--ease)}
.glass::before{content:"";position:absolute;top:0;left:0;right:0;height:1px;background:linear-gradient(90deg,transparent,rgba(255,255,255,0.15),transparent)}
.glass:hover{border-color:var(--border-2);box-shadow:var(--shadow)}

/* Buttons */
.btn{display:inline-flex;align-items:center;gap:8px;padding:10px 22px;border:none;border-radius:var(--radius-sm);font-size:13px;font-weight:600;font-family:var(--font);cursor:pointer;transition:all 0.25s var(--ease)}
.btn svg{width:15px;height:15px;stroke:currentColor;fill:none;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.btn-primary{background:linear-gradient(135deg,var(--accent),#5b7cf0);color:#fff;box-shadow:0 4px 20px rgba(108,140,255,0.35)}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 8px 28px rgba(108,140,255,0.45)}
.btn-primary:active{transform:translateY(0)}
.btn-ghost{background:var(--glass-2);color:var(--text-2);border:1px solid var(--border)}
.btn-ghost:hover{background:var(--glass-3);color:var(--text);border-color:var(--border-2)}
.btn-success{background:linear-gradient(135deg,#22c55e,#16a34a);color:#fff}
.btn-danger{background:linear-gradient(135deg,#ef4444,#dc2626);color:#fff}
.btn:disabled{opacity:0.45;cursor:not-allowed;transform:none!important}

/* Monitor Pane */
.monitor-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:18px}
.stat-card{padding:18px}
.stat-card:hover{transform:translateY(-3px)}
.stat-label{font-size:11px;color:var(--text-3);text-transform:uppercase;letter-spacing:1.2px;margin-bottom:8px;display:flex;align-items:center;gap:6px}
.stat-label .dot{width:6px;height:6px;border-radius:50%}
.stat-value{font-size:30px;font-weight:800;font-family:var(--mono);line-height:1;letter-spacing:-1px}
.stat-sub{font-size:11px;color:var(--text-3);margin-top:8px}
.stat-bar{height:4px;background:var(--glass-2);border-radius:2px;margin-top:12px;overflow:hidden}
.stat-bar-fill{height:100%;border-radius:2px;transition:width 1s var(--ease)}
.monitor-hero{display:grid;grid-template-columns:1.6fr 1fr;gap:14px;margin-bottom:18px}
.hero-main{padding:26px}
.hero-eyebrow{font-size:10px;letter-spacing:2.5px;text-transform:uppercase;color:var(--accent-2);font-weight:600;margin-bottom:10px}
.hero-title{font-size:24px;font-weight:800;line-height:1.25;margin-bottom:10px;background:linear-gradient(135deg,#fff,var(--text-2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.hero-desc{font-size:13px;color:var(--text-2);line-height:1.7;margin-bottom:20px}
.hero-actions{display:flex;gap:10px;flex-wrap:wrap}
.hero-side{display:flex;flex-direction:column;gap:10px}
.mini-stat{padding:14px 16px;display:flex;align-items:center;gap:12px}
.mini-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:17px;flex-shrink:0}
.mini-info{flex:1;min-width:0}
.mini-label{font-size:10.5px;color:var(--text-3)}
.mini-value{font-size:16px;font-weight:700;font-family:var(--mono);margin-top:2px}
.feature-row{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:18px}
.feature-card{padding:18px}
.feature-card:hover{transform:translateY(-3px);border-color:var(--accent)}
.feature-icon{width:38px;height:38px;border-radius:10px;background:linear-gradient(135deg,rgba(108,140,255,0.15),rgba(56,217,245,0.08));display:flex;align-items:center;justify-content:center;font-size:18px;margin-bottom:10px;border:1px solid var(--border)}
.feature-card h4{font-size:13.5px;font-weight:600;margin-bottom:5px}
.feature-card p{font-size:11.5px;color:var(--text-2);line-height:1.6}
.feature-tags{display:flex;gap:5px;margin-top:8px;flex-wrap:wrap}
.feature-tags span{padding:2px 8px;border-radius:10px;font-size:10px;background:var(--glass-2);color:var(--text-3);border:1px solid var(--border)}

/* Monitor iframe */
.monitor-iframe-wrap{position:fixed;inset:64px 0 0 0;z-index:5;display:none;background:var(--bg-0)}
.monitor-iframe-wrap.show{display:block}
#monitorFrame{width:100%;height:100%;border:none;background:var(--bg-0)}
.monitor-close{position:absolute;top:16px;right:20px;z-index:6;width:36px;height:36px;border-radius:10px;background:var(--glass-3);border:1px solid var(--border-2);color:var(--text);cursor:pointer;display:flex;align-items:center;justify-content:center;font-size:18px;backdrop-filter:blur(12px);transition:all 0.2s}
.monitor-close:hover{background:var(--red);border-color:var(--red);transform:rotate(90deg)}

/* Console */
.console-wrap{height:100%;display:flex;flex-direction:column}
#consoleHost{flex:1;display:none;position:relative}
#consoleFrame{width:100%;height:100%;border:none;background:#fff}
.console-setup{flex:1;display:flex;align-items:center;justify-content:center;padding:40px}

/* Lexicon */
.lex-header{margin-bottom:20px}
.lex-title{font-size:22px;font-weight:800;margin-bottom:5px}
.lex-sub{font-size:12.5px;color:var(--text-2)}
.lex-search-row{display:flex;gap:10px;margin-bottom:16px;align-items:center}
.lex-search{flex:1;position:relative}
.lex-search input{width:100%;padding:12px 16px 12px 42px;border-radius:var(--radius-sm);background:var(--glass);border:1px solid var(--border);color:var(--text);font-size:13px;font-family:var(--font);outline:none;transition:all 0.3s var(--ease);backdrop-filter:blur(12px)}
.lex-search input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(108,140,255,0.15);background:var(--glass-2)}
.lex-search input::placeholder{color:var(--text-3)}
.lex-search-icon{position:absolute;left:14px;top:50%;transform:translateY(-50%);color:var(--text-3);font-size:15px}
.lex-fav-toggle{padding:11px 16px;border-radius:var(--radius-sm);background:var(--glass);border:1px solid var(--border);color:var(--text-2);cursor:pointer;font-size:12px;transition:all 0.2s;display:flex;align-items:center;gap:6px;white-space:nowrap}
.lex-fav-toggle.active{background:rgba(251,191,36,0.12);border-color:rgba(251,191,36,0.35);color:var(--amber)}
.lex-cats{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:18px}
.lex-cat{padding:7px 14px;border-radius:20px;background:var(--glass);border:1px solid var(--border);color:var(--text-2);font-size:11.5px;cursor:pointer;transition:all 0.25s var(--ease);display:flex;align-items:center;gap:5px;user-select:none}
.lex-cat:hover{background:var(--glass-2);color:var(--text);transform:translateY(-1px)}
.lex-cat.active{background:linear-gradient(135deg,rgba(108,140,255,0.2),rgba(56,217,245,0.1));border-color:rgba(108,140,255,0.4);color:#fff;box-shadow:0 2px 12px rgba(108,140,255,0.2)}
.lex-cat .count{font-size:10px;background:var(--glass-3);padding:1px 7px;border-radius:10px;color:var(--text-3)}
.lex-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}
.cmd-card{padding:16px;animation:cardIn 0.4s var(--ease) backwards}
@keyframes cardIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.cmd-card:hover{transform:translateY(-3px);border-color:var(--border-3)}
.cmd-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;margin-bottom:8px}
.cmd-name{font-family:var(--mono);font-size:13px;font-weight:600;color:var(--accent-2);background:var(--bg-0);padding:5px 10px;border-radius:7px;border:1px solid var(--border);flex:1;overflow-x:auto;white-space:nowrap}
.cmd-fav{background:none;border:none;color:var(--text-3);cursor:pointer;font-size:15px;padding:3px;transition:all 0.2s;flex-shrink:0}
.cmd-fav:hover{transform:scale(1.2)}
.cmd-fav.active{color:var(--amber)}
.cmd-desc{font-size:12px;color:var(--text-2);line-height:1.6;margin-bottom:8px}
.cmd-syntax{font-family:var(--mono);font-size:10.5px;color:var(--text-3);background:var(--bg-0);padding:7px 10px;border-radius:7px;border:1px solid var(--border);margin-bottom:8px;overflow-x:auto;white-space:pre}
.cmd-example{font-size:11px;color:var(--text-3);line-height:1.5}
.cmd-example strong{color:var(--text-2);font-weight:600}
.cmd-foot{display:flex;align-items:center;justify-content:space-between;margin-top:10px;padding-top:8px;border-top:1px solid var(--border)}
.cmd-level{font-size:10px;padding:2px 9px;border-radius:10px;font-weight:600;letter-spacing:0.5px}
.level-easy{background:rgba(74,222,128,0.1);color:var(--green);border:1px solid rgba(74,222,128,0.25)}
.level-mid{background:rgba(251,191,36,0.1);color:var(--amber);border:1px solid rgba(251,191,36,0.25)}
.level-hard{background:rgba(248,113,113,0.1);color:var(--red);border:1px solid rgba(248,113,113,0.25)}
.cmd-copy{background:var(--glass-2);border:1px solid var(--border);color:var(--text-2);padding:4px 10px;border-radius:7px;font-size:10.5px;cursor:pointer;transition:all 0.2s;display:flex;align-items:center;gap:4px}
.cmd-copy:hover{background:var(--accent);border-color:var(--accent);color:#fff}
.cmd-copy.copied{background:var(--green);border-color:var(--green);color:#fff}
.lex-empty{grid-column:1/-1;text-align:center;padding:50px 20px;color:var(--text-3)}
.lex-empty .icon{font-size:44px;margin-bottom:12px;opacity:0.4}

/* ===== Lab (模拟实战) ===== */
.lab-header{margin-bottom:20px}
.lab-title{font-size:22px;font-weight:800;margin-bottom:5px}
.lab-sub{font-size:12.5px;color:var(--text-2)}
.lab-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px}
.lab-stat{padding:16px;text-align:center}
.lab-stat .num{font-size:28px;font-weight:800;font-family:var(--mono)}
.lab-stat .lbl{font-size:11px;color:var(--text-3);margin-top:4px;text-transform:uppercase;letter-spacing:1px}
.lab-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:14px;margin-bottom:20px}
.scenario-card{padding:20px;cursor:pointer}
.scenario-card:hover{transform:translateY(-4px);border-color:var(--accent);box-shadow:0 12px 32px rgba(108,140,255,0.2)}
.scenario-icon{width:48px;height:48px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:24px;margin-bottom:12px;border:1px solid var(--border)}
.scenario-card h4{font-size:15px;font-weight:700;margin-bottom:6px}
.scenario-card p{font-size:12px;color:var(--text-2);line-height:1.6;margin-bottom:12px}
.scenario-meta{display:flex;gap:8px;align-items:center}
.scenario-diff{font-size:10px;padding:3px 10px;border-radius:10px;font-weight:600}
.scenario-steps{font-size:10.5px;color:var(--text-3)}
.scenario-done{position:absolute;top:14px;right:14px;font-size:20px}

/* Lab Quiz */
.quiz-wrap{max-width:760px;margin:0 auto}
.quiz-head{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}
.quiz-back{background:var(--glass-2);border:1px solid var(--border);color:var(--text-2);padding:8px 16px;border-radius:10px;cursor:pointer;font-size:12px;transition:all 0.2s}
.quiz-back:hover{background:var(--glass-3);color:var(--text)}
.quiz-progress{font-size:12px;color:var(--text-2);font-family:var(--mono)}
.quiz-bar{height:5px;background:var(--glass-2);border-radius:3px;margin-bottom:20px;overflow:hidden}
.quiz-bar-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--accent-2));border-radius:3px;transition:width 0.5s var(--ease)}
.quiz-card{padding:28px;margin-bottom:16px}
.quiz-scene{font-size:12px;color:var(--accent-2);margin-bottom:8px;font-weight:600;letter-spacing:0.5px}
.quiz-question{font-size:17px;font-weight:700;line-height:1.5;margin-bottom:20px}
.quiz-options{display:flex;flex-direction:column;gap:10px}
.quiz-option{padding:14px 18px;border-radius:var(--radius-sm);background:var(--bg-1);border:1px solid var(--border);cursor:pointer;transition:all 0.25s var(--ease);display:flex;align-items:flex-start;gap:12px;font-size:13px;line-height:1.5}
.quiz-option:hover:not(.disabled){border-color:var(--accent);background:var(--glass-2);transform:translateX(4px)}
.quiz-option.disabled{cursor:default}
.quiz-option.correct{border-color:var(--green);background:rgba(74,222,128,0.08)}
.quiz-option.wrong{border-color:var(--red);background:rgba(248,113,113,0.08)}
.quiz-option .opt-letter{width:24px;height:24px;border-radius:7px;background:var(--glass-3);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:700;flex-shrink:0;font-family:var(--mono)}
.quiz-option.correct .opt-letter{background:var(--green);color:#fff}
.quiz-option.wrong .opt-letter{background:var(--red);color:#fff}
.quiz-explain{margin-top:14px;padding:14px 16px;border-radius:var(--radius-sm);background:var(--bg-0);border-left:3px solid var(--accent);font-size:12.5px;color:var(--text-2);line-height:1.7;display:none}
.quiz-explain.show{display:block;animation:fadeIn 0.3s}
@keyframes fadeIn{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:translateY(0)}}
.quiz-explain strong{color:var(--accent-2)}
.quiz-next{margin-top:16px;text-align:right}

/* Quiz Result */
.result-card{padding:36px;text-align:center}
.result-icon{font-size:64px;margin-bottom:16px}
.result-score{font-size:48px;font-weight:800;font-family:var(--mono);margin-bottom:6px}
.result-title{font-size:20px;font-weight:700;margin-bottom:8px}
.result-desc{font-size:13px;color:var(--text-2);line-height:1.7;margin-bottom:24px;max-width:500px;margin-left:auto;margin-right:auto}
.result-actions{display:flex;gap:10px;justify-content:center;flex-wrap:wrap}

/* ===== Tools (工具箱) ===== */
.tools-header{margin-bottom:20px}
.tools-title{font-size:22px;font-weight:800;margin-bottom:5px}
.tools-sub{font-size:12.5px;color:var(--text-2)}
.tools-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:14px}
.tool-card{padding:20px}
.tool-head{display:flex;align-items:center;gap:10px;margin-bottom:14px}
.tool-icon{width:36px;height:36px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:18px;background:linear-gradient(135deg,rgba(108,140,255,0.15),rgba(56,217,245,0.08));border:1px solid var(--border);flex-shrink:0}
.tool-head h4{font-size:14px;font-weight:600}
.tool-input{width:100%;padding:10px 12px;border-radius:var(--radius-xs);background:var(--bg-1);border:1px solid var(--border);color:var(--text);font-size:12px;font-family:var(--mono);outline:none;transition:all 0.25s;resize:vertical;min-height:60px}
.tool-input:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(108,140,255,0.12)}
.tool-output{width:100%;padding:10px 12px;border-radius:var(--radius-xs);background:var(--bg-0);border:1px solid var(--border);color:var(--accent-2);font-size:12px;font-family:var(--mono);min-height:60px;word-break:break-all;white-space:pre-wrap;margin-top:10px}
.tool-row{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
.tool-btn{padding:7px 14px;border-radius:8px;background:var(--glass-2);border:1px solid var(--border);color:var(--text-2);font-size:11.5px;cursor:pointer;transition:all 0.2s;font-family:var(--font)}
.tool-btn:hover{background:var(--accent);border-color:var(--accent);color:#fff}
.tool-btn.primary{background:linear-gradient(135deg,var(--accent),#5b7cf0);border-color:transparent;color:#fff}
.tool-select{padding:7px 10px;border-radius:8px;background:var(--bg-1);border:1px solid var(--border);color:var(--text);font-size:11.5px;outline:none;cursor:pointer}
.tool-label{font-size:11px;color:var(--text-3);margin-bottom:6px;display:block;font-weight:600}

/* Connect */
.connect-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.form-card{padding:22px}
.form-title{font-size:15px;font-weight:700;margin-bottom:5px;display:flex;align-items:center;gap:8px}
.form-desc{font-size:11.5px;color:var(--text-3);margin-bottom:18px;line-height:1.5}
.field{margin-bottom:14px}
.field label{display:block;font-size:11.5px;font-weight:600;color:var(--text-2);margin-bottom:6px}
.field input,.field select,.field textarea{width:100%;padding:10px 14px;border-radius:var(--radius-xs);background:var(--bg-1);border:1px solid var(--border);color:var(--text);font-size:12.5px;font-family:var(--font);outline:none;transition:all 0.25s var(--ease)}
.field input:focus,.field select:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(108,140,255,0.12)}
.field input::placeholder{color:var(--text-3)}
.field-row{display:flex;gap:12px}
.field-row .field{flex:1}
.hint{font-size:11px;color:var(--text-3);margin-top:5px;line-height:1.5}
.hint.err{color:var(--red)}
.hint.ok{color:var(--green)}
.btn-row{display:flex;gap:8px;flex-wrap:wrap;margin-top:4px}

/* Logs */
.logs-wrap{height:100%;display:flex;flex-direction:column;padding:18px 22px}
.logs-card{flex:1;display:flex;flex-direction:column;overflow:hidden}
.logs-head{display:flex;align-items:center;justify-content:space-between;padding:12px 18px;border-bottom:1px solid var(--border)}
.logs-head span{font-size:12.5px;font-weight:600;font-family:var(--mono)}
.logs-body{flex:1;overflow-y:auto;padding:12px 16px;font-family:var(--mono);font-size:11.5px;line-height:1.8;background:rgba(0,0,0,0.2)}
.log-line{display:flex;gap:10px;padding:1px 0}
.log-time{color:var(--text-3);flex-shrink:0;font-size:10.5px}
.log-msg{color:var(--text-2);word-break:break-all}
.log-line.warn .log-msg{color:var(--amber)}
.log-line.error .log-msg{color:var(--red)}
.log-line.console .log-msg{color:var(--accent-2)}

/* Toast */
.toasts{position:fixed;bottom:24px;right:24px;z-index:9998;display:flex;flex-direction:column;gap:10px}
.toast{padding:12px 18px;border-radius:var(--radius-sm);background:var(--glass-3);border:1px solid var(--border-2);backdrop-filter:blur(20px);box-shadow:var(--shadow-lg);font-size:12.5px;color:var(--text);display:flex;align-items:center;gap:8px;animation:toastIn 0.4s var(--ease-spring);min-width:180px}
.toast.success{border-left:3px solid var(--green)}
.toast.error{border-left:3px solid var(--red)}
.toast.info{border-left:3px solid var(--accent)}
@keyframes toastIn{from{opacity:0;transform:translateX(40px) scale(0.9)}to{opacity:1;transform:translateX(0) scale(1)}}
@keyframes toastOut{to{opacity:0;transform:translateX(40px)}}

@media(max-width:1100px){
  .monitor-grid{grid-template-columns:repeat(2,1fr)}
  .monitor-hero{grid-template-columns:1fr}
  .feature-row{grid-template-columns:1fr}
  .connect-grid{grid-template-columns:1fr}
  .lab-stats{grid-template-columns:1fr}
}
@media(max-width:768px){
  .topnav{padding:0 12px;height:56px}
  .brand-sub{display:none}
  .nav-tab span{display:none}
  .nav-tab{padding:8px 10px}
  .pane-inner{padding:16px 14px}
  .monitor-grid{grid-template-columns:1fr}
  .lex-grid{grid-template-columns:1fr}
  .tools-grid{grid-template-columns:1fr}
  .status-pill .pill-text{display:none}
}
</style>
</head>
<body>

<div id="splash">
  <div class="splash-logo">S</div>
  <div class="splash-bar"></div>
  <div class="splash-text">Loading Server Health Monitor</div>
</div>

<div id="app">
  <nav class="topnav">
    <div class="brand" onclick="switchPane('monitor')">
      <div class="brand-mark">S</div>
      <div><div class="brand-name">Server Health</div><div class="brand-sub">Monitor · v4.0</div></div>
    </div>
    <div class="nav-wrapper">
      <button class="nav-arrow" id="navArrowLeft" onclick="scrollNav(-1)"><svg viewBox="0 0 24 24"><polyline points="15 18 9 12 15 6"/></svg></button>
      <div class="nav-fade-left" id="navFadeLeft"></div>
      <div class="nav-tabs" id="navTabs">
      <button class="nav-tab active" data-pane="monitor"><svg viewBox="0 0 24 24"><rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/></svg><span>监控</span></button>
      <button class="nav-tab" data-pane="console"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.6 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></svg><span>控制台</span></button>
      <button class="nav-tab" data-pane="lexicon"><svg viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg><span>命令词典</span></button>
      <button class="nav-tab" data-pane="lab"><svg viewBox="0 0 24 24"><path d="M10 2v7.5L4.5 19a2 2 0 0 0 1.7 3h11.6a2 2 0 0 0 1.7-3L14 9.5V2"/><line x1="8" y1="2" x2="16" y2="2"/><line x1="7" y1="15" x2="17" y2="15"/></svg><span>模拟实战</span></button>
      <button class="nav-tab" data-pane="tools"><svg viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg><span>工具箱</span></button>
      <button class="nav-tab" data-pane="connect"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg><span>连接</span></button>
      <button class="nav-tab" data-pane="logs"><svg viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg><span>日志</span></button>
      </div>
      <div class="nav-fade-right" id="navFadeRight"></div>
      <button class="nav-arrow" id="navArrowRight" onclick="scrollNav(1)"><svg viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"/></svg></button>
    </div>
    <div class="status-group">
      <div class="status-pill"><span class="status-dot" id="connDot"></span><span class="pill-text" id="connText">未连接</span></div>
      <div class="status-pill"><span class="status-dot" id="consoleDot"></span><span class="pill-text">控制台</span></div>
    </div>
  </nav>

  <div class="content">
    <!-- Monitor -->
    <section class="pane active" id="pane-monitor">
      <div class="pane-inner">
        <div class="monitor-grid">
          <div class="glass stat-card"><div class="stat-label"><span class="dot" style="background:var(--green);box-shadow:0 0 6px var(--green)"></span>节点在线</div><div class="stat-value" style="color:var(--green)">96.2%</div><div class="stat-sub">本周稳定运行</div><div class="stat-bar"><div class="stat-bar-fill" style="width:96.2%;background:linear-gradient(90deg,var(--green),#22c55e)"></div></div></div>
          <div class="glass stat-card"><div class="stat-label"><span class="dot" style="background:var(--amber);box-shadow:0 0 6px var(--amber)"></span>待处理告警</div><div class="stat-value" style="color:var(--amber)">3</div><div class="stat-sub">2 警告 · 1 严重</div><div class="stat-bar"><div class="stat-bar-fill" style="width:30%;background:linear-gradient(90deg,var(--amber),#f59e0b)"></div></div></div>
          <div class="glass stat-card"><div class="stat-label"><span class="dot" style="background:var(--cyan);box-shadow:0 0 6px var(--cyan)"></span>平均响应</div><div class="stat-value" style="color:var(--cyan)">128ms</div><div class="stat-sub">网络延迟正常</div><div class="stat-bar"><div class="stat-bar-fill" style="width:25%;background:linear-gradient(90deg,var(--cyan),#06b6d4)"></div></div></div>
          <div class="glass stat-card"><div class="stat-label"><span class="dot" style="background:var(--accent-3);box-shadow:0 0 6px var(--accent-3)"></span>实战完成</div><div class="stat-value" style="color:var(--accent-3)" id="labDoneCount">0</div><div class="stat-sub">模拟实战场景</div><div class="stat-bar"><div class="stat-bar-fill" style="width:0%;background:linear-gradient(90deg,var(--accent-3),#8b5cf6)" id="labDoneBar"></div></div></div>
        </div>
        <div class="monitor-hero">
          <div class="glass hero-main">
            <div class="hero-eyebrow">Server Health Monitor</div>
            <h1 class="hero-title">高可用运维平台<br>从连接到智能治理</h1>
            <p class="hero-desc">面向新手与运维人员的统一桌面入口。聚合实时监控、命令词典、模拟实战、运维工具箱、远程连接与管理控制台，零门槛上手运维。</p>
            <div class="hero-actions">
              <button class="btn btn-primary" onclick="switchPane('connect')"><svg viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>连接服务器</button>
              <button class="btn btn-ghost" onclick="openMonitor()"><svg viewBox="0 0 24 24"><polygon points="5 3 19 12 5 21 5 3"/></svg>实时监控</button>
              <button class="btn btn-ghost" onclick="switchPane('lab')"><svg viewBox="0 0 24 24"><path d="M10 2v7.5L4.5 19a2 2 0 0 0 1.7 3h11.6a2 2 0 0 0 1.7-3L14 9.5V2"/></svg>模拟实战</button>
              <button class="btn btn-ghost" onclick="switchPane('tools')"><svg viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>工具箱</button>
            </div>
          </div>
          <div class="hero-side">
            <div class="glass mini-stat"><div class="mini-icon" style="background:rgba(74,222,128,0.1)">📡</div><div class="mini-info"><div class="mini-label">远程连接</div><div class="mini-value">SSH / 直连</div></div></div>
            <div class="glass mini-stat"><div class="mini-icon" style="background:rgba(251,191,36,0.1)">🧠</div><div class="mini-info"><div class="mini-label">智能诊断</div><div class="mini-value">阈值 + AI</div></div></div>
            <div class="glass mini-stat"><div class="mini-icon" style="background:rgba(108,140,255,0.1)">📚</div><div class="mini-info"><div class="mini-label">命令词典</div><div class="mini-value">120+ 命令</div></div></div>
            <div class="glass mini-stat"><div class="mini-icon" style="background:rgba(167,139,250,0.1)">🧪</div><div class="mini-info"><div class="mini-label">模拟实战</div><div class="mini-value">6 个场景</div></div></div>
          </div>
        </div>
        <div class="feature-row">
          <div class="glass feature-card"><div class="feature-icon">📡</div><h4>远程连接</h4><p>支持 SSH 隧道、直接连接、内网代理三种方式，新手也能安全接入。</p><div class="feature-tags"><span>安全</span><span>稳定</span></div></div>
          <div class="glass feature-card"><div class="feature-icon">🧪</div><h4>模拟实战</h4><p>交互式故障排查场景，CPU飙高、网站宕机、磁盘爆满，边做边学。</p><div class="feature-tags"><span>新手</span><span>互动</span></div></div>
          <div class="glass feature-card"><div class="feature-icon">🛠️</div><h4>运维工具箱</h4><p>Base64编解码、JSON格式化、密码生成、时间戳转换，开箱即用。</p><div class="feature-tags"><span>实用</span><span>离线</span></div></div>
        </div>
      </div>
    </section>

    <!-- Console -->
    <section class="pane" id="pane-console">
      <div class="console-wrap">
        <div id="consoleHost"><iframe id="consoleFrame" src="about:blank"></iframe></div>
        <div class="console-setup" id="consoleSetup"><div class="pane-inner" style="max-width:480px"><div class="glass" style="padding:36px;text-align:center"><div style="font-size:48px;margin-bottom:16px">🧩</div><h3 style="font-size:18px;font-weight:700;margin-bottom:10px">管理控制台未启动</h3><p style="font-size:13px;color:var(--text-2);line-height:1.7;margin-bottom:22px">启动后可在此窗口内管理多台服务器、用户权限、部署与工单。</p><button class="btn btn-primary" onclick="startConsole()">启动管理控制台</button></div></div></div>
      </div>
    </section>

    <!-- Lexicon -->
    <section class="pane" id="pane-lexicon">
      <div class="pane-inner">
        <div class="lex-header"><h2 class="lex-title">📚 命令词典</h2><p class="lex-sub">跨平台运维命令速查 · 120+ 命令 · 支持搜索与收藏</p></div>
        <div class="lex-search-row">
          <div class="lex-search"><span class="lex-search-icon">🔍</span><input type="text" id="lexSearch" placeholder="搜索命令、用途或关键词…" oninput="renderLexicon()"></div>
          <button class="lex-fav-toggle" id="favToggle" onclick="toggleFavFilter()">⭐ 收藏</button>
        </div>
        <div class="lex-cats" id="lexCats"></div>
        <div class="lex-grid" id="lexGrid"></div>
      </div>
    </section>

    <!-- Lab (模拟实战) -->
    <section class="pane" id="pane-lab">
      <div class="pane-inner">
        <div id="labList">
          <div class="lab-header"><h2 class="lab-title">🧪 模拟实战实验室</h2><p class="lab-sub">交互式故障排查训练 · 在真实场景中学习运维思维 · 完成后获得评分和详细解析</p></div>
          <div class="lab-stats">
            <div class="glass lab-stat"><div class="num" style="color:var(--accent-2)" id="labTotal">6</div><div class="lbl">场景总数</div></div>
            <div class="glass lab-stat"><div class="num" style="color:var(--green)" id="labCompleted">0</div><div class="lbl">已完成</div></div>
            <div class="glass lab-stat"><div class="num" style="color:var(--amber)" id="labAvgScore">—</div><div class="lbl">平均得分</div></div>
          </div>
          <div class="lab-grid" id="labGrid"></div>
        </div>
        <div id="labQuiz" style="display:none"></div>
      </div>
    </section>

    <!-- Tools -->
    <section class="pane" id="pane-tools">
      <div class="pane-inner">
        <div class="tools-header"><h2 class="tools-title">🛠️ 运维工具箱</h2><p class="tools-sub">常用运维小工具 · 全部本地运行 · 无需联网</p></div>
        <div class="tools-grid">
          <!-- Base64 -->
          <div class="glass tool-card">
            <div class="tool-head"><div class="tool-icon">🔐</div><h4>Base64 编解码</h4></div>
            <label class="tool-label">输入文本</label>
            <textarea class="tool-input" id="b64Input" placeholder="输入要编码/解码的文本…"></textarea>
            <div class="tool-row">
              <button class="tool-btn primary" onclick="b64Encode()">编码</button>
              <button class="tool-btn" onclick="b64Decode()">解码</button>
              <button class="tool-btn" onclick="copyOutput('b64Output')">复制结果</button>
            </div>
            <div class="tool-output" id="b64Output">结果显示在这里…</div>
          </div>
          <!-- URL -->
          <div class="glass tool-card">
            <div class="tool-head"><div class="tool-icon">🌐</div><h4>URL 编解码</h4></div>
            <label class="tool-label">输入 URL 或文本</label>
            <textarea class="tool-input" id="urlInput" placeholder="https://example.com/?q=你好"></textarea>
            <div class="tool-row">
              <button class="tool-btn primary" onclick="urlEncode()">编码</button>
              <button class="tool-btn" onclick="urlDecode()">解码</button>
              <button class="tool-btn" onclick="copyOutput('urlOutput')">复制结果</button>
            </div>
            <div class="tool-output" id="urlOutput">结果显示在这里…</div>
          </div>
          <!-- JSON -->
          <div class="glass tool-card">
            <div class="tool-head"><div class="tool-icon">{ }</div><h4>JSON 格式化</h4></div>
            <label class="tool-label">输入 JSON</label>
            <textarea class="tool-input" id="jsonInput" placeholder='{"name":"test","value":123}'></textarea>
            <div class="tool-row">
              <button class="tool-btn primary" onclick="jsonFormat()">格式化</button>
              <button class="tool-btn" onclick="jsonMinify()">压缩</button>
              <button class="tool-btn" onclick="copyOutput('jsonOutput')">复制结果</button>
            </div>
            <div class="tool-output" id="jsonOutput">结果显示在这里…</div>
          </div>
          <!-- 时间戳 -->
          <div class="glass tool-card">
            <div class="tool-head"><div class="tool-icon">⏰</div><h4>时间戳转换</h4></div>
            <label class="tool-label">时间戳（秒）</label>
            <input class="tool-input" id="tsInput" style="min-height:unset" placeholder="1700000000" value="">
            <div class="tool-row">
              <button class="tool-btn primary" onclick="tsToDate()">时间戳→日期</button>
              <button class="tool-btn" onclick="dateToTs()">当前时间戳</button>
              <button class="tool-btn" onclick="copyOutput('tsOutput')">复制结果</button>
            </div>
            <div class="tool-output" id="tsOutput">结果显示在这里…</div>
          </div>
          <!-- 密码生成 -->
          <div class="glass tool-card">
            <div class="tool-head"><div class="tool-icon">🔑</div><h4>密码生成器</h4></div>
            <label class="tool-label">长度：<span id="pwLenVal">16</span> 位</label>
            <input type="range" min="8" max="64" value="16" id="pwLen" oninput="document.getElementById('pwLenVal').textContent=this.value" style="width:100%;margin-bottom:10px">
            <div class="tool-row">
              <button class="tool-btn primary" onclick="genPassword()">生成密码</button>
              <button class="tool-btn" onclick="copyOutput('pwOutput')">复制</button>
            </div>
            <div class="tool-output" id="pwOutput">点击生成密码…</div>
          </div>
          <!-- 哈希 -->
          <div class="glass tool-card">
            <div class="tool-head"><div class="tool-icon">#️⃣</div><h4>哈希计算</h4></div>
            <label class="tool-label">输入文本</label>
            <input class="tool-input" id="hashInput" style="min-height:unset" placeholder="输入要计算哈希的文本…">
            <div class="tool-row">
              <select class="tool-select" id="hashAlgo"><option value="SHA-256">SHA-256</option><option value="SHA-1">SHA-1</option><option value="MD5">MD5</option></select>
              <button class="tool-btn primary" onclick="calcHash()">计算</button>
              <button class="tool-btn" onclick="copyOutput('hashOutput')">复制</button>
            </div>
            <div class="tool-output" id="hashOutput">结果显示在这里…</div>
          </div>
          <!-- 进制转换 -->
          <div class="glass tool-card">
            <div class="tool-head"><div class="tool-icon">🔢</div><h4>进制转换</h4></div>
            <label class="tool-label">输入十进制数</label>
            <input class="tool-input" id="decInput" style="min-height:unset" placeholder="例如 255" oninput="convertBase()">
            <div class="tool-output" id="baseOutput">二进制 / 八进制 / 十六进制 结果…</div>
          </div>
          <!-- 正则测试 -->
          <div class="glass tool-card">
            <div class="tool-head"><div class="tool-icon">.*</div><h4>正则测试</h4></div>
            <label class="tool-label">正则表达式</label>
            <input class="tool-input" id="rePattern" style="min-height:unset" placeholder="例如 \d+">
            <label class="tool-label" style="margin-top:8px">测试文本</label>
            <input class="tool-input" id="reText" style="min-height:unset" placeholder="输入要匹配的文本…" oninput="testRegex()">
            <div class="tool-output" id="reOutput">匹配结果…</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Connect -->
    <section class="pane" id="pane-connect">
      <div class="pane-inner">
        <div class="connect-grid">
          <div class="glass form-card">
            <div class="form-title">🔗 服务器连接</div>
            <div class="form-desc">选择连接方式并填写目标节点参数。SSH 隧道最稳妥。</div>
            <div class="field"><label>连接方式</label><select id="cfgMode" onchange="modeChanged()"><option value="tunnel">SSH 隧道（推荐）</option><option value="direct">直接连接</option><option value="proxy">内网代理</option></select></div>
            <div class="field-row"><div class="field"><label id="lblServer">服务器地址</label><input type="text" id="cfgIp" placeholder="例如 1.2.3.4"></div><div class="field" style="flex:0 0 100px"><label>端口</label><input type="number" id="cfgPort" value="8080"></div></div>
            <div id="sshFields" style="display:none">
              <div class="field-row"><div class="field"><label>SSH 用户名</label><input type="text" id="cfgSshUser" value="root"></div><div class="field" style="flex:0 0 100px"><label>SSH 端口</label><input type="number" id="cfgSshPort" value="22"></div></div>
              <div class="field"><label>SSH 私钥路径</label><input type="text" id="cfgSshKey" placeholder="留空则用 ~/.ssh/id_ed25519"></div>
            </div>
            <div class="field-row"><div class="field"><label>认证用户（可选）</label><input type="text" id="cfgAuthUser" placeholder="Agent 认证用户"></div><div class="field"><label>认证密码（可选）</label><input type="password" id="cfgAuthPass" placeholder="Agent 认证密码"></div></div>
            <div class="btn-row"><button class="btn btn-primary" onclick="saveConfig()">保存</button><button class="btn btn-ghost" onclick="testConn()">测试</button><button class="btn btn-ghost" onclick="connect()">连接</button><button class="btn btn-ghost" onclick="disconnect()">断开</button></div>
            <div class="hint" id="connResult" style="margin-top:10px"></div>
          </div>
          <div class="glass form-card">
            <div class="form-title">🧩 管理控制台</div>
            <div class="form-desc">本地管理控制台，多服务器控制、权限、部署、工单。</div>
            <div class="btn-row"><button class="btn btn-primary" onclick="startConsole()">启动控制台</button><button class="btn btn-ghost" onclick="stopConsole()">停止</button></div>
            <div class="hint" id="consoleResult" style="margin-top:10px"></div>
            <div style="margin-top:20px;padding-top:16px;border-top:1px solid var(--border)">
              <div class="form-title" style="font-size:13px">💡 新手提示</div>
              <div style="font-size:11.5px;color:var(--text-2);line-height:1.9;margin-top:8px">
                • 首次使用推荐 SSH 隧道，无需暴露公网端口<br>
                • 连接前先点"测试"确认网络通畅<br>
                • 控制台密码至少 12 位，含大小写+数字+特殊字符<br>
                • 遇到问题去"日志"页面排查错误<br>
                • 想练手去"模拟实战"做故障排查训练
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Logs -->
    <section class="pane" id="pane-logs">
      <div class="logs-wrap">
        <div class="glass logs-card">
          <div class="logs-head"><span>📋 运行日志</span><button class="btn btn-ghost" style="padding:5px 12px;font-size:11px" onclick="clearLogs()">清空</button></div>
          <div class="logs-body" id="logList"></div>
        </div>
      </div>
    </section>
  </div>
</div>

<div class="monitor-iframe-wrap" id="monitorWrap"><button class="monitor-close" onclick="closeMonitor()">✕</button><iframe id="monitorFrame" src="/monitor"></iframe></div>
<div class="toasts" id="toasts"></div>

<script>
/* ===== State ===== */
var STATE = null;
var activeCat = 'all';
var favOnly = false;
var favorites = JSON.parse(localStorage.getItem('shm_favs') || '[]');
var labResults = JSON.parse(localStorage.getItem('shm_lab_results') || '{}');
var currentLab = null;
var currentStep = 0;
var currentScore = 0;

/* ===== Command Library ===== */
var COMMANDS = {
  linux:{name:'Linux',icon:'🐧',color:'#4ade80',list:[
    {cmd:'top',desc:'实时查看 CPU、内存、进程负载。',syntax:'top [-d 秒数] [-p PID]',example:'top -d 2  每2秒刷新',level:'easy'},
    {cmd:'htop',desc:'top 增强版，彩色界面，支持鼠标和进程树。',syntax:'htop [-u 用户] [-p PID]',example:'htop -u root',level:'easy'},
    {cmd:'ps aux',desc:'查看所有进程，配合 grep 筛选。',syntax:'ps aux | grep 关键词',example:'ps aux | grep nginx',level:'easy'},
    {cmd:'df -h',desc:'查看磁盘分区使用情况。',syntax:'df -h [路径]',example:'df -h /',level:'easy'},
    {cmd:'free -h',desc:'查看内存和交换分区。',syntax:'free -h [-s 秒数]',example:'free -h -s 2',level:'easy'},
    {cmd:'systemctl status',desc:'查看服务运行状态和日志。',syntax:'systemctl status 服务名',example:'systemctl status nginx',level:'easy'},
    {cmd:'journalctl -xe',desc:'查看系统日志详情。',syntax:'journalctl -xe [-u 服务] [-f]',example:'journalctl -u nginx -f',level:'mid'},
    {cmd:'tail -f',desc:'实时跟踪文件末尾。',syntax:'tail -f 文件 [-n 行数]',example:'tail -f /var/log/syslog -n 100',level:'easy'},
    {cmd:'grep',desc:'在文件中搜索文本，支持正则。',syntax:'grep [选项] 关键词 文件',example:'grep -rn "error" /var/log/',level:'mid'},
    {cmd:'chmod',desc:'修改文件权限。',syntax:'chmod [选项] 权限 文件',example:'chmod 600 ~/.ssh/id_rsa',level:'mid'},
    {cmd:'chown',desc:'修改文件所有者。',syntax:'chown 用户:组 文件',example:'chown www-data:www-data /var/www',level:'mid'},
    {cmd:'ss -tulpn',desc:'查看监听端口和进程。',syntax:'ss -tulpn | grep 端口',example:'ss -tulpn | grep :8080',level:'mid'},
    {cmd:'kill / kill -9',desc:'终止进程。',syntax:'kill [-信号] PID',example:'kill -9 1234',level:'mid'},
    {cmd:'tar',desc:'打包/解压 tar.gz。',syntax:'tar [选项] 归档 [文件]',example:'tar -xzf file.tar.gz',level:'mid'},
    {cmd:'awk',desc:'按列处理文本。',syntax:"awk '模式{动作}' 文件",example:"awk '{print $1}' log",level:'hard'},
    {cmd:'sed',desc:'流编辑器，文本替换/删除。',syntax:'sed [选项] 命令 文件',example:"sed -i 's/old/new/g' f.txt",level:'hard'},
    {cmd:'crontab -e',desc:'编辑定时任务。',syntax:'crontab [-e|-l|-r]',example:'分 时 日 月 周 命令',level:'mid'},
    {cmd:'uptime',desc:'查看运行时间和负载。',syntax:'uptime',example:'显示 1/5/15 分钟负载',level:'easy'},
  ]},
  powershell:{name:'PowerShell',icon:'🔷',color:'#38d9f5',list:[
    {cmd:'Get-Process',desc:'获取进程列表。',syntax:'Get-Process [-Name 名称]',example:'Get-Process node',level:'easy'},
    {cmd:'Get-Service',desc:'查看 Windows 服务。',syntax:'Get-Service [-Status 状态]',example:'Get-Service | ? Status -eq Running',level:'easy'},
    {cmd:'Start/Stop-Service',desc:'启动/停止服务。',syntax:'Start-Service 名; Stop-Service 名',example:'Stop-Service wuauserv',level:'easy'},
    {cmd:'Get-ChildItem',desc:'列出目录内容（dir/ls别名）。',syntax:'Get-ChildItem [-Recurse]',example:'Get-ChildItem -Recurse *.log',level:'easy'},
    {cmd:'Select-String',desc:'搜索文本（类似grep）。',syntax:'Select-String -Path f -Pattern k',example:'Select-String *.log "error"',level:'easy'},
    {cmd:'Get-Content',desc:'读取文件，-Wait实时跟踪。',syntax:'Get-Content f [-Tail N] [-Wait]',example:'Get-Content app.log -Tail 50 -Wait',level:'easy'},
    {cmd:'Test-NetConnection',desc:'测试网络和端口。',syntax:'Test-NetConnection -ComputerName h -Port p',example:'Test-NetConnection 1.2.3.4 -Port 8080',level:'easy'},
    {cmd:'Invoke-WebRequest',desc:'发送 HTTP 请求。',syntax:'Invoke-WebRequest -Uri URL',example:'Invoke-WebRequest https://api.example.com',level:'mid'},
    {cmd:'Get-NetTCPConnection',desc:'查看 TCP 连接。',syntax:'Get-NetTCPConnection [-State s]',example:'Get-NetTCPConnection -State Listen',level:'mid'},
    {cmd:'Set-ExecutionPolicy',desc:'修改脚本执行策略。',syntax:'Set-ExecutionPolicy 策略',example:'Set-ExecutionPolicy RemoteSigned',level:'mid'},
    {cmd:'Compress-Archive',desc:'压缩为 ZIP。',syntax:'Compress-Archive -Path s -Dest d.zip',example:'Compress-Archive ./src backup.zip',level:'easy'},
  ]},
  cmd:{name:'CMD',icon:'⬛',color:'#fbbf24',list:[
    {cmd:'ipconfig',desc:'查看网络配置。',syntax:'ipconfig [/all] [/flushdns]',example:'ipconfig /all',level:'easy'},
    {cmd:'ping',desc:'测试连通性。',syntax:'ping [-t] [-n 次数] 主机',example:'ping -t 8.8.8.8',level:'easy'},
    {cmd:'tracert',desc:'追踪路由路径。',syntax:'tracert [-d] 主机',example:'tracert 1.1.1.1',level:'easy'},
    {cmd:'netstat',desc:'查看网络连接和端口。',syntax:'netstat [-ano]',example:'netstat -ano | findstr :8080',level:'mid'},
    {cmd:'tasklist',desc:'列出进程。',syntax:'tasklist [/fi 过滤器]',example:'tasklist /fi "imagename eq node.exe"',level:'easy'},
    {cmd:'taskkill',desc:'终止进程。',syntax:'taskkill /F /PID id 或 /IM 名',example:'taskkill /F /IM node.exe',level:'mid'},
    {cmd:'sfc /scannow',desc:'扫描修复系统文件。',syntax:'sfc /scannow',example:'需管理员权限',level:'mid'},
    {cmd:'chkdsk',desc:'检查磁盘错误。',syntax:'chkdsk [盘:] [/f] [/r]',example:'chkdsk C: /f',level:'mid'},
    {cmd:'dir',desc:'列出目录。',syntax:'dir [路径] [/s]',example:'dir /s *.log',level:'easy'},
    {cmd:'findstr',desc:'搜索文本。',syntax:'findstr [/i] [/s] 词 文件',example:'dir /s | findstr /i ".log"',level:'easy'},
    {cmd:'systeminfo',desc:'显示系统信息。',syntax:'systeminfo',example:'systeminfo | findstr /i "os name"',level:'easy'},
    {cmd:'shutdown',desc:'关机/重启。',syntax:'shutdown [/s|/r|/a] [/t 秒]',example:'shutdown /r /t 0; /a 取消',level:'easy'},
  ]},
  network:{name:'网络诊断',icon:'🌐',color:'#a78bfa',list:[
    {cmd:'curl',desc:'发送 HTTP 请求。',syntax:'curl [选项] URL',example:'curl -I https://example.com',level:'mid'},
    {cmd:'wget',desc:'下载文件。',syntax:'wget [选项] URL',example:'wget -c URL 断点续传',level:'easy'},
    {cmd:'nslookup',desc:'查询 DNS。',syntax:'nslookup 域名 [DNS]',example:'nslookup example.com 8.8.8.8',level:'easy'},
    {cmd:'dig',desc:'详细 DNS 查询。',syntax:'dig [@DNS] 域名 [类型]',example:'dig example.com MX',level:'mid'},
    {cmd:'mtr',desc:'网络质量诊断。',syntax:'mtr [选项] 主机',example:'mtr --report 1.1.1.1',level:'mid'},
    {cmd:'nc',desc:'网络瑞士军刀。',syntax:'nc [选项] 主机 端口',example:'nc -zv 1.2.3.4 8080',level:'hard'},
    {cmd:'tcpdump',desc:'抓包分析。',syntax:'tcpdump [选项] [表达式]',example:'tcpdump -i any port 80 -c 100',level:'hard'},
    {cmd:'iptables',desc:'Linux 防火墙。',syntax:'iptables [-t 表] [-A] 链 规则',example:'iptables -A INPUT -p tcp --dport 8080 -j DROP',level:'hard'},
    {cmd:'nmap',desc:'端口扫描。',syntax:'nmap [选项] 目标',example:'nmap -sV -p 1-1000 1.2.3.4',level:'hard'},
  ]},
  security:{name:'安全权限',icon:'🔒',color:'#f87171',list:[
    {cmd:'sudo',desc:'管理员权限执行。',syntax:'sudo 命令',example:'sudo systemctl restart nginx',level:'easy'},
    {cmd:'ssh-keygen',desc:'生成 SSH 密钥。',syntax:'ssh-keygen [-t 类型] [-b 位]',example:'ssh-keygen -t ed25519 -C "email"',level:'easy'},
    {cmd:'ssh-copy-id',desc:'复制公钥到远程。',syntax:'ssh-copy-id 用户@主机',example:'ssh-copy-id root@1.2.3.4',level:'easy'},
    {cmd:'last / lastb',desc:'登录历史。',syntax:'last [-n 条数]',example:'last -n 20',level:'mid'},
    {cmd:'who / w',desc:'当前登录用户。',syntax:'who; w',example:'w 显示用户在做什么',level:'easy'},
    {cmd:'openssl',desc:'加密工具集。',syntax:'openssl 子命令 [选项]',example:'openssl req -x509 -newkey rsa:2048 ...',level:'hard'},
    {cmd:'fail2ban-client',desc:'防暴力破解。',syntax:'fail2ban-client status [监狱]',example:'fail2ban-client status sshd',level:'mid'},
  ]},
  docker:{name:'Docker',icon:'🐳',color:'#22d3ee',list:[
    {cmd:'docker ps',desc:'查看运行中容器。',syntax:'docker ps [-a] [-q]',example:'docker ps -a',level:'easy'},
    {cmd:'docker logs',desc:'查看容器日志。',syntax:'docker logs [选项] 容器',example:'docker logs -f --tail 100 myapp',level:'easy'},
    {cmd:'docker exec',desc:'在容器内执行命令。',syntax:'docker exec [选项] 容器 命令',example:'docker exec -it myapp bash',level:'easy'},
    {cmd:'docker compose up',desc:'启动服务栈。',syntax:'docker compose up [-d] [--build]',example:'docker compose up -d --build',level:'easy'},
    {cmd:'docker compose down',desc:'停止并删除。',syntax:'docker compose down [-v]',example:'docker compose down -v',level:'easy'},
    {cmd:'docker build',desc:'构建镜像。',syntax:'docker build -t 名:标签 路径',example:'docker build -t myapp:latest .',level:'mid'},
    {cmd:'docker pull/push',desc:'拉取/推送镜像。',syntax:'docker pull 镜像; docker push 镜像',example:'docker pull nginx:alpine',level:'easy'},
    {cmd:'docker stop/rm',desc:'停止/删除容器。',syntax:'docker stop 容器; docker rm 容器',example:'docker stop myapp && docker rm myapp',level:'easy'},
    {cmd:'docker system prune',desc:'清理未使用资源。',syntax:'docker system prune [-a] [--volumes]',example:'docker system prune -a --volumes',level:'mid'},
    {cmd:'docker stats',desc:'实时资源监控。',syntax:'docker stats [容器]',example:'docker stats',level:'easy'},
  ]},
  git:{name:'Git',icon:'📦',color:'#fbbf24',list:[
    {cmd:'git clone',desc:'克隆仓库。',syntax:'git clone URL [目录]',example:'git clone https://gitee.com/u/r.git',level:'easy'},
    {cmd:'git status',desc:'查看状态。',syntax:'git status',example:'查看修改/新增文件',level:'easy'},
    {cmd:'git add',desc:'添加到暂存区。',syntax:'git add <文件|.>',example:'git add .',level:'easy'},
    {cmd:'git commit',desc:'提交。',syntax:'git commit -m "信息"',example:'git commit -m "feat:新增面板"',level:'easy'},
    {cmd:'git push',desc:'推送到远程。',syntax:'git push [远程] [分支] [-u]',example:'git push -u origin main',level:'easy'},
    {cmd:'git pull',desc:'拉取更新。',syntax:'git pull [远程] [分支]',example:'git pull origin main',level:'easy'},
    {cmd:'git branch',desc:'分支管理。',syntax:'git branch [-a] [-d 分支]',example:'git branch feature/new',level:'mid'},
    {cmd:'git switch',desc:'切换分支。',syntax:'git switch 分支',example:'git switch -c feature/new',level:'easy'},
    {cmd:'git merge',desc:'合并分支。',syntax:'git merge 分支',example:'git merge feature/new',level:'mid'},
    {cmd:'git log',desc:'提交历史。',syntax:'git log [--oneline] [--graph]',example:'git log --oneline --graph -10',level:'easy'},
    {cmd:'git diff',desc:'查看改动。',syntax:'git diff [文件] [--staged]',example:'git diff',level:'mid'},
    {cmd:'git stash',desc:'临时保存改动。',syntax:'git stash [push|pop|list]',example:'git stash push -m "wip"',level:'mid'},
    {cmd:'git reset',desc:'撤销提交。',syntax:'git reset [--soft|--hard] [提交]',example:'git reset --hard HEAD~1 (危险)',level:'hard'},
  ]},
  database:{name:'数据库',icon:'🗄️',color:'#4ade80',list:[
    {cmd:'mysql -u -p',desc:'连接 MySQL。',syntax:'mysql -u 用户 -p [库]',example:'mysql -u root -p mydb',level:'easy'},
    {cmd:'SHOW DATABASES;',desc:'列出数据库。',syntax:'SHOW DATABASES;',example:'在客户端执行',level:'easy'},
    {cmd:'SHOW TABLES;',desc:'列出表。',syntax:'SHOW TABLES;',example:'先 USE 库名;',level:'easy'},
    {cmd:'SELECT',desc:'查询数据。',syntax:'SELECT 列 FROM 表 [WHERE] [LIMIT]',example:'SELECT * FROM users LIMIT 10;',level:'easy'},
    {cmd:'mysqldump',desc:'导出备份。',syntax:'mysqldump -u u -p 库 > 文件.sql',example:'mysqldump -u root -p mydb > bk.sql',level:'mid'},
    {cmd:'redis-cli',desc:'连接 Redis。',syntax:'redis-cli [-h 主机] [-p 端口]',example:'redis-cli -h 127.0.0.1 -p 6379',level:'easy'},
    {cmd:'redis-cli INFO',desc:'Redis 信息统计。',syntax:'redis-cli INFO [section]',example:'redis-cli INFO memory',level:'mid'},
  ]},
  monitor:{name:'监控运维',icon:'📊',color:'#6c8cff',list:[
    {cmd:'systemctl start/stop/restart',desc:'管理服务。',syntax:'systemctl 动作 服务',example:'systemctl restart nginx',level:'easy'},
    {cmd:'systemctl enable/disable',desc:'开机自启。',syntax:'systemctl enable 服务',example:'systemctl enable nginx',level:'easy'},
    {cmd:'vmstat',desc:'虚拟内存统计。',syntax:'vmstat [延迟] [次数]',example:'vmstat 1 5',level:'mid'},
    {cmd:'iostat',desc:'磁盘 I/O 统计。',syntax:'iostat [-x] [延迟]',example:'iostat -xz 1',level:'mid'},
    {cmd:'sar',desc:'系统活动报告。',syntax:'sar [-u] [-r] [延迟]',example:'sar -u 1 5; sar -r',level:'hard'},
    {cmd:'dmesg',desc:'内核日志。',syntax:'dmesg [-T] | tail',example:'dmesg -T | tail -30',level:'mid'},
    {cmd:'lsof',desc:'打开的文件/连接。',syntax:'lsof [-i 端口] [-p PID]',example:'lsof -i :8080',level:'mid'},
    {cmd:'strace',desc:'跟踪系统调用。',syntax:'strace [-p PID] 命令',example:'strace -p 1234',level:'hard'},
  ]},
  text:{name:'文本处理',icon:'📝',color:'#a78bfa',list:[
    {cmd:'cat',desc:'查看文件内容。',syntax:'cat [选项] 文件',example:'cat -n file.txt',level:'easy'},
    {cmd:'less',desc:'分页查看大文件。',syntax:'less 文件',example:'按q退出, /搜索',level:'easy'},
    {cmd:'head / tail',desc:'查看开头/末尾。',syntax:'head -n N 文件; tail -n N 文件',example:'tail -f file.log',level:'easy'},
    {cmd:'wc',desc:'统计行/词/字符。',syntax:'wc [-l] [-w] [-c] 文件',example:'wc -l file.txt',level:'easy'},
    {cmd:'sort',desc:'排序。',syntax:'sort [选项] 文件',example:'sort -n -r nums.txt',level:'easy'},
    {cmd:'uniq',desc:'去重（需先sort）。',syntax:'uniq [选项] 文件',example:'sort f | uniq -c',level:'mid'},
    {cmd:'cut',desc:'按分隔符提取列。',syntax:'cut -d 分隔 -f 列 文件',example:"cut -d: -f1 /etc/passwd",level:'mid'},
    {cmd:'tr',desc:'字符转换。',syntax:'tr [选项] 源 目标',example:'cat f | tr a-z A-Z',level:'mid'},
    {cmd:'xargs',desc:'参数传递。',syntax:'命令 | xargs 命令',example:'cat urls.txt | xargs wget',level:'hard'},
    {cmd:'jq',desc:'JSON 处理。',syntax:"jq [选项] '过滤器' 文件",example:"cat d.json | jq '.users[].name'",level:'hard'},
  ]},
  disk:{name:'磁盘文件',icon:'💾',color:'#fbbf24',list:[
    {cmd:'lsblk',desc:'列出块设备。',syntax:'lsblk [-f]',example:'lsblk -f 显示文件系统',level:'easy'},
    {cmd:'mount / umount',desc:'挂载/卸载。',syntax:'mount 设备 点; umount 点',example:'mount /dev/sdb1 /mnt/data',level:'mid'},
    {cmd:'du -sh',desc:'查看目录大小。',syntax:'du -sh [路径]',example:'du -sh /var/log/*',level:'easy'},
    {cmd:'ln -s',desc:'创建软链接。',syntax:'ln -s 源 链接',example:'ln -s /opt/app /var/www/app',level:'mid'},
    {cmd:'find',desc:'查找文件。',syntax:'find 路径 [选项]',example:'find / -name "*.log" -size +100M',level:'mid'},
    {cmd:'rsync',desc:'高效同步备份。',syntax:'rsync [选项] 源 目标',example:'rsync -avz --delete ./src/ host:/backup/',level:'hard'},
  ]}
};

/* ===== Scenarios (模拟实战) ===== */
var SCENARIOS = [
  {id:'cpu_high',title:'CPU 飙高排查',icon:'🔥',difficulty:'入门',color:'#f87171',desc:'服务器 CPU 突然飙升到 95%，业务响应变慢，你该怎么办？',steps:[
    {q:'监控告警显示 CPU 使用率 95%，第一步应该做什么？',opts:[
      {t:'直接重启服务器',c:false,e:'重启会丢失现场，无法定位根因。运维第一原则：先保留现场，再排查。'},
      {t:'用 top/htop 查看哪个进程占 CPU',c:true,e:'正确！先定位高负载进程，观察 PID、用户、CPU%、内存%，再决定下一步。'},
      {t:'立即拔网线断网',c:false,e:'断网影响业务，且不能解决 CPU 问题。'},
      {t:'关机等待冷却',c:false,e:'关机不能解决问题，还会导致业务中断。'}
    ]},
    {q:'top 看到一个未知进程占 90% CPU，下一步？',opts:[
      {t:'直接 kill -9 杀掉',c:false,e:'太鲁莽！可能是重要业务进程，先确认是什么。'},
      {t:'用 ps -fp PID 查看进程详情，确认是什么程序',c:true,e:'正确！查看进程路径、启动用户、启动参数，判断是业务进程还是异常进程。'},
      {t:'不管它，等它自己降下来',c:false,e:'CPU 95% 会影响业务，不能被动等待。'},
      {t:'重启整个服务器',c:false,e:'还是没定位根因，重启后可能复现。'}
    ]},
    {q:'确认是陌生的挖矿进程，下一步？',opts:[
      {t:'kill 掉就完事了',c:false,e:'只杀进程不清除来源，会再次启动。需要排查定时任务、启动脚本、SSH 密钥。'},
      {t:'kill 进程 → 查定时任务和启动项 → 清除后门 → 修复漏洞',c:true,e:'正确！完整流程：终止进程→清除持久化（crontab/systemd）→排查入侵入口→修补漏洞。'},
      {t:'格式化重装系统',c:false,e:'太极端，先尝试清除和修复，同时做好数据备份。'},
      {t:'断网后不管了',c:false,e:'断网只是隔离，不清除后门，一联网就复发。'}
    ]},
    {q:'排查发现是 Redis 未设密码被入侵，最终修复方案？',opts:[
      {t:'给 Redis 设密码 + 绑定 127.0.0.1 + 升级版本',c:true,e:'正确！Redis 未授权访问是常见入侵入口。设密码、绑内网、禁用危险命令、升级到最新版。'},
      {t:'把 Redis 端口改成别的就行',c:false,e:'改端口只是隐蔽，不是安全，扫描器依然能找到。'},
      {t:'卸载 Redis',c:false,e:'业务可能依赖 Redis，应该加固而不是卸载。'},
      {t:'加防火墙只允许自己 IP',c:false,e:'这只是临时措施，根本问题是 Redis 未认证。'}
    ]}
  ]},
  {id:'site_down',title:'网站无法访问',icon:'🌐',difficulty:'入门',color:'#38d9f5',desc:'用户反馈网站打不开，502 错误，如何一步步排查？',steps:[
    {q:'网站返回 502 Bad Gateway，首先排查什么？',opts:[
      {t:'直接重启服务器',c:false,e:'502 通常是反向代理连不上后端，先确认后端服务状态。'},
      {t:'检查 Nginx/Apache 反向代理和后端服务状态',c:true,e:'正确！502 = 网关收到无效响应。先看 Nginx 状态，再看后端服务（如 Node/Java/Python）是否在运行。'},
      {t:'检查域名是否过期',c:false,e:'域名过期通常是 DNS 解析失败，不是 502。'},
      {t:'换个浏览器试试',c:false,e:'502 是服务端错误，和浏览器无关。'}
    ]},
    {q:'systemctl status 发现后端服务已停止，下一步？',opts:[
      {t:'启动服务，能跑就行',c:false,e:'只启动不查原因，可能再次崩溃。先看日志找崩溃原因。'},
      {t:'先看 journalctl 日志找崩溃原因，修复后再启动',c:true,e:'正确！查看服务日志（journalctl -u 服务名），找到 OOM/配置错误/依赖缺失等根因，修复后启动。'},
      {t:'删除服务重装',c:false,e:'太激进，先看日志定位问题。'},
      {t:'换台服务器部署',c:false,e:'没解决根本问题，换环境可能依然崩溃。'}
    ]},
    {q:'日志显示后端 OOM（内存溢出）被 kill，怎么处理？',opts:[
      {t:'加内存就完事了',c:false,e:'加内存是治标，可能存在内存泄漏，需要排查代码。'},
      {t:'限制服务内存上限 + 排查内存泄漏 + 必要时加内存',c:true,e:'正确！用 systemd MemoryMax 限制上限防止拖垮系统，排查代码内存泄漏，同时评估是否需要扩容。'},
      {t:'设置定时重启服务',c:false,e:'定时重启是临时规避，不是修复，会导致业务中断。'},
      {t:'关闭其他服务腾内存',c:false,e:'只是临时缓解，根因是内存泄漏或配置不当。'}
    ]}
  ]},
  {id:'disk_full',title:'磁盘空间爆满',icon:'💾',difficulty:'入门',color:'#fbbf24',desc:'磁盘告警 98%，服务随时可能崩溃，如何快速清理？',steps:[
    {q:'磁盘使用率 98%，第一步做什么？',opts:[
      {t:'直接删 /var/log 下所有文件',c:false,e:'盲目删日志可能丢失重要排障信息，先看哪个目录占空间。'},
      {t:'用 du -sh /* 或 du -sh /var/* 定位大目录',c:true,e:'正确！先定位空间占用：du -sh /* 看根目录，再逐层深入，找到真正的大户。'},
      {t:'重启服务器释放空间',c:false,e:'重启不会释放磁盘空间，临时文件可能还在。'},
      {t:'格式化数据盘',c:false,e:'极端操作，会丢失数据，绝对不能第一步就做。'}
    ]},
    {q:'发现 /var/log 占了 80G，大部分是 nginx 日志，怎么清理？',opts:[
      {t:'rm -rf /var/log/* 全部删除',c:false,e:'太粗暴！可能删除系统日志和其他服务日志。只清理目标日志。'},
      {t:'用 truncate 或 echo 清空大日志文件，配置 logrotate 轮转',c:true,e:'正确！echo "" > 大文件 清空（不删除文件，不影响进程写入），然后配置 logrotate 自动轮转压缩。'},
      {t:'停止 nginx 再删日志',c:false,e:'不需要停服务，truncate 可以在服务运行时安全清空。'},
      {t:'把日志目录移到别的盘',c:false,e:'可以作为长期方案，但紧急情况先清空。'}
    ]},
    {q:'清理后空间只释放了 10G，还有 70G 找不到，可能原因？',opts:[
      {t:'有已删除但被进程占用的文件（deleted but open）',c:true,e:'正确！用 lsof | grep deleted 查找已删除但被进程持有的文件，重启对应进程或服务才能真正释放空间。'},
      {t:'磁盘坏道',c:false,e:'坏道不会占用空间，且会有 IO 错误。'},
      {t:'文件系统损坏',c:false,e:'文件系统损坏会报错，不是隐藏占用。'},
      {t:'计算错误',c:false,e:'du 和 df 差异通常就是 deleted but open 文件导致的。'}
    ]}
  ]},
  {id:'ssh_fail',title:'SSH 登录失败',icon:'🔑',difficulty:'进阶',color:'#a78bfa',desc:'SSH 连接被拒绝，无法远程登录服务器，如何排查？',steps:[
    {q:'SSH 连接提示 Connection refused，首先确认什么？',opts:[
      {t:'服务器是否宕机',c:false,e:'Connection refused 说明网络通但端口没监听，不是宕机（宕机是 timeout）。'},
      {t:'sshd 服务是否运行、22端口是否监听',c:true,e:'正确！refused = 网络可达但端口关闭。用 systemctl status sshd 和 ss -tulpn | grep :22 确认。'},
      {t:'密码是否正确',c:false,e:'密码错误是 Permission denied，不是 refused。'},
      {t:'DNS 是否解析',c:false,e:'DNS 问题是无法解析，不是 refused。'}
    ]},
    {q:'sshd 运行正常但还是连不上，可能原因？',opts:[
      {t:'防火墙拦截了 22 端口',c:true,e:'正确！检查 iptables/ufw/安全组是否放行 22 端口。云服务器还要看云平台安全组规则。'},
      {t:'服务器内存不足',c:false,e:'内存不足不会导致 connection refused。'},
      {t:'SSH 客户端版本太旧',c:false,e:'客户端旧会报协议错误，不是 refused。'},
      {t:'服务器时区不对',c:false,e:'时区不影响 SSH 连接。'}
    ]},
    {q:'能连上但提示 Permission denied (publickey)，如何处理？',opts:[
      {t:'重置服务器密码',c:false,e:'这是密钥认证失败，不是密码问题。'},
      {t:'检查本地私钥权限(~600)、服务器 authorized_keys、sshd 配置',c:true,e:'正确！依次检查：本地私钥权限必须600、服务器 ~/.ssh/authorized_keys 存在且权限正确、sshd_config 是否允许密钥认证。'},
      {t:'删除 ~/.ssh 重新生成',c:false,e:'可能丢失已配置的密钥，先排查再操作。'},
      {t:'换个网络试试',c:false,e:'网络不影响认证失败。'}
    ]}
  ]},
  {id:'mem_leak',title:'内存泄漏排查',icon:'📈',difficulty:'进阶',color:'#6c8cff',desc:'服务内存持续增长不释放，几天后 OOM，如何定位泄漏点？',steps:[
    {q:'内存持续增长，第一步用什么工具观察？',opts:[
      {t:'直接重启服务',c:false,e:'重启只是临时缓解，泄漏点还在。先观察趋势和进程。'},
      {t:'用 top/htop 观察哪个进程内存增长，记录 RES 列',c:true,e:'正确！top 按 M 排序看内存，关注 RES（实际物理内存）。持续增长的进程就是嫌疑对象。'},
      {t:'加内存条',c:false,e:'加内存只是延缓 OOM，泄漏依然存在。'},
      {t:'关闭 swap',c:false,e:'swap 和内存泄漏无关。'}
    ]},
    {q:'确认是 Java 服务内存增长，用什么工具分析？',opts:[
      {t:'用 jmap 导出堆快照，MAT 分析对象占用',c:true,e:'正确！jmap -dump:format=b,file=heap.hprof PID 导出堆，用 Eclipse MAT 或 JProfiler 分析大对象和泄漏点。'},
      {t:'用 top 看就行',c:false,e:'top 只能看到总量，无法定位代码中的泄漏对象。'},
      {t:'重启后观察',c:false,e:'重启后泄漏会复现，但无法定位具体代码。'},
      {t:'修改 JVM 堆大小',c:false,e:'调整堆大小只是参数调优，不是排查泄漏。'}
    ]},
    {q:'分析发现是缓存无上限增长，修复方案？',opts:[
      {t:'给缓存加过期时间和最大容量（LRU 淘汰）',c:true,e:'正确！缓存必须设 TTL 和 max-size，用 LRU/LFU 策略淘汰，否则内存必然耗尽。Guava Cache/Caffeine 都支持。'},
      {t:'定时清空缓存',c:false,e:'定时清空会导致缓存击穿，且清空瞬间可能有性能抖动。'},
      {t:'不用缓存了',c:false,e:'缓存是性能优化手段，应该合理配置而不是放弃。'},
      {t:'加更多内存',c:false,e:'无上限缓存加多少内存都会满。'}
    ]}
  ]},
  {id:'db_timeout',title:'数据库连接超时',icon:'🗄️',difficulty:'高级',color:'#4ade80',desc:'业务报数据库连接超时，查询缓慢，如何系统排查？',steps:[
    {q:'数据库连接超时，首先检查什么？',opts:[
      {t:'数据库服务是否存活、端口是否通',c:true,e:'正确！先确认基础连通性：systemctl status mysql、telnet/nc 测试端口、查看错误日志。'},
      {t:'直接重启数据库',c:false,e:'重启会中断业务，且可能丢失排查现场。先确认状态。'},
      {t:'优化 SQL 语句',c:false,e:'SQL 优化是后续步骤，先确认服务是否正常。'},
      {t:'升级数据库配置',c:false,e:'没定位问题前升级配置是盲目操作。'}
    ]},
    {q:'数据库存活但连接数满了（Too many connections），怎么处理？',opts:[
      {t:'kill 所有连接',c:false,e:'kill 所有连接会中断业务，先看哪些是慢查询/空闲连接。'},
      {t:'查看 processlist 找长事务/慢查询，kill 异常连接，临时调大 max_connections',c:true,e:'正确！SHOW PROCESSLIST 找 Sleep 很久的连接和慢查询，kill 异常的，临时调大 max_connections 应急，长期优化连接池和 SQL。'},
      {t:'重启数据库释放连接',c:false,e:'重启是最后手段，先尝试 kill 异常连接。'},
      {t:'不管它，等连接自动释放',c:false,e:'连接满了新连接进不来，业务持续报错。'}
    ]},
    {q:'慢查询导致连接堆积，长期优化方案？',opts:[
      {t:'加索引 + 优化 SQL + 配置慢查询日志 + 连接池合理设置',c:true,e:'正确！系统方案：开启 slow_query_log 定位慢SQL、EXPLAIN 分析加索引、优化业务SQL、连接池设置合理的最大连接数和超时。'},
      {t:'只加索引就行',c:false,e:'加索引是一部分，还需要 SQL 优化和连接池配置。'},
      {t:'定时重启数据库',c:false,e:'定时重启会导致业务中断，不是解决方案。'},
      {t:'换更大的服务器',c:false,e:'硬件升级不能替代 SQL 和架构优化。'}
    ]}
  ]}
];

/* ===== Navigation ===== */
var paneTitles = {monitor:'监控面板',console:'管理控制台',lexicon:'命令词典',lab:'模拟实战',tools:'运维工具箱',connect:'连接设置',logs:'运行日志'};
function switchPane(name){
  document.querySelectorAll('.nav-tab').forEach(function(t){ t.classList.toggle('active', t.dataset.pane === name); });
  document.querySelectorAll('.pane').forEach(function(p){ p.classList.toggle('active', p.id === 'pane-'+name); });
  // Scroll active tab into view
  var activeTab=document.querySelector('.nav-tab.active');
  if(activeTab){ activeTab.scrollIntoView({behavior:'smooth',block:'nearest',inline:'center'}); }
  if(name==='console') refreshConsole();
  if(name==='lexicon'){ document.getElementById('lexSearch').focus(); renderLexicon(); }
  if(name==='lab'){ renderLabList(); }
  if(name==='tools'){ initTools(); }
}
document.querySelectorAll('.nav-tab').forEach(function(t){ t.addEventListener('click', function(){ switchPane(t.dataset.pane); }); });

/* ===== Nav Scroll ===== */
function scrollNav(dir){
  var tabs=document.getElementById('navTabs');
  var amount=tabs.clientWidth*0.6;
  tabs.scrollBy({left:dir*amount,behavior:'smooth'});
}
function updateNavArrows(){
  var tabs=document.getElementById('navTabs');
  var left=document.getElementById('navArrowLeft');
  var right=document.getElementById('navArrowRight');
  var fadeL=document.getElementById('navFadeLeft');
  var fadeR=document.getElementById('navFadeRight');
  var canScroll=tabs.scrollWidth>tabs.clientWidth+2;
  var atLeft=tabs.scrollLeft<=2;
  var atRight=tabs.scrollLeft+tabs.clientWidth>=tabs.scrollWidth-2;
  left.classList.toggle('show',canScroll&&!atLeft);
  right.classList.toggle('show',canScroll&&!atRight);
  fadeL.classList.toggle('show',canScroll&&!atLeft);
  fadeR.classList.toggle('show',canScroll&&!atRight);
}
document.getElementById('navTabs').addEventListener('scroll',updateNavArrows);
window.addEventListener('resize',updateNavArrows);
setTimeout(updateNavArrows,200);

/* ===== Mouse Follow ===== */
document.addEventListener('pointermove', function(e){
  document.documentElement.style.setProperty('--mx', (e.clientX/window.innerWidth*100)+'%');
  document.documentElement.style.setProperty('--my', (e.clientY/window.innerHeight*100)+'%');
});

/* ===== Splash ===== */
function hideSplash(){ document.getElementById('splash').classList.add('gone'); document.getElementById('app').classList.add('ready'); setTimeout(function(){ document.getElementById('splash').style.display='none'; },700); }
setTimeout(hideSplash, 1100);

/* ===== Toast ===== */
function toast(msg,type){
  type=type||'info';
  var t=document.createElement('div'); t.className='toast '+type; t.textContent=msg;
  document.getElementById('toasts').appendChild(t);
  setTimeout(function(){ t.style.animation='toastOut 0.3s forwards'; setTimeout(function(){ t.remove(); },300); },2500);
}

/* ===== Lexicon ===== */
function renderCats(){
  var c=document.getElementById('lexCats');
  var all={all:{name:'全部',icon:'📋'}};
  var cats=Object.assign({},all,COMMANDS);
  c.innerHTML='';
  Object.keys(cats).forEach(function(key){
    var cat=cats[key];
    var count=key==='all'?Object.values(COMMANDS).reduce(function(s,c){return s+c.list.length;},0):cat.list.length;
    var btn=document.createElement('button');
    btn.className='lex-cat'+(activeCat===key?' active':'');
    btn.innerHTML='<span>'+cat.icon+'</span> '+cat.name+' <span class="count">'+count+'</span>';
    btn.onclick=function(){ activeCat=key; renderCats(); renderLexicon(); };
    c.appendChild(btn);
  });
}
function renderLexicon(){
  var grid=document.getElementById('lexGrid');
  var q=document.getElementById('lexSearch').value.toLowerCase().trim();
  var items=[];
  Object.keys(COMMANDS).forEach(function(key){
    if(activeCat!=='all'&&activeCat!==key) return;
    COMMANDS[key].list.forEach(function(cmd){
      if(favOnly&&favorites.indexOf(cmd.cmd)===-1) return;
      if(q&&cmd.cmd.toLowerCase().indexOf(q)===-1&&cmd.desc.toLowerCase().indexOf(q)===-1&&cmd.syntax.toLowerCase().indexOf(q)===-1) return;
      items.push(cmd);
    });
  });
  if(items.length===0){ grid.innerHTML='<div class="lex-empty"><div class="icon">🔍</div><h3>没有找到匹配的命令</h3><p>试试其他关键词</p></div>'; return; }
  grid.innerHTML='';
  items.forEach(function(cmd,i){
    var isFav=favorites.indexOf(cmd.cmd)!==-1;
    var lc=cmd.level==='easy'?'level-easy':cmd.level==='mid'?'level-mid':'level-hard';
    var lt=cmd.level==='easy'?'入门':cmd.level==='mid'?'进阶':'高级';
    var card=document.createElement('div');
    card.className='glass cmd-card'; card.style.animationDelay=(i*0.03)+'s';
    card.innerHTML='<div class="cmd-head"><div class="cmd-name">'+cmd.cmd+'</div><button class="cmd-fav'+(isFav?' active':'')+'" onclick="toggleFav(\''+cmd.cmd.replace(/'/g,"\\'")+'\',this)">'+(isFav?'⭐':'☆')+'</button></div><div class="cmd-desc">'+cmd.desc+'</div><div class="cmd-syntax">'+cmd.syntax+'</div><div class="cmd-example"><strong>示例：</strong>'+cmd.example+'</div><div class="cmd-foot"><span class="cmd-level '+lc+'">'+lt+'</span><button class="cmd-copy" onclick="copyCmd(this,\''+cmd.cmd.replace(/'/g,"\\'")+'\')">📋 复制</button></div>';
    grid.appendChild(card);
  });
}
function toggleFav(cmd,btn){
  var idx=favorites.indexOf(cmd);
  if(idx===-1){ favorites.push(cmd); btn.classList.add('active'); btn.textContent='⭐'; toast('已收藏 '+cmd,'success'); }
  else{ favorites.splice(idx,1); btn.classList.remove('active'); btn.textContent='☆'; toast('已取消收藏','info'); }
  localStorage.setItem('shm_favs',JSON.stringify(favorites));
  if(favOnly) renderLexicon();
}
function toggleFavFilter(){ favOnly=!favOnly; document.getElementById('favToggle').classList.toggle('active',favOnly); renderLexicon(); }
function copyCmd(btn,cmd){
  navigator.clipboard.writeText(cmd).then(function(){ btn.classList.add('copied'); btn.textContent='✓ 已复制'; setTimeout(function(){ btn.classList.remove('copied'); btn.textContent='📋 复制'; },1500); }).catch(function(){ toast('复制失败','error'); });
}

/* ===== Lab ===== */
function renderLabList(){
  updateLabStats();
  var grid=document.getElementById('labGrid');
  grid.innerHTML='';
  SCENARIOS.forEach(function(s){
    var done=labResults[s.id];
    var dc=s.difficulty==='入门'?'level-easy':s.difficulty==='进阶'?'level-mid':'level-hard';
    var card=document.createElement('div');
    card.className='glass scenario-card';
    card.innerHTML=(done?'<div class="scenario-done">✅</div>':'')+
      '<div class="scenario-icon" style="background:'+s.color+'15;border-color:'+s.color+'30">'+s.icon+'</div>'+
      '<h4>'+s.title+'</h4><p>'+s.desc+'</p>'+
      '<div class="scenario-meta"><span class="cmd-level '+dc+'">'+s.difficulty+'</span><span class="scenario-steps">'+s.steps.length+' 道题</span>'+(done?'<span class="scenario-steps" style="color:var(--green)">得分 '+done.score+'%</span>':'')+'</div>';
    card.onclick=function(){ startLab(s.id); };
    grid.appendChild(card);
  });
}
function updateLabStats(){
  var done=Object.keys(labResults).length;
  document.getElementById('labCompleted').textContent=done;
  document.getElementById('labDoneCount').textContent=done;
  document.getElementById('labDoneBar').style.width=(done/SCENARIOS.length*100)+'%';
  if(done>0){
    var avg=Math.round(Object.values(labResults).reduce(function(s,r){return s+r.score;},0)/done);
    document.getElementById('labAvgScore').textContent=avg+'%';
  }
}
function startLab(id){
  currentLab=SCENARIOS.find(function(s){return s.id===id;});
  currentStep=0; currentScore=0;
  document.getElementById('labList').style.display='none';
  document.getElementById('labQuiz').style.display='block';
  renderLabStep();
}
function renderLabStep(){
  var s=currentLab; var step=s.steps[currentStep];
  var q=document.getElementById('labQuiz');
  q.innerHTML='<div class="quiz-wrap">'+
    '<div class="quiz-head"><button class="quiz-back" onclick="exitLab()">← 返回场景</button><div class="quiz-progress">第 '+(currentStep+1)+' / '+s.steps.length+' 题</div></div>'+
    '<div class="quiz-bar"><div class="quiz-bar-fill" style="width:'+((currentStep)/s.steps.length*100)+'%"></div></div>'+
    '<div class="glass quiz-card">'+
      '<div class="quiz-scene">'+s.icon+' '+s.title+'</div>'+
      '<div class="quiz-question">'+step.q+'</div>'+
      '<div class="quiz-options" id="quizOpts">'+
      step.opts.map(function(o,i){return '<div class="quiz-option" onclick="answerLab('+i+')"><span class="opt-letter">'+String.fromCharCode(65+i)+'</span><span>'+o.t+'</span></div>';}).join('')+
      '</div>'+
      '<div class="quiz-explain" id="quizExplain"></div>'+
      '<div class="quiz-next" id="quizNext" style="display:none"><button class="btn btn-primary" onclick="nextLabStep()">'+(currentStep<s.steps.length-1?'下一题 →':'查看结果 🏆')+'</button></div>'+
    '</div></div>';
}
function answerLab(idx){
  var step=currentLab.steps[currentStep];
  var opts=document.querySelectorAll('.quiz-option');
  opts.forEach(function(o){ o.classList.add('disabled'); o.onclick=null; });
  var chosen=step.opts[idx];
  if(chosen.c){ currentScore++; opts[idx].classList.add('correct'); }
  else{ opts[idx].classList.add('wrong'); step.opts.forEach(function(o,i){ if(o.c) opts[i].classList.add('correct'); }); }
  var exp=document.getElementById('quizExplain');
  exp.innerHTML='<strong>'+(chosen.c?'✅ 回答正确！':'❌ 回答错误')+'</strong><br>'+chosen.e;
  exp.classList.add('show');
  document.getElementById('quizNext').style.display='block';
}
function nextLabStep(){
  if(currentStep<currentLab.steps.length-1){ currentStep++; renderLabStep(); }
  else{ finishLab(); }
}
function finishLab(){
  var pct=Math.round(currentScore/currentLab.steps.length*100);
  labResults[currentLab.id]={score:pct,date:Date.now()};
  localStorage.setItem('shm_lab_results',JSON.stringify(labResults));
  var icon=pct>=80?'🏆':pct>=60?'👍':'💪';
  var title=pct>=80?'优秀！运维达人':pct>=60?'不错，继续加油':'还需多练习';
  var desc=pct>=80?'你对 '+currentLab.title+' 的排查流程掌握得很好，思路清晰，能准确选择每一步。':pct>=60?'基本思路正确，但有些步骤选择不够精准。回顾解析，理解为什么选这个。':'不要灰心！运维排查需要经验积累。仔细看每道题的解析，理解排查思路比记住答案更重要。';
  var q=document.getElementById('labQuiz');
  q.innerHTML='<div class="quiz-wrap"><div class="glass result-card">'+
    '<div class="result-icon">'+icon+'</div>'+
    '<div class="result-score" style="color:'+(pct>=80?'var(--green)':pct>=60?'var(--amber)':'var(--red)')+'">'+pct+'%</div>'+
    '<div class="result-title">'+title+'</div>'+
    '<div class="result-desc">'+desc+'<br><br>正确 '+currentScore+' / '+currentLab.steps.length+' 题</div>'+
    '<div class="result-actions">'+
      '<button class="btn btn-primary" onclick="startLab(\''+currentLab.id+'\')">🔄 再做一次</button>'+
      '<button class="btn btn-ghost" onclick="exitLab()">📋 场景列表</button>'+
    '</div></div></div>';
  updateLabStats();
}
function exitLab(){
  document.getElementById('labQuiz').style.display='none';
  document.getElementById('labList').style.display='block';
  renderLabList();
}

/* ===== Tools ===== */
function initTools(){
  document.getElementById('tsInput').value=Math.floor(Date.now()/1000);
}
function b64Encode(){ var v=document.getElementById('b64Input').value; document.getElementById('b64Output').textContent=v?btoa(unescape(encodeURIComponent(v))):'请输入内容'; }
function b64Decode(){ try{ document.getElementById('b64Output').textContent=decodeURIComponent(escape(atob(document.getElementById('b64Input').value))); }catch(e){ document.getElementById('b64Output').textContent='解码失败：无效的 Base64'; } }
function urlEncode(){ document.getElementById('urlOutput').textContent=encodeURIComponent(document.getElementById('urlInput').value); }
function urlDecode(){ try{ document.getElementById('urlOutput').textContent=decodeURIComponent(document.getElementById('urlInput').value); }catch(e){ document.getElementById('urlOutput').textContent='解码失败'; } }
function jsonFormat(){ try{ document.getElementById('jsonOutput').textContent=JSON.stringify(JSON.parse(document.getElementById('jsonInput').value),null,2); }catch(e){ document.getElementById('jsonOutput').textContent='JSON 格式错误：'+e.message; } }
function jsonMinify(){ try{ document.getElementById('jsonOutput').textContent=JSON.stringify(JSON.parse(document.getElementById('jsonInput').value)); }catch(e){ document.getElementById('jsonOutput').textContent='JSON 格式错误：'+e.message; } }
function tsToDate(){ var ts=parseInt(document.getElementById('tsInput').value); if(isNaN(ts)){ document.getElementById('tsOutput').textContent='请输入有效时间戳'; return; } var d=new Date(ts*1000); document.getElementById('tsOutput').textContent=d.toLocaleString('zh-CN')+'\nUTC: '+d.toUTCString(); }
function dateToTs(){ var now=Math.floor(Date.now()/1000); document.getElementById('tsInput').value=now; document.getElementById('tsOutput').textContent='当前时间戳：'+now+'\n'+new Date().toLocaleString('zh-CN'); }
function genPassword(){
  var len=parseInt(document.getElementById('pwLen').value);
  var chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*';
  var p=''; for(var i=0;i<len;i++) p+=chars[Math.floor(Math.random()*chars.length)];
  document.getElementById('pwOutput').textContent=p;
}
async function calcHash(){
  var text=document.getElementById('hashInput').value; var algo=document.getElementById('hashAlgo').value;
  if(!text){ document.getElementById('hashOutput').textContent='请输入文本'; return; }
  try{
    var buf=await crypto.subtle.digest(algo,new TextEncoder().encode(text));
    var hex=Array.from(new Uint8Array(buf)).map(function(b){return b.toString(16).padStart(2,'0');}).join('');
    document.getElementById('hashOutput').textContent=algo+': '+hex;
  }catch(e){ document.getElementById('hashOutput').textContent='计算失败：'+e.message; }
}
function convertBase(){
  var n=parseInt(document.getElementById('decInput').value);
  if(isNaN(n)){ document.getElementById('baseOutput').textContent='请输入有效数字'; return; }
  document.getElementById('baseOutput').textContent='二进制: '+n.toString(2)+'\n八进制: '+n.toString(8)+'\n十进制: '+n+'\n十六进制: 0x'+n.toString(16).toUpperCase();
}
function testRegex(){
  var p=document.getElementById('rePattern').value; var t=document.getElementById('reText').value;
  if(!p){ document.getElementById('reOutput').textContent='请输入正则表达式'; return; }
  try{
    var re=new RegExp(p,'g'); var matches=t.match(re);
    document.getElementById('reOutput').textContent=matches?('匹配到 '+matches.length+' 个:\n'+matches.join(', ')):'无匹配';
  }catch(e){ document.getElementById('reOutput').textContent='正则错误：'+e.message; }
}
function copyOutput(id){
  var text=document.getElementById(id).textContent;
  navigator.clipboard.writeText(text).then(function(){ toast('已复制到剪贴板','success'); }).catch(function(){ toast('复制失败','error'); });
}

/* ===== Monitor iframe ===== */
function openMonitor(){ document.getElementById('monitorWrap').classList.add('show'); var f=document.getElementById('monitorFrame'); if(!f.src||f.src.indexOf('about:')!==-1) f.src='/monitor'; }
function closeMonitor(){ document.getElementById('monitorWrap').classList.remove('show'); }

/* ===== Connect ===== */
function modeChanged(){
  var m=document.getElementById('cfgMode').value;
  document.getElementById('sshFields').style.display=m==='tunnel'?'block':'none';
  document.getElementById('lblServer').textContent=m==='tunnel'?'服务器地址（SSH主机）':m==='proxy'?'网关地址':'服务器地址';
}
function fillConfig(cfg){
  document.getElementById('cfgMode').value=cfg.mode||'tunnel';
  document.getElementById('cfgIp').value=cfg.server_ip||'';
  document.getElementById('cfgPort').value=cfg.server_port||8080;
  document.getElementById('cfgSshUser').value=cfg.ssh_user||'root';
  document.getElementById('cfgSshPort').value=cfg.ssh_port||22;
  document.getElementById('cfgSshKey').value=cfg.ssh_key||'';
  document.getElementById('cfgAuthUser').value=cfg.auth_user||'';
  document.getElementById('cfgAuthPass').value='';
  modeChanged();
}
function readConfig(){
  return {mode:document.getElementById('cfgMode').value,server_ip:document.getElementById('cfgIp').value.trim(),server_port:parseInt(document.getElementById('cfgPort').value)||8080,ssh_user:document.getElementById('cfgSshUser').value.trim()||'root',ssh_port:parseInt(document.getElementById('cfgSshPort').value)||22,ssh_key:document.getElementById('cfgSshKey').value.trim(),auth_user:document.getElementById('cfgAuthUser').value.trim(),auth_pass:document.getElementById('cfgAuthPass').value,auto_connect:true};
}
function setResult(id,ok,msg){ var el=document.getElementById(id); el.textContent=msg||''; el.className='hint'+(ok===true?' ok':ok===false?' err':''); }
async function post(url,body){ var r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})}); return await r.json(); }
async function saveConfig(){ var r=await post('/api/app/config',readConfig()); setResult('connResult',r.success!==false,r.success!==false?'配置已保存':(r.message||'保存失败')); refreshState(); }
async function testConn(){ await post('/api/app/config',readConfig()); setResult('connResult',null,'正在测试…'); var r=await post('/api/app/test'); setResult('connResult',r.success,r.success?('连接正常 · 延迟 '+(r.latency_ms||0)+' ms'):('测试失败：'+(r.message||''))); refreshState(); }
async function connect(){ await post('/api/app/config',readConfig()); setResult('connResult',null,'正在连接…'); var r=await post('/api/app/connect'); setResult('connResult',r.success,r.success?'已连接':('连接失败：'+(r.message||''))); refreshState(); }
async function disconnect(){ var r=await post('/api/app/disconnect'); setResult('connResult',r.success,r.message); refreshState(); }

/* ===== Console ===== */
async function startConsole(){
  if(STATE&&!STATE.console_admin_exists){ showAdminSetup(); return; }
  setResult('consoleResult',null,'正在启动…');
  var r=await post('/api/app/console/start',{});
  setResult('consoleResult',r.success,r.message||'');
  refreshConsole(); refreshState();
}
async function stopConsole(){ await post('/api/app/console/stop'); refreshConsole(); refreshState(); }
function showAdminSetup(){
  document.getElementById('consoleSetup').innerHTML='<div class="pane-inner" style="max-width:480px"><div class="glass" style="padding:30px"><div style="font-size:36px;margin-bottom:12px">🔒</div><h3 style="font-size:16px;font-weight:700;margin-bottom:8px">创建管理员账户</h3><p style="font-size:12px;color:var(--text-2);margin-bottom:16px">密码至少 12 位，含大写、小写、数字和特殊字符。</p><div class="field"><label>用户名</label><input type="text" id="admUser" placeholder="admin"></div><div class="field"><label>密码</label><input type="password" id="admPass" placeholder="强密码"></div><div class="btn-row"><button class="btn btn-primary" onclick="createAdmin()">创建并启动</button></div><div class="hint" id="admResult" style="margin-top:10px"></div></div></div>';
}
async function createAdmin(){
  var u=document.getElementById('admUser').value.trim(); var p=document.getElementById('admPass').value;
  if(!u||!p){ setResult('admResult',false,'请填写用户名和密码'); return; }
  if(p.length<12||!/[A-Z]/.test(p)||!/[a-z]/.test(p)||!/[0-9]/.test(p)||!/[!@#$%^&*._\-~]/.test(p)){ setResult('admResult',false,'密码不满足要求'); return; }
  setResult('admResult',null,'正在创建…');
  var r=await post('/api/app/console/start',{admin_user:u,admin_pass:p});
  if(r.success){
    if(r.api_key){
      document.getElementById('consoleSetup').innerHTML='<div class="pane-inner" style="max-width:480px"><div class="glass" style="padding:30px;text-align:center"><div style="font-size:36px;margin-bottom:12px">✅</div><h3 style="font-size:16px;margin-bottom:8px">管理员已创建</h3><div class="hint err" style="background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.25);padding:10px;border-radius:8px;margin-bottom:12px">API 密钥只显示一次，请立即复制！</div><div style="font-family:var(--mono);font-size:12px;color:var(--accent-2);background:var(--bg-0);padding:12px;border-radius:8px;border:1px solid var(--border);word-break:break-all;margin-bottom:14px">'+r.api_key+'</div><button class="btn btn-primary" onclick="refreshConsole()">进入控制台</button></div></div>';
    }else{ setResult('admResult',true,'管理员已创建'); }
  }else{ setResult('admResult',false,r.message||'创建失败'); }
  refreshState();
}
function refreshConsole(){
  if(!STATE) return;
  var host=document.getElementById('consoleHost'); var setup=document.getElementById('consoleSetup');
  if(STATE.console_running){
    host.style.display='block'; setup.style.display='none';
    var frame=document.getElementById('consoleFrame'); var src='http://127.0.0.1:'+STATE.console_port+'/console/';
    if(frame.getAttribute('src')!==src) frame.setAttribute('src',src);
  }else{
    host.style.display='none'; setup.style.display='flex';
    if(!STATE.console_admin_exists){
      setup.innerHTML='<div class="pane-inner" style="max-width:480px"><div class="glass" style="padding:36px;text-align:center"><div style="font-size:48px;margin-bottom:16px">🧩</div><h3 style="font-size:18px;font-weight:700;margin-bottom:10px">管理控制台未启动</h3><p style="font-size:13px;color:var(--text-2);line-height:1.7;margin-bottom:22px">尚未创建管理员。启动后可管理多台服务器、权限、部署与工单。</p><button class="btn btn-primary" onclick="showAdminSetup()">创建管理员并启动</button></div></div>';
    }else{
      setup.innerHTML='<div class="pane-inner" style="max-width:480px"><div class="glass" style="padding:36px;text-align:center"><div style="font-size:48px;margin-bottom:16px">🧩</div><h3 style="font-size:18px;font-weight:700;margin-bottom:10px">管理控制台未启动</h3><p style="font-size:13px;color:var(--text-2);line-height:1.7;margin-bottom:22px">点击下方按钮启动，随后在此窗口内登录管理。</p><button class="btn btn-primary" onclick="startConsole()">启动管理控制台</button></div></div>';
    }
  }
}

/* ===== State & Logs ===== */
async function refreshState(){
  try{
    var r=await fetch('/api/app/state'); STATE=await r.json();
    var map={connected:['ok','已连接'],connecting:['warn','连接中'],error:['err','连接失败'],disconnected:['','未连接']};
    var c=map[STATE.conn_status]||['','—'];
    document.getElementById('connDot').className='status-dot '+c[0];
    document.getElementById('connText').textContent=c[1];
    document.getElementById('consoleDot').className='status-dot '+(STATE.console_running?'ok':'');
  }catch(e){}
}
var lastLogLen=0;
async function refreshLogs(){
  try{
    var r=await fetch('/api/app/logs'); var data=await r.json(); var logs=data.logs||[];
    var list=document.getElementById('logList');
    for(var i=lastLogLen;i<logs.length;i++){
      var l=logs[i]; var div=document.createElement('div');
      div.className='log-line '+(l.level||'info');
      div.innerHTML='<span class="log-time">'+l.t+'</span><span class="log-msg"></span>';
      div.querySelector('.log-msg').textContent=l.msg; list.appendChild(div);
    }
    if(lastLogLen!==logs.length){ lastLogLen=logs.length; list.scrollTop=list.scrollHeight; }
  }catch(e){}
}
async function clearLogs(){ await post('/api/app/logs/clear'); document.getElementById('logList').innerHTML=''; lastLogLen=0; refreshLogs(); }

/* ===== Init ===== */
(async function init(){
  renderCats(); renderLexicon(); updateLabStats();
  try{ var c=await (await fetch('/api/app/config')).json(); fillConfig(c); }catch(e){}
  await refreshState(); refreshConsole();
  setInterval(refreshState,2000); setInterval(refreshLogs,1500);
})();
</script>
</body>
</html>
'''
