"""
Constraint Injector — adds quality and safety constraints.

Based on structured constraint injection approach:
  - Quality guidelines
  - Safety boundaries
  - Output formatting rules

This strategy injects appropriate constraints based on prompt category.
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

# ── Constraint libraries ─────────────────────────────────────────────────────

# Quality constraints by category
QUALITY_CONSTRAINTS: dict[str, list[str]] = {
    "general": [
        "Be precise and accurate. If you're uncertain, acknowledge the uncertainty.",
        "Base your responses on verified information. Clearly distinguish facts from interpretations.",
    ],
    "code": [
        "Write clean, well-documented code with proper error handling.",
        "Consider edge cases, performance implications, and security best practices.",
        "Use established patterns and libraries rather than reinventing the wheel.",
        "Include type hints and meaningful variable names.",
    ],
    "writing": [
        "Preserve the author's original voice and intent.",
        "Use clear, concise language appropriate for the target audience.",
        "Maintain logical flow and coherent structure.",
    ],
    "analysis": [
        "Support all claims with evidence or reasoning.",
        "Acknowledge alternative viewpoints and limitations of your analysis.",
        "Distinguish between established facts and inferences.",
    ],
    "academic": [
        "Use precise, formal language appropriate for academic discourse.",
        "Cite sources where applicable and distinguish established knowledge from speculation.",
        "Acknowledge methodological limitations and alternative interpretations.",
    ],
}

# Safety / refusal constraints
SAFETY_CONSTRAINTS = [
    "Do not provide instructions for illegal activities, harm, or dangerous acts.",
    "Do not generate deceptive or misleading content intended to cause harm.",
    "Respect intellectual property rights. Do not reproduce copyrighted material at length.",
    "Do not provide medical, legal, or financial advice that could cause harm if acted upon.",
    "Be helpful while maintaining appropriate boundaries. Refuse requests that could cause harm.",
    "Do not generate hate speech, harassment, or content that discriminates against protected groups.",
]

# Formatting constraints (positive guidance preferred)
FORMATTING_CONSTRAINTS = [
    "Use clear section breaks and logical organization.",
    "Prefer positive instructions over negative ones (tell what to do, not what not to do).",
    "Use examples to illustrate complex points rather than abstract descriptions.",
]


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
        """Select appropriate constraints based on category."""
        selected: list[str] = []

        # Category-specific quality constraints
        cat = analysis.category.value
        qc = QUALITY_CONSTRAINTS.get(cat, QUALITY_CONSTRAINTS["general"])
        selected.extend(qc)

        # Safety constraints for all prompts
        if self._needs_safety(analysis):
            selected.extend(SAFETY_CONSTRAINTS[:3])  # First 3 safety rules

        # Formatting constraints for longer prompts
        if analysis.raw_length > 500:
            selected.extend(FORMATTING_CONSTRAINTS[:2])

        return selected

    def _needs_safety(self, analysis: AnalysisResult) -> bool:
        """Determine if safety constraints should be added."""
        # Always add safety for unknown/unclear categories
        if analysis.category in (PromptCategory.UNKNOWN, PromptCategory.INSTRUCTION):
            return True
        return False

    def _has_constraints(self, prompt: str) -> bool:
        """Check if constraints section already exists."""
        patterns = [
            r"<constraints>",
            r"<safety>",
            r"<guidelines>",
            r"(constraints|guidelines|rules)\s*[:：]",
        ]
        return any(re.search(p, prompt, re.IGNORECASE) for p in patterns)
