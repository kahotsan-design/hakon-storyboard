# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置 - 桌面窗口应用。

打包后是一个文件夹（dist/HAKON/），内含 HAKON.exe 和 _internal/。
整个文件夹复制给别人即可使用。

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
    "clr",  # webview Windows 需要的 .NET bridge
    "pythoncom",
    "win32com",
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
    runtime_hooks=[],
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
    console=False,  # 不显示控制台窗口！
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以设为 "static/hakon_logo.ico"
)
