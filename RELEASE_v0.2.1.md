# Prompt Rewrite System v0.2.1 — 安全与质量加固

## 概述

v0.2.1 是一个以**安全修复、可靠性提升、工程质量加固**为核心的版本。
通过多 Agent 深度分析发现了 52 项问题，本版本修复了其中 P0（9 项）和 P1（18 项）共 **27 项**高优先级问题。

测试用例 55 → **94**（+71%），覆盖率 ~40% → **82%**。

---

## 🔴 P0 安全修复（8 项）

| 修复 | 说明 |
|------|------|
| **安全红线** | `app.py` 的 `server_name` 从 `"0.0.0.0"` 改为 `"127.0.0.1"`，符合安全约束 |
| **类型安全** | `RewriteResult` dataclass 正式声明 `_llm_error` / `_llm_score` / `_llm_feedback` 字段，消除运行时动态属性注入 |
| **策略名语义** | 新增 `StrategyName.LLM_REWRITE` 枚举，LLM 重写结果不再伪装为 `CONTEXT_OPTIMIZER` |
| **Timeout 重试** | DeepSeek 客户端的 Timeout 异常现在进入重试循环，指数退避（`min(2^attempt, 8)` 秒） |
| **429 重试** | HTTP 429 (Rate Limit) 现在会读取 `Retry-After` header 并重试 |
| **Prompt Injection 防护** | 所有发送给 LLM 的用户输入使用 `---BEGIN/END USER INPUT---` delimiter 隔离，system prompt 增加注入防护指令 |
| **last_raw 清空** | 每次 API 调用前清空上次的原始返回数据，避免误导 |
| **示例代码修复** | `examples/basic_usage.py` 的 `StrategyName` import 移到模块顶部，消除 NameError |

## 🟡 P1 质量提升（15 项）

### 分析器改进

| 改进 | 说明 |
|------|------|
| **语言检测修复** | 使用字符级比例（cjk_ratio / en_ratio）替代原来不一致的字符数 vs 词数比较 |
| **结构化输出检测收紧** | 消除 "format"、"output"、"return" 等宽泛单词的误报，要求与格式说明符配对出现 |
| **分类权重文档化** | 为评分权重差异（2 vs 3）添加文档说明理由 |

### Pipeline 改进

| 改进 | 说明 |
|------|------|
| **异常处理分级** | 区分编程错误（`TypeError`/`AttributeError` → `log.error`）和可恢复异常（`log.warning`） |
| **run_with_strategies** | 使用 `dataclasses.replace()` 保留原 config 的 LLM 设置，不再丢失 |
| **移除 deepcopy** | `get_workflow()` 热路径上移除不必要的深拷贝 |

### 策略改进

| 改进 | 说明 |
|------|------|
| **workflow 策略覆盖** | EXTRACTION 类别补充 `ExampleFormatter`，INSTRUCTION 类别补充 `ContextOptimizer` |
| **StructureFormatter header** | 仅删除纯标签行（如 `Context:`），保留含实质内容的行 |
| **CoT 模板激活** | debate / comparison 模板现在可通过关键词检测被选中 |
| **安全约束扩大** | CODE 和 CREATIVE 类别也添加安全约束 |

### LLM 模块改进

| 改进 | 说明 |
|------|------|
| **线程安全** | 替换共享 `requests.Session` 为无状态的 `requests.post()` 调用 |
| **dead code 修复** | `LLMRewriter` 的 `extra` 变量（domain 信息）注入到实际 prompt 中 |
| **prompt 截断** | LLM prompt 限制 4000 字符，避免 token 浪费 |

### 工程改进

| 改进 | 说明 |
|------|------|
| **CLI --api-key** | 新增 `--api-key` 和 `--model` 命令行选项，CLI 可直接调用 LLM |
| **依赖拆分** | 核心依赖仅 `pyyaml` / `click` / `requests`；UI 框架移至 `[project.optional-dependencies] web` |

---

## 🧪 测试

| 指标 | v0.2.0 | v0.2.1 |
|------|--------|--------|
| 测试用例 | 55 | **94**（+71%） |
| 覆盖率 | ~40% | **82%** |
| 测试文件 | 3 | **6** |

新增测试文件：

| 文件 | 用例数 | 覆盖范围 |
|------|--------|----------|
| `tests/test_deepseek_client.py` | 13 | 重试逻辑、last_raw、线程安全、JSON 解析 |
| `tests/test_llm_analyzer.py` | 10 | 增强逻辑、注入防护、回退机制 |
| `tests/test_cli.py` | 16 | 参数解析、预设、LLM 选项、帮助文档 |

---

## 📋 变更文件清单

```
修改 (15):
  app.py                                    — 安全红线修复
  examples/basic_usage.py                   — import 修复
  pyproject.toml                            — 依赖拆分
  src/prompt_rewrite/cli.py                 — --api-key / --model 选项
  src/prompt_rewrite/core/analyzer.py       — 语言检测 + 输出检测 + 权重文档
  src/prompt_rewrite/core/pipeline.py       — 异常分级 + config 保留
  src/prompt_rewrite/core/types.py          — LLM_REWRITE 枚举 + RewriteResult 字段
  src/prompt_rewrite/core/workflow_defs.py  — 策略覆盖 + 移除 deepcopy
  src/prompt_rewrite/llm/deepseek_client.py — 重试逻辑 + 线程安全
  src/prompt_rewrite/llm/llm_analyzer.py    — 注入防护
  src/prompt_rewrite/llm/llm_strategies.py  — dead code + 截断 + 注入防护
  src/prompt_rewrite/strategies/chain_of_thought.py    — CoT 模板激活
  src/prompt_rewrite/strategies/constraint_injector.py — 安全约束扩大
  src/prompt_rewrite/strategies/structure_formatter.py — header 修复
  tests/test_pipeline.py                    — 适配 get_workflow 变更

新增 (3):
  tests/test_deepseek_client.py             — 13 个用例
  tests/test_llm_analyzer.py                — 10 个用例
  tests/test_cli.py                         — 16 个用例
```

---

## 🔜 后续计划（v0.3.0）

- **中文支持增强**：中文实体提取、中文 section 检测
- **策略间协调**：统一 StructureFormatter / ContextOptimizer 的 section 解析
- **BaseLLMClient 抽象层**：支持 DeepSeek / GPT / Claude / Ollama 多 provider
- **策略自动注册**：装饰器机制，新增策略只需 1 个文件
- **端到端集成测试**：9 类别 × 3 复杂度 = 27 场景全覆盖
