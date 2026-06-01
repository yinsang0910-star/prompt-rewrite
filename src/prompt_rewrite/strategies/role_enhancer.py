"""
Role Enhancer — injects persona/role based on prompt domain and category.

Uses role-based prompting:
  identity + domain expertise + behavioral guidelines

Roles are loaded from YAML templates (templates/roles.yaml) with i18n support.
User can override by placing roles.yaml at ~/.prompt_rewrite/templates/
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
from prompt_rewrite.templates.loader import load_role


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

# Available role keys for domain matching
_KNOWN_ROLES = {
    "programming", "data_science", "writing", "business", "academic",
    "finance", "education", "creative", "law", "health", "qa", "code", "analysis",
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

    def apply(self, prompt: str, analysis: AnalysisResult, config: RewriteConfig, **kwargs: object) -> str:
        # Determine best role key
        role_key = self._select_role(analysis)
        lang = analysis.language if analysis.language in ("zh", "ja") else "en"

        # Load from YAML templates (with fallback chain)
        role_text = load_role(role_key, lang)
        if not role_text:
            role_text = load_role("default", lang)

        # Check if prompt already has a role definition
        if self._has_role(prompt):
            return prompt  # Don't override existing role

        # Wrap in role tag
        role_section = f"<role>\n{role_text}\n</role>"

        return f"{role_section}\n\n{prompt}"

    def _select_role(self, analysis: AnalysisResult) -> str:
        """Select the most appropriate role template."""
        # Priority 1: detected domains that match known role keys
        for domain in analysis.domains:
            if domain in _KNOWN_ROLES:
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
