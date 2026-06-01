# -*- coding: utf-8 -*-
"""Tests for RewriteHistory."""

import pytest
from pathlib import Path
from prompt_rewrite.core.history import RewriteHistory


@pytest.fixture
def hist(tmp_path):
    return RewriteHistory(path=tmp_path / "test_history.json")


class TestRewriteHistory:
    def test_add_and_count(self, hist):
        assert hist.count == 0
        hist.add("original", "rewritten", "code", "medium", ["role_enhancer"], "diff")
        assert hist.count == 1

    def test_list_recent(self, hist):
        for i in range(5):
            hist.add(f"p{i}", f"r{i}", "qa", "simple", [])
        entries = hist.list_recent(3)
        assert len(entries) == 3
        assert entries[0].original == "p4"

    def test_get_by_id(self, hist):
        hist.add("find me", "found", "code", "simple", ["structure_formatter"])
        entry = hist.get(1)
        assert entry is not None
        assert entry.original == "find me"
        assert entry.applied_strategies == ["structure_formatter"]

    def test_get_nonexistent(self, hist):
        assert hist.get(999) is None

    def test_clear(self, hist):
        hist.add("a", "b", "code", "simple", [])
        hist.add("c", "d", "qa", "simple", [])
        count = hist.clear()
        assert count == 2
        assert hist.count == 0

    def test_persistence(self, tmp_path):
        path = tmp_path / "persist.json"
        h1 = RewriteHistory(path=path)
        h1.add("persisted", "yes", "code", "simple", [])
        h2 = RewriteHistory(path=path)
        assert h2.count == 1
        assert h2.get(1).original == "persisted"

    def test_max_entries_trims(self, tmp_path):
        path = tmp_path / "trim.json"
        h = RewriteHistory(path=path, max_entries=3)
        for i in range(5):
            h.add(f"p{i}", f"r{i}", "code", "simple", [])
        assert h.count == 3
        assert h.get(1) is None
        assert h.get(3) is not None

    def test_corrupted_file(self, tmp_path):
        path = tmp_path / "corrupt.json"
        path.write_text("not json!!!", encoding="utf-8")
        h = RewriteHistory(path=path)
        assert h.count == 0

    def test_entry_fields(self, hist):
        entry = hist.add(
            original="test prompt",
            rewritten="rewritten prompt",
            category="code",
            complexity="complex",
            applied_strategies=["role_enhancer", "chain_of_thought"],
            diff_summary="some diff",
            output_style="chat_ml",
        )
        assert entry.id == 1
        assert entry.timestamp > 0
        assert entry.output_style == "chat_ml"
        assert entry.diff_summary == "some diff"
