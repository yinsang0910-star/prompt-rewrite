"""
OpenAI API 客户端 — 兼容 GPT-4o / GPT-4o-mini 等模型。
"""

from __future__ import annotations

import requests

from prompt_rewrite.core.types import LLMConfig
from prompt_rewrite.llm.base_client import BaseLLMClient

# Default OpenAI endpoints
_OPENAI_API_BASE = "https://api.openai.com/v1"

# Recommended models per use case
RECOMMENDED_MODELS = {
    "gpt-4o": "GPT-4o — 最强综合能力",
    "gpt-4o-mini": "GPT-4o Mini — 性价比之选",
    "gpt-4-turbo": "GPT-4 Turbo — 长上下文",
    "gpt-3.5-turbo": "GPT-3.5 Turbo — 最快最便宜",
}


class OpenAIClient(BaseLLMClient):
    """OpenAI Chat Completions API 客户端。

    用法:
        client = OpenAIClient(LLMConfig(
            provider="openai",
            api_key="sk-...",
            model="gpt-4o",
        ))
        reply = client.chat("Hello")
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        base = config.api_base or _OPENAI_API_BASE
        self._url = f"{base.rstrip('/')}/chat/completions"
        self._headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }

    def _call(self, messages: list[dict]) -> str:

        def do_request():
            resp = requests.post(
                self._url,
                headers=self._headers,
                json={
                    "model": self.config.model or "gpt-4o-mini",
                    "messages": messages,
                    "temperature": self.config.temperature,
                    "max_tokens": self.config.max_tokens,
                    "stream": False,
                },
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
            data = resp.json()
            self._save_raw(data)
            return data["choices"][0]["message"]["content"].strip()

        return self._retry_loop(do_request, label="OpenAI")
