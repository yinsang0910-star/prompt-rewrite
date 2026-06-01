# -*- coding: utf-8 -*-
"""Template Editor API — CRUD endpoints for YAML templates.

Mount this router in launch_ui.py:
    from prompt_rewrite.api.template_editor import router
    app.include_router(router)
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any, Optional

try:
    from fastapi import APIRouter, HTTPException
    from pydantic import BaseModel
except ImportError:
    raise ImportError("Template editor requires fastapi: pip install prompt-rewrite[web]")

import yaml

router = APIRouter(prefix="/api/templates", tags=["templates"])

_TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"

_ALLOWED_FILES = {"roles.yaml", "constraints.yaml", "patterns.yaml"}


class TemplateUpdate(BaseModel):
    key: str
    data: Any


def _load_yaml(filename: str) -> dict:
    path = _TEMPLATES_DIR / filename
    if not path.exists():
        raise HTTPException(404, f"Template file {filename} not found")
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _save_yaml(filename: str, data: dict) -> None:
    path = _TEMPLATES_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


@router.get("")
def list_templates() -> dict:
    """List all template files and their top-level keys."""
    result = {}
    for name in sorted(_ALLOWED_FILES):
        try:
            data = _load_yaml(name)
            result[name] = list(data.keys()) if isinstance(data, dict) else []
        except HTTPException:
            result[name] = []
    return result


@router.get("/{filename}")
def get_template(filename: str) -> dict:
    """Get full content of a template file."""
    if filename not in _ALLOWED_FILES:
        raise HTTPException(400, f"Not a template file: {filename}")
    return _load_yaml(filename)


@router.get("/{filename}/{key}")
def get_template_key(filename: str, key: str) -> Any:
    """Get a specific key from a template file."""
    if filename not in _ALLOWED_FILES:
        raise HTTPException(400, f"Not a template file: {filename}")
    data = _load_yaml(filename)
    if key not in data:
        raise HTTPException(404, f"Key {key} not found in {filename}")
    return data[key]


@router.put("/{filename}/{key}")
def update_template_key(filename: str, key: str, body: TemplateUpdate) -> dict:
    """Update a specific key in a template file."""
    if filename not in _ALLOWED_FILES:
        raise HTTPException(400, f"Not a template file: {filename}")
    data = _load_yaml(filename)
    data[key] = body.data
    _save_yaml(filename, data)
    return {"status": "ok", "key": key}


@router.delete("/{filename}/{key}")
def delete_template_key(filename: str, key: str) -> dict:
    """Delete a key from a template file."""
    if filename not in _ALLOWED_FILES:
        raise HTTPException(400, f"Not a template file: {filename}")
    data = _load_yaml(filename)
    if key not in data:
        raise HTTPException(404, f"Key {key} not found in {filename}")
    del data[key]
    _save_yaml(filename, data)
    return {"status": "deleted", "key": key}
