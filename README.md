# Prompt Rewrite System (PRS)

> **基于 Prompt Engineering 最佳实践的 Prompt 重写引擎**

## 概述

PRS 是一个智能 prompt 重写系统，自动分析原始用户 prompt，并应用 prompt engineering 最佳实践，生成结构清晰、质量更高的优化 prompt。

### 核心策略

| 策略 | 说明 |
|---|---|
| `StructureFormatter` | XML 标签结构化（instructions / context / input） |
| `RoleEnhancer` | 角色注入（工程师 / 分析师 / 编辑等） |
| `ChainOfThoughtInjector` | CoT 推理脚手架 |
| `ConstraintInjector` | 质量与安全约束 |
| `OutputFormatter` | 输出格式约束 |
| `ExampleFormatter` | Few-shot 示例格式化 |
| `ContextOptimizer` | 上下文排序（数据在前，查询在后） |

### Dynamic Workflows

每个 prompt 类别走专属工作流，而非固定流水线：

```
Analyze → 按类别路由:
    ├─ CODE:      Structure → Role(engineer) → CoT → Constraint → Output    [5步]
    ├─ QA:        Structure → Role(qa) → Output                              [3步]
    ├─ ANALYSIS:  Structure → Role(analyst) → CoT → Output(analysis)         [4步]
    ├─ WRITING:   Structure → Role(writer) → Output(writing)                 [3步]
    ├─ CREATIVE:  Structure → Role(creative) → Output(writing)               [3步]
    ├─ EXTRACTION:Structure → Role(engineer) → Output(extraction)            [3步]
    ├─ INSTRUCTION:Structure → Role(default) → Constraint → Output           [4步]
    ├─ CONVERSATION:[不处理]                                                  [0步]
    └─ UNKNOWN:   Structure → Role(default) → Constraint(safety) → Output    [4步]
```

## 快速开始

### 安装

```bash
pip install -e .
```

### 命令行使用

```bash
# 基本用法
prompt-rewrite "Write a Python function to sort a list"

# 显示详细分析信息
prompt-rewrite "Explain recursion" --verbose

# 完整模式（默认）
prompt-rewrite "Analyze the trade-offs..." --preset full

# 基础模式（仅角色 + 结构 + 输出格式）
prompt-rewrite "Write a blog post about AI" --preset basic

# 输出到文件
prompt-rewrite "Your prompt here" -o optimized.txt

# 从文件读取
prompt-rewrite my_prompt.txt
```

### Web UI

```bash
python launch_ui.py
# 浏览器打开 http://localhost:7860
```

### Python API

```python
from prompt_rewrite import RewritePipeline

pipeline = RewritePipeline()
result = pipeline.run("Write a Python function to sort a list")

print(f"分类: {result.analysis.category.value}")
print(f"工作流: {result.workflow_name}")
print(f"应用策略: {[s.value for s in result.applied_strategies]}")
print(f"重写结果:\n{result.rewritten}")
```

## 架构

```
src/prompt_rewrite/
├── core/
│   ├── analyzer.py        # Prompt 分析器（分类、复杂度、语言、领域）
│   ├── pipeline.py        # Dynamic Workflow 编排引擎
│   ├── workflow_defs.py   # 所有类别的工作流定义
│   └── types.py           # 核心数据类型
├── strategies/
│   ├── base.py            # 策略基类 + 注册表
│   ├── role_enhancer.py
│   ├── structure_formatter.py
│   ├── chain_of_thought.py
│   ├── constraint_injector.py
│   ├── output_formatter.py
│   ├── example_formatter.py
│   └── context_optimizer.py
├── templates/
│   ├── roles.yaml
│   ├── constraints.yaml
│   └── patterns.yaml
└── cli.py
```

## 分析能力

| 维度 | 检测内容 |
|---|---|
| 类别 | code, qa, writing, analysis, creative, extraction, instruction, conversation |
| 复杂度 | simple, medium, complex |
| 语言 | zh, en, ja |
| 领域 | programming, data_science, writing, business, academic, finance, law, health, education, creative |
| 特征 | 是否含代码、示例、结构化输出要求 |

## 测试

```bash
pytest tests/ -v
```

## 路线图

- [x] 核心分析器与 7 个重写策略
- [x] Dynamic Workflows 动态编排
- [x] YAML 模板库
- [x] CLI 与 Python API
- [x] Web UI（Gradio）
- [ ] LLM-as-judge 自动评估重写质量
- [ ] 更多语言支持（ja, ko, fr, de）
- [ ] Prompt 版本对比和 A/B 测试
- [ ] VSCode 插件

## 许可证

MIT
