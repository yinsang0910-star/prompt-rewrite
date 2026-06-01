# -*- coding: utf-8 -*-
"""Shared test fixtures for Prompt Rewrite System."""

from typing import Optional
import pytest
from prompt_rewrite.core.types import (
    AnalysisResult, RewriteConfig, RewriteResult, PromptCategory,
    ComplexityLevel, StrategyName, LLMConfig,
)
from prompt_rewrite.core.analyzer import PromptAnalyzer
from prompt_rewrite.core.pipeline import RewritePipeline


@pytest.fixture
def analyzer():
    """Shared PromptAnalyzer instance."""
    return PromptAnalyzer()


@pytest.fixture
def pipeline():
    """Default RewritePipeline instance."""
    return RewritePipeline()


@pytest.fixture
def config():
    """Default RewriteConfig."""
    return RewriteConfig()


@pytest.fixture
def llm_config():
    """LLM config with test API key."""
    return LLMConfig(api_key="test-key")


def make_analysis(
    category: PromptCategory = PromptCategory.UNKNOWN,
    complexity: ComplexityLevel = ComplexityLevel.MEDIUM,
    language: str = "en",
    has_examples: bool = False,
    has_code: bool = False,
    has_structured_output: bool = False,
    estimated_tokens: int = 100,
    domains: Optional[list] = None,
    key_entities: Optional[list] = None,
    raw_length: int = 200,
) -> AnalysisResult:
    """Helper to create AnalysisResult with sensible defaults."""
    return AnalysisResult(
        category=category,
        complexity=complexity,
        language=language,
        has_examples=has_examples,
        has_code=has_code,
        has_structured_output=has_structured_output,
        estimated_tokens=estimated_tokens,
        domains=domains or [],
        key_entities=key_entities or [],
        raw_length=raw_length,
    )
