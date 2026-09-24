"""
Server Health Monitor - 桌面应用后端

负责本地 HTTP 服务（外壳界面 + 监控面板 + 数据代理）、
配置持久化、SSH 隧道管理、Go 管理控制台子进程、以及实时日志。
纯使用软件的一部分：所有功能在一个桌面窗口内完成，不打开浏览器。
"""

import base64
import ctypes
import ctypes.wintypes
import http.server
import json
import os
import re
import secrets
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import urllib.error
from collections import deque
from urllib.parse import urlparse

import ui
from dashboard_client import DASHBOARD_HTML

APP_NAME = "Server Health Monitor"
APP_VERSION = "2.1.0"

DEFAULT_CONFIG = {
    "mode": "tunnel",            # tunnel / direct / proxy
    "server_ip": "",             # tunnel: SSH 主机；direct: Agent 主机；proxy: 网关 URL
    "server_port": 8080,         # Agent HTTP 端口
    "ssh_user": "root",
    "ssh_port": 22,
    "ssh_key": "",               # 留空则用 ~/.ssh/id_ed25519
    "auth_user": "",
    "auth_pass": "",
    "local_port": 8090,          # 本地面板端口
    "tunnel_port": 18080,        # 本地隧道端口
    "console_port": 8081,        # 管理控制台端口
    "auto_connect": True,
}


def app_data_dir():
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.path.join(os.path.expanduser("~"), ".config")
    d = os.path.join(base, "ServerHealthMonitor")
    os.makedirs(d, exist_ok=True)
    return d


def config_path():
    return os.path.join(app_data_dir(), "config.json")


def secret_path():
    return os.path.join(app_data_dir(), "auth_pass.secret")


def _dpapi(plain, decrypt=False):
    """Encrypt/decrypt bytes with the current Windows user's DPAPI key."""
    if sys.platform != "win32":
        raise RuntimeError("DPAPI 仅适用于 Windows")

    class Blob(ctypes.Structure):
        _fields_ = [("cbData", ctypes.wintypes.DWORD),
                    ("pbData", ctypes.POINTER(ctypes.c_byte))]

    crypt32 = ctypes.windll.crypt32
    kernel32 = ctypes.windll.kernel32
    raw = ctypes.create_string_buffer(plain if plain else b"\0")
    source = Blob(len(plain), ctypes.cast(raw, ctypes.POINTER(ctypes.c_byte)))
    result = Blob()
    fn = crypt32.CryptUnprotectData if decrypt else crypt32.CryptProtectData
    fn.argtypes = [
        ctypes.POINTER(Blob), ctypes.c_wchar_p, ctypes.POINTER(Blob),
        ctypes.c_void_p, ctypes.c_void_p, ctypes.wintypes.DWORD,
        ctypes.POINTER(Blob),
    ]
    fn.restype = ctypes.wintypes.BOOL
    if not fn(ctypes.byref(source), None, None, None, None, 0, ctypes.byref(result)):
        raise ctypes.WinError()
    try:
        return ctypes.string_at(result.pbData, result.cbData)
    finally:
        kernel32.LocalFree(result.pbData)


def _read_secret():
    try:
        with open(secret_path(), "rb") as f:
            value = f.read()
        if sys.platform == "win32":
            return _dpapi(value, decrypt=True).decode("utf-8")
        return value.decode("utf-8")
    except (OSError, UnicodeError, RuntimeError):
        return ""


def _write_secret(value):
    raw = value.encode("utf-8")
    if sys.platform == "win32":
        raw = _dpapi(raw)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(secret_path(), flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
        fd = None
    finally:
        if fd is not None:
            os.close(fd)
    if sys.platform != "win32":
        os.chmod(secret_path(), 0o600)


def find_ssh():
    """定位系统 OpenSSH 客户端。"""
    p = shutil.which("ssh")
    if p:
        return p
    if sys.platform == "win32":
        for candidate in (
            r"C:\Windows\System32\OpenSSH\ssh.exe",
            r"C:\Windows\Sysnative\OpenSSH\ssh.exe",
        ):
            if os.path.isfile(candidate):
                return candidate
    return None


class Backend:
    def __init__(self):
        self._local_api_token = secrets.token_urlsafe(32)
        self._legacy_password = None
        self.config = dict(DEFAULT_CONFIG)
        self.config.update(self._load_config())
        if self._legacy_password is not None:
            self.save_config()

        self._logs = deque(maxlen=2000)
        self._log_lock = threading.Lock()

        self._conn_status = "disconnected"  # disconnected/connecting/connected/error
        self._conn_detail = ""
        self._last_error_category = ""
        self._target_url = ""
        self._tunnel_proc = None
        self._tunnel_lock = threading.Lock()

        self._console_proc = None
        self._console_lock = threading.Lock()
        self._last_api_key = None
        self._console_secrets = set()

        self._httpd = None
        self._http_thread = None

        self.log("info", f"{APP_NAME} v{APP_VERSION} 后端初始化完成")

    # ------------------------------------------------------------------ 配置
    def _load_config(self):
        try:
            with open(config_path(), "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                if "auth_pass" in data:
                    self._legacy_password = str(data["auth_pass"])
                elif data.get("auth_pass_ref"):
                    data["auth_pass"] = _read_secret()
                data.pop("auth_pass_ref", None)
                data.pop("auth_pass", None)
                if self._legacy_password is not None:
                    data["auth_pass"] = self._legacy_password
                return data
        except Exception:
            pass
        return {}

    def save_config(self):
        os.makedirs(app_data_dir(), exist_ok=True)
        password = str(self.config.get("auth_pass") or "")
        if password:
            _write_secret(password)
        elif os.path.isfile(secret_path()):
            try:
                os.remove(secret_path())
            except OSError:
                pass
        persisted = dict(self.config)
        persisted.pop("auth_pass", None)
        persisted["auth_pass_ref"] = "dpapi" if sys.platform == "win32" else "file"
        with open(config_path(), "w", encoding="utf-8", newline="\n") as f:
            json.dump(persisted, f, ensure_ascii=False, indent=2)
        self._legacy_password = None

    def update_config(self, incoming):
        for key in (
            "mode", "server_ip", "server_port", "ssh_user", "ssh_port",
            "ssh_key", "auth_user", "local_port",
            "tunnel_port", "console_port", "auto_connect",
        ):
            if key in incoming:
                self.config[key] = incoming[key]
        # The UI sends an empty password because the stored value is never
        # returned. An empty value therefore means "leave it unchanged".
        if incoming.get("auth_pass"):
            self.config["auth_pass"] = str(incoming["auth_pass"])
        for key in ("server_port", "ssh_port", "local_port", "tunnel_port", "console_port"):
            try:
                self.config[key] = int(self.config[key])
            except (TypeError, ValueError):
                pass
        self.save_config()

    def public_config(self):
        cfg = dict(self.config)
        cfg["auth_pass"] = ""  # 密码不回传前端
        return cfg

    # ------------------------------------------------------------------ 日志
    def log(self, level, msg):
        msg = self._redact_sensitive(str(msg))
        with self._log_lock:
            self._logs.append({
                "t": time.strftime("%H:%M:%S"),
                "level": level,
                "msg": msg,
            })

    def _redact_sensitive(self, text):
        for value in (self.config.get("auth_pass"), *self._console_secrets):
            if value:
                text = text.replace(str(value), "[已脱敏]")
        return re.sub(
            r"(?i)((?:密码|password|admin[_ -]*pass|api[\s_-]*key|api\s*密钥|"
            r"token|secret)\s*(?:is\s+)?[:=：]?\s*)([^\s,;，；]+)",
            r"\1[已脱敏]",
            text,
        )

    def get_logs(self):
        with self._log_lock:
            return list(self._logs)

    def clear_logs(self):
        with self._log_lock:
            self._logs.clear()
        self.log("info", "日志已清空")

    # ------------------------------------------------------------------ 目标
    def ssh_key_path(self):
        key = self.config.get("ssh_key") or ""
        key = os.path.expanduser(key.strip())
        if not key:
            key = os.path.join(os.path.expanduser("~"), ".ssh", "id_ed25519")
        return key

    def build_target(self):
        mode = self.config.get("mode", "direct")
        if mode == "tunnel":
            return f"http://127.0.0.1:{self.config['tunnel_port']}"
        ip = (self.config.get("server_ip") or "").strip().rstrip("/")
        if "://" in ip or "/" in ip or "@" in ip:
            raise ValueError("服务器地址必须是主机名或 IP，不能包含 URL、路径或凭据")
        if not re.match(r"^[A-Za-z0-9.:-]+$", ip):
            raise ValueError("服务器地址格式无效")
        return f"http://{ip}:{self.config['server_port']}"

    # ------------------------------------------------------------------ 隧道
    def _tunnel_running(self):
        with self._tunnel_lock:
            return self._tunnel_proc is not None and self._tunnel_proc.poll() is None

    def start_tunnel(self):
        if self.config.get("mode") != "tunnel":
            return True, ""
        if self._tunnel_running():
            return True, "隧道已在运行"

        ssh = find_ssh()
        if not ssh:
            self._last_error_category = "ssh"
            return False, "SSH：未找到 OpenSSH 客户端（ssh.exe）。请安装 Windows OpenSSH Client。"

        key = self.ssh_key_path()
        if not os.path.isfile(key):
            self._last_error_category = "ssh"
            return False, f"SSH：未找到私钥 {key}。请检查 SSH 私钥路径。"

        host = (self.config.get("server_ip") or "").strip()
        if not host:
            self._last_error_category = "ssh"
            return False, "SSH：未填写服务器地址。请填写 SSH 主机名或 IP。"

        args = [
            ssh, "-N",
            "-o", "BatchMode=yes",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-o", "StrictHostKeyChecking=yes",
            "-o", "UserKnownHostsFile=" + os.path.join(app_data_dir(), "known_hosts"),
            "-i", key,
            "-L", f"{self.config['tunnel_port']}:127.0.0.1:{self.config['server_port']}",
            "-p", str(self.config['ssh_port']),
            f"{self.config['ssh_user']}@{host}",
        ]
        self.log("info", f"正在建立 SSH 隧道：{self.config['ssh_user']}@{host}")
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen(
                args, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace",
                stdin=subprocess.DEVNULL, creationflags=creationflags,
            )
        except Exception as e:
            self._last_error_category = "ssh"
            return False, f"SSH：启动隧道失败：{e}。请确认 OpenSSH 可执行。"

        with self._tunnel_lock:
            self._tunnel_proc = proc

        deadline = time.time() + 10
        while time.time() < deadline:
            if proc.poll() is not None:
                detail = ""
                if proc.stderr:
                    detail = proc.stderr.read().strip()
                self.stop_tunnel()
                lowered = detail.lower()
                if "address already in use" in lowered or "bind" in lowered or "端口" in detail:
                    self._last_error_category = "port"
                    return False, f"端口冲突：本地隧道端口 {self.config['tunnel_port']} 已被占用。请修改隧道端口后重试。"
                if "permission denied" in lowered or "authentication" in lowered:
                    self._last_error_category = "auth"
                    return False, "认证失败：SSH 用户、私钥或服务器授权不正确。请检查 authorized_keys 和私钥。"
                self._last_error_category = "ssh"
                return False, "SSH 连接失败：请检查主机、SSH 端口、网络和 known_hosts。"
            if self._port_open("127.0.0.1", self.config["tunnel_port"]):
                self.log("info", f"SSH 隧道已建立：127.0.0.1:{self.config['tunnel_port']} -> {host}:{self.config['server_port']}")
                return True, ""
            time.sleep(0.3)
        self.stop_tunnel()
        self._last_error_category = "timeout"
        return False, "连接超时：SSH 隧道未能在 10 秒内建立。请检查网络、防火墙和 SSH 端口。"

    def stop_tunnel(self):
        with self._tunnel_lock:
            proc = self._tunnel_proc
            self._tunnel_proc = None
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                time.sleep(0.3)
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass
            self.log("info", "SSH 隧道已关闭")

    @staticmethod
    def _port_open(host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(1.0)
        try:
            s.connect((host, port))
            return True
        except Exception:
            return False
        finally:
            s.close()

    # ------------------------------------------------------------------ 连接
    def connect(self):
        self._conn_status = "connecting"
        self._conn_detail = ""
        self._last_error_category = ""
        mode = self.config.get("mode", "direct")

        if mode == "tunnel":
            ok, err = self.start_tunnel()
            if not ok:
                self._conn_status = "error"
                self._conn_detail = err
                self.log("error", "连接失败：" + err)
                return {"success": False, "message": err, "category": self._last_error_category}

        self._target_url = self.build_target()
        ok, msg = self._test_health(self._target_url)
        if ok:
            self._conn_status = "connected"
            self._conn_detail = ""
            self.log("info", f"已连接：{self._target_url}")
            return {"success": True, "message": "连接成功"}
        else:
            self._conn_status = "error"
            self._conn_detail = msg
            self.log("error", "连接失败：" + msg)
            return {"success": False, "message": msg, "category": self._last_error_category}

    def disconnect(self):
        self.stop_tunnel()
        self._conn_status = "disconnected"
        self._conn_detail = ""
        self._target_url = ""
        self.log("info", "已断开连接")
        return {"success": True, "message": "已断开"}

    def test_connection(self):
        mode = self.config.get("mode")
        if mode == "tunnel":
            ok, err = self.start_tunnel()
            if not ok:
                return {"success": False, "message": err, "category": self._last_error_category}
            target = self.build_target()
        else:
            if not (self.config.get("server_ip") or "").strip():
                return {"success": False, "message": "请先填写服务器地址"}
            target = self.build_target()
        t0 = time.time()
        ok, msg = self._test_health(target)
        latency = int((time.time() - t0) * 1000)
        if ok:
            return {"success": True, "message": "连接正常", "latency_ms": latency}
        return {"success": False, "message": msg, "category": self._last_error_category}

    def _test_health(self, target):
        url = target.rstrip("/") + "/api/health"
        try:
            req = urllib.request.Request(url)
            self._add_auth(req)
            with urllib.request.urlopen(req, timeout=6) as resp:
                if resp.status == 200:
                    return True, "正常"
                self._last_error_category = "connection"
                return False, f"HTTP {resp.status}"
        except urllib.error.HTTPError as e:
            self._last_error_category = "auth" if e.code in (401, 403) else "connection"
            if e.code in (401, 403):
                return False, "认证失败：服务器拒绝了用户名或密码。请检查认证配置。"
            return False, f"服务器返回 HTTP {e.code}。请检查 Agent 状态和配置。"
        except urllib.error.URLError as e:
            reason = str(e.reason)
            lowered = reason.lower()
            if "timed out" in lowered or "timeout" in lowered:
                self._last_error_category = "timeout"
                return False, "连接超时：请检查服务器地址、端口和防火墙。"
            self._last_error_category = "ssh" if self.config.get("mode") == "tunnel" else "connection"
            return False, f"无法连接：{reason}。请检查地址和端口。"
        except Exception as e:
            self._last_error_category = "connection"
            return False, f"连接错误：{e}。请检查服务器状态和配置。"

    def _add_auth(self, req):
        if self.config.get("auth_user"):
            cred = f"{self.config['auth_user']}:{self.config.get('auth_pass', '')}"
            req.add_header("Authorization", "Basic " + base64.b64encode(cred.encode()).decode())

    # ------------------------------------------------------------------ 管理控制台
    def console_dir(self):
        return os.path.join(app_data_dir(), "console-data")

    def console_exe_path(self):
        if getattr(sys, "frozen", False):
            base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            p = os.path.join(base, "server-health-monitor-console.exe")
            if os.path.isfile(p):
                return p
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        for p in (
            os.path.join(root, "build", "server-health-monitor-console.exe"),
            os.path.join(root, "server-health-monitor-console.exe"),
        ):
            if os.path.isfile(p):
                return p
        return None

    def _console_running(self):
        with self._console_lock:
            return self._console_proc is not None and self._console_proc.poll() is None

    def console_admin_exists(self):
        p = os.path.join(self.console_dir(), "users.json")
        if not os.path.isfile(p):
            return False
        return os.path.getsize(p) > 2

    def start_console(self, admin_user="", admin_pass=""):
        if self._console_running():
            return {"success": False, "message": "管理控制台已在运行"}

        exe = self.console_exe_path()
        if not exe:
            return {"success": False, "message": "未找到管理控制台程序（server-health-monitor-console.exe）"}

        os.makedirs(self.console_dir(), exist_ok=True)
        if self._port_open("127.0.0.1", self.config["console_port"]):
            return {"success": False, "message": f"端口冲突：管理控制台端口 {self.config['console_port']} 已被占用，请修改端口。", "category": "port"}
        args = [
            exe,
            "--host", "127.0.0.1",
            "--port", str(self.config["console_port"]),
            "--data", self.console_dir(),
        ]
        if admin_user and admin_pass:
            args += ["--admin-user", admin_user, "--admin-pass", admin_pass]
            self._console_secrets.add(str(admin_pass))

        self.log("info", f"正在启动管理控制台：http://127.0.0.1:{self.config['console_port']}/console/")
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            proc = subprocess.Popen(
                args,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace",
                bufsize=1, creationflags=creationflags,
            )
        except Exception as e:
            return {"success": False, "message": f"启动失败：{e}"}

        with self._console_lock:
            self._console_proc = proc

        self._last_api_key = None
        threading.Thread(target=self._pump_console, args=(proc,), daemon=True).start()

        deadline = time.time() + 8
        while time.time() < deadline:
            if proc.poll() is not None:
                return {"success": False, "message": "管理控制台启动失败，请查看运行日志。可能是端口冲突或配置错误。", "category": "port"}
            if self._port_open("127.0.0.1", self.config["console_port"]):
                self.log("info", "管理控制台已就绪")
                result = {"success": True, "message": "管理控制台已启动"}
                time.sleep(0.6)
                if self._last_api_key:
                    result["api_key"] = self._last_api_key
                return result
            time.sleep(0.25)
        return {"success": True, "message": "管理控制台启动中（稍后刷新）"}

    def stop_console(self):
        with self._console_lock:
            proc = self._console_proc
            self._console_proc = None
        if proc and proc.poll() is None:
            try:
                proc.terminate()
                time.sleep(0.3)
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass
            self.log("info", "管理控制台已停止")
        return {"success": True, "message": "已停止"}

    def _pump_console(self, proc):
        for line in proc.stdout:
            line = line.rstrip()
            m = re.search(r"API 密钥:\s*(\S+)", line)
            if m:
                self._last_api_key = m.group(1)
                self._console_secrets.add(m.group(1))
            if line:
                self.log("console", line)
        if proc.poll() is not None:
            self.log("warn", f"管理控制台已退出（code={proc.poll()}）")

    # ------------------------------------------------------------------ 状态
    def get_state(self):
        return {
            "connected": self._conn_status == "connected",
            "conn_status": self._conn_status,
            "conn_detail": self._conn_detail,
            "conn_category": getattr(self, "_last_error_category", ""),
            "target_url": self._target_url,
            "mode": self.config.get("mode"),
            "tunnel_running": self._tunnel_running(),
            "console_running": self._console_running(),
            "console_admin_exists": self.console_admin_exists(),
            "console_port": self.config["console_port"],
            "version": APP_VERSION,
        }

    # ------------------------------------------------------------------ HTTP 服务
    def start(self):
        self._start_http()
        self._start_console_auto()
        if self.config.get("auto_connect"):
            threading.Thread(target=self.connect, daemon=True).start()

    def _start_console_auto(self):
        try:
            result = self.start_console()
            if not result.get("success"):
                self.log("warn", result.get("message", "管理控制台未启动"))
        except Exception as e:
            self.log("error", f"管理控制台启动异常：{e}")

    def _start_http(self):
        handler = self._make_handler()
        for port in (self.config["local_port"], self.config["local_port"] + 1,
                     self.config["local_port"] + 2):
            try:
                self._httpd = http.server.ThreadingHTTPServer(("127.0.0.1", port), handler)
                self.config["local_port"] = port
                break
            except OSError:
                continue
        if self._httpd is None:
            self._last_error_category = "port"
            raise RuntimeError("端口冲突：本地端口及后续两个端口均被占用，请修改本地端口后重试")
        self._http_thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._http_thread.start()
        self.log("info", f"本地服务已启动：http://127.0.0.1:{self.config['local_port']}/")

    @property
    def local_url(self):
        return f"http://127.0.0.1:{self.config['local_port']}/"

    def _make_handler(self):
        backend = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):
                pass  # 静默默认访问日志

            def _send(self, body, ctype="application/json; charset=utf-8", status=200):
                try:
                    if isinstance(body, bytes):
                        data = body
                    else:
                        if isinstance(body, (dict, list)):
                            body = json.dumps(body, ensure_ascii=False)
                        data = body.encode("utf-8")
                    self.send_response(status)
                    self.send_header("Content-Type", ctype)
                    self.send_header("Content-Length", str(len(data)))
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(data)
                except OSError:
                    pass  # 客户端提前断开时静默忽略

            def _read_body(self):
                try:
                    length = int(self.headers.get("Content-Length", 0))
                except ValueError:
                    length = 0
                if length <= 0:
                    return {}
                try:
                    return json.loads(self.rfile.read(length).decode("utf-8"))
                except Exception:
                    return {}

            def _authorize_local_request(self):
                host = self.headers.get("Host", "")
                if not (host == f"127.0.0.1:{backend.config['local_port']}" or
                        host == f"localhost:{backend.config['local_port']}"):
                    self._send({"error": "invalid host"}, status=403)
                    return False
                token = self.headers.get("X-Local-Token", "")
                origin = self.headers.get("Origin", "")
                expected_origin = {
                    f"http://127.0.0.1:{backend.config['local_port']}",
                    f"http://localhost:{backend.config['local_port']}",
                }
                if token != backend._local_api_token and origin not in expected_origin:
                    self._send({"error": "local authorization required"}, status=403)
                    return False
                if origin and origin not in expected_origin:
                    self._send({"error": "invalid origin"}, status=403)
                    return False
                return True

            def do_GET(self):
                path = urlparse(self.path).path
                if path in ("/", "/index.html", "/shell"):
                    self._send(ui.SHELL_HTML, "text/html; charset=utf-8")
                elif path == "/monitor":
                    self._send(DASHBOARD_HTML, "text/html; charset=utf-8")
                elif path == "/api/status":
                    self._proxy("/api/status", 200)
                elif path == "/api/health":
                    self._proxy("/api/health", 200)
                elif path == "/api/app/state":
                    self._send(backend.get_state())
                elif path == "/api/app/config":
                    self._send(backend.public_config())
                elif path == "/api/app/logs":
                    self._send({"logs": backend.get_logs()})
                else:
                    self._send({"error": "not_found"}, status=404)

            def do_POST(self):
                if not self._authorize_local_request():
                    return
                path = urlparse(self.path).path
                body = self._read_body()
                if path == "/api/app/config":
                    backend.update_config(body)
                    self._send({"success": True})
                elif path == "/api/app/connect":
                    self._send(backend.connect())
                elif path == "/api/app/disconnect":
                    self._send(backend.disconnect())
                elif path == "/api/app/test":
                    self._send(backend.test_connection())
                elif path == "/api/app/logs/clear":
                    backend.clear_logs()
                    self._send({"success": True})
                elif path == "/api/app/console/start":
                    self._send(backend.start_console(
                        body.get("admin_user", ""), body.get("admin_pass", "")))
                elif path == "/api/app/console/stop":
                    self._send(backend.stop_console())
                else:
                    self._send({"error": "not_found"}, status=404)

            def _proxy(self, api_path, ok_status):
                mode = backend.config.get("mode")
                if mode != "tunnel" and not (backend.config.get("server_ip") or "").strip():
                    self._send({"status": "offline", "error": "未配置服务器"}, status=200)
                    return
                url = backend.build_target().rstrip("/") + api_path
                try:
                    req = urllib.request.Request(url)
                    backend._add_auth(req)
                    with urllib.request.urlopen(req, timeout=8) as resp:
                        data = resp.read()
                        self._send(data, resp.headers.get("Content-Type", "application/json"),
                                   resp.status)
                except urllib.error.URLError as e:
                    self._send({"status": "offline", "error": str(e.reason)}, status=502)
                except Exception as e:
                    self._send({"status": "offline", "error": str(e)}, status=500)

        return Handler

    def shutdown(self):
        try:
            self.disconnect()
        except Exception:
            pass
        try:
            self.stop_console()
        except Exception:
            pass
        try:
            if self._httpd:
                self._httpd.shutdown()
        except Exception:
            pass