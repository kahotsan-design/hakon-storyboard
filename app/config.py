"""全局配置：DeepSeek API 与服务参数。"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # DeepSeek API（OpenAI 兼容协议）
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
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
