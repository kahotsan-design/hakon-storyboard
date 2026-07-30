"""HAKON 桌面应用启动器。

双击运行后弹出独立桌面窗口，内嵌完整应用界面。
无浏览器、无黑色控制台、像一个正常的桌面软件。
"""
import os
import sys
import time
import threading
import socket
import logging

# 日志写入文件，不显示控制台
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    filename=os.path.join(os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.path.dirname(__file__), "HAKON.log"),
    filemode="a",
)
logger = logging.getLogger("HAKON")


def find_free_port():
    """找到一个可用端口。"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def wait_for_server(port, timeout=30):
    """等待服务器就绪。"""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                s.connect(("127.0.0.1", port))
                return True
        except (ConnectionRefusedError, socket.timeout, OSError):
            time.sleep(0.3)
    return False


def start_server(port, ready_event):
    """在后台线程中启动 FastAPI 服务。"""
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
        os.chdir(base_dir)

    os.environ["PORT"] = str(port)

    try:
        from app.main import app
        import uvicorn
        uvicorn.run(
            app,
            host="127.0.0.1",
            port=port,
            log_level="warning",  # 减少日志输出
            log_config=None,
        )
    except Exception as e:
        logger.error(f"Server failed: {e}", exc_info=True)
        ready_event.set()  # 释放等待


def main():
    port = find_free_port()

    # 启动后台服务器
    ready_event = threading.Event()
    server_thread = threading.Thread(
        target=start_server,
        args=(port, ready_event),
        daemon=True,
    )
    server_thread.start()

    # 等待服务器就绪
    if not wait_for_server(port, timeout=30):
        # 服务器启动失败
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("HAKON", "服务器启动失败，请检查 HAKON.log 文件。")
        except Exception:
            pass
        sys.exit(1)

    # 打开桌面窗口
    import webview
    url = f"http://127.0.0.1:{port}"
    webview.create_window(
        title="HAKON - AI影视剧本改编与分镜生成系统",
        url=url,
        width=1280,
        height=800,
        min_size=(960, 600),
        text_select=False,
    )
    webview.start()


if __name__ == "__main__":
    main()
