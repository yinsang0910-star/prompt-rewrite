"""
LLM 重写策略 — 用 DeepSeek 深度优化 prompt 内容。
"""

from __future__ import annotations

import re
from typing import ClassVar, Optional

from prompt_rewrite.core.types import (
    AnalysisResult, RewriteConfig, StrategyName, PromptCategory, LLMConfig,
)
from prompt_rewrite.strategies.base import RewriteStrategy, StrategyRegistry
from prompt_rewrite.llm.deepseek_client import DeepSeekClient

SYSTEM_REWRITE = """You are a prompt engineering expert. Your job is to IMPROVE the user's raw prompt.

IMPORTANT RULES:
- Output plain natural-language English (or the user's language)
- Use markdown headings (##), bullet lists (-), and **bold** for structure
- NEVER use XML/HTML tags like <role>, <instructions>, <context>, <input>, <output>, <thinking>
- NEVER wrap content in angle brackets
- Write as if you are a senior engineer instructing a junior colleague

Return ONLY the rewritten prompt text, no explanations, no meta-commentary."""

SYSTEM_VALIDATE = """Evaluate the quality of this rewritten prompt on a scale of 1-10.
Consider: clarity, specificity, structure, completeness, and actionability.

Return ONLY a JSON object with:
- "score": integer 1-10
- "strengths": list of strengths (max 3)
- "weaknesses": list of weaknesses (max 3)
- "suggestion": one-sentence improvement"""


class LLMRewriter(RewriteStrategy):
    """用 DeepSeek 深度重写 prompt。

    与规则策略不同，这个策略让 LLM 理解 prompt 语义后，
    生成更自然、上下文感知的重写版本。
    """

    name: ClassVar[StrategyName] = StrategyName.CONTEXT_OPTIMIZER  # 复用排序的优先级位置
    # 运行时标记，不注册为新策略名
    _is_llm: bool = True
    priority: ClassVar[int] = 75  # 最后阶段

    def __init__(self, llm_config: Optional[LLMConfig] = None):
        self.client = DeepSeekClient(llm_config) if (llm_config and llm_config.enabled) else None
        self.last_error: str = ""

    def apply(
        self,
        prompt: str,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> str:
        if not self.client:
            return prompt

        # 构建增强指令
        extra = ""
        if analysis.domains:
            extra += f"\nDomain: {', '.join(analysis.domains[:3])}"
        extra += f"\nCategory: {analysis.category.value}"
        if analysis.has_code:
            extra += "\nThis prompt contains code — format code blocks properly."

        result = self.client.chat(
            f"Improve this prompt:\n{prompt}\n\nCategory: {analysis.category.value}",
            system=SYSTEM_REWRITE,
        )
        self.last_error = ""

        if result.startswith("[LLM"):
            self.last_error = result
            return prompt  # LLM 失败，回退到原始
        return result

    def should_apply(self, analysis: AnalysisResult, config: RewriteConfig) -> bool:
        return config.llm_enhance_rewrite and self.client is not None


class LLMValidator:
    """用 DeepSeek 校验重写结果质量，给出评分和改进建议。"""

    def __init__(self, llm_config: LLMConfig):
        self.client = DeepSeekClient(llm_config) if llm_config.enabled else None

    def validate(self, original: str, rewritten: str) -> dict:
        """校验重写质量，返回 {"score": 8, "strengths": [...], "weaknesses": [...], "suggestion": "..."}"""
        if not self.client:
            return {"score": 0, "note": "LLM not configured"}

        result = self.client.chat_json(
            f"Original prompt:\n{original}\n\nRewritten prompt:\n{rewritten}",
            system=SYSTEM_VALIDATE,
        )
        return result if isinstance(result, dict) else {"score": 0, "raw": result}
