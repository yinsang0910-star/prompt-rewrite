# -*- coding: utf-8 -*-
"""Local rewrite history — JSON-file persistence for prompt rewrites."""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Optional

_DEFAULT_HISTORY_DIR = Path(os.environ.get(
    "PRS_HISTORY_DIR", str(Path.home() / ".prompt_rewrite")
))


@dataclass
class HistoryEntry:
    """A single rewrite record."""
    id: int
    timestamp: float
    original: str
    rewritten: str
    category: str
    complexity: str
    applied_strategies: list[str]
    diff_summary: str = ""
    output_style: str = "instruction"


class RewriteHistory:
    """Append-only JSON store for prompt rewrites."""

    def __init__(self, path: Optional[Path] = None, max_entries: int = 200):
        self._path = path or (_DEFAULT_HISTORY_DIR / "history.json")
        self._max = max_entries
        self._entries: list[HistoryEntry] = []
        self._load()

    def add(self, original: str, rewritten: str, category: str,
            complexity: str, applied_strategies: list[str],
            diff_summary: str = "", output_style: str = "instruction") -> HistoryEntry:
        """Record a rewrite and persist."""
        entry = HistoryEntry(
            id=len(self._entries) + 1,
            timestamp=time.time(),
            original=original,
            rewritten=rewritten,
            category=category,
            complexity=complexity,
            applied_strategies=applied_strategies,
            diff_summary=diff_summary,
            output_style=output_style,
        )
        self._entries.append(entry)
        # Trim oldest if over limit
        if len(self._entries) > self._max:
            self._entries = self._entries[-self._max:]
        self._save()
        return entry

    def list_recent(self, n: int = 10) -> list[HistoryEntry]:
        """Return the N most recent entries."""
        return list(reversed(self._entries[-n:]))

    def get(self, entry_id: int) -> Optional[HistoryEntry]:
        """Get a single entry by ID."""
        for e in reversed(self._entries):
            if e.id == entry_id:
                return e
        return None

    def clear(self) -> int:
        """Delete all history. Returns count of removed entries."""
        count = len(self._entries)
        self._entries = []
        self._save()
        return count

    @property
    def count(self) -> int:
        return len(self._entries)

    def _load(self) -> None:
        if not self._path.exists():
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._entries = [HistoryEntry(**e) for e in data]
        except (json.JSONDecodeError, TypeError, KeyError):
            self._entries = []

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(e) for e in self._entries]
        self._path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
