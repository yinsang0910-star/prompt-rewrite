"""
Rewrite Pipeline — orchestrates strategy application via Dynamic Workflows.

Each prompt category has its own curated workflow (defined in workflow_defs.py),
replacing the old static "one priority order fits all" approach.

How Dynamic Workflows work:
1. Analyze the prompt → category + complexity + features
2. Look up the workflow definition for that category
3. Execute steps in the workflow ORDER (not priority order)
4. Each step can have conditions (e.g. "only for complex prompts")
5. Conversation prompts get an EMPTY workflow → no transformation
6. Optional LLM enhancement: better analysis + deeper rewriting + quality validation
"""

from __future__ import annotations

import dataclasses
import difflib
import logging
from typing import Optional

from prompt_rewrite.core.types import (
    AnalysisResult,
    RewriteConfig,
    RewriteResult,
    StrategyName,
    PromptCategory,
    LLMConfig,
)
from prompt_rewrite.core.analyzer import PromptAnalyzer
from prompt_rewrite.strategies.base import StrategyRegistry
from prompt_rewrite.core.workflow_defs import (
    get_workflow,
    evaluate_condition,
)

logger = logging.getLogger(__name__)

# Lazily import LLM modules (they're optional)
_llm_available = False
try:
    from prompt_rewrite.llm.llm_analyzer import LLMAnalyzer
    from prompt_rewrite.llm.llm_strategies import LLMRewriter, LLMValidator
    _llm_available = True
except ImportError:
    LLMAnalyzer = None
    LLMRewriter = None
    LLMValidator = None


class RewritePipeline:
    """Orchestrates the full prompt rewrite process using Dynamic Workflows.

    Usage:
        pipeline = RewritePipeline()
        result = pipeline.run("Write a Python function to sort a list")

    LLM enhancement (optional, requires DeepSeek API key):
        config = RewriteConfig(
            llm_config=LLMConfig(api_key="sk-..."),
            llm_enhance_analysis=True,
            llm_enhance_rewrite=True,
        )
        pipeline = RewritePipeline(config=config)
        result = pipeline.run("帮我分析一下这个架构方案")
    """

    def __init__(
        self,
        config: Optional[RewriteConfig] = None,
        analyzer: Optional[PromptAnalyzer] = None,
    ):
        self.config = config or RewriteConfig()
        self.analyzer = analyzer or PromptAnalyzer()
        self._last_llm_raw: Optional[dict] = None

    @property
    def last_llm_raw_response(self) -> Optional[dict]:
        return self._last_llm_raw

    def run(self, prompt: str) -> RewriteResult:
        """Execute the rewrite using Dynamic Workflow routing.

        Flow:
        1. Rule-based analysis → category + complexity + features
        2. [Optional] LLM-enhanced analysis → refine classification
        3. Look up the workflow for that category
        4. Execute each step in WORKFLOW ORDER
        5. [Optional] LLM deep rewrite → semantic-level optimization
        6. [Optional] LLM validation → quality score + feedback
        7. Return the result
        """
        # Early exit for empty prompts
        if not prompt or not prompt.strip():
            empty = RewriteResult(
                original=prompt, rewritten=prompt,
                analysis=self.analyzer.analyze(prompt),
                config=self.config, applied_strategies=[], workflow_steps=[],
            )
            return self._maybe_llm_validate(prompt, prompt, empty)

        # Step 1: Rule-based analysis
        analysis = self.analyzer.analyze(prompt)

        # Step 2: Optional LLM-enhanced analysis
        if self.config.llm_enhance_analysis and _llm_available and LLMAnalyzer:
            llm_analyzer = LLMAnalyzer(self.config.llm_config)
            if llm_analyzer.should_enhance(analysis):
                enhanced = llm_analyzer.enhance(prompt, analysis)
                if enhanced.category != PromptCategory.UNKNOWN or enhanced.domains:
                    logger.info(
                        f"LLM enhanced analysis: {analysis.category.value} → {enhanced.category.value}, "
                        f"domains: {analysis.domains} → {enhanced.domains}"
                    )
                    analysis = enhanced

        # Step 3: Look up workflow
        workflow = get_workflow(analysis.category)
        applied: list[StrategyName] = []
        executed_steps: list[StrategyName] = []

        if not workflow.steps:
            # Empty workflow (e.g. CONVERSATION) — skip
            base_result = RewriteResult(
                original=prompt, rewritten=prompt,
                analysis=analysis, config=self.config,
                applied_strategies=[], workflow_steps=[],
                workflow_name=analysis.category.value,
            )
            return self._maybe_llm_rewrite(prompt, base_result)

        # Step 4: Execute workflow steps in order
        current = prompt
        for step in workflow.steps:
            if not evaluate_condition(step.condition, analysis):
                continue
            if step.strategy not in self.config.enabled_strategies:
                continue

            executed_steps.append(step.strategy)
            try:
                strategy = StrategyRegistry.get(step.strategy)
                transformed = strategy.apply(current, analysis, self.config)
                if transformed != current:
                    applied.append(step.strategy)
                    current = transformed
            except Exception as e:
                # Distinguish programming errors from recoverable failures
                if isinstance(e, (TypeError, AttributeError, KeyError)):
                    logger.error(
                        f"Workflow step '{step.strategy.value}' bug: {e}. "
                        f"This is likely a code issue, not a data issue."
                    )
                else:
                    logger.warning(f"Workflow step '{step.strategy.value}' failed: {e}.")

        base_result = RewriteResult(
            original=prompt, rewritten=current,
            analysis=analysis, config=self.config,
            applied_strategies=applied,
            workflow_steps=executed_steps,
            workflow_name=analysis.category.value,
            diff_summary=self._generate_diff(prompt, current) if current != prompt else "",
        )

        # Step 5: Optional LLM deep rewrite
        result = self._maybe_llm_rewrite(prompt, base_result)

        # Step 6: Optional LLM validation (validate the FINAL rewritten version)
        result = self._maybe_llm_validate(prompt, result.rewritten, result)

        return result

    def _maybe_llm_rewrite(self, original: str, base: RewriteResult) -> RewriteResult:
        """当启用时，用 DeepSeek 从原始 prompt 做语义级深度重写（非模板方式）。"""
        if not (self.config.llm_enhance_rewrite and _llm_available and LLMRewriter):
            return base

        rewriter = LLMRewriter(self.config.llm_config)
        # 传入原始 prompt，而非 base.rewritten，让 LLM 从零开始重写
        llm_rewritten = rewriter.apply(original, base.analysis, self.config)
        # 保存 LLM 原始返回数据
        if rewriter.client and rewriter.client.last_raw:
            self._last_llm_raw = rewriter.client.last_raw
        else:
            self._last_llm_raw = None

        # Determine the real error
        error = rewriter.last_error or ""
        if not error and llm_rewritten == original:
            error = "LLM returned identical content (may have failed silently)"
        elif not error and llm_rewritten.startswith("[LLM"):
            error = llm_rewritten
        base._llm_error = error
        
        if error:
            return base  # LLM 失败

        return RewriteResult(
            original=original,
            rewritten=llm_rewritten,
            analysis=base.analysis,
            config=self.config,
            applied_strategies=base.applied_strategies + [StrategyName.LLM_REWRITE],
            workflow_steps=base.workflow_steps,
            workflow_name=base.workflow_name,
            diff_summary=self._generate_diff(original, llm_rewritten),
        )

    def _maybe_llm_validate(self, original: str, rewritten: str, result: RewriteResult) -> RewriteResult:
        """当启用时，用 DeepSeek 校验重写质量。"""
        if not (self.config.llm_validate and _llm_available and LLMValidator):
            return result

        validator = LLMValidator(self.config.llm_config)
        score = validator.validate(original, rewritten)
        # 将评分信息附加到 result（扩展属性）
        result._llm_score = score.get("score", 0)
        result._llm_feedback = score.get("suggestion", "")
        return result

    def run_with_strategies(self, prompt: str, strategy_names: list[StrategyName]) -> RewriteResult:
        """Run the pipeline with a custom strategy list (legacy mode)."""
        config = dataclasses.replace(self.config, enabled_strategies=strategy_names)
        pipeline = RewritePipeline(config=config, analyzer=self.analyzer)
        return pipeline.run(prompt)

    def _generate_diff(self, original: str, rewritten: str) -> str:
        if original == rewritten:
            return "无变更"
        original_lines = original.splitlines()
        rewritten_lines = rewritten.splitlines()
        diff = difflib.unified_diff(original_lines, rewritten_lines, fromfile="原始", tofile="重写后", lineterm="")
        diff_text = "\n".join(list(diff)[:100])
        added = sum(1 for line in rewritten_lines if line not in original_lines)
        removed = sum(1 for line in original_lines if line not in rewritten_lines)
        return (
            f"📊 变更统计: +{added} / -{removed} 行\n"
            f"📐 原始: {len(original)} 字符 → 重写后: {len(rewritten)} 字符\n"
            f"───\n{diff_text}"
        )
