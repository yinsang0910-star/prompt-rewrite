"""
CLI entry point for the Prompt Rewrite System.
Usage: prompt-rewrite [OPTIONS] [PROMPT_FILE]
"""

from __future__ import annotations

import sys
from typing import Optional

import click

from prompt_rewrite.core.types import (
    RewriteConfig,
    StrategyName,
    LLMConfig,
)
# Pipeline imported lazily inside main() to allow step-by-step development


def _read_input(prompt_text: Optional[str] = None) -> str:
    """Read prompt from argument, file, or stdin."""
    if prompt_text:
        # Try as file first, then as literal text
        try:
            with open(prompt_text, "r", encoding="utf-8") as f:
                return f.read()
        except (FileNotFoundError, OSError):
            return prompt_text
    # Read from stdin
    return sys.stdin.read()


STRATEGY_OPTIONS = {
    "all": [s.value for s in StrategyName],
    "basic": [
        StrategyName.ROLE_ENHANCER.value,
        StrategyName.STRUCTURE_FORMATTER.value,
        StrategyName.OUTPUT_FORMATTER.value,
    ],
    "full": [
        StrategyName.ROLE_ENHANCER.value,
        StrategyName.STRUCTURE_FORMATTER.value,
        StrategyName.CHAIN_OF_THOUGHT.value,
        StrategyName.CONSTRAINT_INJECTOR.value,
        StrategyName.OUTPUT_FORMATTER.value,
        StrategyName.EXAMPLE_FORMATTER.value,
        StrategyName.CONTEXT_OPTIMIZER.value,
    ],
}


@click.command(
    name="prompt-rewrite",
    help="Prompt Rewrite System — 智能 Prompt 优化工具",
)
@click.argument("prompt", required=False)
@click.option(
    "-p", "--preset",
    type=click.Choice(["basic", "full", "all", "minimal"]),
    default="full",
    help="策略预设 (default: full)",
)
@click.option(
    "-s", "--strategies",
    multiple=True,
    help="单独启用指定策略 (覆盖 preset)",
)
@click.option(
    "--lang",
    default="auto",
    help="输出语言 (auto / zh / en)",
)
@click.option(
    "--style",
    type=click.Choice(["instruction", "system_prompt", "chat_ml"]),
    default="instruction",
    help="输出格式风格 (default: instruction)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="输出详细分析信息",
)
@click.option(
    "--show-diff",
    is_flag=True,
    help="显示重写前后的 diff",
)
@click.option(
    "--no-cot",
    is_flag=True,
    help="禁用 Chain-of-Thought 注入",
)
@click.option(
    "--provider",
    type=click.Choice(["deepseek", "openai", "claude", "ollama"]),
    default="deepseek",
    help="LLM 供应商 (default: deepseek)",
)
@click.option(
    "--api-key",
    default=None,
    help="LLM API Key (Ollama 不需要)",
)
@click.option(
    "--model",
    default=None,
    help="LLM 模型名 (留空使用推荐模型)",
)
@click.option(
    "-o", "--output",
    type=click.Path(writable=True),
    help="输出到文件而非 stdout",
)
def main(
    prompt: Optional[str] = None,
    preset: str = "full",
    strategies: tuple[str, ...] = (),
    lang: str = "auto",
    style: str = "instruction",
    verbose: bool = False,
    show_diff: bool = False,
    no_cot: bool = False,
    provider: str = "deepseek",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    output: Optional[str] = None,
) -> None:
    """Prompt Rewrite System — 读取原始 prompt，输出优化后的高质量 prompt。"""

    raw = _read_input(prompt)
    if not raw.strip():
        click.echo("错误: 请输入 prompt 文本", err=True)
        sys.exit(1)

    # Lazy import pipeline (allows step-by-step development)
    from prompt_rewrite.core.pipeline import RewritePipeline

    # Resolve strategies
    if strategies:
        enabled = [StrategyName(s) for s in strategies]
    elif preset == "minimal":
        enabled = [StrategyName.STRUCTURE_FORMATTER]
    elif preset == "basic":
        enabled = [StrategyName.ROLE_ENHANCER, StrategyName.STRUCTURE_FORMATTER, StrategyName.OUTPUT_FORMATTER]
    elif preset == "full":
        enabled = [s for s in StrategyName]  # all
    else:
        enabled = [s for s in StrategyName]

    if no_cot and StrategyName.CHAIN_OF_THOUGHT in enabled:
        enabled.remove(StrategyName.CHAIN_OF_THOUGHT)

    # Determine if LLM is enabled
    llm_enabled = bool(api_key) or provider == "ollama"

    config = RewriteConfig(
        enabled_strategies=enabled,
        language=lang,
        output_style=style,
        add_refusal_guard=True,
        inject_chain_of_thought=not no_cot,
        # LLM enhancement
        llm_config=LLMConfig(
            provider=provider,
            api_key=api_key or "",
            **({"model": model} if model else {}),
        ),
        llm_enhance_rewrite=llm_enabled,
        llm_enhance_analysis=llm_enabled,
    )

    pipeline = RewritePipeline(config)
    result = pipeline.run(raw)

    out_lines = []
    if verbose:
        out_lines.append("=" * 60)
        out_lines.append("📊 Prompt 分析结果")
        out_lines.append("=" * 60)
        a = result.analysis
        out_lines.append(f"  类别:     {a.category.value}")
        out_lines.append(f"  复杂度:   {a.complexity.value}")
        out_lines.append(f"  语言:     {a.language}")
        out_lines.append(f"  领域:     {', '.join(a.domains) or '未检测'}")
        out_lines.append(f"  预估 Tokens: {a.estimated_tokens}")
        out_lines.append(f"  原始长度: {a.raw_length} 字符")
        out_lines.append(f"  含代码:   {'是' if a.has_code else '否'}")
        out_lines.append(f"  含示例:   {'是' if a.has_examples else '否'}")
        out_lines.append("")
        if result.workflow_name:
            out_lines.append(f"  工作流:   {result.workflow_name}")
        out_lines.append("")
        out_lines.append("应用策略:")
        for s in result.applied_strategies:
            out_lines.append(f"  ✅ {s.value}")
        out_lines.append("")
        out_lines.append("─" * 60)

    out_lines.append("")
    out_lines.append(result.rewritten)
    out_lines.append("")

    if show_diff:
        out_lines.append("─" * 60)
        out_lines.append("📝 变更摘要:")
        out_lines.append(result.diff_summary)
        out_lines.append("")

    final = "\n".join(out_lines)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(final)
        click.echo(f"✅ 已写入 {output}")
    else:
        click.echo(final)


if __name__ == "__main__":
    main()
