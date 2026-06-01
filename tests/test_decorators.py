# -*- coding: utf-8 -*-
"""Tests for @optimize decorator."""

from prompt_rewrite import optimize
from prompt_rewrite.core.pipeline import RewritePipeline


class TestOptimizeDecorator:
    def test_bare_decorator(self):
        @optimize
        def my_prompt():
            return "Write a Python function to sort a list"
        result = my_prompt()
        assert isinstance(result, str)
        assert len(result) > len("Write a Python function to sort a list")

    def test_decorator_with_style(self):
        @optimize(style="system_prompt")
        def my_prompt():
            return "You are a helpful assistant"
        result = my_prompt()
        assert "[SYSTEM]" in result or len(result) > 0

    def test_preserves_function_name(self):
        @optimize
        def named_prompt():
            return "Explain recursion"
        assert named_prompt.__name__ == "named_prompt"

    def test_with_args(self):
        @optimize
        def dynamic_prompt(topic: str):
            return f"Write about {topic}"
        result = dynamic_prompt("quantum computing")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_pipeline_accessible(self):
        @optimize
        def my_prompt():
            return "test"
        assert hasattr(my_prompt, "_prs_pipeline")
        assert isinstance(my_prompt._prs_pipeline, RewritePipeline)
