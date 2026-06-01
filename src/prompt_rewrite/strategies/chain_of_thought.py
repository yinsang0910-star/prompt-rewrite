"""
Chain-of-Thought Injector — adds reasoning scaffolding for complex tasks.

Based on chain-of-thought prompting best practices:
  - The <thinking> tag for internal reasoning
  - Step-by-step before answering

This strategy:
1. Detects complex/code/analysis prompts
2. Injects instruction to think step-by-step before responding
3. Adds appropriate reasoning scaffolding based on task type
"""

from __future__ import annotations

import re
from typing import ClassVar

from prompt_rewrite.core.types import (
    AnalysisResult,
    RewriteConfig,
    StrategyName,
    PromptCategory,
    ComplexityLevel,
)
from prompt_rewrite.strategies.base import RewriteStrategy

# CoT instruction templates for different task types
COT_TEMPLATES: dict[str, str] = {
    "general": (
        "Work through this problem step by step:\n"
        "1. First, understand the problem and what's being asked.\n"
        "2. Break down the problem into sub-problems.\n"
        "3. Solve each sub-problem systematically.\n"
        "4. Verify your solution before finalizing.\n"
        "5. Present your final answer clearly."
    ),
    "code": (
        "Before writing any code, think through:\n"
        "1. Understand the requirements and expected behavior.\n"
        "2. Identify edge cases and error conditions.\n"
        "3. Choose the appropriate algorithm/data structure.\n"
        "4. Sketch the implementation plan.\n"
        "5. Write the code with proper error handling.\n"
        "6. Review the code for bugs and improvements."
    ),
    "analysis": (
        "Approach this analysis systematically:\n"
        "1. Identify the key question or hypothesis.\n"
        "2. Gather and organize the relevant information.\n"
        "3. Analyze each factor or component separately.\n"
        "4. Synthesize findings and identify patterns.\n"
        "5. Draw conclusions supported by evidence.\n"
        "6. Note any limitations or alternative explanations."
    ),
    "math": (
        "Solve this step by step:\n"
        "1. Restate the problem clearly.\n"
        "2. Identify the given information and what needs to be found.\n"
        "3. Choose the appropriate formulas or methods.\n"
        "4. Work through each step, showing your work.\n"
        "5. Verify the result with a sanity check.\n"
        "6. Present the final answer."
    ),
    "debate": (
        "Analyze this topic from multiple perspectives:\n"
        "1. Consider the strongest arguments for each position.\n"
        "2. Evaluate the evidence supporting each view.\n"
        "3. Identify underlying assumptions.\n"
        "4. Acknowledge areas of uncertainty.\n"
        "5. Synthesize a balanced conclusion."
    ),
    "comparison": (
        "Compare these items systematically:\n"
        "1. Identify the key dimensions for comparison.\n"
        "2. Evaluate each item on every dimension.\n"
        "3. Note strengths and weaknesses.\n"
        "4. Consider the context and use case.\n"
        "5. Provide a clear recommendation if appropriate."
    ),
}


class ChainOfThoughtInjector(RewriteStrategy):
    """Injects chain-of-thought reasoning instructions.

    Adds a <thinking> section before the main instructions,
    guiding the model to reason step-by-step before answering.
    """

    name: ClassVar[StrategyName] = StrategyName.CHAIN_OF_THOUGHT
    priority: ClassVar[int] = 45  # After structure and role, before output formatting

    def apply(
        self,
        prompt: str,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> str:
        # Check if CoT already present
        if self._has_cot(prompt):
            return prompt

        cot_template = self._select_cot_template(analysis)
        cot_section = self._wrap_tag(cot_template, "thinking")

        # Inject after role/instructions, before data input
        return f"{cot_section}\n\n{prompt}"

    def _select_cot_template(self, analysis: AnalysisResult) -> str:
        """Pick the most appropriate CoT template."""
        if PromptCategory.CODE in (analysis.category,):
            return COT_TEMPLATES["code"]
        if PromptCategory.ANALYSIS in (analysis.category,):
            return COT_TEMPLATES["analysis"]

        # Check for math/reasoning cues
        if any(kw in str(analysis.domains) for kw in ["math", "physics", "science"]):
            return COT_TEMPLATES["math"]

        # T2.10: Activate debate/comparison templates based on key entities
        entities_lower = " ".join(analysis.key_entities).lower()
        text_repr = entities_lower + " ".join(analysis.domains)
        if any(kw in text_repr for kw in ["debate", "versus", "vs", "argument", "立场"]):
            return COT_TEMPLATES["debate"]
        if any(kw in text_repr for kw in ["compare", "comparison", "versus", "vs", "对比"]):
            return COT_TEMPLATES["comparison"]

        # Default to general
        return COT_TEMPLATES["general"]

    def _has_cot(self, prompt: str) -> bool:
        """Detect if CoT instructions are already present."""
        patterns = [
            r"<thinking>",
            r"step.by.step",
            r"think (step|through)",
            r"chain.of.thought",
            r"一步一步",
            r"逐步思考",
        ]
        return any(re.search(p, prompt[:300], re.IGNORECASE) for p in patterns)

    def should_apply(
        self,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> bool:
        if not config.inject_chain_of_thought:
            return False
        if not super().should_apply(analysis, config):
            return False
        # Only apply to non-trivial prompts
        return analysis.complexity in (
            ComplexityLevel.MEDIUM,
            ComplexityLevel.COMPLEX,
        ) or analysis.category in (
            PromptCategory.CODE,
            PromptCategory.ANALYSIS,
        )
