# Prompt Rewrite System v0.4.0 — 三语言模板支持

## 概述

v0.4.0 为所有重写策略添加了**中文、英文、日文**三语言模板支持。
系统根据检测到的输入语言自动选择对应语言的模板，输出与输入语言一致。

---

## ✨ 核心特性

### 三语言模板（EN / ZH / JA）

| 策略 | 模板数量 | 说明 |
|------|----------|------|
| **RoleEnhancer** | 14 角色 × 3 语言 | 工程师/分析师/编辑/教育者/金融等角色定义 |
| **ChainOfThought** | 6 类型 × 3 语言 | 通用/代码/分析/数学/辩论/对比推理模板 |
| **ConstraintInjector** | 5 类别 × 3 语言 | 质量/安全/格式约束 + 学术/代码等类别 |
| **OutputFormatter** | 7 格式 × 3 语言 | 通用/代码/分析/写作/对比/列表/提取输出格式 |

### 语言选择逻辑

```
输入: "请帮我写一个排序算法"
→ 检测语言: zh
→ 角色: "你是一名资深软件工程师..."
→ 推理: "请按以下步骤逐步解决..."
→ 约束: "请保持精确和准确..."
→ 输出: "以结构化列表的形式提供..."

输入: "Write a sorting algorithm"
→ 检测语言: en
→ 角色: "You are a senior software engineer..."
→ 推理: "Work through this problem step by step..."
→ 约束: "Be precise and accurate..."
→ 输出: "Provide your solution in the following format..."
```

---

## 📦 下载

| 平台 | 文件 |
|------|------|
| Windows | `PromptRewrite-windows.exe` |
| macOS | `PromptRewrite-macos` |
| Linux | `PromptRewrite-linux` |
