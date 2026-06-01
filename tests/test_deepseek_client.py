# -*- coding: utf-8 -*-
"""Tests for DeepSeek client — retry logic, error handling, thread safety."""

from unittest.mock import patch, MagicMock
import requests
import pytest

from prompt_rewrite.llm.deepseek_client import DeepSeekClient
from prompt_rewrite.core.types import LLMConfig


@pytest.fixture
def config():
    return LLMConfig(api_key="test-key", max_retries=2, timeout=5)


@pytest.fixture
def client(config):
    return DeepSeekClient(config)


def _mock_ok_response(content="Hello!"):
    """Create a mock successful API response."""
    mock = MagicMock()
    mock.raise_for_status.return_value = None
    mock.json.return_value = {
        "model": "test",
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        "choices": [{"message": {"content": content}, "finish_reason": "stop"}],
    }
    return mock


class TestRetryLogic:
    """T1.5/T1.6: Timeout and 429 retry."""

    def test_timeout_retries(self, client, config):
        """Timeout should retry max_retries times."""
        with patch("requests.post", side_effect=requests.exceptions.Timeout()) as mock_post:
            result = client.chat("test")
        assert "[LLM Timeout" in result
        assert mock_post.call_count == config.max_retries + 1

    def test_429_retries_with_retry_after(self, client, config):
        """429 should retry and read Retry-After header."""
        mock_resp = MagicMock()
        mock_resp.status_code = 429
        mock_resp.headers = {"Retry-After": "1"}
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        with patch("requests.post", return_value=mock_resp) as mock_post, patch("time.sleep"):
            result = client.chat("test")
        assert "429" in result
        assert mock_post.call_count == config.max_retries + 1

    def test_5xx_retries(self, client, config):
        """5xx should retry."""
        mock_resp = MagicMock()
        mock_resp.status_code = 503
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        with patch("requests.post", return_value=mock_resp) as mock_post, patch("time.sleep"):
            result = client.chat("test")
        assert "503" in result
        assert mock_post.call_count == config.max_retries + 1

    def test_4xx_does_not_retry(self, client):
        """4xx (except 429) should NOT retry."""
        mock_resp = MagicMock()
        mock_resp.status_code = 400
        mock_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_resp)
        with patch("requests.post", return_value=mock_resp) as mock_post:
            result = client.chat("test")
        assert "400" in result
        assert mock_post.call_count == 1  # No retry


class TestLastRaw:
    """T1.8: last_raw lifecycle."""

    def test_cleared_before_call(self, client):
        """last_raw should be None before each call."""
        client.last_raw = {"stale": "data"}
        with patch("requests.post", side_effect=requests.exceptions.Timeout()):
            client.chat("test")
        assert client.last_raw is None

    def test_saved_on_success(self, client):
        """last_raw should be populated on successful call."""
        with patch("requests.post", return_value=_mock_ok_response()):
            client.chat("test")
        assert client.last_raw is not None
        assert client.last_raw["total_tokens"] == 30


class TestNormalFlow:
    """Happy path."""

    def test_chat_returns_content(self, client):
        with patch("requests.post", return_value=_mock_ok_response("Hi there!")):
            result = client.chat("hello")
        assert result == "Hi there!"

    def test_chat_json_parses(self, client):
        with patch("requests.post", return_value=_mock_ok_response('{"score": 8}')):
            result = client.chat_json("test")
        assert result == {"score": 8}

    def test_chat_json_handles_non_json(self, client):
        with patch("requests.post", return_value=_mock_ok_response("not json")):
            result = client.chat_json("test")
        assert result == {"raw": "not json"}

    def test_chat_json_extracts_from_code_block(self, client):
        content = '```json\n{"key": "value"}\n```'
        with patch("requests.post", return_value=_mock_ok_response(content)):
            result = client.chat_json("test")
        assert result == {"key": "value"}

    def test_system_prompt_included(self, client):
        """System prompt should be added as first message."""
        with patch("requests.post", return_value=_mock_ok_response()) as mock_post:
            client.chat("hello", system="You are helpful")
        call_args = mock_post.call_args
        messages = call_args.kwargs.get("json", call_args[1] if len(call_args) > 1 else {}).get("messages", [])
        if not messages:
            messages = call_args[1].get("messages", []) if len(call_args) > 1 else []
        # Verify system message exists
        assert any(m.get("role") == "system" for m in messages)


class TestThreadSafety:
    """T2.12: No shared session — uses requests.post directly."""

    def test_no_session_attribute(self, client):
        """Client should NOT have a shared _session."""
        assert not hasattr(client, "_session")

    def test_concurrent_calls_safe(self, client):
        """Multiple concurrent calls should not interfere."""
        import threading
        results = []
        errors = []

        def call_it(text):
            try:
                with patch("requests.post", return_value=_mock_ok_response(f"reply-{text}")):
                    r = client.chat(text)
                results.append(r)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=call_it, args=(f"t{i}",)) for i in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(errors) == 0
        assert len(results) == 5
