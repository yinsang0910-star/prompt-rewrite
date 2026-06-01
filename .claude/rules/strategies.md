---
paths:
  - "src/prompt_rewrite/strategies/**/*.py"
---

# 策略开发指南

## 实现新策略的步骤
1. 在 `src/prompt_rewrite/strategies/` 下创建新文件
2. 继承 `BaseStrategy`，实现 `apply()` 和 `should_apply()` 方法
3. 策略类会自动被 `StrategyRegistry` 注册（通过 `__init_subclass__`）
4. 在 `workflow_defs.py` 中将新策略加入对应类别的工作流
5. 在 `tests/test_strategies.py` 中添加测试

## 策略基类接口
```python
class BaseStrategy:
    name: StrategyName          # 枚举值，自动注册
    priority: int = 0           # 优先级（仅静态管线使用）
    
    def apply(self, prompt: str, analysis: AnalysisResult, config: RewriteConfig) -> str
    def should_apply(self, analysis: AnalysisResult, config: RewriteConfig) -> bool
```

## 已有策略一览
| 策略 | 文件 | 触发条件 |
|------|------|----------|
| RoleEnhancer | `role_enhancer.py` | 非闲聊类 prompt |
| StructureFormatter | `structure_formatter.py` | 所有任务类 |
| ChainOfThoughtInjector | `chain_of_thought.py` | 中/高复杂度 |
| ConstraintInjector | `constraint_injector.py` | 代码/指令类 |
| OutputFormatter | `output_formatter.py` | 几乎全部 |
| ExampleFormatter | `example_formatter.py` | 含示例时 |
| ContextOptimizer | `context_optimizer.py` | 长 prompt |
