"""
Constraint Injector — adds quality and safety constraints.

Constraints are loaded from YAML templates (templates/constraints.yaml) with i18n.
User can override by placing constraints.yaml at ~/.prompt_rewrite/templates/
"""

from __future__ import annotations

import re
from typing import ClassVar

from prompt_rewrite.core.types import (
    AnalysisResult,
    RewriteConfig,
    StrategyName,
    PromptCategory,
)
from prompt_rewrite.strategies.base import RewriteStrategy
from prompt_rewrite.templates.loader import (
    load_constraints,
    load_safety_constraints,
    load_formatting_constraints,
)


def _pick_lang(analysis: AnalysisResult) -> str:
    """Return the best language code for template selection."""
    if analysis.language in ("zh", "ja"):
        return analysis.language
    return "en"


class ConstraintInjector(RewriteStrategy):
    """Injects quality, safety, and formatting constraints.

    Adds a <constraints> section that mirrors the constitutional
    safety/principles layer.
    """

    name: ClassVar[StrategyName] = StrategyName.CONSTRAINT_INJECTOR
    priority: ClassVar[int] = 30  # After role, before CoT

    def apply(
        self,
        prompt: str,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> str:
        # Don't duplicate if constraints already present
        if self._has_constraints(prompt):
            return prompt

        constraints = self._select_constraints(analysis)
        if not constraints:
            return prompt

        constraint_text = "\n".join(f"- {c}" for c in constraints)
        constraint_section = self._wrap_tag(constraint_text, "constraints")

        return f"{prompt}\n\n{constraint_section}"

    def _select_constraints(self, analysis: AnalysisResult) -> list[str]:
        """Select appropriate constraints based on category and language."""
        lang = _pick_lang(analysis)
        selected: list[str] = []

        # Category-specific quality constraints from YAML
        cat = analysis.category.value
        qc = load_constraints(cat, lang)
        selected.extend(qc)

        # Safety constraints for all prompts
        if self._needs_safety(analysis):
            safety = load_safety_constraints(lang)
            selected.extend(safety[:3])

        # Formatting constraints for longer prompts
        if analysis.raw_length > 500:
            fmt = load_formatting_constraints(lang)
            selected.extend(fmt[:2])

        return selected

    def _needs_safety(self, analysis: AnalysisResult) -> bool:
        """Determine if safety constraints should be added.

        T2.11: Extended to cover CODE (may generate harmful code) and
        CREATIVE (may generate inappropriate content) categories.
        """
        safety_categories = (
            PromptCategory.UNKNOWN,
            PromptCategory.INSTRUCTION,
            PromptCategory.CODE,
            PromptCategory.CREATIVE,
        )
        return analysis.category in safety_categories

    def _has_constraints(self, prompt: str) -> bool:
        """Check if constraints section already exists."""
        patterns = [
            r"<constraints>",
            r"<safety>",
            r"<guidelines>",
            r"(constraints|guidelines|rules)\s*[:：]",
        ]
        return any(re.search(p, prompt, re.IGNORECASE) for p in patterns)
