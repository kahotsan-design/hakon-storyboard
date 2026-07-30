"""PyInstaller runtime hook: 在 exe 启动时加载内置 .env 文件。

这个文件在 PyInstaller 打包时会自动执行，在主程序之前。
它会读取打包进 exe 的 .env 文件，把 API Key 注入环境变量。
"""
import os
import sys
from pathlib import Path

def _load_env():
    """从 _MEIPASS 临时目录加载 .env 文件。"""
    if not hasattr(sys, "_MEIPASS"):
        return
    
    env_path = Path(sys._MEIPASS) / ".env"
    if not env_path.exists():
        return
    
    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if key and value:
                        # 只在环境变量未设置时注入（不覆盖用户已设置的值）
                        if key not in os.environ:
                            os.environ[key] = value
    except Exception:
        pass

_load_env()
