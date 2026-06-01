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

# ── Constraint libraries (EN / ZH / JA) ──────────────────────────────────────

# Quality constraints by category
QUALITY_CONSTRAINTS: dict[str, dict[str, list[str]]] = {
    "general": {
        "en": [
            "Be precise and accurate. If you're uncertain, acknowledge the uncertainty.",
            "Base your responses on verified information. Clearly distinguish facts from interpretations.",
        ],
        "zh": [
            "请保持精确和准确。如果不确定，请坦诚说明。",
            "基于已验证的信息回答，明确区分事实和解读。",
        ],
        "ja": [
            "正確かつ精密であること。不確かな場合は、その旨を明記してください。",
            "検証済みの情報に基づいて回答し、事実と解釈を明確に区別してください。",
        ],
    },
    "code": {
        "en": [
            "Write clean, well-documented code with proper error handling.",
            "Consider edge cases, performance implications, and security best practices.",
            "Use established patterns and libraries rather than reinventing the wheel.",
            "Include type hints and meaningful variable names.",
        ],
        "zh": [
            "编写清晰、文档完善、错误处理得当的代码。",
            "考虑边界情况、性能影响和安全最佳实践。",
            "使用成熟的模式和库，避免重复造轮子。",
            "添加类型注解和有意义的变量名。",
        ],
        "ja": [
            "クリーンでドメントが整い、適切なエラーハンドリングのあるコードを書いてください。",
            "エッジケース、パフォーマンスへの影響、セキュリティのベストプラクティスを考慮してください。",
            "確立されたパターンとライブラリを使用し、車輪の再発明を避けてください。",
            "型ヒントと意味のある変数名を含めてください。",
        ],
    },
    "writing": {
        "en": [
            "Preserve the author's original voice and intent.",
            "Use clear, concise language appropriate for the target audience.",
            "Maintain logical flow and coherent structure.",
        ],
        "zh": [
            "保留作者原有的风格和意图。",
            "使用适合目标受众的清晰、简洁的语言。",
            "保持逻辑流畅和结构连贯。",
        ],
        "ja": [
            "著者のオリジナルの声と意図を保持してください。",
            "対象読者に適した明確で簡潔な言語を使用してください。",
            "論理的な流れと一貫した構造を維持してください。",
        ],
    },
    "analysis": {
        "en": [
            "Support all claims with evidence or reasoning.",
            "Acknowledge alternative viewpoints and limitations of your analysis.",
            "Distinguish between established facts and inferences.",
        ],
        "zh": [
            "用证据或推理支持所有论断。",
            "承认替代观点和分析的局限性。",
            "区分已确立的事实和推论。",
        ],
        "ja": [
            "すべての主張を証拠または論理で裏付けてください。",
            "代替の視点と分析の限界を認識してください。",
            "確立された事実と推論を区別してください。",
        ],
    },
    "academic": {
        "en": [
            "Use precise, formal language appropriate for academic discourse.",
            "Cite sources where applicable and distinguish established knowledge from speculation.",
            "Acknowledge methodological limitations and alternative interpretations.",
        ],
        "zh": [
            "使用适合学术讨论的精确、正式语言。",
            "在适用时引用来源，区分已确立的知识和推测。",
            "承认方法论的局限性和替代解释。",
        ],
        "ja": [
            "学術的議論に適した正確で formal な言語を使用してください。",
            "該当する箇所で出典を明記し、確立された知識と推測を区別してください。",
            "方法論的限界と代替的解釈を認識してください。",
        ],
    },
}

# Safety / refusal constraints
SAFETY_CONSTRAINTS: dict[str, list[str]] = {
    "en": [
        "Do not provide instructions for illegal activities, harm, or dangerous acts.",
        "Do not generate deceptive or misleading content intended to cause harm.",
        "Respect intellectual property rights. Do not reproduce copyrighted material at length.",
        "Do not provide medical, legal, or financial advice that could cause harm if acted upon.",
        "Be helpful while maintaining appropriate boundaries. Refuse requests that could cause harm.",
        "Do not generate hate speech, harassment, or content that discriminates against protected groups.",
    ],
    "zh": [
        "不要提供非法活动、伤害或危险行为的指导。",
        "不要生成旨在造成伤害的欺骗性或误导性内容。",
        "尊重知识产权，不要大量复制受版权保护的材料。",
        "不要提供可能造成伤害的医疗、法律或财务建议。",
        "在保持适当界限的同时提供帮助，拒绝可能造成伤害的请求。",
        "不要生成仇恨言论、骚扰内容或歧视受保护群体的内容。",
    ],
    "ja": [
        "違法行為、危害、危険な行為の手順を提供しないでください。",
        "危害を意図した欺瞞的または誤解を招くコンテンツを生成しないでください。",
        "知的財産権を尊重し、著作権保護された資料を大量に複製しないでください。",
        "実行した場合に害を及ぼす可能性のある医療、法的、または財務のアドバイスを提供しないでください。",
        "適切な境界を守りながら役立つ回答をし、害を及ぼす可能性のあるリクエストは拒否してください。",
        "ヘイトスピーチ、ハラスメント、保護されたグループを差別するコンテンツを生成しないでください。",
    ],
}

# Formatting constraints (positive guidance preferred)
FORMATTING_CONSTRAINTS: dict[str, list[str]] = {
    "en": [
        "Use clear section breaks and logical organization.",
        "Prefer positive instructions over negative ones (tell what to do, not what not to do).",
        "Use examples to illustrate complex points rather than abstract descriptions.",
    ],
    "zh": [
        "使用清晰的分段和逻辑组织。",
        "优先使用正面指令而非否定指令（说明该做什么，而非不该做什么）。",
        "用示例说明复杂要点，而非抽象描述。",
    ],
    "ja": [
        "明確なセクション区切りと論理的な構成を使用してください。",
        "否定的な指示より肯定的な指示を優先してください（何をすべきかを伝えてください）。",
        "抽象的な説明よりも具体例で複雑なポイントを説明してください。",
    ],
}


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

        # Category-specific quality constraints
        cat = analysis.category.value
        qc_dict = QUALITY_CONSTRAINTS.get(cat, QUALITY_CONSTRAINTS["general"])
        qc = qc_dict.get(lang, qc_dict.get("en", []))
        selected.extend(qc)

        # Safety constraints for all prompts
        if self._needs_safety(analysis):
            safety = SAFETY_CONSTRAINTS.get(lang, SAFETY_CONSTRAINTS.get("en", []))
            selected.extend(safety[:3])

        # Formatting constraints for longer prompts
        if analysis.raw_length > 500:
            fmt = FORMATTING_CONSTRAINTS.get(lang, FORMATTING_CONSTRAINTS.get("en", []))
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
