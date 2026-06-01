"""
Structure Formatter — wraps prompt content in XML tags for clarity.

Uses XML tag structure for unambiguous prompt parsing:
  <instructions>...</instructions>
  <context>...</context>
  <input>...</input>
  <examples>...</examples>

This strategy:
1. Detects different sections in the raw prompt
2. Separates instructions from context from input data
3. Wraps each in appropriate XML tags
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


class StructureFormatter(RewriteStrategy):
    """Wraps prompt sections in descriptive XML tags for unambiguous parsing.

    Uses heuristics to identify:
    - Instructions / task description
    - Context / background
    - Input data / text to process
    - Examples
    - Output format specifications
    """

    name: ClassVar[StrategyName] = StrategyName.STRUCTURE_FORMATTER
    priority: ClassVar[int] = 10  # Very early in pipeline

    # Section boundary markers
    _SECTION_PATTERNS: ClassVar[dict[str, list[str]]] = {
        "instructions": [
            r"(instructions?|task|your task|what to do|please)\s*[:：]",
            r"(i want you to|i need you to|your job is)",
            r"(follow these|do the following|perform the)",
        ],
        "context": [
            r"(context|background|situation|scenario|about)\s*[:：]",
            r"(given that|considering|provided that)",
            r"(here's the situation|here is some context)",
        ],
        "input": [
            r"(input|text|content|below|following)\s*[:：]",
            r"(here'?s the|here is the|this is the)",
            r"(data|document|article|passage|code)",
        ],
        "examples": [
            r"(example|e\.g\.|for instance|for example)",
            r"(input\s*\d?\s*[:：].*output\s*\d?\s*[:：])",
        ],
        "output": [
            r"(output|format|response format|expected output)\s*[:：]",
            r"(return as|respond with|in the format)",
        ],
    }

    def apply(
        self,
        prompt: str,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> str:
        # If already structured with XML tags, skip
        if self._already_structured(prompt):
            return prompt

        # Try to split into sections
        sections = self._parse_sections(prompt)

        # If we couldn't identify clear sections, wrap everything in <instructions>
        if len(sections) <= 1:
            return self._wrap_tag(prompt.strip(), "instructions")

        # Rebuild with tags
        tagged_parts: list[str] = []
        for tag_name, content in sections:
            if content.strip():
                tagged_parts.append(self._wrap_tag(content.strip(), tag_name))

        return "\n\n".join(tagged_parts)

    def _already_structured(self, prompt: str) -> bool:
        """Check if the prompt already uses XML section tags."""
        # Count XML-like tags in the first 200 characters
        head = prompt[:200]
        tags = re.findall(r"<(\w+)>", head)
        closing_tags = re.findall(r"</(\w+)>", head)
        return len(tags) >= 2 and len(closing_tags) >= 1

    def _parse_sections(
        self,
        prompt: str,
    ) -> list[tuple[str, str]]:
        """Split prompt into logical sections using heuristic markers.

        Returns list of (tag_name, content) tuples preserving original order.
        """
        lines = prompt.split("\n")
        sections: list[tuple[str, str, int]] = []  # (tag, content, start_line)
        current_tag = "instructions"
        current_lines: list[str] = []
        tag_starts_at = 0

        for i, line in enumerate(lines):
            detected_tag = self._detect_section_header(line)

            if detected_tag and detected_tag != current_tag:
                # Flush current section
                if current_lines:
                    sections.append((current_tag, "\n".join(current_lines), tag_starts_at))
                current_tag = detected_tag
                current_lines = []
                tag_starts_at = i

            current_lines.append(line)

        # Flush last section
        if current_lines:
            sections.append((current_tag, "\n".join(current_lines), tag_starts_at))

        # Simplify: remove pure header lines (e.g. "Context:") but keep lines
        # that happen to match a pattern yet contain substantial content
        # (e.g. "Your task is to write a poem about nature")
        _PURE_HEADER_RE = re.compile(
            r"^\s*(instructions?|task|context|background|input|text|content|"
            r"examples?|output|format|data)\s*[:：]?\s*$",
            re.IGNORECASE,
        )
        cleaned: list[tuple[str, str]] = []
        for tag, content, start in sections:
            lines_c = content.split("\n")
            # Only strip the first line if it's a pure section label (no real content)
            if lines_c and _PURE_HEADER_RE.match(lines_c[0].strip()):
                lines_c = lines_c[1:]
            cleaned_content = "\n".join(lines_c).strip()
            if cleaned_content:
                cleaned.append((tag, cleaned_content))

        return cleaned or [("instructions", prompt.strip())]

    def _detect_section_header(self, line: str) -> str | None:
        """Check if a line marks a section boundary."""
        line_stripped = line.strip().rstrip(":")
        for tag, patterns in self._SECTION_PATTERNS.items():
            for pat in patterns:
                if re.match(pat, line_stripped, re.IGNORECASE):
                    return tag
        return None
