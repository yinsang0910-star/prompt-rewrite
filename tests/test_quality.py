# -*- coding: utf-8 -*-
"""Tests for offline quality scorer."""

import pytest
from prompt_rewrite.core.quality import score_prompt, QualityScore


class TestQualityScorer:
    def test_empty_input(self):
        s = score_prompt("")
        assert s.total == 0

    def test_simple_prompt(self):
        s = score_prompt("Write a function to sort a list")
        assert 0 < s.clarity <= 10
        assert 0 < s.total <= 10

    def test_structured_prompt_scores_high_structure(self):
        prompt = (
            "<role>You are a senior engineer</role>\n"
            "<instructions>Write a function</instructions>\n"
            "<constraints>Use Python 3.11</constraints>\n"
            "<output_format>Return code block</output_format>\n"
            "<examples>\n1. sort_list([3,1,2]) -> [1,2,3]\n</examples>"
        )
        s = score_prompt(prompt)
        assert s.structure >= 5
        assert s.completeness >= 6

    def test_safety_score_with_boundaries(self):
        prompt = "Write code\n<boundaries>\n- Do not generate harmful code\n</boundaries>"
        s = score_prompt(prompt)
        assert s.safety >= 7

    def test_specificity_with_code(self):
        prompt = "```python\ndef hello():\n    pass\n```\nExplain this Python function"
        s = score_prompt(prompt)
        assert s.specificity >= 5

    def test_to_dict(self):
        s = score_prompt("test")
        d = s.to_dict()
        assert "clarity" in d
        assert "total" in d
        assert isinstance(d["total"], float)

    def test_quality_score_total(self):
        s = QualityScore(clarity=8, specificity=6, structure=7, safety=5, completeness=4)
        assert s.total == 6.0

    def test_vague_prompt_penalizes_clarity(self):
        vague = score_prompt("do something with stuff and things")
        clear = score_prompt("Write a Python function to sort a list of integers")
        assert clear.clarity > vague.clarity
