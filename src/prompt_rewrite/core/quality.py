# -*- coding: utf-8 -*-
"""Offline prompt quality scorer — no LLM required.

Scores a prompt on 5 axes (0-10 each):
- clarity: clear instructions, unambiguous language
- specificity: concrete details, not vague
- structure: organized with sections, tags, examples
- safety: has refusal guard, boundaries, constraints
- completeness: covers role, task, format, constraints
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class QualityScore:
    """Quality assessment of a prompt on 5 axes."""
    clarity: float
    specificity: float
    structure: float
    safety: float
    completeness: float

    @property
    def total(self) -> float:
        return round((self.clarity + self.specificity + self.structure
                      + self.safety + self.completeness) / 5, 1)

    def to_dict(self) -> dict:
        return {
            "clarity": self.clarity,
            "specificity": self.specificity,
            "structure": self.structure,
            "safety": self.safety,
            "completeness": self.completeness,
            "total": self.total,
        }


def score_prompt(text: str) -> QualityScore:
    """Score a prompt on 5 quality axes. Returns QualityScore."""
    if not text or not text.strip():
        return QualityScore(0, 0, 0, 0, 0)

    text = text.strip()
    length = len(text)
    lines = text.splitlines()
    word_count = len(text.split())

    # --- Clarity (0-10) ---
    clarity = 5.0
    # Short prompts with clear verbs are clear
    action_verbs = len(re.findall(
        r"\b(write|create|explain|analyze|design|implement|build|list|describe|compare|generate|extract|summarize|translate)\b",
        text, re.IGNORECASE
    ))
    clarity += min(action_verbs * 1.5, 3)
    # Penalize vague words
    vague = len(re.findall(
        r"\b(something|stuff|things|whatever|somehow|maybe|kind of|sort of|etc)\b",
        text, re.IGNORECASE
    ))
    clarity -= min(vague * 1.0, 3)
    # Penalize very long prompts (> 2000 chars) as potentially unclear
    if length > 2000:
        clarity -= 1
    clarity = max(0, min(10, clarity))

    # --- Specificity (0-10) ---
    specificity = 3.0
    # Numbers, versions, specific terms boost specificity
    numbers = len(re.findall(r"\b\d+\b", text))
    specificity += min(numbers * 0.5, 3)
    # Technical terms
    tech = len(re.findall(
        r"\b(python|javascript|api|database|json|html|sql|docker|kubernetes|react|vue|angular|fastapi|flask|django)\b",
        text, re.IGNORECASE
    ))
    specificity += min(tech * 0.8, 2)
    # Code blocks = very specific
    if "```" in text:
        specificity += 2
    specificity = max(0, min(10, specificity))

    # --- Structure (0-10) ---
    structure = 2.0
    # XML tags
    xml_tags = len(re.findall(r"<\w+>", text))
    structure += min(xml_tags * 0.5, 3)
    # Numbered/bullet lists
    list_items = len(re.findall(r"^\s*(\d+[.\)]|[-*+])\s", text, re.MULTILINE))
    structure += min(list_items * 0.3, 2)
    # Sections (headers or labeled blocks)
    if re.search(r"^(#|##|---|===)", text, re.MULTILINE):
        structure += 1.5
    # Multi-line with clear separation
    if len(lines) >= 3:
        structure += 1
    structure = max(0, min(10, structure))

    # --- Safety (0-10) ---
    safety = 5.0
    # Has boundary/refusal guard
    if re.search(r"<boundaries>|<safety>|<refusal>", text, re.IGNORECASE):
        safety += 3
    # Has constraints section
    if re.search(r"<constraints>|constraints|limitations|restrictions", text, re.IGNORECASE):
        safety += 2
    safety = max(0, min(10, safety))

    # --- Completeness (0-10) ---
    completeness = 3.0
    # Has role
    if re.search(r"<role>|you are|act as|as a\b", text, re.IGNORECASE):
        completeness += 2
    # Has output format
    if re.search(r"<output|output format|respond with|format|return", text, re.IGNORECASE):
        completeness += 1.5
    # Has examples
    if re.search(r"<example|example|e\.g\.|for instance", text, re.IGNORECASE):
        completeness += 1.5
    # Has instructions section
    if re.search(r"<instructions>|your task|please\b", text, re.IGNORECASE):
        completeness += 1
    # Has thinking/reasoning
    if re.search(r"<thinking>|think step|chain.of.thought|reasoning", text, re.IGNORECASE):
        completeness += 1
    completeness = max(0, min(10, completeness))

    return QualityScore(
        clarity=round(clarity, 1),
        specificity=round(specificity, 1),
        structure=round(structure, 1),
        safety=round(safety, 1),
        completeness=round(completeness, 1),
    )
