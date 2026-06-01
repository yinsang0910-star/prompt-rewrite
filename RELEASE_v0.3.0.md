# Prompt Rewrite System v0.3.0 — 中文支持增强

## 概述

v0.3.0 聚焦**中文 prompt 处理能力提升**和**代码质量优化**。
所有 8 个分类检测器均增加了中文 pattern，中文实体提取、section 检测全面增强。

---

## ✨ 新特性

### 中文支持全面增强

| 改进 | 说明 |
|------|------|
| **中文分类模式** | 8 个类别（分析/创意/提取/QA/对话/指令/写作/代码）全部增加中文 pattern |
| **中文实体提取** | 支持引号提取（「」""）和技术复合词（XX系统/XX架构/XX方案） |
| **中文 section 检测** | StructureFormatter 支持「任务:」「背景:」「输入:」「输出:」「示例:」标记 |
| **分析类中文关键词** | 分析/评估/对比/权衡/优缺点/利弊 等 |

### 策略改进

| 改进 | 说明 |
|------|------|
| **正则预编译** | 所有分类 pattern 预编译为 `re.compile` 对象，提升匹配性能 |
| **block 分类优化** | ContextOptimizer 使用关键词+标点+长度综合判断，不再仅靠长度 |
| **CoT 检测扩大** | 检测范围从 300 扩大到 1000 字符 |
| **死模板激活** | OutputFormatter 的 comparison/list 模板现在可通过关键词匹配被选中 |

### LLM 增强

| 改进 | 说明 |
|------|------|
| **intent 字段** | AnalysisResult 新增 `intent` 字段，LLM 分析器填充用户意图摘要 |
| **language 校验** | LLM 返回的 language 字段加入白名单校验 |

---

## 🧪 测试

94 测试全部通过，覆盖率 82%。

## 📦 下载

| 平台 | 文件 |
|------|------|
| Windows | `PromptRewrite-windows.exe` |
| macOS | `PromptRewrite-macos` |
| Linux | `PromptRewrite-linux` |
