"""
Base LLM Client — abstract interface for all LLM providers.

All providers implement the same interface so the pipeline can use any of them
without knowing the underlying API differences.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Optional

import requests

from prompt_rewrite.core.types import LLMConfig


class BaseLLMClient(ABC):
    """Abstract base class for LLM clients.

    Subclasses must implement `_call()` to handle provider-specific API formats.
    The base class provides retry logic, JSON parsing, and error handling.
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self.last_raw: Optional[dict] = None

    def chat(self, prompt: str, system: str = "") -> str:
        """Single-turn chat. Returns text reply."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self._call(messages)

    def chat_with_context(self, messages: list[dict]) -> str:
        """Multi-turn chat with message history."""
        return self._call(messages)

    def chat_json(self, prompt: str, system: str = "") -> dict:
        """Call LLM and parse JSON response."""
        text = self.chat(prompt, system=system)
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}

    @abstractmethod
    def _call(self, messages: list[dict]) -> str:
        """Provider-specific API call. Must handle its own request format."""
        ...

    def _retry_loop(self, fn, label: str = "LLM") -> str:
        """Generic retry loop with exponential backoff for Timeout / 429 / 5xx."""
        self.last_raw = None
        last_err = None

        for attempt in range(1 + self.config.max_retries):
            try:
                return fn()

            except requests.exceptions.Timeout:
                last_err = f"[{label} Timeout after {self.config.timeout}s]"
                if attempt < self.config.max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return last_err

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                if status == 429:
                    last_err = f"[{label} Rate Limited (429)]"
                    if attempt < self.config.max_retries:
                        retry_after = int(e.response.headers.get("Retry-After", 2 ** attempt))
                        time.sleep(min(retry_after, 30))
                        continue
                elif status >= 500 and attempt < self.config.max_retries:
                    last_err = f"[{label} HTTP {status}]"
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return f"[{label} HTTP {status}]"

            except Exception as e:
                return f"[{label} Error: {e}]"

        return last_err or f"[{label} Error: max retries exceeded]"

    def _save_raw(self, data: dict) -> None:
        """Save raw API response for debugging."""
        self.last_raw = {
            "model": data.get("model", self.config.model),
            "usage": data.get("usage", {}),
            "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
            "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
            "total_tokens": data.get("usage", {}).get("total_tokens", 0),
            "finish_reason": data.get("choices", [{}])[0].get("finish_reason", ""),
            "raw_preview": json.dumps(data, ensure_ascii=False, indent=2)[:2000],
        }


def create_llm_client(config: LLMConfig) -> BaseLLMClient:
    """Factory: create the right LLM client based on config.provider.

    Supported providers:
    - "deepseek" (default) → DeepSeekClient (OpenAI-compatible)
    - "openai" → OpenAIClient
    - "claude" → ClaudeClient
    - "ollama" → OllamaClient
    """
    provider = getattr(config, "provider", "deepseek")

    if provider == "openai":
        from prompt_rewrite.llm.openai_client import OpenAIClient
        return OpenAIClient(config)
    elif provider == "claude":
        from prompt_rewrite.llm.claude_client import ClaudeClient
        return ClaudeClient(config)
    elif provider == "ollama":
        from prompt_rewrite.llm.ollama_client import OllamaClient
        return OllamaClient(config)
    else:
        # Default: DeepSeek (OpenAI-compatible)
        from prompt_rewrite.llm.deepseek_client import DeepSeekClient
        return DeepSeekClient(config)
