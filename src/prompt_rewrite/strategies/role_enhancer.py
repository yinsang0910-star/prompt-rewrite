"""
Role Enhancer — injects persona/role based on prompt domain and category.

Uses role-based prompting:
  identity + domain expertise + behavioral guidelines

Roles are matched from a template library based on detected domains/category.
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

# ── Role templates ───────────────────────────────────────────────────────────

ROLE_TEMPLATES: dict[str, str] = {
    "default": (
        "You are an intelligent AI assistant. "
        "Provide accurate, helpful, and well-reasoned responses."
    ),
    "programming": (
        "You are a senior software engineer with deep expertise in software architecture, "
        "system design, and multiple programming languages. You write clean, maintainable, "
        "well-documented code and always consider edge cases, performance, and security."
    ),
    "data_science": (
        "You are an experienced data scientist and machine learning engineer. "
        "You excel at statistical analysis, model selection, experimental design, "
        "and communicating complex quantitative findings clearly."
    ),
    "writing": (
        "You are a professional editor and writer with a keen eye for clarity, "
        "style, and structure. You help refine prose while preserving the author's voice."
    ),
    "business": (
        "You are a strategic business consultant with expertise in product strategy, "
        "market analysis, and operational excellence. You provide actionable, "
        "data-driven recommendations."
    ),
    "academic": (
        "You are a rigorous academic researcher. You prioritize precision, "
        "evidence-based reasoning, proper citation, and methodological soundness. "
        "You clearly distinguish established facts from speculation."
    ),
    "finance": (
        "You are a financial analyst with expertise in markets, portfolio management, "
        "and quantitative finance. You ground all recommendations in data and "
        "clearly communicate risks and assumptions."
    ),
    "education": (
        "You are a patient and experienced educator. You explain concepts clearly, "
        "provide concrete examples, check for understanding, and adapt your "
        "explanations to the learner's level."
    ),
    "creative": (
        "You are a creative director with a strong sense of aesthetics and originality. "
        "You think outside the box while keeping practical constraints in mind."
    ),
    "law": (
        "You are a legal analyst. You provide carefully reasoned analysis, "
        "distinguish between settled law and open questions, and avoid "
        "providing specific legal advice or establishing attorney-client relationship."
    ),
    "health": (
        "You are a medical research analyst. You provide evidence-based health information, "
        "clearly distinguish between established medical knowledge and emerging research, "
        "and always include appropriate disclaimers. You never prescribe treatments."
    ),
    "qa": (
        "You are a knowledgeable assistant who provides clear, direct answers. "
        "You explain concepts at the appropriate level of detail, "
        "and you're honest when you don't know something."
    ),
    "code": (
        "You are an expert programmer. You write efficient, well-structured code "
        "with proper error handling. You explain your reasoning and consider "
        "tradeoffs in your implementations."
    ),
    "analysis": (
        "You are a analytical thinker who approaches problems systematically. "
        "You break down complex questions into components, reason step by step, "
        "and support your conclusions with evidence."
    ),
}

# Category → primary role key mapping
_CATEGORY_ROLE_MAP: dict[PromptCategory, str] = {
    PromptCategory.CODE: "programming",
    PromptCategory.WRITING: "writing",
    PromptCategory.ANALYSIS: "analysis",
    PromptCategory.CREATIVE: "creative",
    PromptCategory.EXTRACTION: "programming",
    PromptCategory.QA: "qa",
    PromptCategory.INSTRUCTION: "default",
    PromptCategory.CONVERSATION: "default",
    PromptCategory.UNKNOWN: "default",
}


class RoleEnhancer(RewriteStrategy):
    """Injects a domain-appropriate role definition at the start of the prompt.

    Pattern:
      <role>
      You are a [domain expert]...
      </role>
    """

    name: ClassVar[StrategyName] = StrategyName.ROLE_ENHANCER
    priority: ClassVar[int] = 25  # Early in pipeline

    def apply(
        self,
        prompt: str,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> str:
        # Determine best role
        role_key = self._select_role(analysis)
        role_text = ROLE_TEMPLATES.get(role_key, ROLE_TEMPLATES["default"])

        # Check if prompt already has a role definition
        if self._has_role(prompt):
            return prompt  # Don't override existing role

        # Wrap in role tag
        role_section = f"<role>\n{role_text}\n</role>"

        return f"{role_section}\n\n{prompt}"

    def _select_role(self, analysis: AnalysisResult) -> str:
        """Select the most appropriate role template."""
        # Priority 1: detected domains
        for domain in analysis.domains:
            if domain in ROLE_TEMPLATES:
                return domain

        # Priority 2: category-based mapping
        return _CATEGORY_ROLE_MAP.get(analysis.category, "default")

    def _has_role(self, prompt: str) -> bool:
        """Check if prompt already contains a role/persona definition."""
        patterns = [
            r"<role>",
            r"(act as|you are a|you are an|as a (senior|expert|professional))",
            r"(role.?play|扮演|作为|你是一个)",
        ]
        return any(re.search(p, prompt[:500], re.IGNORECASE) for p in patterns)

    def should_apply(
        self,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> bool:
        return (
            super().should_apply(analysis, config)
            and analysis.category != PromptCategory.CONVERSATION
        )
