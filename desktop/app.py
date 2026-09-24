"""
Server Health Monitor - 桌面应用入口

一体化桌面软件：双击启动，在同一窗口内完成服务器连接、
实时监控、管理控制台操作与日志调试。原生窗口，不打开浏览器。
"""

import os
import sys
import time
import traceback

# 确保能导入同目录模块与项目根目录的 dashboard_client
_here = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(_here)
for _p in (_here, _root):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _setup_stdio():
    """PyInstaller --windowed 模式下 stdout/stderr 为 None，任何库对其写入都会崩溃。
    重定向到空设备，避免无窗口模式下的空流崩溃。"""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w")


def _crash_log_path():
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = _root
    return os.path.join(base, "app-crash.log")


def run():
    import webview  # noqa: E402
    import backend  # noqa: E402

    b = backend.Backend()
    b.start()

    window = webview.create_window(
        "Server Health Monitor",
        b.local_url,
        width=1240,
        height=800,
        min_size=(920, 620),
    )

    # 进入原生窗口事件循环；窗口关闭后返回
    webview.start(gui=None)

    # 清理后台子进程（控制台 / 隧道 / 本地服务）
    b.shutdown()


if __name__ == "__main__":
    _setup_stdio()
    try:
        run()
    except Exception:
        try:
            with open(_crash_log_path(), "a", encoding="utf-8") as f:
                f.write("\n" + time.strftime("[%Y-%m-%d %H:%M:%S]") + " 启动失败\n")
                traceback.print_exc(file=f)
        except Exception:
            pass