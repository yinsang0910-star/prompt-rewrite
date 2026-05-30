# Prompt Rewrite System v0.2.0 — Initial Public Release

## 概述

PRS 是一个**双引擎架构**的智能 prompt 重写系统：

- **引擎 A：规则引擎** — 内置 7 条 prompt engineering 本地策略，**零外部依赖，完全离线运行**
- **引擎 B：AI 引擎** — 可选接入 **DeepSeek API**（默认模型 `deepseek-v4-flash`），实现语义级重写、增强分析与质量验证

不传 API Key 时项目完全可用，所有规则引擎功能不受影响。

---

## ✨ 核心特性

### 7 条本地策略（离线可用）

| 策略 | 说明 |
|------|------|
| **RoleEnhancer** | 角色注入（工程师 / 分析师 / 编辑 / QA 等） |
| **StructureFormatter** | XML 标签结构化（`<instructions>` / `<context>` / `<input>`） |
| **ChainOfThoughtInjector** | CoT 逐步推理脚手架 |
| **ConstraintInjector** | 质量与安全约束（精度 / 完整性 / 安全性 / 伦理） |
| **OutputFormatter** | 输出格式约束（结构 / 一致性 / 正向指令） |
| **ExampleFormatter** | Few-shot 示例格式化 |
| **ContextOptimizer** | 上下文重排序（数据在前，查询在后） |

### Dynamic Workflows — 按类别动态编排

```
CODE:        Structure → Role(engineer) → CoT → Constraint → Output
QA:          Structure → Role(qa) → Output
ANALYSIS:    Structure → Role(analyst) → CoT → Output(analysis)
WRITING:     Structure → Role(writer) → Output(writing)
CREATIVE:    Structure → Role(creative) → Output(writing)
EXTRACTION:  Structure → Role(engineer) → Output(extraction)
INSTRUCTION: Structure → Role(default) → Constraint → Output
CONVERSATION:[跳过，原样返回]
UNKNOWN:     Structure → Role(default) → Constraint(safety) → Output
```

### AI 增强（可选，需 DeepSeek API Key）

| 能力 | 说明 |
|------|------|
| **LLM 增强分析** | 规则引擎无法分类时，用 LLM 补充分类和领域识别 |
| **LLM 语义重写** | 从零开始对原始 prompt 做语义级深度重写（非模板拼接） |
| **LLM 质量验证** | 对重写结果评分 + 改进建议 |

支持的模型：`deepseek-v4-flash`（默认）/ `deepseek-v4-pro`

### 分析能力

- **8 类 prompt 检测**：code / qa / writing / analysis / creative / extraction / instruction / conversation
- **3 级复杂度评估**：simple / medium / complex（基于长度 + 指令 + 推理线索评分）
- **3 语言识别**：zh / en / ja（基于 CJK/JP 字符比例）
- **10 个领域关键词库**：programming / data_science / writing / business / academic / finance / law / health / education / creative
- **3 项特征检测**：代码块 / 示例 / 结构化输出要求

### 界面

- **Gradio Web UI** — 三语言支持（中/英/日），shadcn/ui 风格暗色主题
- **FastAPI + Tailwind CSS Web UI** — 响应式设计，支持 AI 面板配置
- **CLI 命令行工具** — 支持 verbose / diff / 文件输出
- **跨平台启动脚本** — Windows（.bat）/ macOS（.sh / .command）

---

## 🚀 快速开始

```bash
# 方式一：源码安装
pip install -e .

# 方式二：仅安装依赖
pip install -r requirements.txt

# 启动 Web UI
python launch_ui.py
# → 浏览器自动打开 http://localhost:8000

# 或命令行使用
prompt-rewrite "Write a Python function to sort a list" --verbose
```

---

## 📦 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python ≥ 3.8 |
| 规则引擎 | 纯 Python + YAML 模板（`templates/roles.yaml` / `constraints.yaml` / `patterns.yaml`） |
| AI 引擎 | DeepSeek Chat API（`api.deepseek.com`） |
| Web UI | Gradio、FastAPI |
| 前端 | Tailwind CSS、shadcn/ui 风格 |
| CLI | Click |
| 构建 | setuptools + pyproject.toml |

---

## 🔗 链接

- GitHub: https://github.com/yinsang0910-star/prompt-rewrite
- DeepSeek API 申请: https://platform.deepseek.com
