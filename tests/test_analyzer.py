"""Tests for the PromptAnalyzer."""

from prompt_rewrite.core.analyzer import PromptAnalyzer
from prompt_rewrite.core.types import PromptCategory, ComplexityLevel


class TestAnalyzer:
    """Test category, complexity, and feature detection."""

    def setup_method(self):
        self.analyzer = PromptAnalyzer()

    # ── Category Detection ──────────────────────────────────────────────

    def test_detect_code(self):
        r = self.analyzer.analyze("Write a Python function to sort a list")
        assert r.category == PromptCategory.CODE

    def test_detect_code_with_fence(self):
        r = self.analyzer.analyze("```python\nprint('hello')\n```")
        assert r.category == PromptCategory.CODE

    def test_detect_qa(self):
        r = self.analyzer.analyze("What is the meaning of life?")
        assert r.category == PromptCategory.QA

    def test_detect_qa_explain(self):
        r = self.analyzer.analyze("Explain how recursion works")
        assert r.category == PromptCategory.QA

    def test_detect_writing(self):
        r = self.analyzer.analyze("Rewrite this paragraph to be more concise")
        assert r.category == PromptCategory.WRITING

    def test_detect_analysis(self):
        r = self.analyzer.analyze(
            "Compare and contrast microservices vs monolith architecture"
        )
        assert r.category == PromptCategory.ANALYSIS

    def test_detect_creative(self):
        r = self.analyzer.analyze("Brainstorm 5 creative marketing ideas")
        assert r.category == PromptCategory.CREATIVE

    def test_detect_extraction(self):
        r = self.analyzer.analyze("Extract all email addresses from this text")
        assert r.category == PromptCategory.EXTRACTION

    def test_detect_conversation(self):
        r = self.analyzer.analyze("Hello, how are you today?")
        assert r.category == PromptCategory.CONVERSATION

    def test_detect_instruction(self):
        r = self.analyzer.analyze(
            "Please follow these steps to configure the server"
        )
        assert r.category == PromptCategory.INSTRUCTION

    # ── Complexity Detection ─────────────────────────────────────────────

    def test_simple_complexity(self):
        r = self.analyzer.analyze("Hello world")
        assert r.complexity == ComplexityLevel.SIMPLE

    def test_medium_complexity(self):
        prompt = (
            "I need a system that does X, Y, and Z.\n"
            "Step one: set up the database with proper indexing.\n"
            "Step two: configure the API endpoints.\n"
            "Step three: implement caching.\n\n"
            "Consider: performance, scalability, and cost.\n"
            "Please provide a detailed design."
        )
        r = self.analyzer.analyze(prompt)
        assert r.complexity == ComplexityLevel.MEDIUM

    def test_complex_complexity(self):
        prompt = (
            "Analyze the trade-offs between X and Y. Consider:\n"
            "1. Performance - we need <100ms latency\n"
            "2. Cost - must be under $100/month\n"
            "3. Scalability - must handle 100k users\n"
            "4. Security - must be SOC2 compliant\n"
            "5. Maintenance - team of 3 engineers\n\n"
            "For each approach evaluate: speed, cost, scalability, and DX.\n"
            "Then provide a step-by-step recommendation with reasoning."
        )
        r = self.analyzer.analyze(prompt)
        assert r.complexity == ComplexityLevel.COMPLEX

    # ── Feature Detection ───────────────────────────────────────────────

    def test_detect_language_zh(self):
        r = self.analyzer.analyze("请帮我写一个 Python 函数")
        assert r.language == "zh"

    def test_detect_language_en(self):
        r = self.analyzer.analyze("Write a Python function")
        assert r.language == "en"

    def test_has_code(self):
        r = self.analyzer.analyze("Here's my code: `print(1)`")
        assert r.has_code is True

    def test_has_examples(self):
        r = self.analyzer.analyze(
            "For example:\nInput: hello\nOutput: olleh"
        )
        assert r.has_examples is True

    def test_has_structured_output(self):
        r = self.analyzer.analyze("Return the result as JSON")
        assert r.has_structured_output is True

    # ── Domain Detection ────────────────────────────────────────────────

    def test_domain_programming(self):
        r = self.analyzer.analyze(
            "Write a Python function to query the database API"
        )
        assert "programming" in r.domains

    def test_domain_data_science(self):
        r = self.analyzer.analyze(
            "Train a machine learning model for classification"
        )
        assert "data_science" in r.domains

    def test_domain_finance(self):
        r = self.analyzer.analyze(
            "Analyze this stock portfolio for risk assessment"
        )
        assert "finance" in r.domains
