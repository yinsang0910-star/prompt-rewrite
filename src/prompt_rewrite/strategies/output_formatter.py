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

# ── Output format templates ──────────────────────────────────────────────────

OUTPUT_TEMPLATES: dict[str, str] = {
    "general": (
        "Provide a clear, well-organized response. "
        "Use appropriate formatting (headings, lists, code blocks) "
        "to improve readability."
    ),
    "code": (
        "Provide your solution in the following format:\n"
        "1. Brief explanation of the approach\n"
        "2. The complete code in a code block with the correct language tag\n"
        "3. Usage example if applicable\n"
        "4. Notes on edge cases or limitations"
    ),
    "analysis": (
        "Structure your analysis as:\n"
        "1. **Summary**: One-paragraph overview of findings\n"
        "2. **Detailed Analysis**: Systematic breakdown with evidence\n"
        "3. **Conclusions**: Key takeaways and recommendations\n"
        "4. **Limitations**: Caveats and areas of uncertainty"
    ),
    "writing": (
        "Present the output as clean prose. "
        "Use appropriate paragraph breaks and section headings. "
        "Maintain consistent tone and style throughout."
    ),
    "comparison": (
        "Present the comparison as:\n"
        "1. **Overview**: Brief context for each item\n"
        "2. **Comparison Table**: Key dimensions as a markdown table\n"
        "3. **Recommendation**: Which option is best for which scenario"
    ),
    "list": (
        "Provide the output as a structured list. "
        "Group related items under clear headings."
    ),
    "extraction": (
        "Present the extracted information in a structured format:\n"
        "- Use JSON for structured data extraction\n"
        "- Use markdown tables for comparisons\n"
        "- Use bullet points for lists of items"
    ),
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


class OutputFormatter(RewriteStrategy):
    """Adds explicit output formatting instructions.

    Appends an <output_format> section that tells the model
    exactly how to structure its response.
    """

    name: ClassVar[StrategyName] = StrategyName.OUTPUT_FORMATTER
    priority: ClassVar[int] = 70  # Late in pipeline, after content is structured

    def apply(
        self,
        prompt: str,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> str:
        # Don't duplicate
        if self._has_output_format(prompt):
            return prompt

        template_key = self._select_template(analysis)
        output_text = OUTPUT_TEMPLATES.get(template_key, OUTPUT_TEMPLATES["general"])

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
