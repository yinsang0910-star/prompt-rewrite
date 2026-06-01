"""Tests for individual rewrite strategies."""

from prompt_rewrite.core.types import (
    AnalysisResult,
    RewriteConfig,
    PromptCategory,
    ComplexityLevel,
    StrategyName,
)
from prompt_rewrite.strategies.role_enhancer import RoleEnhancer
from prompt_rewrite.strategies.structure_formatter import StructureFormatter
from prompt_rewrite.strategies.chain_of_thought import ChainOfThoughtInjector
from prompt_rewrite.strategies.constraint_injector import ConstraintInjector
from prompt_rewrite.strategies.output_formatter import OutputFormatter
from prompt_rewrite.strategies.example_formatter import ExampleFormatter
from prompt_rewrite.strategies.context_optimizer import ContextOptimizer


def _make_analysis(
    category=PromptCategory.UNKNOWN,
    complexity=ComplexityLevel.SIMPLE,
    language="en",
    has_examples=False,
    has_code=False,
    has_structured_output=False,
    raw_length=50,
    domains=None,
):
    return AnalysisResult(
        category=category,
        complexity=complexity,
        language=language,
        has_examples=has_examples,
        has_code=has_code,
        has_structured_output=has_structured_output,
        raw_length=raw_length,
        domains=domains or [],
    )


def _make_config(enabled_strategies=None):
    return RewriteConfig(
        enabled_strategies=enabled_strategies or [s for s in StrategyName],
        inject_chain_of_thought=True,
    )


class TestRoleEnhancer:
    def test_injects_role_for_code(self):
        s = RoleEnhancer()
        analysis = _make_analysis(category=PromptCategory.CODE, domains=["programming"])
        config = _make_config()
        result = s.apply("write a function", analysis, config)
        assert "<role>" in result
        assert "senior software engineer" in result

    def test_skips_existing_role(self):
        s = RoleEnhancer()
        analysis = _make_analysis()
        config = _make_config()
        result = s.apply("Act as a poet and write a haiku", analysis, config)
        assert result == "Act as a poet and write a haiku"

    def test_skips_conversation(self):
        s = RoleEnhancer()
        analysis = _make_analysis(category=PromptCategory.CONVERSATION)
        config = _make_config()
        assert s.should_apply(analysis, config) is False


class TestStructureFormatter:
    def test_wraps_in_instructions(self):
        s = StructureFormatter()
        analysis = _make_analysis()
        config = _make_config()
        result = s.apply("do something", analysis, config)
        assert "<instructions>" in result
        assert "do something" in result

    def test_skips_already_structured(self):
        s = StructureFormatter()
        analysis = _make_analysis()
        config = _make_config()
        result = s.apply("<task>\n<instruction>do X</instruction>\n</task>", analysis, config)
        # Should keep original since already structured
        assert result == "<task>\n<instruction>do X</instruction>\n</task>"


class TestChainOfThoughtInjector:
    def test_injects_cot_for_complex(self):
        s = ChainOfThoughtInjector()
        analysis = _make_analysis(
            complexity=ComplexityLevel.COMPLEX,
            category=PromptCategory.ANALYSIS,
        )
        config = _make_config()
        result = s.apply("analyze this", analysis, config)
        assert "<thinking>" in result

    def test_skips_simple(self):
        s = ChainOfThoughtInjector()
        analysis = _make_analysis(complexity=ComplexityLevel.SIMPLE)
        config = _make_config()
        assert s.should_apply(analysis, config) is False


class TestConstraintInjector:
    def test_injects_constraints(self):
        s = ConstraintInjector()
        analysis = _make_analysis(category=PromptCategory.CODE)
        config = _make_config()
        result = s.apply("write code", analysis, config)
        assert "<constraints>" in result

    def test_skips_existing_constraints(self):
        s = ConstraintInjector()
        analysis = _make_analysis()
        config = _make_config()
        result = s.apply("Do X\n<constraints>\nBe safe\n</constraints>", analysis, config)
        # Should not duplicate
        assert result.count("<constraints>") == 1


class TestOutputFormatter:
    def test_injects_output_format(self):
        s = OutputFormatter()
        analysis = _make_analysis(category=PromptCategory.CODE)
        config = _make_config()
        result = s.apply("write code", analysis, config)
        assert "<output_format>" in result


class TestExampleFormatter:
    def test_formats_examples(self):
        s = ExampleFormatter()
        analysis = _make_analysis(has_examples=True)
        config = _make_config()
        prompt = "Do X\nExample 1:\nInput: hello\nOutput: olleh"
        result = s.apply(prompt, analysis, config)
        # T3.13: Stronger assertion — example formatter should produce XML tags
        assert "<examples>" in result or "<input>" in result, \
            f"Expected XML tags in output, got: {result[:200]}"

    def test_skips_no_examples(self):
        s = ExampleFormatter()
        analysis = _make_analysis(has_examples=False)
        config = _make_config()
        assert s.should_apply(analysis, config) is False


class TestContextOptimizer:
    def test_skips_short_prompts(self):
        s = ContextOptimizer()
        analysis = _make_analysis(raw_length=100)
        config = _make_config()
        assert s.should_apply(analysis, config) is False

    def test_processes_long_prompts(self):
        s = ContextOptimizer()
        analysis = _make_analysis(raw_length=1000)
        config = _make_config()
        assert s.should_apply(analysis, config) is True


class TestStrategyRegistry:
    def test_all_strategies_registered(self):
        from prompt_rewrite.strategies.base import StrategyRegistry
        assert len(StrategyRegistry._strategies) >= 6

    def test_get_all_sorted(self):
        from prompt_rewrite.strategies.base import StrategyRegistry
        all_s = StrategyRegistry.get_all()
        priorities = [s.priority for s in all_s]
        assert priorities == sorted(priorities)

from prompt_rewrite.strategies.refusal_guard import RefusalGuard


class TestRefusalGuard:
    def test_injects_boundaries_for_code(self):
        s = RefusalGuard()
        analysis = _make_analysis(category=PromptCategory.CODE)
        config = _make_config()
        result = s.apply("write a function", analysis, config)
        assert "<boundaries>" in result
        assert "不要生成" in result or "Do not generate" in result

    def test_skips_existing_boundaries(self):
        s = RefusalGuard()
        analysis = _make_analysis()
        config = _make_config()
        prompt = "Do something\n<boundaries>\nBe safe\n</boundaries>"
        result = s.apply(prompt, analysis, config)
        assert result.count("<boundaries>") == 1

    def test_skips_conversation(self):
        s = RefusalGuard()
        analysis = _make_analysis(category=PromptCategory.CONVERSATION)
        config = _make_config()
        assert s.should_apply(analysis, config) is False

    def test_uses_zh_for_chinese(self):
        s = RefusalGuard()
        analysis = _make_analysis(language="zh", category=PromptCategory.CODE)
        config = _make_config()
        result = s.apply("write code", analysis, config)
        assert "不要生成" in result or "拒绝" in result

    def test_professional_disclaimer_for_qa(self):
        s = RefusalGuard()
        analysis = _make_analysis(category=PromptCategory.QA)
        config = _make_config()
        result = s.apply("what is medicine", analysis, config)
        assert "持牌" in result or "licensed" in result
