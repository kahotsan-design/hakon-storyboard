"""DeepSeek LLM 客户端封装。

使用 OpenAI 兼容协议调用 DeepSeek，统一管理调用、JSON 解析、错误处理。
包含自动重试机制和增强的 JSON 修复能力。
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from openai import OpenAI

from app.config import config

logger = logging.getLogger("ai-storyboard.llm")


class LLMError(RuntimeError):
    """LLM 调用或解析失败。"""


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.DEEPSEEK_API_KEY:
            raise LLMError("DEEPSEEK_API_KEY 未配置，无法调用 LLM。")
        _client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            timeout=config.TIMEOUT,
        )
    return _client


# 最大重试次数
MAX_RETRIES = 2
# 重试间隔（秒）
RETRY_DELAY = 2


def chat(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """调用 LLM 返回纯文本响应。带自动重试。"""
    client = get_client()

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            resp = client.chat.completions.create(
                model=config.DEEPSEEK_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature if temperature is not None else config.TEMPERATURE,
                max_tokens=max_tokens or config.MAX_TOKENS,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            # 判断是否值得重试
            should_retry = any(keyword in error_msg for keyword in [
                "timeout", "timed out", "connection", "reset",
                "429", "rate limit", "overloaded", "502", "503", "504",
                "internal server error", "temporary",
            ])
            if should_retry and attempt < MAX_RETRIES:
                wait = RETRY_DELAY * (attempt + 1)
                logger.warning(f"LLM 调用失败（第{attempt+1}次），{wait}s 后重试: {e}")
                time.sleep(wait)
                continue
            # 不可重试的错误或重试次数用完
            raise LLMError(f"LLM 调用失败：{e}") from e

    raise LLMError(f"LLM 调用失败（重试{MAX_RETRIES}次后仍失败）：{last_error}")


def chat_json(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """调用 LLM 并解析为 JSON dict。

    包含自动重试：如果 JSON 解析失败，会自动重试最多 2 次。
    """
    last_error = None

    for attempt in range(MAX_RETRIES + 1):
        try:
            raw = chat(
                system_prompt,
                user_prompt,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return extract_json(raw)
        except LLMError as e:
            last_error = e
            error_str = str(e)
            # JSON 解析失败才重试（不是 API 调用失败，那个在 chat 里已重试过）
            if "JSON 解析失败" in error_str or "未找到 JSON" in error_str:
                if attempt < MAX_RETRIES:
                    wait = RETRY_DELAY * (attempt + 1)
                    logger.warning(
                        f"JSON 解析失败（第{attempt+1}次），{wait}s 后重试。"
                        f"错误: {error_str[:200]}"
                    )
                    time.sleep(wait)
                    # 重试时稍微调整 temperature 增加变化
                    retry_temp = (temperature or config.TEMPERATURE) + 0.05
                    continue
            # 其他错误直接抛出
            raise

    raise LLMError(f"JSON 解析失败（重试{MAX_RETRIES}次后仍失败）：{last_error}")


def extract_json(text: str) -> dict[str, Any]:
    """从模型输出中稳健地提取 JSON。

    多层修复策略：
    1. 提取 ```json 代码块或直接找 {}
    2. 尝试直接解析
    3. 修复未转义的引号（台词中的常见问题）
    4. 修复被截断的 JSON
    """
    # 1. 优先尝试 ```json ... ``` 代码块
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        candidate = m.group(1)
    else:
        # 2. 找第一个 { 到最后一个 }
        first = text.find("{")
        last = text.rfind("}")
        if first == -1:
            raise LLMError(f"响应中未找到 JSON：{text[:200]}")
        if last == -1 or last <= first:
            # JSON 被截断
            candidate = _repair_truncated_json(text[first:])
        else:
            candidate = text[first : last + 1]

    # 3. 尝试直接解析
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass

    # 4. 修复未转义的引号（台词中最常见的问题）
    fixed = _fix_unescaped_quotes(candidate)
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass

    # 5. 修复截断的 JSON
    repaired = _repair_truncated_json(candidate)
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass

    # 6. 最后再试修复+引号修复
    repaired_fixed = _fix_unescaped_quotes(repaired)
    try:
        return json.loads(repaired_fixed)
    except json.JSONDecodeError as e:
        raise LLMError(f"JSON 解析失败：{e}\n原始片段：{candidate[:300]}")


def _fix_unescaped_quotes(text: str) -> str:
    """修复 JSON 中未转义的双引号。

    LLM 经常在台词内容里直接写双引号而忘记转义，
    例如: "dialogue": 他说"你好"
    这会导致 JSON 解析失败。

    策略：逐字符扫描，识别字符串值内部的未转义引号并转义。
    """
    result = []
    i = 0
    in_string = False
    string_start = False

    while i < len(text):
        ch = text[i]

        if not in_string:
            result.append(ch)
            if ch == '"':
                in_string = True
                string_start = True
            i += 1
            continue

        # 在字符串内部
        if ch == "\\":
            # 转义字符，直接复制两个字符
            result.append(ch)
            if i + 1 < len(text):
                result.append(text[i + 1])
                i += 2
            else:
                i += 1
            continue

        if ch == '"':
            # 判断这个引号是字符串结束还是字符串内部的未转义引号
            # 看后面的字符：如果紧跟的是 : , } ] 或换行后的这些，认为是字符串结束
            # 否则认为是字符串内部的引号，需要转义
            rest = text[i + 1:].lstrip()
            if string_start and (rest.startswith(":") or rest.startswith(",") or
                                 rest.startswith("}") or rest.startswith("]")):
                # 字符串正常结束
                result.append(ch)
                in_string = False
                string_start = False
                i += 1
            elif not string_start:
                # 不太可能的情况
                result.append(ch)
                in_string = False
                i += 1
            else:
                # 字符串内部的引号，转义它
                result.append('\\"')
                i += 1
            continue

        result.append(ch)
        string_start = False  # 已经不是字符串的第一个字符了
        i += 1

    return "".join(result)


def _repair_truncated_json(text: str) -> str:
    """尝试修复被截断的 JSON 字符串。

    策略：补齐未闭合的括号/引号，截断到最后一个完整元素。
    """
    depth_brace = 0
    depth_bracket = 0
    in_string = False
    escape = False
    last_safe_pos = 0

    i = 0
    while i < len(text):
        ch = text[i]
        if escape:
            escape = False
            i += 1
            continue
        if ch == "\\":
            escape = True
            i += 1
            continue
        if ch == '"':
            in_string = not in_string
            i += 1
            continue
        if in_string:
            i += 1
            continue
        if ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace -= 1
            if depth_brace >= 0:
                last_safe_pos = i + 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket -= 1
        i += 1

    result = text[:last_safe_pos] if last_safe_pos > 0 else text

    # 如果还在字符串内，闭合字符串
    if in_string:
        result += '"'

    # 重新计算深度
    depth_brace = 0
    depth_bracket = 0
    in_string = False
    escape = False
    for ch in result:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth_brace += 1
        elif ch == "}":
            depth_brace -= 1
        elif ch == "[":
            depth_bracket += 1
        elif ch == "]":
            depth_bracket -= 1

    # 处理末尾可能的逗号
    result = result.rstrip()
    if result.endswith(","):
        result = result[:-1]

    result += "]" * depth_bracket + "}" * depth_brace
    return result
