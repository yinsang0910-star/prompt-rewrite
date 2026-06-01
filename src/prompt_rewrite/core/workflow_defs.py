"""
Dynamic Workflow Definitions.

Each prompt category gets its own workflow — an ordered sequence of strategies
optimized for that type of prompt. This replaces the old "one pipeline fits all"
approach with targeted, category-specific orchestration.

Design principles:
1. Each workflow is a CURATED sequence — not auto-sorted by priority
2. Steps can have CONDITIONS (e.g. only for complex prompts)
3. Categories with minimal needs get SHORTER workflows
4. Adding a new category = adding one workflow definition
"""

from __future__ import annotations

from prompt_rewrite.core.types import (
    PromptCategory,
    ComplexityLevel,
    StrategyName,
    WorkflowDef,
    WorkflowStep,
    AnalysisResult,
)

# ── Helper to build steps with complexity gates ─────────────────────────

def _step(
    strategy: StrategyName,
    *,
    min_complexity: ComplexityLevel | None = None,
    params: dict | None = None,
) -> WorkflowStep:
    """Create a workflow step, optionally gated by minimum complexity."""
    condition = None
    if min_complexity:
        condition = f"complexity >= {min_complexity.value}"
    return WorkflowStep(
        strategy=strategy,
        params=params or {},
        condition=condition,
    )


def _s() -> WorkflowStep:
    """Shorthand for StructureFormatter step."""
    return WorkflowStep(strategy=StrategyName.STRUCTURE_FORMATTER)


def _r(role_type: str = "") -> WorkflowStep:
    """Shorthand for RoleEnhancer step with optional type."""
    return WorkflowStep(
        strategy=StrategyName.ROLE_ENHANCER,
        params={"role_type": role_type} if role_type else {},
    )


def _t() -> WorkflowStep:
    """Shorthand for ChainOfThought step."""
    return WorkflowStep(strategy=StrategyName.CHAIN_OF_THOUGHT)


def _c() -> WorkflowStep:
    """Shorthand for ConstraintInjector step."""
    return WorkflowStep(strategy=StrategyName.CONSTRAINT_INJECTOR)


def _o(output_type: str = "") -> WorkflowStep:
    """Shorthand for OutputFormatter step."""
    return WorkflowStep(
        strategy=StrategyName.OUTPUT_FORMATTER,
        params={"output_type": output_type} if output_type else {},
    )


def _e() -> WorkflowStep:
    """Shorthand for ExampleFormatter step."""
    return WorkflowStep(strategy=StrategyName.EXAMPLE_FORMATTER)


def _cx() -> WorkflowStep:
    """Shorthand for ContextOptimizer step."""
    return WorkflowStep(strategy=StrategyName.CONTEXT_OPTIMIZER)


def _g() -> WorkflowStep:
    """Shorthand for RefusalGuard step."""
    return WorkflowStep(strategy=StrategyName.REFUSAL_GUARD)


# ── Workflow Definitions ────────────────────────────────────────────────

# Each workflow is hand-crafted for its category.
# Order matters — steps execute in exactly this sequence.

WORKFLOWS: dict[PromptCategory, WorkflowDef] = {
    # ── CODE ──────────────────────────────────────────────────────────────
    PromptCategory.CODE: WorkflowDef(
        category=PromptCategory.CODE,
        description="代码类 prompt：工程师角色 → 推理 → 约束 → 边界防护 → 输出格式",
        steps=[
            _s(),                          # 1. 结构化
            _r("programming"),             # 2. 注入高级工程师角色
            _t(),                          # 3. 代码推理步骤
            _c(),                          # 4. 代码质量约束
            _g(),                          # 5. 边界防护
            _o("code"),                    # 6. 代码输出格式
        ],
    ),

    # ── QA ────────────────────────────────────────────────────────────────
    PromptCategory.QA: WorkflowDef(
        category=PromptCategory.QA,
        description="问答类 prompt：结构化 → 角色 → （可选输出格式）",
        steps=[
            _s(),                          # 1. 结构化
            _r("qa"),                      # 2. QA 角色
            _o("general"),                 # 3. 通用输出格式
        ],
    ),

    # ── WRITING ───────────────────────────────────────────────────────────
    PromptCategory.WRITING: WorkflowDef(
        category=PromptCategory.WRITING,
        description="写作类 prompt：结构化 → 编辑角色 → 写作输出格式",
        steps=[
            _s(),                          # 1. 结构化
            _r("writing"),                 # 2. 编辑/写作角色
            _o("writing"),                 # 3. 写作输出格式
        ],
    ),

    # ── ANALYSIS ──────────────────────────────────────────────────────────
    PromptCategory.ANALYSIS: WorkflowDef(
        category=PromptCategory.ANALYSIS,
        description="分析类 prompt：结构化 → 分析师角色 → 推理 → 分析报告格式",
        steps=[
            _s(),                          # 1. 结构化
            _r("analysis"),                # 2. 分析师角色
            _t(),                          # 3. 分析推理步骤
            _o("analysis"),                # 4. 分析报告格式
        ],
    ),

    # ── CREATIVE ──────────────────────────────────────────────────────────
    PromptCategory.CREATIVE: WorkflowDef(
        category=PromptCategory.CREATIVE,
        description="创意类 prompt：结构化 → 创意角色 → 输出格式",
        steps=[
            _s(),                          # 1. 结构化
            _r("creative"),                # 2. 创意角色
            _o("writing"),                 # 3. 写作输出格式
        ],
    ),

    # ── EXTRACTION ────────────────────────────────────────────────────────
    PromptCategory.EXTRACTION: WorkflowDef(
        category=PromptCategory.EXTRACTION,
        description="提取类 prompt：结构化 → 工程角色 → 示例格式 → 提取输出格式",
        steps=[
            _s(),                          # 1. 结构化
            _r("programming"),             # 2. 工程角色
            _e(),                          # 3. 示例格式化 (T2.7: 补充覆盖)
            _o("extraction"),              # 4. 结构化输出格式
        ],
    ),

    # ── INSTRUCTION ──────────────────────────────────────────────────────
    PromptCategory.INSTRUCTION: WorkflowDef(
        category=PromptCategory.INSTRUCTION,
        description="指令类 prompt：结构化 → 默认角色 → 约束 → 边界防护 → 上下文优化 → 输出格式",
        steps=[
            _s(),                          # 1. 结构化
            _r("default"),                 # 2. 默认助手角色
            _c(),                          # 3. 通用约束
            _g(),                          # 4. 边界防护
            _cx(),                         # 5. 上下文优化 (T2.7: 补充覆盖)
            _o("general"),                 # 6. 输出格式
        ],
    ),

    # ── CONVERSATION ─────────────────────────────────────────────────────
    # 闲聊类：不应用任何策略，保持原样
    PromptCategory.CONVERSATION: WorkflowDef(
        category=PromptCategory.CONVERSATION,
        description="对话类 prompt：不应用策略（保持自然）",
        steps=[],  # 空 = 不执行任何操作
    ),

    # ── UNKNOWN ──────────────────────────────────────────────────────────
    PromptCategory.UNKNOWN: WorkflowDef(
        category=PromptCategory.UNKNOWN,
        description="未分类 prompt：保守处理，结构化+安全约束+边界防护",
        steps=[
            _s(),                          # 1. 结构化
            _r("default"),                 # 2. 默认角色
            _c(),                          # 3. 安全约束
            _g(),                          # 4. 边界防护
            _o("general"),                 # 5. 通用输出格式
        ],
    ),
}


# ── Helpers ─────────────────────────────────────────────────────────────

def get_workflow(category: PromptCategory) -> WorkflowDef:
    """Get the workflow definition for a prompt category.

    Returns the definition directly (read-only usage by pipeline).
    """
    if category in WORKFLOWS:
        return WORKFLOWS[category]
    return WORKFLOWS[PromptCategory.UNKNOWN]


def evaluate_condition(condition: str | None, analysis: AnalysisResult) -> bool:
    """Evaluate a workflow step condition against the analysis result.

    Supported conditions:
    - "complexity >= medium" → True if complexity >= MEDIUM
    - "complexity >= complex" → True if complexity == COMPLEX
    """
    if condition is None:
        return True

    condition = condition.strip().lower()

    # Parse "complexity >= X"
    if condition.startswith("complexity >="):
        level_str = condition.split(">=")[1].strip()
        try:
            required = ComplexityLevel(level_str)
        except ValueError:
            return True
        level_order = {
            ComplexityLevel.UNKNOWN: 0,
            ComplexityLevel.SIMPLE: 1,
            ComplexityLevel.MEDIUM: 2,
            ComplexityLevel.COMPLEX: 3,
        }
        return level_order.get(analysis.complexity, 0) >= level_order.get(required, 0)

    # Parse "has_code == True"
    if condition == "has_code == true":
        return analysis.has_code

    return True  # Unknown conditions pass through
