"""DeepSeek LLM 客户端封装。

使用 OpenAI 兼容协议调用 DeepSeek，统一管理调用、JSON 解析、错误处理。
"""
from __future__ import annotations

import json
import re
from typing import Any

from openai import OpenAI

from app.config import config


class LLMError(RuntimeError):
    """LLM 调用或解析失败。"""


_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.DEEPSEEK_API_KEY:
            raise LLMError("DEEPSEEK_API_KEY 未配置，无法调用 LLM。请在 .env 中设置��")
        _client = OpenAI(
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            timeout=config.TIMEOUT,
        )
    return _client


def chat(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> str:
    """调用 LLM 返回纯文本响应。"""
    client = get_client()
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
        raise LLMError(f"LLM 调用失败：{e}") from e


def chat_json(
    system_prompt: str,
    user_prompt: str,
    *,
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """调用 LLM 并解析为 JSON dict。

    会从响应中提取首个 ```json 代码块或直接解析整段文本。
    """
    raw = chat(system_prompt, user_prompt, temperature=temperature, max_tokens=max_tokens)
    return extract_json(raw)


def extract_json(text: str) -> dict[str, Any]:
    """从模型输出中稳健地提取 JSON。

    对被 max_tokens 截断的 JSON 做容错修复尝试。
    """
    # 1. 优先尝试 ```json ... ``` 代码块
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        candidate = m.group(1)
    else:
        # 2. 退而求其次：找第一个 { 到最后一个 }
        first = text.find("{")
        last = text.rfind("}")
        if first == -1:
            raise LLMError(f"响应中未找到 JSON：{text[:200]}")
        if last == -1 or last <= first:
            # JSON 被截断（没有闭合 }），尝试修复
            candidate = _repair_truncated_json(text[first:])
        else:
            candidate = text[first : last + 1]

    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        # 尝试修复后解析
        repaired = _repair_truncated_json(candidate)
        try:
            return json.loads(repaired)
        except json.JSONDecodeError as e:
            raise LLMError(f"JSON 解析失败：{e}\n原始片段：{candidate[:300]}")


def _repair_truncated_json(text: str) -> str:
    """尝试修复被截断的 JSON 字符串。

    策略：补齐未闭合的括号/引号，截断到最后一个完整元素。
    """
    # 追踪括号深度和字符串状态
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

    # 补齐括号
    # 重新计算深度（基于截断后的文本）
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
