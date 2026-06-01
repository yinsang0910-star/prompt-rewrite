#!/usr/bin/env python3
"""
Benchmark Suite for Prompt Rewrite System.

Runs curated prompts through the pipeline and measures:
- Category detection accuracy
- Strategy hit rate
- Output length ratio (rewritten / original)
- Processing time

Usage:
    python -m benchmark.run
    python benchmark/run.py [--output report.json]
"""

from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from prompt_rewrite.core.pipeline import RewritePipeline
from prompt_rewrite.core.types import RewriteConfig, StrategyName


def load_prompts(path: Path | None = None) -> dict[str, list[str]]:
    p = path or Path(__file__).parent / "prompts.json"
    return json.loads(p.read_text(encoding="utf-8"))


def run_benchmarks(output: str | None = None) -> dict:
    prompts = load_prompts()
    pipeline = RewritePipeline()
    results: list[dict] = []
    category_accuracy: dict[str, dict] = {}
    strategy_counts: defaultdict[str, int] = defaultdict(int)
    total = 0
    correct = 0

    for expected_cat, prompt_list in prompts.items():
        cat_correct = 0
        cat_total = 0
        for prompt_text in prompt_list:
            t0 = time.perf_counter()
            r = pipeline.run(prompt_text)
            elapsed = time.perf_counter() - t0

            detected = r.analysis.category.value
            is_correct = detected == expected_cat
            cat_total += 1
            cat_correct += int(is_correct)
            total += 1
            correct += int(is_correct)

            for s in r.applied_strategies:
                strategy_counts[s.value] += 1

            results.append({
                "prompt": prompt_text[:80],
                "expected": expected_cat,
                "detected": detected,
                "correct": is_correct,
                "complexity": r.analysis.complexity.value,
                "strategies": [s.value for s in r.applied_strategies],
                "original_len": len(r.original),
                "rewritten_len": len(r.rewritten),
                "length_ratio": round(len(r.rewritten) / max(len(r.original), 1), 2),
                "time_ms": round(elapsed * 1000, 1),
            })

        category_accuracy[expected_cat] = {
            "correct": cat_correct,
            "total": cat_total,
            "accuracy": round(cat_correct / max(cat_total, 1) * 100, 1),
        }

    report = {
        "total": total,
        "correct": correct,
        "overall_accuracy": round(correct / max(total, 1) * 100, 1),
        "category_accuracy": category_accuracy,
        "strategy_hit_counts": dict(strategy_counts),
        "details": results,
    }

    out_path = output or str(Path(__file__).parent / "report.json")
    Path(out_path).write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Print summary
    print("\nBenchmark Results")
    print(f"{'=' * 50}")
    print(f"Total prompts: {total}")
    print(f"Category accuracy: {report['overall_accuracy']}%")
    print("\nPer-category accuracy:")
    for cat, acc in category_accuracy.items():
        bar = "#" * int(acc['accuracy'] / 5)
        print(f"  {cat:15s} {acc['accuracy']:5.1f}% {bar} ({acc['correct']}/{acc['total']})")
    print("\nStrategy hit counts:")
    for s, c in sorted(strategy_counts.items(), key=lambda x: -x[1]):
        print(f"  {s:25s} {c}")
    avg_time = sum(d['time_ms'] for d in results) / max(len(results), 1)
    print(f"\nAvg processing time: {avg_time:.1f}ms")
    print(f"Report saved to: {out_path}")

    return report


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else None
    run_benchmarks(out)
