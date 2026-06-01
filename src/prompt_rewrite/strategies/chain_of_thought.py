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

# CoT instruction templates for different task types (EN / ZH / JA)
COT_TEMPLATES: dict[str, dict[str, str]] = {
    "general": {
        "en": (
            "Work through this problem step by step:\n"
            "1. First, understand the problem and what's being asked.\n"
            "2. Break down the problem into sub-problems.\n"
            "3. Solve each sub-problem systematically.\n"
            "4. Verify your solution before finalizing.\n"
            "5. Present your final answer clearly."
        ),
        "zh": (
            "请按以下步骤逐步解决这个问题：\n"
            "1. 首先，理解问题本身和具体要求。\n"
            "2. 将问题分解为若干子问题。\n"
            "3. 系统地解决每个子问题。\n"
            "4. 在最终确定前验证你的解答。\n"
            "5. 清晰地呈现最终答案。"
        ),
        "ja": (
            "この問題を段階的に解決してください：\n"
            "1. まず、問題とその要求を理解する。\n"
            "2. 問題をサブ問題に分解する。\n"
            "3. 各サブ問題を体系的に解決する。\n"
            "4. 最終決定前に解答を検証する。\n"
            "5. 最終回答を明確に提示する。"
        ),
    },
    "code": {
        "en": (
            "Before writing any code, think through:\n"
            "1. Understand the requirements and expected behavior.\n"
            "2. Identify edge cases and error conditions.\n"
            "3. Choose the appropriate algorithm/data structure.\n"
            "4. Sketch the implementation plan.\n"
            "5. Write the code with proper error handling.\n"
            "6. Review the code for bugs and improvements."
        ),
        "zh": (
            "在编写代码之前，请先思考以下步骤：\n"
            "1. 理解需求和预期行为。\n"
            "2. 识别边界情况和错误条件。\n"
            "3. 选择合适的算法/数据结构。\n"
            "4. 概述实现计划。\n"
            "5. 编写代码并做好错误处理。\n"
            "6. 审查代码中的 bug 和改进空间。"
        ),
        "ja": (
            "コードを書く前に、以下を検討してください：\n"
            "1. 要件と期待される動作を理解する。\n"
            "2. エッジケースとエラー条件を特定する。\n"
            "3. 適切なアルゴリズム/データ構造を選択する。\n"
            "4. 実装計画を概説する。\n"
            "5. 適切なエラーハンドリングでコードを書く。\n"
            "6. バグと改善点についてコードをレビューする。"
        ),
    },
    "analysis": {
        "en": (
            "Approach this analysis systematically:\n"
            "1. Identify the key question or hypothesis.\n"
            "2. Gather and organize the relevant information.\n"
            "3. Analyze each factor or component separately.\n"
            "4. Synthesize findings and identify patterns.\n"
            "5. Draw conclusions supported by evidence.\n"
            "6. Note any limitations or alternative explanations."
        ),
        "zh": (
            "请按以下步骤系统地进行分析：\n"
            "1. 确定关键问题或假设。\n"
            "2. 收集并整理相关信息。\n"
            "3. 分别分析每个因素或组成部分。\n"
            "4. 综合发现并识别模式。\n"
            "5. 得出有证据支持的结论。\n"
            "6. 注明局限性或替代解释。"
        ),
        "ja": (
            "この分析を体系的に進めてください：\n"
            "1. 核心的な質問または仮説を特定する。\n"
            "2. 関連情報を収集・整理する。\n"
            "3. 各要因を個別に分析する。\n"
            "4. 発見を統合しパターンを特定する。\n"
            "5. 証拠に基づいた結論を導く。\n"
            "6. 制限事項や代替的説明を記す。"
        ),
    },
    "math": {
        "en": (
            "Solve this step by step:\n"
            "1. Restate the problem clearly.\n"
            "2. Identify the given information and what needs to be found.\n"
            "3. Choose the appropriate formulas or methods.\n"
            "4. Work through each step, showing your work.\n"
            "5. Verify the result with a sanity check.\n"
            "6. Present the final answer."
        ),
        "zh": (
            "请按以下步骤逐步求解：\n"
            "1. 清晰地重述问题。\n"
            "2. 确定已知信息和待求目标。\n"
            "3. 选择合适的公式或方法。\n"
            "4. 逐步推导，展示计算过程。\n"
            "5. 通过合理性检查验证结果。\n"
            "6. 呈现最终答案。"
        ),
        "ja": (
            "段階的に解いてください：\n"
            "1. 問題を明確に再述する。\n"
            "2. 与えられた情報と求めるものを特定する。\n"
            "3. 適切な公式や方法を選択する。\n"
            "4. 各ステップを計算過程を示しながら進める。\n"
            "5. 妥当性チェックで結果を検証する。\n"
            "6. 最終回答を提示する。"
        ),
    },
    "debate": {
        "en": (
            "Analyze this topic from multiple perspectives:\n"
            "1. Consider the strongest arguments for each position.\n"
            "2. Evaluate the evidence supporting each view.\n"
            "3. Identify underlying assumptions.\n"
            "4. Acknowledge areas of uncertainty.\n"
            "5. Synthesize a balanced conclusion."
        ),
        "zh": (
            "请从多个角度分析这个话题：\n"
            "1. 考虑每种立场的最强论据。\n"
            "2. 评估支持每种观点的证据。\n"
            "3. 识别潜在的假设。\n"
            "4. 承认不确定的领域。\n"
            "5. 综合得出平衡的结论。"
        ),
        "ja": (
            "このトピックを多角的に分析してください：\n"
            "1. 各立場の最も強力な議論を検討する。\n"
            "2. 各見解を支持する証拠を評価する。\n"
            "3. 潜在的な仮定を特定する。\n"
            "4. 不確実な領域を認識する。\n"
            "5. バランスの取れた結論を統合する。"
        ),
    },
    "comparison": {
        "en": (
            "Compare these items systematically:\n"
            "1. Identify the key dimensions for comparison.\n"
            "2. Evaluate each item on every dimension.\n"
            "3. Note strengths and weaknesses.\n"
            "4. Consider the context and use case.\n"
            "5. Provide a clear recommendation if appropriate."
        ),
        "zh": (
            "请按以下步骤系统地进行对比：\n"
            "1. 确定对比的关键维度。\n"
            "2. 在每个维度上评估各个项目。\n"
            "3. 列出各自的优势和劣势。\n"
            "4. 考虑具体场景和使用情况。\n"
            "5. 如有必要，给出明确的推荐建议。"
        ),
        "ja": (
            "これらの項目を体系的に比較してください：\n"
            "1. 比較の重要な軸を特定する。\n"
            "2. 各項目をあらゆる軸で評価する。\n"
            "3. 強みと弱みを記す。\n"
            "4. コンテキストとユースケースを考慮する。\n"
            "5. 適切であれば明確な推奨を提供する。"
        ),
    },
}


def _pick_lang(analysis: AnalysisResult) -> str:
    """Return the best language code for template selection."""
    if analysis.language in ("zh", "ja"):
        return analysis.language
    return "en"


class ChainOfThoughtInjector(RewriteStrategy):
    """Injects chain-of-thought reasoning instructions.

    Adds a <thinking> section before the main instructions,
    guiding the model to reason step-by-step before answering.
    """

    name: ClassVar[StrategyName] = StrategyName.CHAIN_OF_THOUGHT
    priority: ClassVar[int] = 45  # After structure and role, before output formatting

    def apply(self, prompt: str, analysis: AnalysisResult, config: RewriteConfig, **kwargs: object) -> str:
        # Check if CoT already present
        if self._has_cot(prompt):
            return prompt

        cot_template = self._select_cot_template(analysis)
        cot_section = self._wrap_tag(cot_template, "thinking")

        # Inject after role/instructions, before data input
        return f"{cot_section}\n\n{prompt}"

    def _select_cot_template(self, analysis: AnalysisResult) -> str:
        """Pick the most appropriate CoT template in the detected language."""
        lang = _pick_lang(analysis)

        if PromptCategory.CODE in (analysis.category,):
            return COT_TEMPLATES["code"].get(lang, COT_TEMPLATES["code"]["en"])
        if PromptCategory.ANALYSIS in (analysis.category,):
            return COT_TEMPLATES["analysis"].get(lang, COT_TEMPLATES["analysis"]["en"])

        # Check for math/reasoning cues
        if any(kw in str(analysis.domains) for kw in ["math", "physics", "science"]):
            return COT_TEMPLATES["math"].get(lang, COT_TEMPLATES["math"]["en"])

        # T2.10: Activate debate/comparison templates based on key entities
        entities_lower = " ".join(analysis.key_entities).lower()
        text_repr = entities_lower + " ".join(analysis.domains)
        if any(kw in text_repr for kw in ["debate", "versus", "vs", "argument", "立场"]):
            return COT_TEMPLATES["debate"].get(lang, COT_TEMPLATES["debate"]["en"])
        if any(kw in text_repr for kw in ["compare", "comparison", "versus", "vs", "对比"]):
            return COT_TEMPLATES["comparison"].get(lang, COT_TEMPLATES["comparison"]["en"])

        # Default to general
        return COT_TEMPLATES["general"].get(lang, COT_TEMPLATES["general"]["en"])

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
        return any(re.search(p, prompt[:1000], re.IGNORECASE) for p in patterns)

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
