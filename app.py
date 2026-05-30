#!/usr/bin/env python
"""
Prompt Rewrite System — Web UI (i18n: EN / ZH / JA)
"""

from __future__ import annotations

import gradio as gr

from prompt_rewrite import RewritePipeline, RewriteConfig
from prompt_rewrite.core.types import StrategyName

# ══════════════════════════════════════════════════════════════════════════
#  i18n Dictionary
# ══════════════════════════════════════════════════════════════════════════

LANG = {
    "en": {
        "title": "🪄 Prompt Rewrite System",
        "subtitle": "Smart Prompt Optimization · Dynamic Workflows",
        "input_label": "📥 Input Prompt",
        "input_placeholder": "Type or paste your prompt here...",
        "output_label": "📤 Optimized Prompt",
        "preset_label": "Mode",
        "preset_full": "full (all strategies)",
        "preset_basic": "basic (role+structure+output)",
        "preset_minimal": "minimal (structure only)",
        "lang_label": "Lang",
        "no_cot_label": "🚫 Disable Chain-of-Thought",
        "rewrite_btn": "🚀  Rewrite",
        "copy_btn": "📋  Copy",
        "clear_btn": "🗑️  Clear",
        "try_label": "⚡ Try:",
        "results_label": "📊 Results",
        "tab_analysis": "🔍 Analysis",
        "tab_strategies": "⚙️ Strategies",
        "tab_changes": "📝 Changes",
        "analysis_empty": "Run a rewrite to see analysis",
        "no_strategies": "No strategies applied",
        "no_changes": "No changes",
        "error_prefix": "❌",
        "empty_hint": "Please enter a prompt",
        "footer": "Prompt Rewrite System · Prompt Engineering Best Practices",
        "preset_choices": [
            "full (all strategies)",
            "basic (role+structure+output)",
            "minimal (structure only)",
        ],
        "lang_choices": ["auto", "zh", "en", "ja"],
    },
    "zh": {
        "title": "🪄 Prompt Rewrite System",
        "subtitle": "智能 Prompt 优化 · Dynamic Workflows",
        "input_label": "📥 原始 Prompt",
        "input_placeholder": "在此输入 prompt...",
        "output_label": "📤 优化后 Prompt",
        "preset_label": "模式",
        "preset_full": "完整（全部策略）",
        "preset_basic": "基础（角色+结构+格式）",
        "preset_minimal": "最简（仅结构化）",
        "lang_label": "语言",
        "no_cot_label": "🚫 禁用 CoT 推理",
        "rewrite_btn": "🚀  重写",
        "copy_btn": "📋  复制",
        "clear_btn": "🗑️  清空",
        "try_label": "⚡ 试试:",
        "results_label": "📊 结果",
        "tab_analysis": "🔍 分析",
        "tab_strategies": "⚙️ 策略",
        "tab_changes": "📝 变更",
        "analysis_empty": "重写后查看分析结果",
        "no_strategies": "未应用策略",
        "no_changes": "无变更",
        "error_prefix": "❌",
        "empty_hint": "请输入 prompt",
        "footer": "Prompt Rewrite System · Prompt Engineering 最佳实践",
        "preset_choices": [
            "完整（全部策略）",
            "基础（角色+结构+格式）",
            "最简（仅结构化）",
        ],
        "lang_choices": ["auto", "中文", "English", "日本語"],
    },
    "ja": {
        "title": "🪄 Prompt Rewrite System",
        "subtitle": "スマートプロンプト最適化 · Dynamic Workflows",
        "input_label": "📥 入力プロンプト",
        "input_placeholder": "プロンプトを入力...",
        "output_label": "📤 最適化後プロンプト",
        "preset_label": "モード",
        "preset_full": "フル（全ストラテジ）",
        "preset_basic": "ベーシック（役割+構造+出力）",
        "preset_minimal": "ミニマル（構造のみ）",
        "lang_label": "言語",
        "no_cot_label": "🚫 CoT 推論を無効化",
        "rewrite_btn": "🚀  書き換え",
        "copy_btn": "📋  コピー",
        "clear_btn": "🗑️  クリア",
        "try_label": "⚡ 試す:",
        "results_label": "📊 結果",
        "tab_analysis": "🔍 分析",
        "tab_strategies": "⚙️ 戦略",
        "tab_changes": "📝 差分",
        "analysis_empty": "書き換えを実行すると分析が表示されます",
        "no_strategies": "適用された戦略はありません",
        "no_changes": "変更なし",
        "error_prefix": "❌",
        "empty_hint": "プロンプトを入力してください",
        "footer": "Prompt Rewrite System · プロンプトエンジニアリングベストプラクティス",
        "preset_choices": [
            "フル（全ストラテジ）",
            "ベーシック（役割+構造+出力）",
            "ミニマル（構造のみ）",
        ],
        "lang_choices": ["auto", "中文", "English", "日本語"],
    },
}

# Map display labels to internal preset values
PRESET_VALUES = {
    # EN
    "full (all strategies)": "full",
    "basic (role+structure+output)": "basic",
    "minimal (structure only)": "minimal",
    # ZH
    "完整（全部策略）": "full",
    "基础（角色+结构+格式）": "basic",
    "最简（仅结构化）": "minimal",
    # JA
    "フル（全ストラテジ）": "full",
    "ベーシック（役割+構造+出力）": "basic",
    "ミニマル（構造のみ）": "minimal",
}

# ══════════════════════════════════════════════════════════════════════════
#  Styles — shadcn/ui inspired dark theme
# ══════════════════════════════════════════════════════════════════════════

CSS = r"""
/* ── Design tokens ── */
:root {
  --primary: #6366f1;
  --primary-soft: #818cf8;
  --primary-glow: rgba(99,102,241,0.25);
  --bg: #0a0a14;
  --bg-card: #12121e;
  --bg-card-hover: #1a1a2e;
  --bg-input: #16162a;
  --bg-elevated: #1e1e38;
  --text: #e8e8f0;
  --text-dim: #a0a0b8;
  --text-muted: #6b6b82;
  --text-inverse: #0a0a14;
  --border: #22223a;
  --border-focus: #6366f1;
  --success: #22c55e;
  --warning: #eab308;
  --error: #ef4444;
  --radius-sm: 6px;
  --radius-md: 10px;
  --radius-lg: 14px;
  --shadow-card: 0 1px 3px rgba(0,0,0,0.3), 0 1px 2px rgba(0,0,0,0.2);
  --shadow-elevated: 0 4px 12px rgba(0,0,0,0.4);
  --transition: 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Reset ── */
* { box-sizing: border-box; margin: 0; padding: 0; }

/* ── Body ── */
body {
  background: var(--bg) !important;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Noto Sans SC', sans-serif !important;
  color: var(--text) !important;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Container ── */
.gradio-container {
  max-width: 1120px !important;
  margin: 0 auto !important;
  background: transparent !important;
  padding: 0 1.25rem !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--text-muted); }

/* ── Header ── */
.header {
  text-align: center;
  padding: 2rem 0 0.75rem;
  margin-bottom: 1rem;
}
.header h1 {
  font-size: 1.65rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  background: linear-gradient(135deg, #a78bfa 0%, #6366f1 50%, #818cf8 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 0.2rem;
}
.header p {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin: 0;
  font-weight: 400;
}

/* ── Cards ── */
.card {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-lg) !important;
  padding: 1rem 1.25rem !important;
  box-shadow: var(--shadow-card) !important;
  transition: border-color var(--transition), box-shadow var(--transition) !important;
}
.card:hover {
  border-color: rgba(99,102,241,0.15) !important;
}
.card-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

/* ── Textareas ── */
textarea, .prose, .gr-textarea textarea {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  color: var(--text) !important;
  font-family: 'JetBrains Mono', 'SF Mono', 'Fira Code', Consolas, monospace !important;
  font-size: 0.82rem !important;
  line-height: 1.7 !important;
  padding: 0.7rem 0.85rem !important;
  resize: vertical !important;
  transition: border-color var(--transition), box-shadow var(--transition) !important;
}
textarea:focus, .gr-textarea textarea:focus {
  border-color: var(--border-focus) !important;
  box-shadow: 0 0 0 3px var(--primary-glow) !important;
  outline: none !important;
}

/* ── Buttons ── */
button.primary-btn {
  background: linear-gradient(135deg, var(--primary), #4f46e5) !important;
  border: none !important;
  border-radius: var(--radius-md) !important;
  color: #fff !important;
  font-weight: 600 !important;
  font-size: 0.88rem !important;
  padding: 0.55rem 1.2rem !important;
  cursor: pointer !important;
  transition: all var(--transition) !important;
  width: 100% !important;
  box-shadow: 0 2px 8px rgba(99,102,241,0.25) !important;
}
button.primary-btn:hover {
  opacity: 0.92 !important;
  box-shadow: 0 4px 16px rgba(99,102,241,0.35) !important;
  transform: translateY(-1px) !important;
}
button.primary-btn:active {
  transform: translateY(0) !important;
  box-shadow: 0 1px 4px rgba(99,102,241,0.2) !important;
}

button.sec-btn {
  background: transparent !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-dim) !important;
  font-size: 0.78rem !important;
  padding: 0.35rem 0.85rem !important;
  cursor: pointer !important;
  transition: all var(--transition) !important;
  font-weight: 500 !important;
}
button.sec-btn:hover {
  border-color: var(--primary) !important;
  color: var(--primary-soft) !important;
  background: rgba(99,102,241,0.06) !important;
}

/* ── Chip buttons (examples) ── */
.chip-btn {
  background: rgba(99,102,241,0.06) !important;
  border: 1px solid rgba(99,102,241,0.12) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-dim) !important;
  font-size: 0.72rem !important;
  padding: 0.25rem 0.6rem !important;
  cursor: pointer !important;
  transition: all var(--transition) !important;
  white-space: nowrap !important;
  font-weight: 450 !important;
}
.chip-btn:hover {
  background: rgba(99,102,241,0.15) !important;
  border-color: var(--primary) !important;
  color: var(--text) !important;
  transform: translateY(-1px) !important;
}

/* ── Badges ── */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.18rem 0.6rem;
  border-radius: 8px;
  font-size: 0.7rem;
  font-weight: 500;
  white-space: nowrap;
  line-height: 1.5;
  letter-spacing: 0.01em;
}
.badge-info {
  background: rgba(99,102,241,0.1);
  color: #a5b4fc;
  border: 1px solid rgba(99,102,241,0.18);
}
.badge-success {
  background: rgba(34,197,94,0.08);
  color: #4ade80;
  border: 1px solid rgba(34,197,94,0.15);
}

/* ── Utility classes ── */
.flex { display: flex; align-items: center; }
.flex-wrap { flex-wrap: wrap; }
.gap-1 { gap: 0.3rem; }
.gap-2 { gap: 0.5rem; }
.gap-3 { gap: 0.75rem; }
.mt-1 { margin-top: 0.3rem; }
.mb-1 { margin-bottom: 0.3rem; }
.mb-2 { margin-bottom: 0.6rem; }
.text-center { text-align: center; }

/* ── Gradio overrides ── */
.gr-box, .gr-form, .gr-panel, .gr-group {
  box-shadow: none !important;
  border: none !important;
  background: transparent !important;
}
.gr-form, .gr-group {
  margin-bottom: 0 !important;
  padding: 0 !important;
}

/* ── Labels ── */
label {
  margin-bottom: 0 !important;
  font-size: 0.78rem !important;
  color: var(--text-dim) !important;
  font-weight: 450 !important;
}

/* ── Dropdowns ── */
.gr-dropdown select {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  color: var(--text) !important;
  font-size: 0.78rem !important;
  border-radius: var(--radius-sm) !important;
  padding: 0.3rem 0.55rem !important;
  cursor: pointer !important;
  transition: border-color var(--transition) !important;
  appearance: auto !important;
}
.gr-dropdown select:focus {
  border-color: var(--border-focus) !important;
  box-shadow: 0 0 0 3px var(--primary-glow) !important;
  outline: none !important;
}

/* ── Checkbox ── */
.gr-checkbox {
  accent-color: var(--primary) !important;
}

/* ── Password input ── */
.gr-text-input input[type="password"] {
  background: var(--bg-input) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text) !important;
  font-size: 0.8rem !important;
  padding: 0.4rem 0.7rem !important;
  transition: border-color var(--transition) !important;
}
.gr-text-input input[type="password"]:focus {
  border-color: var(--border-focus) !important;
  box-shadow: 0 0 0 3px var(--primary-glow) !important;
  outline: none !important;
}

/* ── Tabs / Markdown ── */
.prose {
  max-width: none !important;
  font-size: 0.82rem !important;
}

/* ── Language Switcher ── */
.lang-switcher {
  display: flex !important;
  justify-content: center !important;
}
.lang-switcher .gr-radio {
  display: flex !important;
  flex-direction: row !important;
  gap: 0.2rem !important;
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-md) !important;
  padding: 0.2rem !important;
}
.lang-switcher label {
  padding: 0.25rem 0.75rem !important;
  border-radius: var(--radius-sm) !important;
  cursor: pointer !important;
  font-size: 0.78rem !important;
  transition: all var(--transition) !important;
  color: var(--text-muted) !important;
  font-weight: 450 !important;
  margin: 0 !important;
}
.lang-switcher label:hover {
  color: var(--text-dim) !important;
  background: rgba(99,102,241,0.06) !important;
}
.lang-switcher input[type="radio"]:checked + label,
.lang-switcher input[type="radio"]:checked + label:hover {
  background: rgba(99,102,241,0.12) !important;
  color: var(--primary-soft) !important;
}
.lang-switcher input[type="radio"] {
  display: none !important;
}
"""

# ══════════════════════════════════════════════════════════════════════════
#  Data
# ══════════════════════════════════════════════════════════════════════════

EXAMPLES = {
    "en": [
        "Write a Python function to sort a list of dicts by a key",
        "Explain recursion to a beginner",
        "Compare microservices vs monolithic architecture",
        "Brainstorm 5 startup ideas for AI in healthcare",
    ],
    "zh": [
        "写一个 Python 函数按 key 排序字典列表",
        "向初学者解释递归的概念",
        "比较微服务与单体架构的优缺点",
        "为 AI 医疗领域 brainstorm 5 个创业想法",
    ],
    "ja": [
        "Python関数でdictリストをキーでソートする",
        "初心者に再帰を説明する",
        "マイクロサービスとモノリスの比較",
        "AIヘルスケアのスタートアップアイデア5つ",
    ],
}

LABEL_MAP = {
    StrategyName.ROLE_ENHANCER:       ("🎭", "Role"),
    StrategyName.STRUCTURE_FORMATTER: ("📋", "Structure"),
    StrategyName.CHAIN_OF_THOUGHT:    ("🧠", "CoT"),
    StrategyName.CONSTRAINT_INJECTOR: ("🛡️", "Constraints"),
    StrategyName.OUTPUT_FORMATTER:    ("📤", "Output"),
    StrategyName.EXAMPLE_FORMATTER:   ("📝", "Examples"),
    StrategyName.CONTEXT_OPTIMIZER:   ("📐", "Reorder"),
}

CAT_ICON = {"code": "💻", "qa": "❓", "writing": "✍️", "analysis": "🔬", "creative": "🎨", "extraction": "📊", "instruction": "📋", "conversation": "💬", "unknown": "❔"}
CMP_ICON = {"simple": "🟢", "medium": "🟡", "complex": "🔴", "unknown": "⚪"}

# ══════════════════════════════════════════════════════════════════════════
#  Rewrite Logic
# ══════════════════════════════════════════════════════════════════════════

def do_rewrite(
    prompt: str, preset_label: str, no_cot: bool, lang: str,
    api_key: str = "", enhance_analysis: bool = False,
    enhance_rewrite: bool = False, validate: bool = False,
):
    if not prompt or not prompt.strip():
        return "", "", "", "", "⚠️ Please enter a prompt"

    try:
        preset = PRESET_VALUES.get(preset_label, "full")
        strategy_map = {
            "full": [s for s in StrategyName],
            "basic": [StrategyName.ROLE_ENHANCER, StrategyName.STRUCTURE_FORMATTER, StrategyName.OUTPUT_FORMATTER],
            "minimal": [StrategyName.STRUCTURE_FORMATTER],
        }
        enabled = strategy_map.get(preset, [s for s in StrategyName])
        if no_cot and StrategyName.CHAIN_OF_THOUGHT in enabled:
            enabled.remove(StrategyName.CHAIN_OF_THOUGHT)

        from prompt_rewrite.core.types import LLMConfig
        llm_config = LLMConfig(api_key=api_key) if api_key else LLMConfig()

        config = RewriteConfig(
            enabled_strategies=enabled, language=lang,
            inject_chain_of_thought=not no_cot,
            llm_config=llm_config,
            llm_enhance_analysis=enhance_analysis,
            llm_enhance_rewrite=enhance_rewrite,
            llm_validate=validate,
        )
        pipeline = RewritePipeline(config=config)
        result = pipeline.run(prompt)
        a = result.analysis

        cat = CAT_ICON.get(a.category.value, "❔")
        cmp = CMP_ICON.get(a.complexity.value, "⚪")
        domain_html = "".join(f'<span class="badge badge-info">#{d}</span> ' for d in a.domains[:4])
        wf = f'<span class="badge badge-info">🔄 {result.workflow_name.upper()}</span>' if getattr(result, "workflow_name", None) else ""

        analysis_html = f"""<div class="flex flex-wrap gap-2" style="padding:0.25rem 0">
<span class="badge badge-info">{cat} {a.category.value.upper()}</span>
<span class="badge badge-info">{cmp} {a.complexity.value.upper()}</span>
<span class="badge badge-info">🌐 {a.language.upper()}</span>
<span class="badge badge-info">📏 {a.estimated_tokens} tok</span>
<span class="badge badge-info">{'✅ code' if a.has_code else '— code'}</span>
<span class="badge badge-info">{'✅ examples' if a.has_examples else '— examples'}</span>
{domain_html}{wf}</div>"""

        vals = []
        for s in result.applied_strategies:
            icon, label = LABEL_MAP.get(s, ("🔧", s.value))
            vals.append(f'<span class="badge badge-success">{icon} {label}</span>')
        strat_html = '<div class="flex flex-wrap gap-2" style="padding:0.25rem 0">' + "".join(vals) + "</div>" if vals else '<span style="color:var(--text-muted);font-size:0.78rem;">No strategies applied</span>'

        diff_html = ""
        if result.original != result.rewritten:
            orig_set = set(result.original.splitlines())
            new_set = set(result.rewritten.splitlines())
            added = sum(1 for l in result.rewritten.splitlines() if l not in orig_set)
            removed = sum(1 for l in result.original.splitlines() if l not in new_set)
            preview = result.rewritten[:300] + ("..." if len(result.rewritten) > 300 else "")
            diff_html = f"""<div class="flex gap-3 mb-1" style="color:var(--text-muted);font-size:0.75rem;">
<span>📐 {len(result.original)} → {len(result.rewritten)} chars</span>
<span style="color:var(--success)">+{added}</span>
<span style="color:#ef4444">-{removed}</span></div>
<pre style="background:var(--bg-input);border-radius:6px;padding:0.6rem;font-size:0.7rem;color:var(--text-dim);max-height:160px;overflow:auto;margin:0">{preview.replace("<","&lt;").replace(">","&gt;")}</pre>"""
        else:
            diff_html = '<span style="color:var(--text-muted);font-size:0.78rem;">No changes</span>'

        return result.rewritten, analysis_html, strat_html, diff_html, ""

    except Exception as e:
        return "", "", "", "", f"❌ {e}"


# ══════════════════════════════════════════════════════════════════════════
#  UI Build
# ══════════════════════════════════════════════════════════════════════════

with gr.Blocks(css=CSS, title="Prompt Rewrite System", theme=gr.themes.Soft(primary_hue="indigo", neutral_hue="slate")) as demo:
    # ── State: current language ──
    current_lang = gr.State("en")

    # ── Header with decorative gradient ──
    gr.HTML("""
    <div style="position:relative;overflow:hidden;text-align:center;padding:2.5rem 0 1rem;margin-bottom:1.25rem">
        <div style="position:absolute;top:-120px;left:50%;transform:translateX(-50%);width:400px;height:400px;background:radial-gradient(circle,rgba(99,102,241,0.08) 0%,transparent 70%);pointer-events:none;border-radius:50%"></div>
        <div class="header">
            <h1>🪄 Prompt Rewrite System</h1>
            <p>Smart Prompt Optimization · Dynamic Workflows</p>
        </div>
        <div style="display:flex;justify-content:center;gap:0.4rem;margin-top:0.6rem">
            <span class="badge badge-info" style="font-size:0.65rem">✨ 7 Strategies</span>
            <span class="badge badge-info" style="font-size:0.65rem">🔄 Dynamic Workflows</span>
            <span class="badge badge-info" style="font-size:0.65rem">🌐 i18n Support</span>
        </div>
    </div>
    """)

    # ── Language switcher row ──
    with gr.Row():
        gr.HTML('<div style="flex:1"></div>')
        with gr.Column(scale=1, min_width=240):
            lang_selector = gr.Radio(
                choices=["English", "中文", "日本語"],
                value="English",
                label="",
                show_label=False,
                elem_classes="lang-switcher",
            )
        gr.HTML('<div style="flex:1"></div>')

    # ── Main area ──
    with gr.Row(equal_height=True):
        # Left: Input
        with gr.Column(scale=1, min_width=340):
            with gr.Group(elem_classes="card"):
                input_label = gr.HTML('<div class="card-label">📥 Input Prompt</div>')
                prompt_input = gr.Textbox(label="", placeholder="Type or paste your prompt here...", lines=8, max_lines=12, show_label=False)

                # Example chips
                try_html = gr.HTML('<div class="flex flex-wrap gap-1 mt-1" style="margin-bottom:0.3rem"><span style="color:var(--text-muted);font-size:0.7rem;font-weight:600;margin-right:0.2rem">⚡ Try:</span>')
                ex_btns = []
                for ex in EXAMPLES["en"]:
                    btn = gr.Button(ex, elem_classes="chip-btn", size="sm")
                    btn.click(fn=lambda e=ex: e, inputs=[], outputs=[prompt_input])
                    ex_btns.append(btn)
                gr.HTML('</div>')

                # Config row
                with gr.Row():
                    preset_dd = gr.Dropdown(
                        choices=LANG["en"]["preset_choices"], value=LANG["en"]["preset_choices"][0],
                        label="", show_label=False, scale=2,
                    )
                    lang_dd = gr.Dropdown(
                        choices=LANG["en"]["lang_choices"], value="auto",
                        label="", show_label=False, scale=1,
                    )

                with gr.Row():
                    no_cot_cb = gr.Checkbox(value=False, label=LANG["en"]["no_cot_label"], scale=1)

                rewrite_btn = gr.Button(LANG["en"]["rewrite_btn"], variant="primary", elem_classes="primary-btn")

            # ── AI Enhancement Panel ──
            with gr.Group(elem_classes="card"):
                gr.HTML('<div class="card-label">🤖 AI Enhancement <span style="font-weight:400;text-transform:none;color:var(--text-muted)">· DeepSeek</span></div>')
                api_key_input = gr.Textbox(
                    label="", placeholder="sk-... (leave empty to disable)",
                    lines=1, max_lines=1, show_label=False, type="password",
                )
                with gr.Row():
                    enhance_analysis_cb = gr.Checkbox(value=False, label="🔍 Enhance analysis", scale=1)
                    enhance_rewrite_cb = gr.Checkbox(value=False, label="✍️ AI rewrite", scale=1)
                    validate_cb = gr.Checkbox(value=False, label="✅ Validate quality", scale=1)

        # Right: Output
        with gr.Column(scale=1, min_width=340):
            with gr.Group(elem_classes="card"):
                output_label = gr.HTML('<div class="card-label">📤 Optimized Prompt</div>')
                output_text = gr.Textbox(label="", lines=8, max_lines=16, show_label=False, interactive=False)
                with gr.Row():
                    copy_btn = gr.Button(LANG["en"]["copy_btn"], elem_classes="sec-btn", scale=1)
                    clear_btn = gr.Button(LANG["en"]["clear_btn"], elem_classes="sec-btn", scale=1)

    # ── Results ──
    with gr.Group(elem_classes="card"):
        results_label = gr.HTML('<div class="card-label">📊 Results</div>')
        with gr.Row():
            tab_analysis = gr.Button(LANG["en"]["tab_analysis"], elem_classes="sec-btn", size="sm", scale=1)
            tab_strategies = gr.Button(LANG["en"]["tab_strategies"], elem_classes="sec-btn", size="sm", scale=1)
            tab_diff = gr.Button(LANG["en"]["tab_changes"], elem_classes="sec-btn", size="sm", scale=1)

        analysis_output = gr.HTML(value=f'<span style="color:var(--text-muted);font-size:0.8rem;">{LANG["en"]["analysis_empty"]}</span>', show_label=False, visible=True)
        strategies_output = gr.HTML(value="", show_label=False, visible=False)
        diff_output = gr.HTML(value="", show_label=False, visible=False)
        error_output = gr.HTML(value="", show_label=False, visible=False)

    # ── Decorative footer ──
    footer_html = gr.HTML(f'''
    <div style="text-align:center;padding:1.25rem 0 0.75rem;position:relative">
        <div style="position:absolute;bottom:0;left:50%;transform:translateX(-50%);width:200px;height:1px;background:linear-gradient(90deg,transparent,var(--border),transparent)"></div>
        <span style="color:var(--text-muted);font-size:0.6rem;letter-spacing:0.04em">{LANG["en"]["footer"]}</span>
    </div>
    ''')

    # ══════════════════════════════════════════════════════════════════════
    #  Language Switch
    # ══════════════════════════════════════════════════════════════════════

    LANG_KEY = {"English": "en", "中文": "zh", "日本語": "ja"}

    def switch_lang(lang_display: str):
        code = LANG_KEY.get(lang_display, "en")
        t = LANG[code]

        # Build preset & lang dropdown values
        preset_val = t["preset_choices"][0]
        lang_val = "auto"

        # Build example buttons
        example_texts = EXAMPLES.get(code, EXAMPLES["en"])
        example_updates = [gr.update(value=ex, visible=True) for ex in example_texts]
        # Hide extras if fewer examples
        for _ in range(len(EXAMPLES["en"]) - len(example_texts)):
            example_updates.append(gr.update(visible=False))

        return (
            code,                                                          # current_lang
            gr.update(value=f'<div class="card-label">{t["input_label"]}</div>'),  # input_label
            gr.update(placeholder=t["input_placeholder"]),                  # prompt_input placeholder
            gr.update(value=f'<div class="card-label">{t["output_label"]}</div>'), # output_label
            gr.update(choices=t["preset_choices"], value=preset_val),      # preset_dd
            gr.update(choices=t["lang_choices"], value=lang_val),          # lang_dd
            gr.update(label=t["no_cot_label"]),                            # no_cot_cb
            gr.update(value=t["rewrite_btn"]),                             # rewrite_btn
            gr.update(value=t["copy_btn"]),                                # copy_btn
            gr.update(value=t["clear_btn"]),                               # clear_btn
            gr.update(value=f'<div class="card-label">{t["results_label"]}</div>'), # results_label
            gr.update(value=t["tab_analysis"]),                            # tab_analysis
            gr.update(value=t["tab_strategies"]),                          # tab_strategies
            gr.update(value=t["tab_changes"]),                             # tab_diff
            gr.update(value=f'<span style="color:var(--text-muted);font-size:0.8rem;">{t["analysis_empty"]}</span>'), # analysis_output (reset)
            gr.update(value="", visible=False),                            # strategies_output (reset)
            gr.update(value="", visible=False),                            # diff_output (reset)
            gr.update(value=""),                                           # error_output (reset)
            gr.update(value=""),                                           # output_text (reset)
            gr.update(value=f'<div style="text-align:center;padding:0.75rem 0;color:var(--text-muted);font-size:0.65rem;">{t["footer"]}</div>'),  # footer
            gr.update(value=f'<div class="flex flex-wrap gap-1 mt-1" style="margin-bottom:0.3rem"><span style="color:var(--text-muted);font-size:0.7rem;font-weight:600;margin-right:0.2rem">{t["try_label"]}</span>'), # try_html
            *example_updates,                                              # example buttons
        )

    lang_selector.change(
        fn=switch_lang,
        inputs=[lang_selector],
        outputs=[
            current_lang,
            input_label, prompt_input, output_label,
            preset_dd, lang_dd, no_cot_cb,
            rewrite_btn, copy_btn, clear_btn,
            results_label,
            tab_analysis, tab_strategies, tab_diff,
            analysis_output, strategies_output, diff_output, error_output,
            output_text,
            footer_html, try_html,
            *ex_btns,
        ],
    )

    # ══════════════════════════════════════════════════════════════════════
    #  Rewrite
    # ══════════════════════════════════════════════════════════════════════

    def on_rewrite(prompt, preset_label, no_cot, lang, cur_lang, api_key, enhance_analysis, enhance_rewrite, validate):
        rewritten, analysis_html, strat_html, diff_html, err = do_rewrite(
            prompt, preset_label, no_cot, lang,
            api_key=api_key,
            enhance_analysis=enhance_analysis,
            enhance_rewrite=enhance_rewrite,
            validate=validate,
        )
        if err:
            return rewritten, analysis_html, "", "", err, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)
        return rewritten, analysis_html, strat_html, diff_html, "", gr.update(visible=True), gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    all_rewrite_inputs = [prompt_input, preset_dd, no_cot_cb, lang_dd, current_lang, api_key_input, enhance_analysis_cb, enhance_rewrite_cb, validate_cb]
    all_rewrite_outputs = [
        output_text, analysis_output, strategies_output, diff_output, error_output,
        analysis_output, strategies_output, diff_output, error_output,
    ]

    rewrite_btn.click(fn=on_rewrite, inputs=all_rewrite_inputs, outputs=all_rewrite_outputs)
    prompt_input.submit(fn=on_rewrite, inputs=all_rewrite_inputs, outputs=all_rewrite_outputs)

    # ── Tab switching ──
    tab_analysis.click(
        fn=lambda: (gr.update(visible=True), gr.update(visible=False), gr.update(visible=False)),
        inputs=[], outputs=[analysis_output, strategies_output, diff_output],
    )
    tab_strategies.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=True), gr.update(visible=False)),
        inputs=[], outputs=[analysis_output, strategies_output, diff_output],
    )
    tab_diff.click(
        fn=lambda: (gr.update(visible=False), gr.update(visible=False), gr.update(visible=True)),
        inputs=[], outputs=[analysis_output, strategies_output, diff_output],
    )

    # ── Copy / Clear ──
    copy_btn.click(fn=lambda t: t, inputs=[output_text], outputs=[])
    clear_btn.click(
        fn=lambda: ("", "", "", "", ""),
        inputs=[], outputs=[prompt_input, output_text, analysis_output, strategies_output, diff_output, error_output],
    )
