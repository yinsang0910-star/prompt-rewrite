"""
Example Formatter — wraps user-provided examples in structured XML tags.

Uses the few-shot prompting pattern:
  <examples>
    <example>
      <input>...</input>
      <output>...</output>
    </example>
  </examples>

This strategy:
1. Detects examples in the raw prompt
2. Parses input/output pairs
3. Wraps them in <example> tags
4. Optionally numbers/labels them
"""

from __future__ import annotations

import re
from typing import ClassVar, Optional

from prompt_rewrite.core.types import (
    AnalysisResult,
    RewriteConfig,
    StrategyName,
)
from prompt_rewrite.strategies.base import RewriteStrategy


class ExampleFormatter(RewriteStrategy):
    """Detects and structures examples in the prompt.

    If the prompt contains input/output examples, this strategy
    wraps them in proper <example> tags and separates them
    from the main instructions.
    """

    name: ClassVar[StrategyName] = StrategyName.EXAMPLE_FORMATTER
    priority: ClassVar[int] = 55  # After CoT, before output

    def apply(self, prompt: str, analysis: AnalysisResult, config: RewriteConfig, **kwargs: object) -> str:
        if not analysis.has_examples:
            return prompt

        # If already wrapped in <example> tags, skip
        if re.search(r"<example[^>]*>", prompt):
            return prompt

        # Try to extract and restructure examples
        examples, rest = self._extract_examples(prompt)
        if not examples:
            return prompt

        # Build the examples section
        example_parts: list[str] = []
        for i, (inp, out) in enumerate(examples, 1):
            ex_parts: list[str] = []
            if inp:
                ex_parts.append(self._wrap_tag(inp, "input"))
            if out:
                ex_parts.append(self._wrap_tag(out, "output"))
            example_body = "\n".join(ex_parts)
            example_parts.append(self._wrap_tag(example_body, "example", f'index="{i}"'))

        examples_section = self._wrap_tag("\n".join(example_parts), "examples")

        # Place examples after instructions
        return f"{rest}\n\n{examples_section}"

    def _extract_examples(
        self,
        text: str,
    ) -> tuple[list[tuple[str, str]], str]:
        """Extract input/output example pairs from the prompt.

        Returns (examples, remaining_text).
        """
        examples: list[tuple[str, str]] = []
        remaining = text

        # Pattern 1: "Example N:" labeled sections
        example_blocks = re.split(
            r"(?:example\s*\d*\s*[:：]|示例\s*\d*\s*[:：])",
            text,
            flags=re.IGNORECASE,
        )

        if len(example_blocks) > 1:
            # First block is before the first example
            remaining = example_blocks[0]
            for block in example_blocks[1:]:
                inp, out = self._parse_io_block(block)
                if inp or out:
                    examples.append((inp, out))
            if examples:
                return examples, remaining

        # Pattern 2: "Input: ... Output: ..." inline pairs
        io_pairs = re.findall(
            r"(?:input|入参|输入)\s*[:：]\s*(.*?)\s*(?:output|出参|输出)\s*[:：]\s*(.*?)(?=(?:\s*(?:input|入参|输入)\s*[:：]|$))",
            text,
            re.IGNORECASE | re.DOTALL,
        )
        if io_pairs:
            examples = [(inp.strip(), out.strip()) for inp, out in io_pairs]
            # Remove matched examples from text
            remaining = re.sub(
                r"(?:input|入参|输入)\s*[:：].*?(?=(?:\s*(?:input|入参|输入)\s*[:：]|$))",
                "",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )
            return examples, remaining

        return [], text

    def _parse_io_block(self, block: str) -> tuple[Optional[str], Optional[str]]:
        """Parse a single example block into (input, output)."""
        inp = out = None

        input_match = re.search(
            r"(?:input|入参|输入|question|问题)\s*[:：]\s*(.*?)(?=(?:output|出参|输出|answer|答案)\s*[:：])",
            block,
            re.IGNORECASE | re.DOTALL,
        )
        if input_match:
            inp = input_match.group(1).strip()

        output_match = re.search(
            r"(?:output|出参|输出|answer|答案)\s*[:：]\s*(.*?)$",
            block,
            re.IGNORECASE | re.DOTALL,
        )
        if output_match:
            out = output_match.group(1).strip()

        return inp, out

    def should_apply(
        self,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> bool:
        return (
            super().should_apply(analysis, config)
            and analysis.has_examples
            and config.preserve_user_examples
        )
