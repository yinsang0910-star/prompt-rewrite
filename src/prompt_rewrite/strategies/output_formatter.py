"""
Output Formatter — specifies output structure and formatting.

Based on structured output patterns:
  - Explicit output formatting instructions
  - Positive guidance over negative prohibitions

This strategy adds explicit output formatting instructions
based on the detected prompt type and user's implicit needs.
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

# ── Output format templates (EN / ZH / JA) ───────────────────────────────────

OUTPUT_TEMPLATES: dict[str, dict[str, str]] = {
    "general": {
        "en": (
            "Provide a clear, well-organized response. "
            "Use appropriate formatting (headings, lists, code blocks) "
            "to improve readability."
        ),
        "zh": (
            "请提供清晰、组织良好的回答。"
            "使用适当的格式（标题、列表、代码块）来提高可读性。"
        ),
        "ja": (
            "明確で整理された回答を提供してください。"
            "適切なフォーマット（見出し、リスト、コードブロック）を使用して可読性を向上させてください。"
        ),
    },
    "code": {
        "en": (
            "Provide your solution in the following format:\n"
            "1. Brief explanation of the approach\n"
            "2. The complete code in a code block with the correct language tag\n"
            "3. Usage example if applicable\n"
            "4. Notes on edge cases or limitations"
        ),
        "zh": (
            "请按以下格式提供解决方案：\n"
            "1. 方法的简要说明\n"
            "2. 完整代码（放在带有正确语言标签的代码块中）\n"
            "3. 使用示例（如适用）\n"
            "4. 边界情况或局限性说明"
        ),
        "ja": (
            "以下の形式で回答を提供してください：\n"
            "1. アプローチの簡単な説明\n"
            "2. 正しい言語タグ付きコードブロックに完全なコード\n"
            "3. 該当する場合は使用例\n"
            "4. エッジケースまたは制限事項に関する注意"
        ),
    },
    "analysis": {
        "en": (
            "Structure your analysis as:\n"
            "1. **Summary**: One-paragraph overview of findings\n"
            "2. **Detailed Analysis**: Systematic breakdown with evidence\n"
            "3. **Conclusions**: Key takeaways and recommendations\n"
            "4. **Limitations**: Caveats and areas of uncertainty"
        ),
        "zh": (
            "请按以下结构组织分析：\n"
            "1. **摘要**：一段话概述主要发现\n"
            "2. **详细分析**：附带证据的系统化分析\n"
            "3. **结论**：关键要点和建议\n"
            "4. **局限性**：注意事项和不确定领域"
        ),
        "ja": (
            "分析を以下の構造で整理してください：\n"
            "1. **要約**: 発見の一段落概要\n"
            "2. **詳細分析**: 証拠を伴う体系的な分析\n"
            "3. **結論**: 重要なポイントと推奨事項\n"
            "4. **限界**: 注意事項と不確実な領域"
        ),
    },
    "writing": {
        "en": (
            "Present the output as clean prose. "
            "Use appropriate paragraph breaks and section headings. "
            "Maintain consistent tone and style throughout."
        ),
        "zh": (
            "以整洁的行文呈现输出。"
            "使用适当的段落分隔和章节标题。"
            "全文保持一致的语气和风格。"
        ),
        "ja": (
            "整理された文章で出力を提示してください。"
            "適切な段落区切りとセクション見出しを使用してください。"
            "全体を通じて一貫したトーンとスタイルを維持してください。"
        ),
    },
    "comparison": {
        "en": (
            "Present the comparison as:\n"
            "1. **Overview**: Brief context for each item\n"
            "2. **Comparison Table**: Key dimensions as a markdown table\n"
            "3. **Recommendation**: Which option is best for which scenario"
        ),
        "zh": (
            "请按以下格式呈现对比：\n"
            "1. **概述**：每个项目的简要背景\n"
            "2. **对比表格**：以 markdown 表格展示关键维度\n"
            "3. **推荐建议**：哪种方案最适合哪种场景"
        ),
        "ja": (
            "比較を以下の形式で提示してください：\n"
            "1. **概要**: 各項目の簡単な背景\n"
            "2. **比較表**: 重要な軸を markdown テーブルで\n"
            "3. **推奨**: どのオプションがどのシナリオに最適か"
        ),
    },
    "list": {
        "en": (
            "Provide the output as a structured list. "
            "Group related items under clear headings."
        ),
        "zh": (
            "以结构化列表的形式提供输出。"
            "将相关项目分组在清晰的标题下。"
        ),
        "ja": (
            "構造化リストとして出力を提供してください。"
            "関連項目を明確な見出しの下にグループ化してください。"
        ),
    },
    "extraction": {
        "en": (
            "Present the extracted information in a structured format:\n"
            "- Use JSON for structured data extraction\n"
            "- Use markdown tables for comparisons\n"
            "- Use bullet points for lists of items"
        ),
        "zh": (
            "以结构化格式呈现提取的信息：\n"
            "- 结构化数据提取使用 JSON\n"
            "- 对比内容使用 markdown 表格\n"
            "- 列表项目使用要点符号"
        ),
        "ja": (
            "抽出情報を構造化形式で提示してください：\n"
            "- 構造化データ抽出には JSON を使用\n"
            "- 比較には markdown テーブルを使用\n"
            "- 項目リストには箇条書きを使用"
        ),
    },
}

# Category → output format mapping
_CATEGORY_OUTPUT_MAP: dict[PromptCategory, str] = {
    PromptCategory.CODE: "code",
    PromptCategory.ANALYSIS: "analysis",
    PromptCategory.WRITING: "writing",
    PromptCategory.CREATIVE: "writing",
    PromptCategory.EXTRACTION: "extraction",
    PromptCategory.QA: "general",
    PromptCategory.INSTRUCTION: "general",
    PromptCategory.CONVERSATION: "general",
    PromptCategory.UNKNOWN: "general",
}


def _pick_lang(analysis: AnalysisResult) -> str:
    """Return the best language code for template selection."""
    if analysis.language in ("zh", "ja"):
        return analysis.language
    return "en"


class OutputFormatter(RewriteStrategy):
    """Adds explicit output formatting instructions.

    Appends an <output_format> section that tells the model
    exactly how to structure its response.
    """

    name: ClassVar[StrategyName] = StrategyName.OUTPUT_FORMATTER
    priority: ClassVar[int] = 70  # Late in pipeline, after content is structured

    def apply(self, prompt: str, analysis: AnalysisResult, config: RewriteConfig, **kwargs: object) -> str:
        # Don't duplicate
        if self._has_output_format(prompt):
            return prompt

        template_key = self._select_template(analysis)
        lang = _pick_lang(analysis)
        template_dict = OUTPUT_TEMPLATES.get(template_key, OUTPUT_TEMPLATES["general"])
        output_text = template_dict.get(lang, template_dict.get("en", ""))

        # Wrap in output_format tag
        output_section = self._wrap_tag(output_text, "output_format")

        return f"{prompt}\n\n{output_section}"

    def _select_template(self, analysis: AnalysisResult) -> str:
        """Pick the best output format template.

        T3.10: Activated comparison/list templates via domain + keyword matching.
        """
        # Domain-specific templates
        domain = analysis.domains[0] if analysis.domains else ""
        if domain in ("data_science", "finance"):
            return "extraction"

        # Keyword-based matching for comparison/list templates
        entities_lower = " ".join(analysis.key_entities).lower()
        if any(kw in entities_lower for kw in ["compare", "versus", "vs", "对比", "比较"]):
            return "comparison"
        if analysis.category == PromptCategory.EXTRACTION:
            return "list"

        # Category-based mapping
        return _CATEGORY_OUTPUT_MAP.get(analysis.category, "general")

    def _has_output_format(self, prompt: str) -> bool:
        """Check if output format instructions already exist."""
        patterns = [
            r"<output_format>",
            r"<output>",
            r"(output|response) (format|structure|should be)",
            r"(format your response|respond in the following|output as)",
            r"(返回格式|输出格式|请以.*格式)",
        ]
        return any(re.search(p, prompt[:400], re.IGNORECASE) for p in patterns)
