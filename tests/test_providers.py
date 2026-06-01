# -*- coding: utf-8 -*-
"""Tests for multi-LLM provider support — factory, clients, provider switching."""

from unittest.mock import patch, MagicMock
import requests
import pytest

from prompt_rewrite.core.types import LLMConfig
from prompt_rewrite.llm.base_client import BaseLLMClient, create_llm_client
from prompt_rewrite.llm.deepseek_client import DeepSeekClient
from prompt_rewrite.llm.openai_client import OpenAIClient
from prompt_rewrite.llm.claude_client import ClaudeClient
from prompt_rewrite.llm.ollama_client import OllamaClient


# ── Factory Tests ────────────────────────────────────────────────────────────

class TestFactory:
    def test_default_provider_is_deepseek(self):
        config = LLMConfig(api_key="test")
        client = create_llm_client(config)
        assert isinstance(client, DeepSeekClient)

    def test_openai_provider(self):
        config = LLMConfig(provider="openai", api_key="sk-test")
        client = create_llm_client(config)
        assert isinstance(client, OpenAIClient)

    def test_claude_provider(self):
        config = LLMConfig(provider="claude", api_key="sk-ant-test")
        client = create_llm_client(config)
        assert isinstance(client, ClaudeClient)

    def test_ollama_provider(self):
        config = LLMConfig(provider="ollama")
        client = create_llm_client(config)
        assert isinstance(client, OllamaClient)

    def test_deepseek_explicit(self):
        config = LLMConfig(provider="deepseek", api_key="test")
        client = create_llm_client(config)
        assert isinstance(client, DeepSeekClient)

    def test_all_clients_are_base_client(self):
        for provider in ("deepseek", "openai", "claude", "ollama"):
            config = LLMConfig(provider=provider, api_key="test")
            client = create_llm_client(config)
            assert isinstance(client, BaseLLMClient), f"{provider} not a BaseLLMClient"


# ── LLMConfig Tests ──────────────────────────────────────────────────────────

class TestLLMConfig:
    def test_provider_field(self):
        config = LLMConfig(provider="openai")
        assert config.provider == "openai"

    def test_ollama_enabled_without_key(self):
        config = LLMConfig(provider="ollama")
        assert config.enabled is True

    def test_deepseek_needs_key(self):
        config = LLMConfig(provider="deepseek")
        assert config.enabled is False

    def test_default_api_base_empty(self):
        config = LLMConfig()
        assert config.api_base == ""


# ── OpenAI Client Tests ──────────────────────────────────────────────────────

class TestOpenAIClient:
    def test_chat_returns_content(self):
        config = LLMConfig(provider="openai", api_key="sk-test")
        client = OpenAIClient(config)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "model": "gpt-4o",
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            "choices": [{"message": {"content": "Hello from GPT!"}, "finish_reason": "stop"}],
        }
        with patch("requests.post", return_value=mock_resp):
            result = client.chat("test")
        assert result == "Hello from GPT!"

    def test_default_url(self):
        config = LLMConfig(provider="openai", api_key="sk-test")
        client = OpenAIClient(config)
        assert "api.openai.com" in client._url

    def test_custom_base_url(self):
        config = LLMConfig(provider="openai", api_key="sk-test", api_base="https://my-proxy.com/v1")
        client = OpenAIClient(config)
        assert "my-proxy.com" in client._url


# ── Claude Client Tests ──────────────────────────────────────────────────────

class TestClaudeClient:
    def test_chat_returns_content(self):
        config = LLMConfig(provider="claude", api_key="sk-ant-test")
        client = ClaudeClient(config)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "model": "claude-sonnet-4-20250514",
            "content": [{"type": "text", "text": "Hello from Claude!"}],
            "usage": {"input_tokens": 10, "output_tokens": 20},
            "stop_reason": "end_turn",
        }
        with patch("requests.post", return_value=mock_resp):
            result = client.chat("test")
        assert result == "Hello from Claude!"

    def test_system_prompt_extracted(self):
        config = LLMConfig(provider="claude", api_key="sk-ant-test")
        client = ClaudeClient(config)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "model": "test",
            "content": [{"type": "text", "text": "ok"}],
            "usage": {"input_tokens": 1, "output_tokens": 1},
            "stop_reason": "end_turn",
        }
        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.chat("hello", system="You are helpful")
        call_body = mock_post.call_args.kwargs.get("json", {})
        assert call_body.get("system") == "You are helpful"
        # system should NOT be in messages
        for msg in call_body.get("messages", []):
            assert msg["role"] != "system"

    def test_anthropic_headers(self):
        config = LLMConfig(provider="claude", api_key="sk-ant-test")
        client = ClaudeClient(config)
        assert "x-api-key" in client._headers
        assert client._headers["x-api-key"] == "sk-ant-test"
        assert client._headers["anthropic-version"] == "2023-06-01"


# ── Ollama Client Tests ──────────────────────────────────────────────────────

class TestOllamaClient:
    def test_chat_returns_content(self):
        config = LLMConfig(provider="ollama", model="qwen2.5:7b")
        client = OllamaClient(config)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "model": "qwen2.5:7b",
            "message": {"role": "assistant", "content": "Hello from Ollama!"},
            "prompt_eval_count": 10,
            "eval_count": 20,
        }
        with patch("requests.post", return_value=mock_resp):
            result = client.chat("test")
        assert result == "Hello from Ollama!"

    def test_no_api_key_needed(self):
        config = LLMConfig(provider="ollama")
        assert config.enabled is True

    def test_default_url(self):
        config = LLMConfig(provider="ollama")
        client = OllamaClient(config)
        assert "localhost:11434" in client._url

    def test_system_prompt_extracted(self):
        config = LLMConfig(provider="ollama")
        client = OllamaClient(config)
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "model": "test",
            "message": {"role": "assistant", "content": "ok"},
        }
        with patch("requests.post", return_value=mock_resp) as mock_post:
            client.chat("hello", system="Be helpful")
        call_body = mock_post.call_args.kwargs.get("json", {})
        assert call_body.get("system") == "Be helpful"


# ── Integration: Pipeline with different providers ────────────────────────────

class TestPipelineProviderIntegration:
    def test_pipeline_with_openai_config(self):
        from prompt_rewrite import RewritePipeline, RewriteConfig, LLMConfig
        config = RewriteConfig(
            llm_config=LLMConfig(provider="openai", api_key="sk-test"),
            llm_enhance_rewrite=True,
        )
        pipeline = RewritePipeline(config=config)
        # Should not crash even without actual API call
        assert pipeline.config.llm_config.provider == "openai"

    def test_pipeline_with_ollama_config(self):
        from prompt_rewrite import RewritePipeline, RewriteConfig, LLMConfig
        config = RewriteConfig(
            llm_config=LLMConfig(provider="ollama", model="qwen2.5:7b"),
            llm_enhance_rewrite=True,
        )
        pipeline = RewritePipeline(config=config)
        assert pipeline.config.llm_config.provider == "ollama"
