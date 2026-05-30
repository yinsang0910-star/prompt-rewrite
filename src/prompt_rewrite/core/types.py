"""
Core data types for the Prompt Rewrite System.
Core data types for the Prompt Rewrite System.
"""

from __future__ import annotations

import enum
import os
from dataclasses import dataclass, field
from typing import Optional


class PromptCategory(str, enum.Enum):
    """Input prompt categories — detected by the analyzer."""
    QA = "qa"                     # 问答
    CODE = "code"                 # 代码生成 / 调试
    WRITING = "writing"           # 写作 / 润色
    ANALYSIS = "analysis"         # 分析 / 推理
    CREATIVE = "creative"         # 创意 / 头脑风暴
    EXTRACTION = "extraction"     # 信息提取 / 结构化
    INSTRUCTION = "instruction"   # 指令 / 任务描述
    CONVERSATION = "conversation" # 对话 / 闲聊
    UNKNOWN = "unknown"           # 未分类


class ComplexityLevel(str, enum.Enum):
    """Estimated complexity of the input prompt."""
    SIMPLE = "simple"             # 单步，不需要推理
    MEDIUM = "medium"             # 多步，少量推理
    COMPLEX = "complex"           # 多步推理，需要规划
    UNKNOWN = "unknown"           # 无法判断


class StrategyName(str, enum.Enum):
    """Available rewrite strategies."""
    ROLE_ENHANCER = "role_enhancer"               # 角色注入
    STRUCTURE_FORMATTER = "structure_formatter"   # XML 标签结构化 — 类似 <thinking> <answer>
    CHAIN_OF_THOUGHT = "chain_of_thought"         # 推理脚手架 — 类似 "think step by step"
    CONSTRAINT_INJECTOR = "constraint_injector"   # 约束注入 — 类似 constitutional principles
    OUTPUT_FORMATTER = "output_formatter"         # 输出格式 — 类似 structured output
    EXAMPLE_FORMATTER = "example_formatter"       # 示例格式化 — 类似 <example> 标签
    CONTEXT_OPTIMIZER = "context_optimizer"       # 上下文排序 — "data first, query last"
    REFUSAL_GUARD = "refusal_guard"               # 边界防护 — 类似 refusal policies


@dataclass
class AnalysisResult:
    """Result of analyzing an input prompt."""
    category: PromptCategory = PromptCategory.UNKNOWN
    complexity: ComplexityLevel = ComplexityLevel.UNKNOWN
    language: str = "unknown"                      # 检测到的自然语言
    has_examples: bool = False                     # 是否包含示例
    has_code: bool = False                         # 是否包含代码块
    has_structured_output: bool = False            # 是否指定了输出格式
    estimated_tokens: int = 0                      # 预估 token 数
    domains: list[str] = field(default_factory=list)  # 检测到的领域
    key_entities: list[str] = field(default_factory=list)  # 关键实体/概念
    raw_length: int = 0                            # 原始字符长度


@dataclass
class RewriteResult:
    """The result of a rewrite operation."""
    original: str
    rewritten: str
    analysis: AnalysisResult
    config: RewriteConfig
    applied_strategies: list[StrategyName] = field(default_factory=list)
    workflow_steps: list[StrategyName] = field(default_factory=list)
    workflow_name: str = ""
    diff_summary: str = ""


@dataclass
class WorkflowStep:
    """A single step in a dynamic workflow.

    Unlike the old static pipeline where all strategies run in priority order,
    a WorkflowStep is a targeted, ordered application of one strategy
    with category-specific parameters.
    """
    strategy: StrategyName
    params: dict = field(default_factory=dict)  # Strategy-specific overrides
    condition: Optional[str] = None  # e.g. "complexity >= MEDIUM"


@dataclass
class WorkflowDef:
    """Definition of a dynamic workflow for one prompt category.

    A workflow is an ordered sequence of steps that are APPLIED
    in exactly this order — not sorted by priority.
    """
    category: PromptCategory
    steps: list[WorkflowStep]
    description: str = ""


@dataclass
class LLMConfig:
    """LLM 连接配置 — 用户自备 API Key，纯本地控制。"""
    api_key: str = ""
    api_base: str = "https://api.deepseek.com"
    model: str = "deepseek-chat"
    temperature: float = 0.3
    max_tokens: int = 2048
    timeout: int = 30
    max_retries: int = 2

    @property
    def enabled(self) -> bool:
        return bool(self.api_key)

    @classmethod
    def from_env(cls) -> LLMConfig:
        return cls(api_key=os.environ.get("DEEPSEEK_API_KEY", ""))


@dataclass
class RewriteConfig:
    """Configuration for the rewrite pipeline.
    Strategies are defined in enabled_strategies.
    """
    enabled_strategies: list[StrategyName] = field(default_factory=lambda: [
        StrategyName.ROLE_ENHANCER,
        StrategyName.STRUCTURE_FORMATTER,
        StrategyName.CONTEXT_OPTIMIZER,
        StrategyName.OUTPUT_FORMATTER,
    ])
    inject_chain_of_thought: bool = True
    language: str = "auto"
    verbosity: str = "balanced"
    add_refusal_guard: bool = True
    preserve_user_examples: bool = True
    output_style: str = "instruction"
    # LLM 增强选项
    llm_config: LLMConfig = field(default_factory=LLMConfig)
    llm_enhance_analysis: bool = False     # 用 LLM 补充分析
    llm_enhance_rewrite: bool = False      # 用 LLM 重写 prompt
    llm_validate: bool = False             # 用 LLM 校验结果


@dataclass
class Prompt:
    """A prompt being processed by the system."""
    raw: str
    analysis: Optional[AnalysisResult] = None
    config: Optional[RewriteConfig] = None

    def analyze(self) -> AnalysisResult:
        """Run analysis if not already done."""
        from prompt_rewrite.core.analyzer import PromptAnalyzer
        if self.analysis is None:
            self.analysis = PromptAnalyzer().analyze(self.raw)
        return self.analysis
