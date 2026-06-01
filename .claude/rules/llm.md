---
paths:
  - "src/prompt_rewrite/llm/**/*.py"
---

# LLM / DeepSeek 集成指南

## 架构
- `deepseek_client.py`: 轻量 API 客户端，基于 `requests`，含自动重试
- `llm_analyzer.py`: LLM 补充分析（规则引擎无法分类时）
- `llm_strategies.py`: LLM 深度重写 + 质量验证

## API 调用
```python
from prompt_rewrite.core.types import LLMConfig
config = LLMConfig(api_key="sk-...", model="deepseek-v4-flash")
```

## 注意事项
- `LLMConfig.api_key` 默认空字符串，`enabled` 属性判断是否启用
- 支持 `from_env()` 从环境变量 `DEEPSEEK_API_KEY` 读取
- 默认 API 端点: `https://api.deepseek.com`
- 默认模型: `deepseek-v4-flash`，可切换为 `deepseek-v4-pro`
- 所有 LLM 调用失败时静默回退到规则引擎结果，不抛异常
