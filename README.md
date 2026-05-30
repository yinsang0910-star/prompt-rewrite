# Prompt Rewrite System (PRS)

> **智能 Prompt 重写引擎 — 本地策略规则 + DeepSeek AI 增强双层架构**

PRS 是一个双引擎 prompt 重写系统，内置 **7 条 prompt engineering 本地策略**，可完全离线运行；同时可选接入 **DeepSeek API** 实现 AI 语义级重写、增强分析与质量验证。

---

## 🧸 小白快速通道

| 你的情况 | 怎么做 |
|----------|--------|
| **Windows 用户·不想装 Python** | 去 [Releases](https://github.com/yinsang0910-star/prompt-rewrite/releases) 下载 `PromptRewrite.exe`，双击运行 |
| **Windows 用户·装了 Python** | 双击 `scripts/start.bat` |
| **macOS 用户** | 双击 `scripts/start_mac.command`，或在终端执行 `bash scripts/start.sh` |
| **任何系统·想用命令行** | `pip install -r requirements.txt` → `python launch_ui.py` |

> 默认使用**规则引擎**，无需任何 API Key，开箱即用。
> 想体验 AI 重写？去 [DeepSeek](https://platform.deepseek.com) 免费申请 API Key。

---

## 🚀 10 秒快速体验（有 Python 环境）

```bash
pip install -r requirements.txt
python launch_ui.py
# → 浏览器自动打开 http://localhost:8000
```

---

## 🏗️ 双引擎架构

```
                         ┌──────────────────────┐
                         │    Original Prompt    │
                         └──────────┬───────────┘
                                    ▼
                     ┌──────────────────────────┐
                     │    PromptAnalyzer        │
                     │  · 类别检测 (8类)         │
                     │  · 复杂度评估 (3级)       │
                     │  · 语言识别 (zh/en/ja)    │
                     │  · 领域检测 (10领域)       │
                     │  · 特征检测 (代码/示例等)   │
                     └──────────┬───────────────┘
                                    ▼
            ┌───────────────────────────────────────┐
            │                                       │
            ▼                                       ▼
  ┌─────────────────────┐              ┌────────────────────────┐
  │  Engine A: 规则引擎   │              │  Engine B: DeepSeek AI  │
  │  (零依赖 · 离线运行)  │              │  (可选 · 需 API Key)    │
  │                     │              │                        │
  │  7 条 prompt 策略：   │   ┌───────  │  · LLM 增强分析         │
  │  · 角色注入           │   │ 可选    │  · LLM 语义重写          │
  │  · XML 结构化         │   │        │  · LLM 质量验证          │
  │  · CoT 推理注入       │   │        │                        │
  │  · 质量/安全约束       │   │        │  默认模型:               │
  │  · 输出格式约束        │   │        │  deepseek-v4-flash      │
  │  · Few-shot 格式化    │   │        │                        │
  │  · 上下文重排序        │   │        │                        │
  └─────────┬───────────┘  │        └───────────┬────────────┘
            │              │                    │
            └──────────────┴────────────────────┘
                           ▼
               ┌────────────────────┐
               │  Optimized Prompt  │
               └────────────────────┘
```

### 引擎 A：规则引擎（默认激活，零依赖）

7 条基于 prompt engineering 最佳实践的本地策略，按 Dynamic Workflow 自动编排：

| 策略 | 作用 | 触发条件 |
|------|------|----------|
| **RoleEnhancer** | 注入角色身份（工程师/分析师/编辑等） | 非闲聊类 prompt |
| **StructureFormatter** | XML 标签结构化（instructions/context/input） | 所有任务类 prompt |
| **ChainOfThoughtInjector** | 植入「逐步推理」思考脚手架 | 中/高复杂度 prompt |
| **ConstraintInjector** | 质量与安全约束注入 | 代码/指令类 prompt |
| **OutputFormatter** | 输出格式约束 | 几乎全部 |
| **ExampleFormatter** | Few-shot 示例格式化 | 含示例时 |
| **ContextOptimizer** | 数据在前、查询在后的上下文排序 | 长 prompt |

每条策略的 `should_apply` 方法决定是否在当前 prompt 上生效，而非无脑全开。

### 引擎 B：DeepSeek AI 增强（可选，需 API Key）

接入 DeepSeek Chat API（默认模型 `deepseek-v4-flash`），提供三层能力：

| 能力 | 说明 | 触发方式 |
|------|------|----------|
| **LLM 增强分析** | 当规则引擎无法分类时（如模糊 prompt、跨领域），用 LLM 做补充分类 | `--enhance-analysis` |
| **LLM 语义重写** | 从零开始对原始 prompt 做语义级深度重写，非模板拼接 | `--enhance-rewrite` |
| **LLM 质量验证** | 对重写结果打分 + 给出改进建议 | `--validate` |

> 不传 API Key 时项目完全可用，所有规则引擎功能不受影响。

---

## 💡 工作流（Dynamic Workflows）

每个 prompt 类别走专属工作流，非固定流水线：

```
Analyze → 按类别路由:
    ├─ CODE:        Structure → Role(engineer) → CoT → Constraint → Output
    ├─ QA:          Structure → Role(qa) → Output
    ├─ ANALYSIS:    Structure → Role(analyst) → CoT → Output(analysis)
    ├─ WRITING:     Structure → Role(writer) → Output(writing)
    ├─ CREATIVE:    Structure → Role(creative) → Output(writing)
    ├─ EXTRACTION:  Structure → Role(engineer) → Output(extraction)
    ├─ INSTRUCTION: Structure → Role(default) → Constraint → Output
    ├─ CONVERSATION: [不处理，原样返回]
    └─ UNKNOWN:     Structure → Role(default) → Constraint(safety) → Output
```

---

## 📦 安装

```bash
# 方式一：源码安装（推荐）
pip install -e .

# 方式二：仅安装依赖
pip install -r requirements.txt
```

## 🖥️ 使用方式

### 命令行

```bash
# 基础使用
prompt-rewrite "Write a Python function to sort a list"

# 显示详细分析信息
prompt-rewrite "Explain recursion" --verbose

# 预设模式
prompt-rewrite "Analyze the trade-offs..." --preset full
prompt-rewrite "Write a blog post" --preset basic
prompt-rewrite "Do X" --preset minimal

# 输出到文件
prompt-rewrite "Your prompt here" -o optimized.txt
```

### Web UI（Gradio）

```bash
python launch_ui.py
# → http://localhost:8000
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

### Python API（带 AI 增强）

```python
from prompt_rewrite import RewritePipeline, RewriteConfig
from prompt_rewrite.core.types import LLMConfig

config = RewriteConfig(
    llm_config=LLMConfig(api_key="sk-xxxxxxxxxxxxxxxx"),
    llm_enhance_analysis=True,    # AI 增强分析
    llm_enhance_rewrite=True,     # AI 深度重写
    llm_validate=True,            # AI 质量验证
)
pipeline = RewritePipeline(config=config)
result = pipeline.run("帮我分析这个架构方案的优缺点")
```

## 🔬 分析能力

| 维度 | 检测范围 |
|------|---------|
| 类别 | code, qa, writing, analysis, creative, extraction, instruction, conversation |
| 复杂度 | simple, medium, complex（基于长度 + 指令数量 + 推理线索评分） |
| 语言 | zh, en, ja（基于 CJK/JP 字符比例） |
| 领域 | programming, data_science, writing, business, academic, finance, law, health, education, creative |
| 特征 | 代码块检测、示例检测、结构化输出要求检测 |

## 🧪 测试

```bash
pytest tests/ -v
```

## 🗺️ 路线图

- [x] 核心分析器与 7 个重写策略
- [x] Dynamic Workflows 动态编排
- [x] YAML 模板库（角色/约束/模式）
- [x] CLI 与 Python API
- [x] Web UI（Gradio + FastAPI，三语言支持）
- [x] DeepSeek AI 增强（分析/重写/验证）
- [ ] LLM-as-judge 自动评估重写质量
- [ ] 更多语言支持（ja, ko, fr, de）
- [ ] Prompt 版本对比和 A/B 测试
- [ ] VSCode 插件

## 🔧 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python ≥ 3.8 |
| 规则引擎 | 纯 Python + YAML 模板，零外部依赖 |
| AI 引擎 | DeepSeek Chat API（`deepseek-v4-flash` / `deepseek-v4-pro` 可选） |
| Web UI | Gradio / FastAPI + Tailwind CSS |
| CLI | Click |
| 构建 | setuptools + pyproject.toml |

## 📄 许可证

MIT © 银桑
