#!/usr/bin/env python
"""Prompt Rewrite System — 基本使用示例."""

from prompt_rewrite import RewritePipeline, RewriteConfig


def demo_basic():
    """基础用法：默认配置重写一个代码 prompt."""
    pipeline = RewritePipeline()
    result = pipeline.run("Write a Python function to sort a list of dictionaries by a key")

    print("=" * 60)
    print("📥 原始 Prompt:")
    print("=" * 60)
    print(result.original)
    print()
    print("📊 分析结果:")
    print(f"  类别:     {result.analysis.category.value}")
    print(f"  复杂度:   {result.analysis.complexity.value}")
    print(f"  语言:     {result.analysis.language}")
    print(f"  领域:     {', '.join(result.analysis.domains) or '未检测'}")
    print(f"  预估 Tokens: {result.analysis.estimated_tokens}")
    print()
    print(f"应用策略: {[s.value for s in result.applied_strategies]}")
    print()
    print("📤 重写后的 Prompt:")
    print("=" * 60)
    print(result.rewritten)


def demo_custom_config():
    """自定义配置：仅使用结构和角色策略."""
    config = RewriteConfig(
        enabled_strategies=[
            StrategyName.ROLE_ENHANCER,
            StrategyName.STRUCTURE_FORMATTER,
        ],
        inject_chain_of_thought=False,
    )
    pipeline = RewritePipeline(config=config)
    result = pipeline.run("Explain the concept of recursion to a beginner")

    print("=" * 60)
    print("📥 原始 Prompt:")
    print(result.original)
    print()
    print("📤 重写结果 (仅角色 + 结构):")
    print("=" * 60)
    print(result.rewritten)


def demo_analysis_prompt():
    """分析型 prompt 的重写."""
    pipeline = RewritePipeline()
    prompt = """Analyze the trade-offs between REST and GraphQL for a real-time dashboard.

Consider:
1. Data fetching efficiency - 20+ widgets per dashboard
2. Caching strategy - some data updates every second
3. Team expertise - mostly familiar with REST
4. Performance - dashboard must load in under 2 seconds

Evaluate each approach: development speed, runtime performance, and scaling cost."""
    
    result = pipeline.run(prompt)
    print("=" * 60)
    print("📥 分析型 Prompt 重写结果:")
    print("=" * 60)
    print(f"分类: {result.analysis.category.value}")
    print(f"复杂度: {result.analysis.complexity.value}")
    print(f"应用策略: {[s.value for s in result.applied_strategies]}")
    print()
    print(result.rewritten)


def demo_zh_prompt():
    """中文 prompt 的重写."""
    pipeline = RewritePipeline()
    result = pipeline.run("请帮我写一个 Python 函数，读取 CSV 文件并计算每列的平均值")

    print("=" * 60)
    print("📥 中文 Prompt 重写结果:")
    print("=" * 60)
    print(f"检测语言: {result.analysis.language}")
    print(f"分类: {result.analysis.category.value}")
    print()
    print(result.rewritten)


if __name__ == "__main__":
    from prompt_rewrite.core.types import StrategyName

    print("\n🔧 Prompt Rewrite System — 使用示例\n")
    
    demo_basic()
    print("\n" + "=" * 60 + "\n")
    
    demo_custom_config()
    print("\n" + "=" * 60 + "\n")
    
    demo_analysis_prompt()
    print("\n" + "=" * 60 + "\n")
    
    demo_zh_prompt()
