"""
DeepSeek API 客户端 — 轻量封装，零外部依赖（只用标准库 + requests）。
"""

from __future__ import annotations

import json
import time
from typing import Optional

import requests

from prompt_rewrite.core.types import LLMConfig


class DeepSeekClient:
    """DeepSeek Chat API 客户端。

    用法:
        client = DeepSeekClient(LLMConfig(api_key="sk-..."))
        reply = client.chat("你是谁？")
        reply = client.chat_with_context([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello"},
        ])
    """

    def __init__(self, config: LLMConfig):
        self.config = config
        self._url = f"{config.api_base.rstrip('/')}/chat/completions"
        self._headers = {
            "Authorization": f"Bearer {config.api_key}",
            "Content-Type": "application/json",
        }
        self.last_raw: Optional[dict] = None  # 最近一次 API 调用的完整返回

    def chat(self, prompt: str, system: str = "") -> str:
        """单轮对话，返回文本回复。"""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return self._call(messages)

    def chat_with_context(self, messages: list[dict]) -> str:
        """多轮对话，messages 格式: [{"role":"user"/"assistant","content":"..."}]"""
        return self._call(messages)

    def _call(self, messages: list[dict]) -> str:
        """调用 DeepSeek Chat API，含自动重试（Timeout / 429 / 5xx）。"""
        self.last_raw = None  # T1.8: 每次调用前清空旧数据
        last_err = None

        for attempt in range(1 + self.config.max_retries):
            try:
                resp = requests.post(
                    self._url,
                    headers=self._headers,
                    json={
                        "model": self.config.model,
                        "messages": messages,
                        "temperature": self.config.temperature,
                        "max_tokens": self.config.max_tokens,
                        "stream": False,
                    },
                    timeout=self.config.timeout,
                )
                resp.raise_for_status()
                data = resp.json()
                # 保存完整原始返回
                self.last_raw = {
                    "model": data.get("model", self.config.model),
                    "usage": data.get("usage", {}),
                    "prompt_tokens": data.get("usage", {}).get("prompt_tokens", 0),
                    "completion_tokens": data.get("usage", {}).get("completion_tokens", 0),
                    "total_tokens": data.get("usage", {}).get("total_tokens", 0),
                    "finish_reason": data.get("choices", [{}])[0].get("finish_reason", ""),
                    "raw_preview": json.dumps(data, ensure_ascii=False, indent=2)[:2000],
                }
                return data["choices"][0]["message"]["content"].strip()

            except requests.exceptions.Timeout:
                last_err = f"[LLM Timeout after {self.config.timeout}s]"
                # T1.5: Timeout 也进入重试循环，指数退避
                if attempt < self.config.max_retries:
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return last_err

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code
                if status == 429:
                    # T1.6: 429 Rate Limit 重试，读取 Retry-After
                    last_err = f"[LLM Rate Limited (429)]"
                    if attempt < self.config.max_retries:
                        retry_after = int(e.response.headers.get("Retry-After", 2 ** attempt))
                        time.sleep(min(retry_after, 30))
                        continue
                elif status >= 500 and attempt < self.config.max_retries:
                    # 5xx 服务端错误重试
                    last_err = f"[LLM HTTP {status}]"
                    time.sleep(min(2 ** attempt, 8))
                    continue
                return f"[LLM HTTP {status}]"

            except Exception as e:
                return f"[LLM Error: {e}]"

        return last_err or "[LLM Error: max retries exceeded]"

    def chat_json(self, prompt: str, system: str = "") -> dict:
        """调用 LLM 并解析 JSON 返回。"""
        text = self.chat(prompt, system=system)
        # 尝试从 ```json ... ``` 中提取
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"raw": text}
