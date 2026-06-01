"""
Template Loader — loads role and constraint templates from YAML files.

Supports:
- Bundled templates (src/prompt_rewrite/templates/*.yaml)
- User override templates (~/.prompt_rewrite/templates/*.yaml)
- i18n: each template can have en/zh/ja variants
- Lazy loading with caching for performance
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import yaml


# ── Template directory resolution ──────────────────────────────────────────

def _bundled_dir() -> Path:
    """Path to bundled YAML templates (inside package)."""
    return Path(__file__).parent.parent / "templates"


def _user_dir() -> Path:
    """Path to user override templates (~/.prompt_rewrite/templates/)."""
    home = Path.home()
    return home / ".prompt_rewrite" / "templates"


# ── Cache ──────────────────────────────────────────────────────────────────

_cache: dict[str, dict] = {}


def _load_yaml(filename: str) -> dict:
    """Load a YAML file with caching. User overrides take priority over bundled."""
    if filename in _cache:
        return _cache[filename]

    # Try user override first
    user_path = _user_dir() / filename
    if user_path.exists():
        with open(user_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        _cache[filename] = data
        return data

    # Fall back to bundled
    bundled_path = _bundled_dir() / filename
    if bundled_path.exists():
        with open(bundled_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        _cache[filename] = data
        return data

    _cache[filename] = {}
    return {}


def clear_cache() -> None:
    """Clear the template cache (useful for testing or hot-reload)."""
    _cache.clear()


# ── Role Templates ────────────────────────────────────────────────────────

def load_role(role_key: str, lang: str = "en") -> str:
    """Load a role template text by key and language.

    YAML structure:
        programming:
          en: "You are a senior software engineer..."
          zh: "你是一名资深软件工程师..."
          ja: "あなたはシニアソフトウェアエンジニアです..."

    Or legacy format (English only, structured):
        programming:
          identity: senior software engineer
          expertise: [...]
          guidelines: [...]

    Falls back: requested lang → en → empty string.
    """
    data = _load_yaml("roles.yaml")
    role_data = data.get(role_key)

    if role_data is None:
        return ""

    # New i18n format: direct string per language
    if isinstance(role_data, str):
        return role_data
    if isinstance(role_data, dict):
        # Check for i18n keys first
        if lang in role_data and isinstance(role_data[lang], str):
            return role_data[lang]
        if "en" in role_data and isinstance(role_data["en"], str):
            return role_data.get(lang, role_data["en"])

        # Legacy structured format: build text from identity + expertise + guidelines
        return _build_role_from_struct(role_data, lang)

    return ""


def _build_role_from_struct(data: dict, lang: str = "en") -> str:
    """Build a role text string from structured YAML (identity + expertise + guidelines)."""
    identity = data.get("identity", "")
    expertise = data.get("expertise", [])
    guidelines = data.get("guidelines", [])

    parts = []
    if identity:
        parts.append(f"You are a {identity}.")
    if expertise:
        parts.append("Your expertise includes " + ", ".join(expertise[:3]) + ".")
    if guidelines:
        parts.extend(guidelines[:3])

    return " ".join(parts)


def load_all_roles() -> dict[str, dict[str, str]]:
    """Load all role templates. Returns {role_key: {lang: text}}."""
    data = _load_yaml("roles.yaml")
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            if any(isinstance(v, str) for v in value.values()):
                # i18n format
                result[key] = {k: v for k, v in value.items() if isinstance(v, str)}
            else:
                # Structured format → build text
                result[key] = {"en": _build_role_from_struct(value, "en")}
        elif isinstance(value, str):
            result[key] = {"en": value}
    return result


# ── Constraint Templates ──────────────────────────────────────────────────

def load_constraints(category: str, lang: str = "en") -> list[str]:
    """Load quality constraints for a category and language.

    YAML structure:
        quality:
          general:
            en:
              - "Be precise and accurate..."
            zh:
              - "请保持精确和准确..."
    """
    data = _load_yaml("constraints.yaml")
    quality = data.get("quality", {})

    # Try category-specific, fall back to general
    cat_data = quality.get(category, quality.get("general", {}))
    if isinstance(cat_data, dict):
        return cat_data.get(lang, cat_data.get("en", []))
    if isinstance(cat_data, list):
        return cat_data
    return []


def load_safety_constraints(lang: str = "en") -> list[str]:
    """Load safety/refusal constraints."""
    data = _load_yaml("constraints.yaml")
    safety = data.get("safety", {})
    # Flatten nested structure
    if isinstance(safety, dict):
        # Check for direct lang key
        if lang in safety and isinstance(safety[lang], list):
            return safety[lang]
        if "en" in safety and isinstance(safety["en"], list):
            return safety.get(lang, safety["en"])
        # Nested by sub-category (harm_prevention, professional_boundaries, etc.)
        all_constraints = []
        for sub_cat in safety.values():
            if isinstance(sub_cat, dict):
                items = sub_cat.get(lang, sub_cat.get("en", []))
                if isinstance(items, list):
                    all_constraints.extend(items)
            elif isinstance(sub_cat, list):
                all_constraints.extend(sub_cat)
        return all_constraints
    if isinstance(safety, list):
        return safety
    return []


def load_formatting_constraints(lang: str = "en") -> list[str]:
    """Load formatting constraints."""
    data = _load_yaml("constraints.yaml")
    fmt = data.get("formatting", {})
    if isinstance(fmt, dict):
        if lang in fmt and isinstance(fmt[lang], list):
            return fmt[lang]
        if "en" in fmt and isinstance(fmt["en"], list):
            return fmt.get(lang, fmt["en"])
        # Nested by sub-category
        all_constraints = []
        for sub_cat in fmt.values():
            if isinstance(sub_cat, dict):
                items = sub_cat.get(lang, sub_cat.get("en", []))
                if isinstance(items, list):
                    all_constraints.extend(items)
            elif isinstance(sub_cat, list):
                all_constraints.extend(sub_cat)
        return all_constraints
    if isinstance(fmt, list):
        return fmt
    return []
