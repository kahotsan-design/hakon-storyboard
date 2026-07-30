"""全局配置：DeepSeek API 与服务参数。"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv


def _find_env_file() -> Path | None:
    """查找 .env 文件，兼容 PyInstaller 打包环境。

    查找顺序:
    1. 当前工作目录（用户自定义 .env）
    2. exe 所在目录（桌面应用场景）
    3. _MEIPASS 临时目录（打包时内置的 .env）
    4. 项目根目录（开发环境）
    """
    candidates = []
    
    # 当前工作目录
    candidates.append(Path.cwd() / ".env")
    
    # PyInstaller 打包环境
    if getattr(sys, "frozen", False):
        # exe 所在目录
        candidates.append(Path(sys.executable).resolve().parent / ".env")
        # _MEIPASS 临时解压目录（打包时内置的 .env）
        if hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / ".env")
    else:
        # 开发环境：项目根目录
        candidates.append(Path(__file__).resolve().parent.parent / ".env")
    
    for path in candidates:
        if path.exists():
            return path
    return None


# 加载 .env
_env_file = _find_env_file()
if _env_file:
    load_dotenv(_env_file)
else:
    load_dotenv()  # fallback to default behavior


class Config:
    # DeepSeek API（OpenAI 兼容协议）
    # API Key 来源优先级:
    #   1. 环境变量 DEEPSEEK_API_KEY（PyInstaller runtime hook 注入）
    #   2. .env 文件
    #   3. HAKON_API_KEY 环境变量（构建时注入的默认值）
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "") or os.getenv("HAKON_API_KEY", "")
    DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # 服务
    PORT = int(os.getenv("PORT", "8000"))
    HOST = os.getenv("HOST", "0.0.0.0")

    # LLM 调用参数
    TEMPERATURE = 0.8          # 偏创作，略高
    MAX_TOKENS = 8192          # 专业模式输出长，需要大窗口
    TIMEOUT = 180              # 单次请求超时（秒）

    @classmethod
    def validate(cls) -> list[str]:
        """返回缺失配置的告警列表，空列表表示配置完整。"""
        warnings = []
        if not cls.DEEPSEEK_API_KEY:
            warnings.append("未配置 DEEPSEEK_API_KEY，LLM 调用将失败。请在 .env 中设置。")
        return warnings


config = Config()
