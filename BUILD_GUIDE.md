# HAKON 桌面应用打包指南

## 概述

HAKON 可以打包为 Windows 桌面应用（.exe），用户双击即可运行，无需安装 Python 或任何依赖。

## 方式一：本地构建（推荐）

### 前提条件
- Windows 10/11 (64位)
- 安装 [Python 3.11+](https://www.python.org/downloads/)（安装时勾选 "Add Python to PATH"）

### 构建步骤

1. 下载项目代码（ZIP 或 git clone）

2. 在项目根目录双击运行 `build_windows.bat`

3. 首次运行时会提示输入 DeepSeek API Key（如果没有 .env 文件）

4. 构建完成后，`dist\HAKON\` 目录就是完整的桌面应用：
   - `HAKON.exe` — 主程序，双击运行
   - `_internal\` — 依赖和资源文件（不要删除）

5. 把整个 `dist\HAKON\` 文件夹复制给用户即可

### 手动构建（如需自定义）

```cmd
pip install -r requirements.txt
pip install pyinstaller
pyinstaller hakon_desktop.spec --noconfirm
```

## 方式二：GitHub Actions 自动构建

项目已配置 GitHub Actions workflow（`.github/workflows/build-windows.yml`），可在 GitHub 的 Windows 环境中自动构建。

### 配置步骤

1. 在 GitHub 仓库页面进入 **Settings > Secrets and variables > Actions**
2. 点击 **New repository secret**，添加：
   - Name: `DEEPSEEK_API_KEY`
   - Value: 你的 DeepSeek API Key

### 触发构建

- **手动触发**：进入 **Actions** 页面 → 选择 "Build Windows Desktop App" → 点击 **Run workflow**
- **自动触发**：推送版本标签 `git tag v1.0 && git push origin v1.0`，会自动构建并创建 Release

### 下载构建产物

- 手动触发：在 Actions 页面找到对应的运行记录，下载 Artifacts
- 标签触发：在 Releases 页面下载 ZIP 文件

## 使用方法

1. 解压下载的 ZIP 文件
2. 双击 `HAKON.exe`
3. 浏览器会自动打开应用页面
4. 按 `Ctrl+C` 或关闭控制台窗口退出

## 常见问题

### 杀毒软件报警
PyInstaller 打包的 exe 可能被杀毒软件误报。可以：
- 将 `HAKON.exe` 添加到杀毒软件白名单
- 或使用方式二通过 GitHub Actions 构建（在可信环境中编译）

### 浏览器没有自动打开
如果浏览器没有自动打开，查看控制台输出的端口号，手动在浏览器输入 `http://127.0.0.1:端口号`

### API Key 相关
- API Key 打包在 exe 中，用户无需额外配置
- 如果需要更换 API Key，在 exe 同目录创建 `.env` 文件覆盖

## 文件说明

| 文件 | 说明 |
|------|------|
| `desktop.py` | 桌面应用入口，启动本地服务+打开浏览器 |
| `hakon_desktop.spec` | PyInstaller 打包配置 |
| `build_windows.bat` | Windows 一键构建脚本 |
| `requirements.txt` | Python 依赖列表 |
| `.env` | API 配置文件（不提交到 git） |
