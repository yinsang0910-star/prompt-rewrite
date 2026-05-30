#!/usr/bin/env python
"""
Prompt Rewrite System — Web UI Server
FastAPI + Tailwind CSS (shadcn/ui inspired) frontend
"""
from __future__ import annotations

import sys
import os
import json
import dataclasses
from pathlib import Path
from typing import Any

# Force UTF-8 on Windows
if sys.platform == "win32":
    os.environ["PYTHONIOENCODING"] = "utf-8"

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from prompt_rewrite import RewritePipeline, RewriteConfig
from prompt_rewrite.core.types import StrategyName, LLMConfig
# from prompt_rewrite.core.workflow_defs import WORKFLOW_REGISTRY  # unused

app = FastAPI(title="Prompt Rewrite System")

# ── Serve the index.html ──
HERE = Path(__file__).parent
INDEX_HTML = HERE / "index.html"


@app.get("/", response_class=HTMLResponse)
async def index():
    return INDEX_HTML.read_text("utf-8")


# ── Helper: dataclass → dict ──
def _asdict(obj: Any) -> dict:
    """Recursively convert dataclass/namedtuple/enum to dict for JSON."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _asdict(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, (list, tuple)):
        return [_asdict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _asdict(v) for k, v in obj.items()}
    if hasattr(obj, "value"):
        return obj.value
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


# ── Strategy metadata ──
STRATEGY_META: dict[str, dict] = {
    "STRUCTURE_FORMATTER":  {"icon": "📋", "label": "Structure",   "color": "#818cf8"},
    "ROLE_ENHANCER":        {"icon": "🎭", "label": "Role",       "color": "#f472b6"},
    "CHAIN_OF_THOUGHT":     {"icon": "🧠", "label": "CoT",        "color": "#34d399"},
    "CONSTRAINT_INJECTOR":  {"icon": "🛡️", "label": "Constraints","color": "#fbbf24"},
    "OUTPUT_FORMATTER":     {"icon": "📤", "label": "Output",     "color": "#60a5fa"},
    "EXAMPLE_FORMATTER":    {"icon": "📝", "label": "Examples",   "color": "#a78bfa"},
    "CONTEXT_OPTIMIZER":    {"icon": "📐", "label": "Reorder",    "color": "#fb923c"},
}

CATEGORY_META: dict[str, dict] = {
    "code":         {"icon": "💻", "label": "Code"},
    "qa":           {"icon": "❓", "label": "Q&A"},
    "writing":      {"icon": "✍️", "label": "Writing"},
    "analysis":     {"icon": "🔬", "label": "Analysis"},
    "creative":     {"icon": "🎨", "label": "Creative"},
    "extraction":   {"icon": "📊", "label": "Extraction"},
    "instruction":  {"icon": "📋", "label": "Instruction"},
    "conversation": {"icon": "💬", "label": "Conversation"},
    "unknown":      {"icon": "❔", "label": "Unknown"},
}

COMPLEXITY_META: dict[str, dict] = {
    "simple":  {"icon": "🟢", "label": "Simple"},
    "medium":  {"icon": "🟡", "label": "Medium"},
    "complex": {"icon": "🔴", "label": "Complex"},
    "unknown": {"icon": "⚪", "label": "Unknown"},
}

# ── API: Rewrite ──
PRESET_STRATEGIES = {
    "full":    [s for s in StrategyName],
    "basic":   [StrategyName.ROLE_ENHANCER, StrategyName.STRUCTURE_FORMATTER, StrategyName.OUTPUT_FORMATTER],
    "minimal": [StrategyName.STRUCTURE_FORMATTER],
}


def _build_workflow_info(result) -> dict:
    """Build workflow visualization data from the result."""
    steps = []
    used_strategies = set(result.applied_strategies) | set(getattr(result, "workflow_steps", []))
    for s in StrategyName:
        meta = STRATEGY_META.get(s.name, {"icon": "🔧", "label": s.name, "color": "#999"})
        steps.append({
            "name": s.name,
            "icon": meta["icon"],
            "label": meta["label"],
            "color": meta["color"],
            "applied": s in used_strategies,
        })
    return {
        "workflow_name": getattr(result, "workflow_name", ""),
        "steps": steps,
    }


@app.post("/api/rewrite")
async def api_rewrite(req: Request):
    body = await req.json()
    prompt = body.get("prompt", "").strip()
    if not prompt:
        return JSONResponse({"error": "Please enter a prompt"}, status_code=400)

    preset = body.get("preset", "full")
    language = body.get("language", "auto")
    no_cot = body.get("no_cot", False)
    api_key = body.get("api_key", "")
    model = body.get("model", "deepseek-v4-flash")
    enhance_analysis = body.get("enhance_analysis", False)
    enhance_rewrite = body.get("enhance_rewrite", False)
    validate = body.get("validate", False)

    try:
        enabled_strategies = PRESET_STRATEGIES.get(preset, list(StrategyName))
        if no_cot and StrategyName.CHAIN_OF_THOUGHT in enabled_strategies:
            enabled_strategies.remove(StrategyName.CHAIN_OF_THOUGHT)

        llm_config = LLMConfig(api_key=api_key, model=model) if api_key else LLMConfig()
        config = RewriteConfig(
            enabled_strategies=enabled_strategies,
            language=language,
            inject_chain_of_thought=not no_cot,
            llm_config=llm_config,
            llm_enhance_analysis=enhance_analysis,
            llm_enhance_rewrite=enhance_rewrite,
            llm_validate=validate,
        )
        pipeline = RewritePipeline(config=config)
        result = pipeline.run(prompt)

        a = result.analysis
        analysis = {
            "category": {
                "value": a.category.value,
                "icon": CATEGORY_META.get(a.category.value, {}).get("icon", "❔"),
                "label": CATEGORY_META.get(a.category.value, {}).get("label", a.category.value.upper()),
            },
            "complexity": {
                "value": a.complexity.value,
                "icon": COMPLEXITY_META.get(a.complexity.value, {}).get("icon", "⚪"),
                "label": COMPLEXITY_META.get(a.complexity.value, {}).get("label", a.complexity.value.upper()),
            },
            "language": a.language,
            "estimated_tokens": a.estimated_tokens,
            "has_code": a.has_code,
            "has_examples": a.has_examples,
            "domains": a.domains,
        }

        strategies_applied = []
        for s in result.applied_strategies:
            meta = STRATEGY_META.get(s.name, {"icon": "🔧", "label": s.name, "color": "#999"})
            strategies_applied.append({
                "name": s.name,
                "icon": meta["icon"],
                "label": meta["label"],
                "color": meta["color"],
            })

        # Diff
        orig_lines = result.original.splitlines()
        new_lines = result.rewritten.splitlines()
        added = sum(1 for l in new_lines if l not in orig_lines)
        removed = sum(1 for l in orig_lines if l not in new_lines)

        # Grab LLM raw response if available
        llm_raw = getattr(pipeline, "last_llm_raw_response", None)
        if llm_raw:
            llm_raw["model_used"] = model

        return {
            "original": result.original,
            "rewritten": result.rewritten,
            "analysis": analysis,
            "strategies": strategies_applied,
            "workflow": _build_workflow_info(result),
            "diff": {
                "added": added,
                "removed": removed,
                "chars_before": len(result.original),
                "chars_after": len(result.rewritten),
            },
            "llm_raw": llm_raw,
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Entry point ──
def main():
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")

    print("=" * 55)
    print("  🪄  Prompt Rewrite System")
    print("  基于 Prompt Engineering 最佳实践")
    print("=" * 55)
    print()
    print(f"  🌐  浏览器打开: http://localhost:{port}")
    print()
    print("  Ctrl+C 停止服务")
    print("=" * 55)
    sys.stdout.flush()

    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
