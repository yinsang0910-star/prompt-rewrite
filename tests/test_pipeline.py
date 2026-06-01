"""Tests for the RewritePipeline."""

from prompt_rewrite.core.pipeline import RewritePipeline
from prompt_rewrite.core.types import RewriteConfig, StrategyName, PromptCategory, ComplexityLevel
from prompt_rewrite.core.workflow_defs import get_workflow, WORKFLOWS, evaluate_condition


class TestPipeline:
    def test_pipeline_runs(self):
        pipeline = RewritePipeline()
        result = pipeline.run("Write a Python function")
        assert result.original == "Write a Python function"
        assert len(result.rewritten) > 0
        assert len(result.applied_strategies) > 0

    def test_pipeline_code_prompt(self):
        pipeline = RewritePipeline()
        r = pipeline.run("Write a Python function to sort a list of dictionaries by a key")
        assert r.analysis.category == PromptCategory.CODE
        assert "<role>" in r.rewritten
        assert "<instructions>" in r.rewritten

    def test_pipeline_qa_prompt(self):
        pipeline = RewritePipeline()
        r = pipeline.run("What is the meaning of life?")
        assert r.analysis.category == PromptCategory.QA

    def test_pipeline_conversation_no_role(self):
        pipeline = RewritePipeline()
        r = pipeline.run("Hello!")
        assert StrategyName.ROLE_ENHANCER not in r.applied_strategies

    def test_pipeline_with_custom_config(self):
        config = RewriteConfig(
            enabled_strategies=[StrategyName.STRUCTURE_FORMATTER],
            inject_chain_of_thought=False,
        )
        pipeline = RewritePipeline(config=config)
        r = pipeline.run("Write a Python function")
        assert len(r.applied_strategies) == 1
        assert r.applied_strategies[0] == StrategyName.STRUCTURE_FORMATTER

    def test_pipeline_empty_prompt(self):
        pipeline = RewritePipeline()
        r = pipeline.run("")
        assert r.rewritten == ""
        assert r.applied_strategies == []

    def test_pipeline_zh_prompt(self):
        pipeline = RewritePipeline()
        r = pipeline.run("请帮我写一个 Python 函数，用于排序字典列表")
        assert r.analysis.language == "zh"
        assert len(r.rewritten) > 0

    def test_pipeline_long_complex_prompt(self):
        """Test that complex prompts trigger more strategies."""
        pipeline = RewritePipeline()
        prompt = (
            "Analyze the trade-offs between REST and GraphQL for a real-time dashboard. "
            "Consider:\n"
            "1. Data fetching efficiency\n"
            "2. Caching strategy\n"
            "3. Team expertise\n"
            "4. Tooling\n"
            "5. Performance requirements\n\n"
            "Evaluate: speed, cost, scalability, and developer experience.\n"
            "Then provide a step-by-step recommendation with reasoning."
        )
        r = pipeline.run(prompt)
        # Complex analysis prompts should trigger CoT
        # Note: depends on analyzer classification
        assert len(r.applied_strategies) >= 3

    def test_rewrite_idempotent(self):
        """Running the pipeline twice on the same prompt should be stable."""
        pipeline = RewritePipeline()
        prompt = "Write a Python function to sort a list"
        r1 = pipeline.run(prompt)
        r2 = pipeline.run(prompt)
        # Analysis results should be identical
        assert r1.analysis.category == r2.analysis.category
        assert r1.analysis.complexity == r2.analysis.complexity


class TestDynamicWorkflows:
    """Tests for Dynamic Workflow routing."""

    def test_code_workflow_has_role_engineer(self):
        pipeline = RewritePipeline()
        r = pipeline.run("Write a Python function")
        assert r.workflow_name == "code"
        assert StrategyName.ROLE_ENHANCER in r.applied_strategies
        assert "senior software engineer" in r.rewritten

    def test_conversation_workflow_empty(self):
        """Conversation prompts should have empty workflow = no transformation."""
        pipeline = RewritePipeline()
        r = pipeline.run("Hello, how are you today?")
        assert r.workflow_name == "conversation"
        assert r.applied_strategies == []
        assert r.rewritten == r.original

    def test_qa_workflow_has_role(self):
        """QA prompts get a role (domain-based if detected, fallback to QA)."""
        pipeline = RewritePipeline()
        # Pure QA without domain keywords should get QA role
        r = pipeline.run("What is the meaning of life?")
        assert r.workflow_name == "qa"
        assert "<role>" in r.rewritten
        assert "knowledgeable assistant" in r.rewritten

    def test_analysis_workflow_has_analysis_role(self):
        pipeline = RewritePipeline()
        r = pipeline.run("Analyze the pros and cons of X")
        assert r.workflow_name == "analysis"

    def test_every_category_has_workflow(self):
        """All PromptCategory enum values should have a workflow defined."""
        for cat in PromptCategory:
            assert cat in WORKFLOWS, f"Missing workflow for {cat.value}"

    def test_get_workflow_returns_definition(self):
        """get_workflow should return the correct workflow definition."""
        wf1 = get_workflow(PromptCategory.CODE)
        wf2 = get_workflow(PromptCategory.CODE)
        assert wf1 is wf2  # Same object (read-only, no copy needed)
        assert len(wf1.steps) > 0
        assert wf1.category == PromptCategory.CODE

    def test_workflow_steps_have_valid_strategies(self):
        """All workflow steps should reference registered strategies."""
        from prompt_rewrite.strategies.base import StrategyRegistry
        for cat, wf in WORKFLOWS.items():
            for step in wf.steps:
                assert step.strategy in StrategyRegistry._strategies, \
                    f"{cat.value}: {step.strategy.value} not registered"

    def test_condition_evaluator_simple(self):
        """Test evaluate_condition helper."""
        analysis = type('obj', (object,), {'complexity': ComplexityLevel.MEDIUM, 'has_code': True})
        assert evaluate_condition(None, analysis) is True
        assert evaluate_condition("complexity >= medium", analysis) is True
        assert evaluate_condition("complexity >= complex", analysis) is False

    def test_conversation_no_role_from_strategy(self):
        """Even if role is enabled in config, conversation should skip it."""
        from prompt_rewrite.strategies.role_enhancer import RoleEnhancer
        strategy = RoleEnhancer()
        analysis = type('obj', (object,), {
            'category': PromptCategory.CONVERSATION,
            'domains': [],
            'complexity': ComplexityLevel.SIMPLE,
        })
        config = RewriteConfig(enabled_strategies=[s for s in StrategyName])
        assert strategy.should_apply(analysis, config) is False
