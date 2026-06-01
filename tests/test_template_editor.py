# -*- coding: utf-8 -*-
"""Tests for template editor API."""

import pytest
from pathlib import Path

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False

from prompt_rewrite.api.template_editor import router, _TEMPLATES_DIR, _ALLOWED_FILES


@pytest.fixture
def client():
    if not HAS_FASTAPI:
        pytest.skip("fastapi not installed")
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


class TestTemplateEditorAPI:
    def test_list_templates(self, client):
        r = client.get("/api/templates")
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, dict)
        assert "roles.yaml" in data or "constraints.yaml" in data

    def test_get_template(self, client):
        r = client.get("/api/templates/roles.yaml")
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_get_template_not_found(self, client):
        r = client.get("/api/templates/nonexistent.yaml")
        assert r.status_code == 400

    def test_get_template_key(self, client):
        # Get first available key from roles.yaml
        data = client.get("/api/templates/roles.yaml").json()
        if data:
            first_key = list(data.keys())[0]
            r = client.get(f"/api/templates/roles.yaml/{first_key}")
            assert r.status_code == 200

    def test_get_template_key_not_found(self, client):
        r = client.get("/api/templates/roles.yaml/__nonexistent_key__")
        assert r.status_code == 404

    def test_templates_dir_exists(self):
        assert _TEMPLATES_DIR.is_dir()
