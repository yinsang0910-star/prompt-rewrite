# -*- coding: utf-8 -*-
"""Tests for plugin discovery."""

import pytest
from pathlib import Path
from prompt_rewrite.plugins import discover_user_strategies
from prompt_rewrite.strategies.base import StrategyRegistry, RewriteStrategy
from prompt_rewrite.core.types import StrategyName, AnalysisResult, RewriteConfig


class TestPluginDiscovery:
    def test_discover_empty_dir(self, tmp_path):
        count = discover_user_strategies(tmp_path / "nonexistent")
        assert count == 0

    def test_discover_user_strategy(self, tmp_path):
        strategy_code = 'from prompt_rewrite.strategies.base import RewriteStrategy\nfrom prompt_rewrite.core.types import StrategyName\n\nclass MyPlugin(RewriteStrategy):\n    name = StrategyName.STRUCTURE_FORMATTER\n    priority = 99\n    def apply(self, prompt, analysis, config, **kwargs):\n        return f"PLUGIN:{prompt}"\n'
        (tmp_path / "my_plugin.py").write_text(strategy_code, encoding="utf-8")
        count = discover_user_strategies(tmp_path)
        assert count >= 1

    def test_skips_underscore_files(self, tmp_path):
        (tmp_path / "_private.py").write_text("x = 1", encoding="utf-8")
        count = discover_user_strategies(tmp_path)
        assert count == 0

    def test_skips_invalid_files(self, tmp_path):
        (tmp_path / "bad.py").write_text("raise ValueError()", encoding="utf-8")
        count = discover_user_strategies(tmp_path)
        assert count == 0
