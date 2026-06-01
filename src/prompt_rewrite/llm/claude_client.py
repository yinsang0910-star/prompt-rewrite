"""
Claude API 客户端 — 接入 Anthropic Claude 模型。
"""

from __future__ import annotations

import json

import requests

from prompt_rewrite.core.types import LLMConfig
from prompt_rewrite.llm.base_client import BaseLLMClient

_ANTHROPIC_API_BASE = "https://api.anthropic.com"

RECOMMENDED_MODELS = {
    "claude-sonnet-4-20250514": "Claude Sonnet 4 — 平衡性能与速度",
    "claude-haiku-3-5-20241022": "Claude Haiku 3.5 — 最快最便宜",
    "claude-opus-4-20250514": "Claude Opus 4 — 最强推理能力",
}


class ClaudeClient(BaseLLMClient):
    """Anthropic Claude API 客户端。

    API 格式与 OpenAI 不同：
    - 使用 x-api-key header
    - system prompt 是顶级字段，不在 messages 中
    - 响应格式: {"content": [{"type": "text", "text": "..."}]}

    用法:
        client = ClaudeClient(LLMConfig(
            provider="claude",
            api_key="sk-ant-...",
            model="claude-sonnet-4-20250514",
        ))
        reply = client.chat("Hello")
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        base = config.api_base or _ANTHROPIC_API_BASE
        self._url = f"{base.rstrip('/')}/v1/messages"
        self._headers = {
            "x-api-key": config.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

    def _call(self, messages: list[dict]) -> str:

        # Extract system prompt from messages (Anthropic uses top-level system field)
        system_prompt = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                user_messages.append(msg)

        def do_request():
            body: dict = {
                "model": self.config.model or "claude-sonnet-4-20250514",
                "max_tokens": self.config.max_tokens,
                "messages": user_messages,
                "stream": False,
            }
            if system_prompt:
                body["system"] = system_prompt

            resp = requests.post(
                self._url,
                headers=self._headers,
                json=body,
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            # Convert Anthropic response format to our standard format
            self.last_raw = {
                "model": data.get("model", self.config.model),
                "usage": data.get("usage", {}),
                "prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                "total_tokens": (
                    data.get("usage", {}).get("input_tokens", 0)
                    + data.get("usage", {}).get("output_tokens", 0)
                ),
                "finish_reason": data.get("stop_reason", ""),
                "raw_preview": json.dumps(data, ensure_ascii=False, indent=2)[:2000],
            }

            # Extract text from content blocks
            content = data.get("content", [])
            if content and isinstance(content[0], dict):
                return content[0].get("text", "").strip()
            return str(content).strip()

        return self._retry_loop(do_request, label="Claude")
