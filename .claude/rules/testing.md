---
paths:
  - "tests/**/*.py"
  - "src/**/*.py"
---

# 测试与代码质量规范

## 测试编写
- 使用 pytest，测试类以 `Test` 开头，测试方法以 `test_` 开头
- 测试文件命名：`test_<模块名>.py`
- 使用 `setup_method` 初始化测试环境
- 新增策略或核心逻辑必须附带测试

## 运行测试
```bash
pytest tests/ -v                    # 全部测试
pytest tests/test_analyzer.py -v    # 单个文件
pytest -k "test_code" -v            # 按关键字过滤
```

## 测试覆盖范围
- 每个 `StrategyName` 的 `apply()` 和 `should_apply()` 方法
- 每个 `PromptCategory` 的分类检测
- 边界条件（空输入、超长输入、特殊字符）
- Dynamic Workflow 路由正确性
