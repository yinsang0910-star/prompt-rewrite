# Prompt Rewrite System v0.6.0 — YAML 模板系统

## 概述

v0.6.0 还清了项目最大的技术债：**YAML 模板系统正式上线**。

之前 `roles.yaml`（295 行）和 `constraints.yaml` 设计了但完全没用，模板全硬编码在代码里。
现在所有角色和约束都从 YAML 文件加载，支持三语言，支持用户自定义覆盖。

---

## ✨ 核心变更

### TemplateLoader 模板加载器

新增 `templates/loader.py`，提供：

| 功能 | 说明 |
|------|------|
| **YAML 加载** | 从 `roles.yaml` / `constraints.yaml` 加载模板 |
| **i18n 支持** | 每个模板有 en/zh/ja 三个版本 |
| **用户覆盖** | `~/.prompt_rewrite/templates/` 目录的模板优先于内置 |
| **懒加载 + 缓存** | 首次访问时加载，后续命中缓存 |

### YAML 模板更新

**roles.yaml** — 14 个角色 × 3 语言：

| 角色 | 适用场景 |
|------|----------|
| programming | 代码生成/调试 |
| data_science | 数据分析/ML |
| writing | 写作/润色 |
| analysis | 分析/推理 |
| creative | 创意/设计 |
| business | 商业咨询 |
| academic | 学术研究 |
| finance | 金融分析 |
| education | 教育/教学 |
| law | 法律分析 |
| health | 医学研究 |
| qa | 问答 |
| code | 编程 |
| default | 通用助手 |

**constraints.yaml** — 约束模板 × 3 语言：

| 类别 | 子类别 |
|------|--------|
| quality | general / code / writing / analysis / academic |
| safety | harm_prevention / professional_boundaries / ip_protection |
| formatting | structure / positive_instruction / consistency |
| ethics | transparency / fairness |

### 用户自定义模板

用户可以通过放置 YAML 文件来自定义任何模板：

```bash
# 创建自定义目录
mkdir ~/.prompt_rewrite/templates/

# 复制内置模板
cp src/prompt_rewrite/templates/roles.yaml ~/.prompt_rewrite/templates/

# 编辑自定义版本
# ~/.prompt_rewrite/templates/roles.yaml 的内容会覆盖内置模板
```

自定义目录的模板优先级高于内置模板，无需修改代码。

---

## 🧪 测试

135 测试全部通过（+19 新增模板加载测试）。

| 测试文件 | 用例数 | 覆盖范围 |
|----------|--------|----------|
| test_template_loader.py | 19 | YAML 加载、i18n、回退、缓存、集成 |

## 📦 下载

| 平台 | 文件 |
|------|------|
| Windows | `PromptRewrite-windows.exe` |
| macOS | `PromptRewrite-macos` |
| Linux | `PromptRewrite-linux` |
