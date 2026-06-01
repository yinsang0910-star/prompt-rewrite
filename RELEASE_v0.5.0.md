# Prompt Rewrite System v0.5.0 — 多 LLM 支持

## 概述

v0.5.0 打破了对 DeepSeek 的单一依赖，支持 **4 种 LLM 供应商**：

| 供应商 | 模型 | 适用场景 |
|--------|------|----------|
| **DeepSeek** | deepseek-v4-flash/pro | 性价比高，中文能力强 |
| **OpenAI** | GPT-4o / GPT-4o-mini | 最强综合能力 |
| **Claude** | Sonnet 4 / Haiku 3.5 / Opus 4 | 长上下文，推理能力强 |
| **Ollama** | qwen2.5 / llama3.1 / mistral 等 | **本地运行，完全免费** |

---

## ✨ 新特性

### 多 LLM 供应商

```python
from prompt_rewrite import RewritePipeline, RewriteConfig, LLMConfig

# 使用 OpenAI GPT-4o
config = RewriteConfig(
    llm_config=LLMConfig(provider="openai", api_key="sk-...", model="gpt-4o"),
    llm_enhance_rewrite=True,
)

# 使用 Claude Sonnet
config = RewriteConfig(
    llm_config=LLMConfig(provider="claude", api_key="sk-ant-...", model="claude-sonnet-4-20250514"),
    llm_enhance_rewrite=True,
)

# 使用本地 Ollama（无需 API Key）
config = RewriteConfig(
    llm_config=LLMConfig(provider="ollama", model="qwen2.5:7b"),
    llm_enhance_rewrite=True,
)
```

### CLI 多供应商

```bash
# DeepSeek（默认）
prompt-rewrite --provider deepseek --api-key sk-xxx "写一个排序算法"

# OpenAI
prompt-rewrite --provider openai --api-key sk-xxx --model gpt-4o "Write a sort function"

# Claude
prompt-rewrite --provider claude --api-key sk-ant-xxx "分析这个架构"

# Ollama 本地（不需要 API Key）
prompt-rewrite --provider ollama --model qwen2.5:7b "Hello"
```

### 架构

- `BaseLLMClient` 抽象基类 — 统一接口 `chat()` / `chat_json()` / `chat_with_context()`
- `create_llm_client(config)` 工厂函数 — 根据 `provider` 自动创建对应客户端
- 共享重试逻辑（Timeout / 429 / 5xx 指数退避）

---

## 🧪 测试

116 测试全部通过（+22 新增 provider 测试）。

## 📦 下载

| 平台 | 文件 |
|------|------|
| Windows | `PromptRewrite-windows.exe` |
| macOS | `PromptRewrite-macos` |
| Linux | `PromptRewrite-linux` |
