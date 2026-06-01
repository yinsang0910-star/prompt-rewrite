# -*- coding: utf-8 -*-
"""Plugin loader — discovers custom strategies from entry points and user directory.

Discovery order:
1. Built-in strategies (registered in strategies/__init__.py)
2. Entry points: [project.entry-points."prompt_rewrite.strategies"]
3. User directory: ~/.prompt_rewrite/strategies/*.py
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
import os
from pathlib import Path
from typing import Optional

from prompt_rewrite.strategies.base import RewriteStrategy, StrategyRegistry

logger = logging.getLogger(__name__)

_USER_STRATEGIES_DIR = Path(os.environ.get(
    "PRS_STRATEGIES_DIR",
    str(Path.home() / ".prompt_rewrite" / "strategies"),
))


def discover_entry_point_plugins() -> int:
    """Load strategies registered via pyproject.toml entry points.

    Entry point group: "prompt_rewrite.strategies"
    Each entry should point to a RewriteStrategy subclass.
    Returns count of newly registered plugins.
    """
    try:
        from importlib.metadata import entry_points
    except ImportError:
        # Python 3.8 fallback
        try:
            from importlib_metadata import entry_points  # type: ignore[no-redef]
        except ImportError:
            return 0

    count = 0
    try:
        eps = entry_points(group="prompt_rewrite.strategies")
    except TypeError:
        # Python 3.8: entry_points() returns dict
        eps = entry_points().get("prompt_rewrite.strategies", [])  # type: ignore[assignment]

    for ep in eps:
        try:
            cls = ep.load()
            if (isinstance(cls, type)
                    and issubclass(cls, RewriteStrategy)
                    and cls is not RewriteStrategy):
                StrategyRegistry.register(cls)
                count += 1
                logger.info(f"Loaded plugin strategy: {ep.name} from {ep.value}")
        except Exception as e:
            logger.warning(f"Failed to load plugin {ep.name}: {e}")

    return count


def discover_user_strategies(directory: Optional[Path] = None) -> int:
    """Load user-authored strategies from a local directory.

    Each .py file in the directory is inspected for RewriteStrategy subclasses.
    Returns count of newly registered strategies.
    """
    strat_dir = directory or _USER_STRATEGIES_DIR
    if not strat_dir.is_dir():
        return 0

    count = 0
    for py_file in sorted(strat_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        try:
            spec = importlib.util.spec_from_file_location(
                f"prompt_rewrite_user.{py_file.stem}", str(py_file),
            )
            if spec is None or spec.loader is None:
                continue
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (isinstance(attr, type)
                        and issubclass(attr, RewriteStrategy)
                        and attr is not RewriteStrategy
                        and hasattr(attr, "name")):
                    StrategyRegistry.register(attr)
                    count += 1
                    logger.info(f"Loaded user strategy: {attr_name} from {py_file.name}")
        except Exception as e:
            logger.warning(f"Failed to load {py_file.name}: {e}")

    return count


def discover_all_plugins() -> int:
    """Run all plugin discovery mechanisms. Returns total new registrations."""
    ep_count = discover_entry_point_plugins()
    user_count = discover_user_strategies()
    total = ep_count + user_count
    if total:
        logger.info(f"Plugin discovery: {ep_count} entry-point + {user_count} user = {total} new strategies")
    return total
