# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller 打包配置。

打包命令（在项目根目录运行）：
  pyinstaller hakon_desktop.spec

生成 dist/HAKON/ 目录，包含：
- HAKON.exe（主程序）
- _internal/（依赖和资源）
"""

import os
import sys
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# 项目根目录
BASE_DIR = os.path.abspath(".")

# 自动收集所有子模块（解决 PyInstaller 静态分析遗漏的问题）
hiddenimports = []
hiddenimports += collect_submodules("uvicorn")
hiddenimports += collect_submodules("fastapi")
hiddenimports += collect_submodules("starlette")
hiddenimports += collect_submodules("pydantic")
hiddenimports += collect_submodules("jinja2")
hiddenimports += collect_submodules("openai")
hiddenimports += collect_submodules("sse_starlette")
hiddenimports += collect_submodules("docx")

# 额外确保关键模块
hiddenimports += [
    "app",
    "app.agents",
    "app.agents.script_understanding_agent",
    "app.agents.storyboard_agent",
    "app.schemas",
    "app.schemas.models",
    "app.services",
    "app.services.export",
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
    "websockets",
    "email_validator",
]

# 收集所有数据文件
datas = [
    # 前端模板和静态文件
    ("templates", "templates"),
    ("static", "static"),
    # .env 文件（包含 API key）
    (".env", "."),
]

# 收集 jinja2 / docx 等包的数据文件
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
    # 调试期间显示控制台，发布时改为 console=False
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以加 icon="static/hakon_logo.ico"
)
