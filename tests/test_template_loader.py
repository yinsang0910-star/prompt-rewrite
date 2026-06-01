# -*- coding: utf-8 -*-
"""Tests for YAML template loading system."""

import pytest
from prompt_rewrite.templates.loader import (
    load_role,
    load_constraints,
    load_safety_constraints,
    load_formatting_constraints,
    load_all_roles,
    clear_cache,
)


class TestRoleLoading:
    def test_load_english_role(self):
        role = load_role("programming", "en")
        assert len(role) > 0
        assert "engineer" in role.lower() or "software" in role.lower()

    def test_load_chinese_role(self):
        role = load_role("programming", "zh")
        assert len(role) > 0
        assert "软件" in role or "工程" in role

    def test_load_japanese_role(self):
        role = load_role("programming", "ja")
        assert len(role) > 0

    def test_load_default_role(self):
        role = load_role("default", "en")
        assert len(role) > 0
        assert "assistant" in role.lower()

    def test_fallback_to_english(self):
        """Unknown language should fall back to English."""
        role = load_role("programming", "xx_unknown")
        assert len(role) > 0
        assert "engineer" in role.lower() or "software" in role.lower()

    def test_unknown_role_returns_empty(self):
        role = load_role("nonexistent_role_xyz", "en")
        assert role == ""

    def test_all_roles_loadable(self):
        all_roles = load_all_roles()
        assert len(all_roles) >= 10  # At least 10 roles
        assert "programming" in all_roles
        assert "default" in all_roles


class TestConstraintLoading:
    def test_load_code_constraints_en(self):
        constraints = load_constraints("code", "en")
        assert len(constraints) > 0
        assert any("code" in c.lower() for c in constraints)

    def test_load_code_constraints_zh(self):
        constraints = load_constraints("code", "zh")
        assert len(constraints) > 0
        assert any("代码" in c or "编码" in c for c in constraints)

    def test_load_general_constraints(self):
        constraints = load_constraints("general", "en")
        assert len(constraints) > 0

    def test_fallback_to_general(self):
        """Unknown category should fall back to general."""
        constraints = load_constraints("nonexistent_cat", "en")
        assert len(constraints) > 0


class TestSafetyConstraints:
    def test_load_safety_en(self):
        safety = load_safety_constraints("en")
        assert len(safety) > 0
        assert any("illegal" in s.lower() or "harm" in s.lower() for s in safety)

    def test_load_safety_zh(self):
        safety = load_safety_constraints("zh")
        assert len(safety) > 0

    def test_load_safety_ja(self):
        safety = load_safety_constraints("ja")
        assert len(safety) > 0


class TestFormattingConstraints:
    def test_load_formatting_en(self):
        fmt = load_formatting_constraints("en")
        assert len(fmt) > 0

    def test_load_formatting_zh(self):
        fmt = load_formatting_constraints("zh")
        assert len(fmt) > 0


class TestCache:
    def test_cache_clear(self):
        """clear_cache should not raise."""
        load_role("default", "en")  # populate cache
        clear_cache()
        # Should still work after cache clear
        role = load_role("default", "en")
        assert len(role) > 0


class TestIntegration:
    def test_role_enhancer_uses_yaml(self):
        """RoleEnhancer should produce YAML-sourced role text."""
        from prompt_rewrite.strategies.role_enhancer import RoleEnhancer
        from prompt_rewrite.core.types import AnalysisResult, RewriteConfig, PromptCategory

        enhancer = RoleEnhancer()
        analysis = AnalysisResult(category=PromptCategory.CODE, language="en")
        config = RewriteConfig()
        result = enhancer.apply("Write a sort function", analysis, config)
        assert "<role>" in result
        assert "software engineer" in result.lower() or "programmer" in result.lower()

    def test_constraint_injector_uses_yaml(self):
        """ConstraintInjector should produce YAML-sourced constraints."""
        from prompt_rewrite.strategies.constraint_injector import ConstraintInjector
        from prompt_rewrite.core.types import AnalysisResult, RewriteConfig, PromptCategory

        injector = ConstraintInjector()
        analysis = AnalysisResult(category=PromptCategory.CODE, language="en", raw_length=200)
        config = RewriteConfig()
        result = injector.apply("Write code", analysis, config)
        assert "<constraints>" in result
