"""
CLI entry point for the Prompt Rewrite System.
Usage: prompt-rewrite [OPTIONS] [PROMPT_FILE]
"""

from __future__ import annotations

import pathlib
import sys
from typing import Optional

import click

from prompt_rewrite.core.types import (
    RewriteConfig,
    StrategyName,
    LLMConfig,
)
from prompt_rewrite.core.history import RewriteHistory
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
        StrategyName.REFUSAL_GUARD.value,
        StrategyName.OUTPUT_FORMATTER.value,
        StrategyName.EXAMPLE_FORMATTER.value,
        StrategyName.CONTEXT_OPTIMIZER.value,
    ],
}



# -- i18n messages for CLI output --
_MESSAGES = {
    "zh": {
        "empty_input": "错误: 请输入 prompt 文本",
        "written_to": "✅ 已写入 {}",
    },
    "en": {
        "empty_input": "Error: please provide prompt text",
        "written_to": "✅ Written to {}",
    },
}

def _msg(key: str, lang: str = "zh", *args) -> str:
    """Lookup an i18n message by key, falling back to zh."""
    table = _MESSAGES.get(lang, _MESSAGES["zh"])
    text = table.get(key, _MESSAGES["zh"].get(key, key))
    if args:
        return text.format(*args)
    return text

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
@click.option(
    "--history",
    is_flag=True,
    help="保存本次重写到本地历史",
)
@click.option(
    "--list-history",
    type=int, default=0, metavar="N",
    help="列出最近 N 条历史记录 (default: 0=不列出)",
)
@click.option(
    "--clear-history",
    is_flag=True,
    help="清空所有历史记录",
)
@click.option(
    "--json", "output_json",
    is_flag=True,
    help="输出 JSON 格式 (用于 CI/CD 集成)",
)
@click.option(
    "--score",
    is_flag=True,
    help="显示重写前后的质量评分对比",
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
    history: bool = False,
    list_history: int = 0,
    clear_history: bool = False,
    output_json: bool = False,
    score: bool = False,
) -> None:
    """Prompt Rewrite System — 读取原始 prompt，输出优化后的高质量 prompt。"""

    # Handle --clear-history and --list-history before requiring input
    hist = RewriteHistory()
    if clear_history:
        count = hist.clear()
        click.echo(f"✅ 已清空 {count} 条历史记录")
        if not prompt and list_history == 0:
            return
    if list_history > 0:
        entries = hist.list_recent(list_history)
        if not entries:
            click.echo("(无历史记录)")
        else:
            click.echo(f"最近 {len(entries)} 条重写历史:")
            click.echo("─" * 60)
            import time as _time
            for e in entries:
                ts = _time.strftime("%Y-%m-%d %H:%M", _time.localtime(e.timestamp))
                preview = e.original[:50].replace(chr(10), " ")
                click.echo(f"  #{e.id} [{ts}] [{e.category}] {preview}...")
                click.echo(f"       策略: {', '.join(e.applied_strategies)}")
            click.echo()
        if not prompt:
            return

    raw = _read_input(prompt)
    if not raw.strip():
        click.echo(_msg("empty_input", lang), err=True)
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

    # Show quality scores if --score flag
    if score:
        from prompt_rewrite.core.quality import score_prompt
        original_qs = score_prompt(raw)
        rewritten_qs = score_prompt(result.rewritten)
        click.echo("\nQuality Scores (0-10):")
        click.echo(f"  {'Axis':15s} {'Original':>8s} {'Rewritten':>9s} {'Delta':>6s}")
        click.echo("  " + "─" * 42)
        for axis in ("clarity", "specificity", "structure", "safety", "completeness"):
            orig = getattr(original_qs, axis)
            rew = getattr(rewritten_qs, axis)
            delta = rew - orig
            sign = "+" if delta > 0 else ""
            click.echo(f"  {axis:15s} {orig:8.1f} {rew:9.1f} {sign}{delta:5.1f}")
        click.echo("  " + "─" * 42)
        click.echo(f"  {'TOTAL':15s} {original_qs.total:8.1f} {rewritten_qs.total:9.1f} {rewritten_qs.total - original_qs.total:+.1f}")
        click.echo()

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

    # Save to history if --history flag
    if history:
        entry = hist.add(
            original=raw,
            rewritten=result.rewritten,
            category=result.analysis.category.value,
            complexity=result.analysis.complexity.value,
            applied_strategies=[s.value for s in result.applied_strategies],
            diff_summary=result.diff_summary,
            output_style=style,
        )
        click.echo(f"💾 已保存到历史 #{entry.id}")

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(final)
        click.echo(_msg("written_to", lang, output))
    else:
        click.echo(final)


if __name__ == "__main__":
    main()
