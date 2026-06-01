# Prompt Rewrite System (PRS) — Project Instructions

## 📦 技术栈
- **语言**: Python ≥ 3.8（推荐 3.11+）
- **构建**: setuptools + pyproject.toml
- **Web UI**: Gradio, FastAPI + Tailwind CSS
- **CLI**: Click
- **依赖管理**: requirements.txt / pip install -e .

## 🚀 常用命令
```bash
pip install -e .         # 安装项目（开发模式）
pip install -r requirements.txt  # 仅安装依赖
python launch_ui.py      # 启动 FastAPI Web UI → http://localhost:8000
python app.py            # 启动 Gradio Web UI → http://localhost:7860
prompt-rewrite "prompt"  # CLI 使用
pytest tests/ -v         # 运行测试
git status               # 检查变更
git add -A && git commit -m "msg"  # 提交
git push                 # 推送
```

## 🏗️ 项目架构

```
src/prompt_rewrite/
├── core/               # 核心引擎
│   ├── analyzer.py     # Prompt 分析器（分类、复杂度、语言、领域）
│   ├── pipeline.py     # Dynamic Workflow 编排引擎
│   ├── workflow_defs.py # 9 个类别的工作流定义
│   └── types.py        # 核心数据类型
├── strategies/         # 7 个重写策略
│   ├── base.py         # 策略基类 + 注册表
│   ├── role_enhancer.py
│   ├── structure_formatter.py
│   ├── chain_of_thought.py
│   ├── constraint_injector.py
│   ├── output_formatter.py
│   ├── example_formatter.py
│   └── context_optimizer.py
├── llm/                # DeepSeek AI 集成（可选）
│   ├── deepseek_client.py
│   ├── llm_analyzer.py
│   └── llm_strategies.py
├── templates/          # YAML 模板
│   ├── roles.yaml
│   ├── constraints.yaml
│   └── patterns.yaml
└── cli.py              # 命令行入口
```

## ⚠️ 核心约束

1. **所有非 `__init__.py` 的源代码文件必须包含 type hints**
2. **策略类必须继承 `BaseStrategy` 并注册到 `StrategyRegistry`**
3. **YAML 模板文件 (`templates/*.yaml`) 是只读数据源**，不要硬编码模板内容到 Python 代码中
4. **DeepSeek API Key 必须通过运行时参数传入**，严禁硬编码
5. **`dist/`、`build/`、`__pycache__/` 目录已 gitignored**
6. **修改 `.gitignore`、`pyproject.toml`、`setup.py` 等配置文件时请先确认影响范围**

## 🧪 测试规范
- 测试文件位于 `tests/`，与被测模块对应（`test_analyzer.py` → `analyzer.py`）
- 新增策略时必须附带对应的单元测试
- 提交前确保 `pytest tests/ -v` 全部通过

## 🔐 安全红线
- 绝对不要在代码中写入任何 API Key、Token 或密码
- 用户输入的 API Key 通过 UI 或 CLI 参数传入，不做持久化存储
- `launch_ui.py` 中的 `host` 保持为 `"127.0.0.1"`，不要改为 `"0.0.0.0"`

## 🌐 部署
- GitHub 仓库: https://github.com/yinsang0910-star/prompt-rewrite
- Hugging Face 在线 Demo: https://yinsang0910-prompt-rewrite.hf.space
- 发布新版本: 创建 tag → GitHub Release（附上 `dist/PromptRewrite.exe`）
