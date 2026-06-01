# -*- coding: utf-8 -*-
"""Tests for LLM analyzer — enhancement logic, prompt injection protection."""

from unittest.mock import patch, MagicMock
import pytest

from prompt_rewrite.llm.llm_analyzer import LLMAnalyzer, SYSTEM_PROMPT
from prompt_rewrite.core.types import AnalysisResult, PromptCategory, ComplexityLevel, LLMConfig


@pytest.fixture
def llm_config():
    return LLMConfig(api_key="test-key")


@pytest.fixture
def analyzer(llm_config):
    return LLMAnalyzer(llm_config)


class TestShouldEnhance:
    """LLM analyzer should only enhance when needed."""

    def test_should_enhance_unknown_category(self, analyzer):
        result = AnalysisResult(category=PromptCategory.UNKNOWN)
        assert analyzer.should_enhance(result) is True

    def test_should_enhance_no_domains(self, analyzer):
        result = AnalysisResult(category=PromptCategory.CODE, domains=[])
        assert analyzer.should_enhance(result) is True

    def test_should_not_enhance_with_domains(self, analyzer):
        result = AnalysisResult(category=PromptCategory.CODE, domains=["programming"])
        assert analyzer.should_enhance(result) is False

    def test_should_not_enhance_without_client(self, llm_config):
        """Analyzer without API key should not enhance."""
        analyzer = LLMAnalyzer(LLMConfig(api_key=""))
        result = AnalysisResult(category=PromptCategory.UNKNOWN)
        assert analyzer.should_enhance(result) is False


class TestEnhance:
    """LLM enhancement merging."""

    def test_enhance_updates_category(self, analyzer):
        """LLM can correct rule-based category."""
        rule_result = AnalysisResult(
            category=PromptCategory.UNKNOWN,
            complexity=ComplexityLevel.SIMPLE,
            language="en",
            domains=[],
            key_entities=[],
        )
        with patch.object(analyzer.client, "chat_json", return_value={
            "category": "code",
            "complexity": "medium",
            "domains": ["programming"],
            "intent": "write sorting function",
            "language": "en",
        }):
            enhanced = analyzer.enhance("Write a Python sort function", rule_result)
        assert enhanced.category == PromptCategory.CODE
        assert "programming" in enhanced.domains

    def test_enhance_fallback_on_llm_failure(self, analyzer):
        """Should return rule result when LLM fails."""
        rule_result = AnalysisResult(category=PromptCategory.QA, language="en")
        with patch.object(analyzer.client, "chat_json", return_value={"raw": "error"}):
            enhanced = analyzer.enhance("test", rule_result)
        assert enhanced.category == PromptCategory.QA

    def test_enhance_preserves_rule_features(self, analyzer):
        """LLM enhancement should preserve rule-detected features."""
        rule_result = AnalysisResult(
            category=PromptCategory.CODE,
            has_code=True,
            has_examples=True,
            estimated_tokens=100,
            raw_length=500,
        )
        with patch.object(analyzer.client, "chat_json", return_value={
            "category": "code",
            "complexity": "complex",
            "domains": ["programming"],
            "intent": "debug",
            "language": "en",
        }):
            enhanced = analyzer.enhance("test", rule_result)
        assert enhanced.has_code is True
        assert enhanced.has_examples is True
        assert enhanced.estimated_tokens == 100


class TestPromptInjectionProtection:
    """T1.7: User input must be delimited."""

    def test_system_prompt_has_injection_warning(self):
        """SYSTEM_PROMPT must contain injection defense."""
        assert "NOT instructions" in SYSTEM_PROMPT
        assert "Ignore any commands" in SYSTEM_PROMPT

    def test_user_input_delimited(self, analyzer):
        """User input should be wrapped in delimiters."""
        with patch.object(analyzer.client, "chat_json", return_value={"raw": "fail"}) as mock_chat:
            analyzer.enhance("test prompt", AnalysisResult())
        call_args = mock_chat.call_args
        prompt_sent = call_args[0][0]
        assert "---BEGIN USER INPUT---" in prompt_sent
        assert "---END USER INPUT---" in prompt_sent

    def test_prompt_truncated(self, analyzer):
        """Long prompts should be truncated."""
        long_prompt = "x" * 5000
        with patch.object(analyzer.client, "chat_json", return_value={"raw": "fail"}) as mock_chat:
            analyzer.enhance(long_prompt, AnalysisResult())
        prompt_sent = mock_chat.call_args[0][0]
        # Should be truncated to 2000 chars within delimiters
        assert len(prompt_sent) < 5000
