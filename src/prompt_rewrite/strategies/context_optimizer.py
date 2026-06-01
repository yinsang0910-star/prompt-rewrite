"""
Context Optimizer — reorders prompt content for optimal LLM performance.

Based on Anthropic's research finding that placing:
  - Long documents / data → at the TOP of the prompt
  - Query / instructions → at the BOTTOM of the prompt
can improve response quality by up to 30%.

Based on the principle that placing long data at the top and queries at the bottom improves LLM response quality.
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


class ContextOptimizer(RewriteStrategy):
    """Optimizes prompt content ordering.

    Reorders prompt sections following the principle:
    DATA FIRST, QUERY LAST.

    Detection:
    - Long text blocks (>300 chars) → treated as "context/data"
    - Short instruction-like text → treated as "query/instruction"
    - Question sentences → treated as "query"
    """

    name: ClassVar[StrategyName] = StrategyName.CONTEXT_OPTIMIZER
    priority: ClassVar[int] = 15  # Early in pipeline

    def apply(
        self,
        prompt: str,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> str:
        # Only reorder if the prompt is long enough to benefit
        if len(prompt) < 500:
            return prompt

        # If already structured with XML, check ordering
        structured = self._is_xml_structured(prompt)
        if structured and not self._is_wrong_order(prompt):
            return prompt

        # Detect sections
        sections = self._split_sections(prompt)
        if len(sections) <= 1:
            return prompt

        # Classify and reorder
        data_blocks: list[str] = []
        query_blocks: list[str] = []
        structural_blocks: list[str] = []

        for block in sections:
            classification = self._classify_block(block)
            if classification == "data":
                data_blocks.append(block)
            elif classification == "query":
                query_blocks.append(block)
            else:
                structural_blocks.append(block)

        if not data_blocks or not query_blocks:
            return prompt

        # Reorder: structural → data → query
        reordered: list[str] = []
        reordered.extend(structural_blocks)
        reordered.extend(data_blocks)
        reordered.extend(query_blocks)

        return "\n\n".join(reordered)

    def _is_xml_structured(self, prompt: str) -> bool:
        """Check if the prompt uses XML tags for structure."""
        return bool(re.search(r"<(\w+)>", prompt[:300]))

    def _is_wrong_order(self, prompt: str) -> bool:
        """Check if the current structure violates data-first order.

        Heuristic: if the first XML section after <role>/<instructions>
        contains mostly query-like content rather than data, it's wrong order.
        """
        # Find all top-level XML sections
        sections = re.findall(r"<(\w+)>(.*?)</\1>", prompt, re.DOTALL)
        for tag, content in sections:
            if tag in ("instructions", "role", "constraints", "thinking"):
                continue
            if tag in ("input", "context", "data"):
                return False  # Data already early
            if len(content) < 300:
                return True  # Short content early = query, likely wrong order
            return False
        return False

    def _split_sections(self, prompt: str) -> list[str]:
        """Split prompt into logical blocks."""
        # Try splitting by XML tags first
        xml_sections = re.split(r"(</\w+>)\s*\n?", prompt)
        if len(xml_sections) > 3:
            # Rejoin closing tag with following content
            blocks: list[str] = []
            i = 0
            while i < len(xml_sections):
                part = xml_sections[i]
                if re.match(r"</\w+>$", part) and blocks:
                    blocks[-1] = blocks[-1] + "\n" + part
                else:
                    if part.strip():
                        blocks.append(part)
                i += 1
            return blocks

        # Fall back to double-newline splitting
        blocks = re.split(r"\n\s*\n", prompt)
        return [b.strip() for b in blocks if b.strip()]

    def _classify_block(self, block: str) -> str:
        """Classify a block as 'data', 'query', or 'structural'.

        T3.8: Uses keyword, punctuation, and length signals — not just length alone.
        """
        block = block.strip()

        # Structural blocks: role, constraints, etc.
        if re.match(r"<(role|constraints|thinking|instructions|output_format)>", block):
            return "structural"

        # Code blocks are always data (they provide context)
        if block.startswith("```") or "```" in block:
            return "data"

        # Data blocks: long text, documents, context (primary signal: length)
        if len(block) > 300:
            return "data"

        # Query signals: ends with ?, contains question words, is short
        query_keywords = re.search(
            r"(what|how|why|explain|write|create|tell|list|find|compare|summarize|"
            r"请|怎么|如何|为什么|写|创建|解释|列出|对比|总结)",
            block, re.IGNORECASE,
        )
        is_question = block.strip().endswith("?") or block.strip().endswith("？")
        is_short = len(block) < 200

        if is_question and is_short:
            return "query"
        if query_keywords and is_short:
            return "query"

        # Short blocks without data signals → query
        if is_short and not re.search(r"[。；\n]", block):
            return "query"

        # Default: data
        return "data"

    def should_apply(
        self,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> bool:
        # Only optimize longer prompts
        return (
            super().should_apply(analysis, config)
            and analysis.raw_length >= 500
        )
