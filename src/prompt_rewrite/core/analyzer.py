"""Prompt Analyzer — classifies raw prompts for targeted rewrite strategies."""

from __future__ import annotations

import re
from typing import Optional

from prompt_rewrite.core.types import (
    AnalysisResult,
    PromptCategory,
    ComplexityLevel,
)

# ── category detection patterns (precompiled for performance) ──────────────────

_CODE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"```\w*\s*\n",          # code fences
    r"(def |class |import |from |function|const |let |var )",
    r"(print\(|console\.log|return |=>\s*\{)",
    r"(SELECT |INSERT |UPDATE |DELETE |CREATE TABLE)",
    r"(git |npm |pip |docker )",
    r"(write a function|implement|refactor|debug|code review)",
]]

_WRITING_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"(write an? \w*\s*(essay|article|story|poem|report|email|letter))",
    r"(rewrite|paraphrase|summarize|translate)",
    r"(proofread|grammar|polish|tone|style)",
    r"(improve this (writing|text|paragraph))",
    r"(draft|outline|blog post|newsletter)",
    # Chinese writing patterns
    r"(写.*(文章|博客|报告|故事|邮件|信|稿))",
    r"(翻译|润色|改写|总结|摘要|校对)",
    r"(语法|风格|语调|措辞|修辞|文风)",
]]

_ANALYSIS_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"(compare and contrast|analyze|evaluate|explain why)",
    r"(pros and cons|advantages?|disadvantages?)",
    r"(root cause|impact|implication|significance)",
    r"(break down|deconstruct|examine|investigate)",
    r"(what if|how does|why does|what causes)",
    r"(architecture|system design|architecture design)",
    r"(trade.?offs|tradeoffs|trade offs)",
    r"(design a (system|architecture|solution|platform))",
    # Chinese analysis patterns
    r"(分析|评估|对比|权衡|优缺点|利弊|影响|意义)",
    r"(设计.*(系统|架构|方案|平台))",
    r"(为什么|怎么回事|根本原因|深层原因)",
]]

_CREATIVE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"(brainstorm|generate ideas|creative writing)",
    r"(come up with|imagine|invent)",
    r"(design a (logo|poster|ui|interface|homepage|website|dashboard))",
    r"(story (idea|setting|character|plot))",
    r"\b(names?|slogans?|taglines?|brand names?)\b",
    r"(what would happen if|alternate)",
    r"(write a (poem|story|song|script))",
    r"(creative|artistic|aesthetic)",
    # Chinese creative patterns
    r"(头脑风暴|创意|灵感|构思|想象)",
    r"(设计.*(logo|海报|界面|网页|仪表盘))",
]]

_EXTRACTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"(extract|parse|convert this (to|into))",
    r"(structured data|JSON|CSV|table|schema)",
    r"(pull out|gather|collect|list all)",
    r"(named entities|keywords?|summary)",
    r"(from this text|from the following)",
    # Chinese extraction patterns
    r"(提取|解析|转换|结构化)",
    r"(从.*(中提取|中解析|中找出))",
    r"(关键词|摘要|实体|表格)",
]]

_QA_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"^(what|who|where|when|why|how|which)",
    r"(tell me about|explain|define|describe)",
    r"(difference between|meaning of|example of)",
    r"(\?$)",  # ends with question mark
    r"(clarify|confused about|wondering)",
    # Chinese QA patterns
    r"^(什么是|谁是|在哪|为什么|怎么|如何|哪个)",
    r"(告诉我|解释一下|定义|描述)",
    r"(区别|含义|意思|是什么)",
]]

_CONVERSATION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"\b(hello|hi|hey)\b",
    r"\b(good morning|good evening|good afternoon)\b",
    r"\b(how are you|nice to meet|what'?s up|how do you do)\b",
    r"\b(thanks|thank you|appreciate it)\b",
    # Chinese conversation patterns
    r"(你好|嗨|早上好|晚上好|下午好)",
    r"(谢谢|感谢|怎么样|最近好吗)",
]]

_INSTRUCTION_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r"(please |i need you to|your task is)",
    r"(act as|you are a|role.?play|as an? )",
    r"(follow these steps|step [1-9]|step.by.step)",
    r"(do not |don'?t |never |always )",
    r"(output|return|respond with|format)",
    r"(provide a detailed )",
    r"(write a (tutorial|guide|walkthrough|how.to))",
    r"(create a (tutorial|guide|walkthrough|step.by.step))",
    r"(how to (set up|configure|install|deploy|build|create|use))",
    r"(set up|configure|install|deploy) .* (server|container|environment|pipeline|service)",
    # Chinese instruction patterns
    r"(请|你需要|你的任务是|帮我)",
    r"(作为|扮演|你是|角色扮演)",
    r"(按照.*步骤|第[1-9]步|不要|必须|始终)",
    r"(教程|指南|入门|搭建|配置|部署|安装)",
]]

# ── language detection ───────────────────────────────────────────────────────

_CJK_PATTERN = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]")
_EN_PATTERN = re.compile(r"[a-zA-Z]{2,}")
_JP_PATTERN = re.compile(r"[\u3040-\u309f\u30a0-\u30ff]")

# ── domain keywords ──────────────────────────────────────────────────────────

_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "programming": ["python", "javascript", "java", "typescript", "go", "rust",
                    "function", "class", "api", "database", "algorithm",
                    "frontend", "backend", "fullstack", "docker", "kubernetes"],
    "data_science": ["machine learning", "deep learning", "neural network",
                     "statistics", "regression", "classification", "dataset",
                     "training", "model", "feature", "tensorflow", "pytorch"],
    "writing": ["essay", "article", "blog", "story", "poem", "novel",
                "paragraph", "sentence", "grammar", "proofread"],
    "business": ["strategy", "marketing", "revenue", "growth", "product",
                 "customer", "market", "sales", "roi", "kpi"],
    "academic": ["research", "paper", "thesis", "citation", "reference",
                 "hypothesis", "methodology", "literature review", "study"],
    "finance": ["stock", "invest", "portfolio", "asset", "risk", "trading",
                "option", "future", "derivative", "financial"],
    "law": ["contract", "legal", "compliance", "regulation", "policy",
            "clause", "liability", "statute"],
    "health": ["medical", "symptom", "diagnosis", "treatment", "patient",
               "drug", "disease", "therapy", "clinical"],
    "education": ["lesson", "curriculum", "student", "teacher", "course",
                  "syllabus", "assignment", "homework", "tutorial"],
    "creative": ["art", "design", "music", "film", "photography", "paint",
                 "draw", "creative", "aesthetic", "color"],
}


class PromptAnalyzer:
    """Analyzes a raw prompt and returns structured metadata.

    Detection methodology:
    - Category: scored pattern matching
    - Complexity: length + instruction count + reasoning cues
    - Language: CJK/JP/EN ratio
    - Domain: keyword frequency matching
    """

    def analyze(self, text: str) -> AnalysisResult:
        """Run full analysis on the input text."""
        text_stripped = text.strip()
        if not text_stripped:
            return AnalysisResult()

        return AnalysisResult(
            category=self._detect_category(text_stripped),
            complexity=self._detect_complexity(text_stripped),
            language=self._detect_language(text_stripped),
            has_examples=self._has_examples(text_stripped),
            has_code=self._has_code(text_stripped),
            has_structured_output=self._has_structured_output(text_stripped),
            estimated_tokens=self._estimate_tokens(text_stripped),
            domains=self._detect_domains(text_stripped),
            key_entities=self._extract_key_entities(text_stripped),
            raw_length=len(text_stripped),
        )

    def _detect_category(self, text: str) -> PromptCategory:
        """Classify prompt into a category using weighted pattern scoring."""
        scores: dict[PromptCategory, int] = {cat: 0 for cat in PromptCategory}

        # Weight rationale: categories with fewer/more specific patterns get weight 3
        # to avoid false negatives; categories with many broad patterns (CODE, QA,
        # CONVERSATION, INSTRUCTION) get weight 2 to reduce false positives.
        for pattern in _CODE_PATTERNS:
            if pattern.search(text):
                scores[PromptCategory.CODE] += 2

        for pattern in _WRITING_PATTERNS:
            if pattern.search(text):
                scores[PromptCategory.WRITING] += 3

        for pattern in _ANALYSIS_PATTERNS:
            if pattern.search(text):
                scores[PromptCategory.ANALYSIS] += 3

        for pattern in _CREATIVE_PATTERNS:
            if pattern.search(text):
                scores[PromptCategory.CREATIVE] += 3

        for pattern in _EXTRACTION_PATTERNS:
            if pattern.search(text):
                scores[PromptCategory.EXTRACTION] += 3

        for pattern in _QA_PATTERNS:
            if pattern.search(text):
                scores[PromptCategory.QA] += 2

        for pattern in _CONVERSATION_PATTERNS:
            if pattern.search(text):
                scores[PromptCategory.CONVERSATION] += 2

        for pattern in _INSTRUCTION_PATTERNS:
            if pattern.search(text):
                scores[PromptCategory.INSTRUCTION] += 2

        best = max(scores, key=scores.get)
        if scores[best] == 0:
            # Fallback: if text is very short and ends with ?, it's QA
            if text.strip().endswith("?") and len(text) < 200:
                return PromptCategory.QA
            return PromptCategory.UNKNOWN
        return best

    def _detect_complexity(self, text: str) -> ComplexityLevel:
        """Estimate complexity based on length, structure, and reasoning cues."""
        length = len(text)
        lines = text.count("\n") + 1

        # Count instruction-like structures
        step_count = len(re.findall(
            r"(step\s+\d+|step\s+(one|two|three|four|five)|first|second|then|finally|after that|next)",
            text, re.IGNORECASE
        ))
        numbered_items = len(re.findall(
            r"^\s*\d+[.、)\s]",
            text, re.MULTILINE
        ))
        constraint_count = len(re.findall(
            r"(must|should|need\s+(to|a|the)|required|condition|if.*then|unless|consider(ations)?|requirements)",
            text, re.IGNORECASE
        ))
        reasoning_cues = len(re.findall(
            r"(because|reason|explain|why|how|compare|analyze|evaluate|trade.?off)",
            text, re.IGNORECASE
        ))
        bullet_items = len(re.findall(
            r"^\s*[-*+]\s",
            text, re.MULTILINE
        ))

        complexity_score = (
            (1 if length > 200 else 0) +
            (1 if length > 800 else 0) +
            (1 if length > 2000 else 0) +
            min(step_count + numbered_items // 3, 3) +
            min(constraint_count // 2, 3) +
            min(reasoning_cues, 3) +
            (1 if lines > 10 else 0) +
            (1 if bullet_items > 3 else 0)
        )

        if complexity_score <= 2:
            return ComplexityLevel.SIMPLE
        elif complexity_score <= 5:
            return ComplexityLevel.MEDIUM
        else:
            return ComplexityLevel.COMPLEX

    def _detect_language(self, text: str) -> str:
        """Detect primary natural language using character-level ratios.

        Fixes: previous version compared character counts (CJK) with word counts (EN),
        which is inconsistent (apples vs oranges). Now uses character ratios for all.
        """
        total = len(text.strip())
        if total == 0:
            return "unknown"

        cjk_chars = len(_CJK_PATTERN.findall(text))
        jp_chars = len(_JP_PATTERN.findall(text))
        en_chars = len(re.findall(r"[a-zA-Z]", text))

        cjk_ratio = cjk_chars / total
        jp_ratio = jp_chars / total
        en_ratio = en_chars / total

        # Japanese kana are unique to Japanese — check first
        if jp_ratio > 0.05:
            return "ja"
        # CJK > 10% of total characters → Chinese
        if cjk_ratio > 0.10:
            return "zh"
        # English letters > 30% → English
        if en_ratio > 0.30:
            return "en"
        return "unknown"

    def _has_code(self, text: str) -> bool:
        """Check if the prompt contains code blocks or inline code."""
        return bool(
            re.search(r"```", text)
            or re.search(r"(?<!`)`[^`\n]+`(?!`)", text)
        )

    def _has_examples(self, text: str) -> bool:
        """Check if the prompt contains examples (input/output patterns)."""
        patterns = [
            r"example",
            r"e\.g\.",
            r"for instance",
            r"for example",
            r"such as",
            r"input:.*output:",
            r"👉",
            r"入参.*出参",
            r"示例",
            r"例子",
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _has_structured_output(self, text: str) -> bool:
        """Check if the prompt requests a specific output format.

        Tightened: broad words like "output"/"return"/"format" alone are NOT enough;
        they must appear near a format specifier (JSON, CSV, etc.) or be part of a
        clear output-format instruction.
        """
        patterns = [
            r"(output|return|respond|format)\s*(as|in|into)\s*(JSON|CSV|YAML|XML|table|markdown)",
            r"(as JSON|as CSV|as YAML|as XML|as table|as markdown)",
            r"(in the format|structured like|formatted as)",
            r"(output format|response format|expected output)\s*[:：]",
            r"\bschema\b",
            r"markdown table",
            r"\bjson\b",
        ]
        return any(re.search(p, text, re.IGNORECASE) for p in patterns)

    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (~4 chars per token for EN, ~2 for CJK)."""
        cjk_chars = len(_CJK_PATTERN.findall(text))
        en_part = len(re.sub(r"[\u0080-\uffff]", " ", text))
        return (cjk_chars // 2) + (en_part // 4) + 1

    def _detect_domains(self, text: str) -> list[str]:
        """Detect knowledge domains present in the prompt."""
        text_lower = text.lower()
        found: list[str] = []
        for domain, keywords in _DOMAIN_KEYWORDS.items():
            for kw in keywords:
                if re.search(r"\b" + re.escape(kw) + r"\b", text_lower):
                    found.append(domain)
                    break
        return found

    def _extract_key_entities(self, text: str) -> list[str]:
        """Extract key named entities and technical terms (EN + CN)."""
        entities: list[str] = []

        # Terms in backticks
        backtick_terms = re.findall(r"`([^`]+)`", text)
        entities.extend(t.strip() for t in backtick_terms if len(t.strip()) > 1)

        # Capitalized multi-word phrases (potential proper nouns) — English
        phrases = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b", text)
        entities.extend(p for p in phrases if len(p) > 5)

        # Chinese technical terms: 2-4 char phrases in quotes or brackets
        cn_quoted = re.findall(r"[「『“](.*?)[」』”]", text)
        entities.extend(t.strip() for t in cn_quoted if 1 < len(t.strip()) <= 10)

        # Chinese compound nouns (技术/系统/架构/方案/框架/模型/算法/接口)
        cn_tech = re.findall(
            r"[一-鿿]{2,6}(?:技术|系统|架构|方案|框架|模型|算法|接口|服务|模块|组件)",
            text,
        )
        entities.extend(cn_tech)

        # Unique only, max 10
        seen: set[str] = set()
        result: list[str] = []
        for e in entities:
            if e.lower() not in seen:
                seen.add(e.lower())
                result.append(e)
            if len(result) >= 10:
                break

        return result
