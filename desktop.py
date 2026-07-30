"""HAKON 桌面应用启动器。

自动启动本地 FastAPI 服务，并打开浏览器。
用户双击运行即可，无需安装任何依赖。
"""
import os
import sys
import time
import threading
import webbrowser
import socket


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


def open_browser(port):
    """等待服务器就绪后打开浏览器。"""
    if wait_for_server(port):
        url = f"http://127.0.0.1:{port}"
        print(f"正在打开浏览器: {url}")
        webbrowser.open(url)
    else:
        print("服务器启动超时，请稍后手动打开浏览器。")


def main():
    # 设置工作目录为 exe 所在目录
    if getattr(sys, "frozen", False):
        # PyInstaller 打包后
        base_dir = os.path.dirname(sys.executable)
        os.chdir(base_dir)

    # 找可用端口
    port = find_free_port()
    os.environ["PORT"] = str(port)

    print("=" * 50)
    print("  HAKON 智能剧本处理系统")
    print("=" * 50)
    print(f"  本地端口: http://127.0.0.1:{port}")
    print(f"  按 Ctrl+C 退出")
    print("=" * 50)

    # 启动浏览器线程
    browser_thread = threading.Thread(target=open_browser, args=(port,), daemon=True)
    browser_thread.start()

    # 直接导入 app 对象，避免字符串导入方式导致 PyInstaller 无法追踪
    # （PyInstaller 静态分析无法解析 "app.main:app" 这样的字符串引用）
    from app.main import app

    # 启动 FastAPI 服务
    try:
        import uvicorn
        uvicorn.run(
            app,          # 直接传入 app 对象，而非字符串
            host="127.0.0.1",
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n正在退出...")
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")
        sys.exit(1)


if __name__ == "__main__":
    main()
