# 🪄 Prompt Rewrite System (PRS)

> **Rewrite your prompts. Unlock better AI responses.**

---

## Language / 语言 / 言語

| 🌐 | Read this document in |
|----|----------------------|
| 🇨🇳 | [**中文**](#中文版) — 完整中文介绍 |
| 🇺🇸 | [**English**](#english) — Full English documentation |
| 🇯🇵 | [**日本語**](#日本語版) — 日本語ドキュメント |

---

<a name="中文版"></a>

# 🇨🇳 中文版

## 📖 这是什么？

**Prompt Rewrite System (PRS)** 是一个智能提示词重写引擎。你输入一段 prompt，它会自动分析并重新组织，生成结构更清晰、质量更高的优化版本。

> 简单说：把你说的话，翻译成 AI 最容易理解的语言。

**在线体验** → https://yinsang0910-prompt-rewrite.hf.space

---

## 🧸 小白快速通道

| 你的情况 | 怎么做 |
|----------|--------|
| **Windows · 不想装 Python** | 去 [Releases](https://github.com/yinsang0910-star/prompt-rewrite/releases) 下载 `PromptRewrite.exe`，双击运行 |
| **Windows · 有 Python** | 双击 `scripts/start.bat` |
| **macOS** | 双击 `scripts/start_mac.command` 或终端执行 `bash scripts/start.sh` |
| **在线体验 · 什么都不用装** | [点这里](https://yinsang0910-prompt-rewrite.hf.space) |

> 默认使用规则引擎，无需 API Key，开箱即用。
> 想体验 AI 重写？去 [DeepSeek](https://platform.deepseek.com) 免费申请 Key。

---

## 🏗️ 双引擎架构

PRS 采用双层设计，你可以在 Web UI 上自由开关 AI 功能：

### 引擎 A：离线规则引擎（默认开启）

7 条内置策略，按类别自动组合：

| 策略 | 作用 | 什么时候生效 |
|------|------|------------|
| **角色注入** | 让 AI 扮演工程师、分析师等角色 | 非闲聊 prompt |
| **XML 结构化** | 用标签整理指令/上下文/输入 | 所有任务类 prompt |
| **CoT 推理** | 植入「请逐步思考」指令 | 中高难度 prompt |
| **质量约束** | 加入精度、安全、伦理约束 | 代码/指令类 |
| **输出格式** | 明确输出格式要求 | 几乎全部 |
| **示例格式** | 规范化 few-shot 示例 | 当 prompt 含示例时 |
| **上下文排序** | 数据在前、要求在后 | 长 prompt |

### 引擎 B：DeepSeek AI 增强（可选）

| 能力 | 说明 |
|------|------|
| **AI 增强分析** | 规则引擎分不清时，让 AI 来做分类 |
| **AI 深度重写** | 让 AI 从零语义级重写 prompt，非简单模板拼接 |
| **AI 质量验证** | 重写后打分 + 给出改进建议 |

默认模型：`deepseek-v4-flash`（也可切换为 `deepseek-v4-pro`）

> 不填 API Key 时项目完全可用，所有规则功能不受影响。

---

## 🚀 快速开始

### 命令行

```bash
# 安装
pip install -r requirements.txt

# 基本使用
prompt-rewrite "写一个 Python 函数排序字典列表" --verbose

# 预设模式
prompt-rewrite "分析微服务与单体架构的优缺点" --preset full

# 输出到文件
prompt-rewrite "帮我写一封英文邮件" -o optimized.txt
```

### Web UI

```bash
python launch_ui.py
# → 浏览器自动打开 http://localhost:8000
```

### Python API

```python
from prompt_rewrite import RewritePipeline

pipeline = RewritePipeline()
result = pipeline.run("写一个 Python 函数排序字典列表")
print(result.rewritten)
```

---

## 🔬 分析能力

| 维度 | 检测范围 |
|------|---------|
| 类别 | 代码、问答、写作、分析、创意、提取、指令、闲聊 |
| 难度 | 简单 / 中等 / 复杂 |
| 语言 | 中文、英文、日文 |
| 领域 | 编程、数据科学、写作、商业、学术、金融、法律、健康、教育、创意 |
| 特征 | 代码块、示例、结构化输出要求 |

---

## 🗺️ 路线图

- [x] 7 条本地策略 + Dynamic Workflows
- [x] DeepSeek AI 增强（分析/重写/验证）
- [x] CLI + Python API + Web UI
- [x] 三语言支持（中/英/日）
- [ ] LLM-as-judge 自动评估
- [ ] Prompt 版本对比
- [ ] VSCode 插件
- [ ] PyPI 发布

---

## 📄 许可证

MIT © 银桑

---

<a name="english"></a>

# 🇺🇸 English

## 📖 What is this?

**Prompt Rewrite System (PRS)** is a smart prompt optimization engine. Feed it a raw prompt, and it automatically analyzes, restructures, and enhances it — producing a clearer, more effective version optimized for AI models.

> Plain English: It translates your words into what AIs understand best.

**Try it online** → https://yinsang0910-prompt-rewrite.hf.space

---

## 🧸 Quick Start for Beginners

| Your situation | What to do |
|---------------|------------|
| **Windows · No Python** | Download `PromptRewrite.exe` from [Releases](https://github.com/yinsang0910-star/prompt-rewrite/releases), double-click |
| **Windows · Has Python** | Double-click `scripts/start.bat` |
| **macOS** | Double-click `scripts/start_mac.command` or run `bash scripts/start.sh` |
| **Try online · Nothing to install** | [Click here](https://yinsang0910-prompt-rewrite.hf.space) |

> The rule engine works out of the box — no API key needed.
> Want AI-powered rewriting? Get a free key at [DeepSeek](https://platform.deepseek.com).

---

## 🏗️ Dual-Engine Architecture

PRS has two engines. Toggle AI features freely in the Web UI.

### Engine A: Offline Rule Engine (default on)

7 built-in strategies, auto-composed by category:

| Strategy | What it does | When it fires |
|----------|-------------|--------------|
| **Role Injection** | Assigns a role (engineer, analyst, editor...) | Non-chat prompts |
| **XML Structure** | Organizes with `<instructions>`, `<context>`, `<input>` tags | All task prompts |
| **Chain-of-Thought** | Injects step-by-step reasoning instructions | Medium/high complexity |
| **Quality Constraints** | Adds precision, safety, ethics guardrails | Code / instruction prompts |
| **Output Format** | Specifies the expected output format | Almost always |
| **Example Format** | Normalizes few-shot examples | When examples present |
| **Context Reorder** | Puts data first, query last | Long prompts |

### Engine B: DeepSeek AI Enhancement (optional)

| Capability | Description |
|------------|-------------|
| **AI Analysis** | LLM classifies ambiguous prompts the rule engine can't handle |
| **AI Rewrite** | Semantic-level rewrite from scratch (not template-based) |
| **AI Validation** | Scores rewrite quality and suggests improvements |

Default model: `deepseek-v4-flash` (switchable to `deepseek-v4-pro`)

> Without an API key, all rule-engine features work perfectly.

---

## 🚀 Quick Start

### Command Line

```bash
# Install
pip install -r requirements.txt

# Basic usage
prompt-rewrite "Write a Python function to sort a list of dicts" --verbose

# Preset modes
prompt-rewrite "Analyze microservices vs monolith" --preset full

# Output to file
prompt-rewrite "Your prompt here" -o optimized.txt
```

### Web UI

```bash
python launch_ui.py
# → Browser opens at http://localhost:8000
```

### Python API

```python
from prompt_rewrite import RewritePipeline

pipeline = RewritePipeline()
result = pipeline.run("Write a Python function to sort a list")
print(result.rewritten)
```

---

## 🔬 Analysis Capabilities

| Dimension | What's detected |
|-----------|----------------|
| Category | code, qa, writing, analysis, creative, extraction, instruction, conversation |
| Complexity | simple, medium, complex |
| Language | zh, en, ja |
| Domain | programming, data_science, writing, business, academic, finance, law, health, education, creative |
| Features | code blocks, examples, structured output requirements |

---

## 🗺️ Roadmap

- [x] 7 local strategies + Dynamic Workflows
- [x] DeepSeek AI enhancement (analysis/rewrite/validation)
- [x] CLI + Python API + Web UI
- [x] i18n support (CN/EN/JP)
- [ ] LLM-as-judge evaluation
- [ ] Prompt version diffing
- [ ] VSCode extension
- [ ] PyPI release

---

## 📄 License

MIT © 银桑

---

<a name="日本語版"></a>

# 🇯🇵 日本語版

## 📖 これは何？

**Prompt Rewrite System (PRS)** は、あなたのプロンプトを自動的に分析・再構成し、AI にとって最適な形に最適化するエンジンです。

> 簡単に言うと：あなたの言葉を、AI が最も理解しやすい形に翻訳します。

**オンラインで試す** → https://yinsang0910-prompt-rewrite.hf.space

---

## 🧸 初心者向けクイックガイド

| あなたの環境 | 操作方法 |
|-------------|---------|
| **Windows · Python なし** | [Releases](https://github.com/yinsang0910-star/prompt-rewrite/releases) から `PromptRewrite.exe` をダウンロードしてダブルクリック |
| **Windows · Python あり** | `scripts/start.bat` をダブルクリック |
| **macOS** | `scripts/start_mac.command` をダブルクリック、または `bash scripts/start.sh` を実行 |
| **オンラインで試す** | [こちらをクリック](https://yinsang0910-prompt-rewrite.hf.space) |

> ルールエンジンは API キー不要ですぐに使えます。
> AI 機能を試したい方は [DeepSeek](https://platform.deepseek.com) で無料キーを取得してください。

---

## 🏗️ デュアルエンジン構造

PRS は 2 層構造です。Web UI で AI 機能を自由に ON/OFF できます。

### エンジン A：オフラインルールエンジン（デフォルト ON）

7 つのビルトイン戦略：

| 戦略 | 説明 | 発動条件 |
|------|------|---------|
| **ロール注入** | AI に役割を付与（エンジニア、アナリストなど） | 雑談以外 |
| **XML 構造化** | 指示・コンテキスト・入力をタグで整理 | すべてのタスク |
| **CoT 推論** | 「段階的に考えて」を追加 | 中〜高難度 |
| **品質制約** | 精度・安全性・倫理のガードレール | コード・指示系 |
| **出力形式** | 出力フォーマットを指定 | ほぼ常時 |
| **例示フォーマット** | few-shot 例を正規化 | 例が含まれる場合 |
| **コンテキスト最適化** | データを先に、クエリを後に | 長いプロンプト |

### エンジン B：DeepSeek AI 拡張（オプション）

| 機能 | 説明 |
|------|------|
| **AI 分析** | ルールエンジンが分類できないプロンプトを AI が補完 |
| **AI リライト** | テンプレートではなく意味レベルで書き換え |
| **AI 品質検証** | スコアリングと改善提案 |

デフォルトモデル：`deepseek-v4-flash`（`deepseek-v4-pro` にも切替可）

> API キーがなくてもルールエンジンは完全に動作します。

---

## 🚀 クイックスタート

### コマンドライン

```bash
# インストール
pip install -r requirements.txt

# 基本
prompt-rewrite "Write a Python function to sort a list" --verbose

# ファイル出力
prompt-rewrite "あなたのプロンプト" -o optimized.txt
```

### Web UI

```bash
python launch_ui.py
# → ブラウザが http://localhost:8000 を開きます
```

---

## 📄 ライセンス

MIT © 銀桑
