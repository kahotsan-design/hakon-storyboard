# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 单文件桌面窗口应用。

打包后生成一个 HAKON.exe，不依赖任何文件夹，放哪都能用。
双击运行 → 弹出桌面窗口 → 内嵌完整应用界面。

打包命令：
  python -m PyInstaller hakon_desktop.spec --noconfirm
"""

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None
BASE_DIR = os.path.abspath(".")

# 自动收集所有子模块
hiddenimports = []
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("fastapi")
hiddenimports += collect_submodules("starlette")
hiddenimports += collect_submodules("pydantic")
hiddenimports += collect_submodules("jinja2")
hiddenimports += collect_submodules("openai")
hiddenimports += collect_submodules("sse_starlette")
hiddenimports += collect_submodules("docx")
hiddenimports += collect_submodules("webview")
hiddenimports += collect_submodules("bottle")
hiddenimports += collect_submodules("proxy_tools")

# 关键模块
hiddenimports += [
    "app",
    "app.agents",
    "app.agents.script_understanding_agent",
    "app.agents.storyboard_agent",
    "app.agents.narration_visual_agent",
    "app.schemas",
    "app.schemas.models",
    "app.services",
    "app.services.export",
    "app.services.llm",
    "app.main",
    "app.pipeline",
    "app.config",
    "dotenv",
    "anyio",
    "anyio._backends",
    "anyio._backends._asyncio",
    "httpx",
    "httpcore",
    "h11",
    "sniffio",
    "certifi",
    "idna",
]

# 数据文件
datas = [
    ("templates", "templates"),
    ("static", "static"),
    (".env", "."),
]

datas += collect_data_files("jinja2")
datas += collect_data_files("docx")

a = Analysis(
    ["desktop.py"],
    pathex=[BASE_DIR],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=["hakon_runtime_hook.py"],  # 启动时加载内置 .env
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "PIL",
        "scipy",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 单文件模式：所有东西打包进一个 HAKON.exe
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="HAKON",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="static/hakon_logo.ico",  # 深蓝色雪花图标
)
