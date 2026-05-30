# Contributing

感谢您考虑为 Prompt Rewrite System 贡献代码！

## 开发环境

```bash
# 克隆仓库后
pip install -e .
pip install pytest  # 运行测试
```

## 代码规范

- 遵循 PEP 8 编码风格
- 类型注解：所有公开函数须包含 type hints
- 文档字符串：模块级和类级 docstring 使用英文，功能说明使用中英文均可
- 测试：新增功能须附带 pytest 测试

## 提交 PR

1. Fork 本仓库
2. 创建特性分支：`feat/your-feature-name`
3. 提交变更
4. 确保 `pytest tests/ -v` 全部通过
5. 发起 Pull Request

## 项目结构

```
src/prompt_rewrite/
├── core/          # 核心引擎（分析器、管线、类型、工作流定义）
├── strategies/    # 7 种重写策略
├── llm/           # DeepSeek API 集成（可选）
├── templates/     # YAML 模板库
└── cli.py         # 命令行入口
```

## 许可证

本仓库采用 MIT 许可证。
