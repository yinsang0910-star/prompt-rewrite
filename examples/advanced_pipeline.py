#!/usr/bin/env python
"""Prompt Rewrite System — 高级 Pipeline 使用示例."""

from prompt_rewrite import RewritePipeline
from prompt_rewrite.core.types import StrategyName


def demo_compare_presets():
    """对比不同预设的输出."""
    prompts = [
        ("简单问答", "What is Python?"),
        ("代码任务", "Write a function to find duplicates in a list"),
        ("复杂分析", """Analyze the impact of microservices migration on team productivity.

Before: monolith, 10 devs, 2-week release cycle, 50% test coverage
After: 8 microservices, 4 teams of 2-3 devs, daily deployments, 80% test coverage

Measure: deployment frequency, lead time, MTTR, change failure rate."""),
    ]

    presets = {
        "minimal": [StrategyName.STRUCTURE_FORMATTER],
        "basic": [StrategyName.ROLE_ENHANCER, StrategyName.STRUCTURE_FORMATTER, StrategyName.OUTPUT_FORMATTER],
        "full": [s for s in StrategyName],
    }

    for name, prompt in prompts:
        print(f"\n{'='*60}")
        print(f"📝 {name}")
        print(f"原始: {prompt[:80]}...")
        print(f"{'='*60}")

        for preset_name, strategies in presets.items():
            from prompt_rewrite.core.types import RewriteConfig
            config = RewriteConfig(enabled_strategies=strategies)
            pipeline = RewritePipeline(config=config)
            result = pipeline.run(prompt)
            
            print(f"\n  [{preset_name}] 策略数: {len(result.applied_strategies)}")
            print(f"  重写后长度: {len(result.rewritten)} 字符")
            print(f"  应用: {[s.value for s in result.applied_strategies]}")
        
        print()


def demo_batch_rewrite():
    """批量重写多个 prompt."""
    prompts = [
        "Write a Python decorator that measures execution time",
        "Please review this code for potential bugs",
        "Compare Flask vs FastAPI for building REST APIs",
        "Write a SQL query to find the top 10 customers by revenue",
    ]

    pipeline = RewritePipeline()

    print(f"{'='*60}")
    print(f"📦 批量重写 ({len(prompts)} prompts)")
    print(f"{'='*60}")

    for i, prompt in enumerate(prompts, 1):
        result = pipeline.run(prompt)
        print(f"\n[{i}] ({result.analysis.category.value:>12}) {prompt[:50]}...")
        print(f"    → 策略: {[s.value for s in result.applied_strategies]}")
        print(f"    → 长度: {len(prompt)} → {len(result.rewritten)} 字符")


if __name__ == "__main__":
    print("🔬 Prompt Rewrite System — 高级使用示例\n")
    
    demo_compare_presets()
    demo_batch_rewrite()
