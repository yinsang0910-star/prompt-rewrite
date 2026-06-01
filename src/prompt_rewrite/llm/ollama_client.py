"""
Ollama 本地模型客户端 — 零成本，无需 API Key。
"""

from __future__ import annotations

import json

import requests

from prompt_rewrite.core.types import LLMConfig
from prompt_rewrite.llm.base_client import BaseLLMClient

_OLLAMA_DEFAULT_BASE = "http://localhost:11434"

RECOMMENDED_MODELS = {
    "qwen2.5:7b": "Qwen 2.5 7B — 中文能力强，推荐",
    "llama3.1:8b": "Llama 3.1 8B — Meta 开源，综合能力好",
    "deepseek-coder-v2:16b": "DeepSeek Coder V2 16B — 代码专用",
    "mistral:7b": "Mistral 7B — 快速，英文能力强",
    "gemma2:9b": "Gemma 2 9B — Google 开源",
}


class OllamaClient(BaseLLMClient):
    """Ollama 本地模型客户端。

    前提：本地运行 Ollama 服务 (https://ollama.com)
    安装: curl -fsSL https://ollama.com/install.sh | sh
    拉取模型: ollama pull qwen2.5:7b

    用法:
        client = OllamaClient(LLMConfig(
            provider="ollama",
            model="qwen2.5:7b",
            # api_key 不需要
        ))
        reply = client.chat("Hello")
    """

    def __init__(self, config: LLMConfig):
        super().__init__(config)
        base = config.api_base or _OLLAMA_DEFAULT_BASE
        self._url = f"{base.rstrip('/')}/api/chat"

    def _call(self, messages: list[dict]) -> str:

        # Extract system prompt (Ollama uses top-level system field)
        system_prompt = ""
        user_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_prompt = msg["content"]
            else:
                user_messages.append(msg)

        def do_request():
            body: dict = {
                "model": self.config.model or "qwen2.5:7b",
                "messages": user_messages,
                "stream": False,
                "options": {
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                },
            }
            if system_prompt:
                body["system"] = system_prompt

            resp = requests.post(
                self._url,
                json=body,
                timeout=self.config.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            # Ollama response: {"model": "...", "message": {"role": "assistant", "content": "..."}}
            self.last_raw = {
                "model": data.get("model", self.config.model),
                "usage": {
                    "prompt_tokens": data.get("prompt_eval_count", 0),
                    "completion_tokens": data.get("eval_count", 0),
                    "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                },
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
                "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
                "finish_reason": "stop",
                "raw_preview": json.dumps(data, ensure_ascii=False, indent=2)[:2000],
            }

            message = data.get("message", {})
            return message.get("content", "").strip()

        return self._retry_loop(do_request, label="Ollama")
