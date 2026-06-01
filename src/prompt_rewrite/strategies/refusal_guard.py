# -*- coding: utf-8 -*-
"""
Refusal Guard — adds boundary protection instructions.

Injects safety boundaries so the model knows when to politely decline
requests that are illegal, harmful, or outside its capabilities.

Based on constitutional AI principles:
  - Clear scope boundaries
  - Polite refusal templates
  - Professional domain disclaimers
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

# ── Refusal guard templates (EN / ZH / JA) ──────────────────────────────

REFUSAL_TEMPLATES: dict[str, dict[str, str]] = {
    "general": {
        "en": (
            "If the request asks for content that is illegal, harmful, unethical, "
            "or outside your capabilities, politely decline and explain why you "
            "cannot fulfill the request. Offer alternative approaches when possible."
        ),
        "zh": (
            "如果请求涉及非法、有害、不道德的内容，或超出你的能力范围，"
            "请礼貌地拒绝并解释原因。在可能的情况下提供替代方案。"
        ),
        "ja": (
            "リクエストが違法、有害、非倫理的、または能力の範囲外の内容を"
            "求めている場合は、丁寧に断り、理由を説明してください。"
            "可能な場合は代替手段を提案してください。"
        ),
    },
    "code": {
        "en": (
            "Do not generate code that is designed to harm systems, steal data, "
            "exploit vulnerabilities, or bypass security measures. "
            "If asked for such code, explain the security risks and suggest "
            "secure alternatives."
        ),
        "zh": (
            "不要生成旨在损害系统、窃取数据、利用漏洞或绕过安全措施的代码。"
            "如果被要求编写此类代码，请解释安全风险并建议安全的替代方案。"
        ),
        "ja": (
            "システムに害を与えたり、データを窃取したり、脆弱性を悪用したり、"
            "セキュリティ対策を迂回したりするコードは生成しないでください。"
            "そのようなコードを要求された場合は、セキュリティリスクを説明し、"
            "安全な代替手段を提案してください。"
        ),
    },
    "professional": {
        "en": (
            "You are not a licensed professional. Do not provide specific medical, "
            "legal, or financial advice. Always recommend consulting a qualified "
            "professional for such matters."
        ),
        "zh": (
            "你不是持牌专业人士。不要提供具体的医疗、法律或财务建议。"
            "始终建议用户就此类事项咨询合格的专业人士。"
        ),
        "ja": (
            "あなたは資格を持つ専門家ではありません。具体的な医療、法的、"
            "または財務のアドバイスを提供しないでください。"
            "このような問題については、必ず資格を持つ専門家に相談するようお勧めください。"
        ),
    },
}

# Categories that need professional disclaimers
_PROFESSIONAL_CATEGORIES = {
    PromptCategory.UNKNOWN,
    PromptCategory.INSTRUCTION,
    PromptCategory.QA,
}


def _pick_lang(analysis: AnalysisResult) -> str:
    if analysis.language in ("zh", "ja"):
        return analysis.language
    return "en"


class RefusalGuard(RewriteStrategy):
    """Adds boundary protection and refusal instructions.

    Injects a <boundaries> section that tells the model
    when and how to decline inappropriate requests.
    """

    name: ClassVar[StrategyName] = StrategyName.REFUSAL_GUARD
    priority: ClassVar[int] = 35  # After constraints, before CoT

    def apply(self, prompt: str, analysis: AnalysisResult, config: RewriteConfig, **kwargs: object) -> str:
        if self._has_boundaries(prompt):
            return prompt

        lang = _pick_lang(analysis)
        sections: list[str] = []

        # General refusal guard
        general = REFUSAL_TEMPLATES["general"].get(lang, REFUSAL_TEMPLATES["general"]["en"])
        sections.append(general)

        # Code-specific guard
        if analysis.category in (PromptCategory.CODE, PromptCategory.EXTRACTION):
            code_guard = REFUSAL_TEMPLATES["code"].get(lang, REFUSAL_TEMPLATES["code"]["en"])
            sections.append(code_guard)

        # Professional disclaimer
        if analysis.category in _PROFESSIONAL_CATEGORIES:
            prof = REFUSAL_TEMPLATES["professional"].get(lang, REFUSAL_TEMPLATES["professional"]["en"])
            sections.append(prof)

        boundary_text = "\n".join(f"- {s}" for s in sections)
        boundary_section = self._wrap_tag(boundary_text, "boundaries")

        return f"{prompt}\n\n{boundary_section}"

    def _has_boundaries(self, prompt: str) -> bool:
        """Check if boundary/refusal instructions already exist."""
        patterns = [
            r"<boundaries>",
            r"<safety>",
            r"<refusal>",
            r"(do not|cannot|will not) (provide|generate|assist)",
            r"(refuse|decline|boundary|limitation)",
            r"(不要|无法|拒绝|禁止|限制)",
        ]
        return any(re.search(p, prompt[:600], re.IGNORECASE) for p in patterns)

    def should_apply(
        self,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> bool:
        return (
            super().should_apply(analysis, config)
            and config.add_refusal_guard
            and analysis.category != PromptCategory.CONVERSATION
        )
