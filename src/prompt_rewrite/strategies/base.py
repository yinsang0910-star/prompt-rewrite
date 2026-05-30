"""
Base classes for all rewrite strategies.

Each strategy applies one specific prompt engineering technique.
"""

from __future__ import annotations

import abc
from typing import ClassVar

from prompt_rewrite.core.types import (
    AnalysisResult,
    RewriteConfig,
    StrategyName,
    PromptCategory,
)


class RewriteStrategy(abc.ABC):
    """Abstract base class for a single rewrite strategy.

    A strategy encapsulates one prompt engineering technique:
    - Role injection
    - XML tag structuring (like <thinking> <answer>)
    - Chain-of-thought scaffolding
    - Constraint injection (constitutional principles)
    - Output formatting
    - Example formatting (<example> tags)
    - Context reordering (data-first, query-last)
    """

    # Each strategy declares its name
    name: ClassVar[StrategyName]

    # Priority: lower number = runs earlier in the pipeline
    # 0-20:  structural (structure, context)
    # 21-40: enhancement (role, constraints)
    # 41-60: reasoning (CoT)
    # 61-80: formatting (output, example)
    priority: ClassVar[int] = 50

    @abc.abstractmethod
    def apply(
        self,
        prompt: str,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> str:
        """Apply the rewrite strategy and return the transformed prompt."""
        ...

    def should_apply(
        self,
        analysis: AnalysisResult,
        config: RewriteConfig,
    ) -> bool:
        """Determine whether this strategy should run given the analysis."""
        return (
            self.name in config.enabled_strategies
        )

    def _wrap_tag(self, content: str, tag: str, attrs: str = "") -> str:
        """Wrap content in an XML tag for structured prompts."""
        if attrs:
            return f"<{tag} {attrs}>\n{content}\n</{tag}>"
        return f"<{tag}>\n{content}\n</{tag}>"


class StrategyRegistry:
    """Registry of all available strategies."""

    _strategies: dict[StrategyName, type[RewriteStrategy]] = {}

    @classmethod
    def register(cls, strategy_cls: type[RewriteStrategy]) -> type[RewriteStrategy]:
        cls._strategies[strategy_cls.name] = strategy_cls
        return strategy_cls

    @classmethod
    def get(cls, name: StrategyName) -> RewriteStrategy:
        if name not in cls._strategies:
            raise KeyError(f"Strategy '{name.value}' not registered")
        return cls._strategies[name]()

    @classmethod
    def get_all(cls) -> list[RewriteStrategy]:
        """Return all registered strategies sorted by priority."""
        strategies = [cls() for cls in cls._strategies.values()]
        strategies.sort(key=lambda s: s.priority)
        return strategies

    @classmethod
    def get_enabled(
        cls,
        config: RewriteConfig,
        analysis: AnalysisResult,
    ) -> list[RewriteStrategy]:
        """Return enabled strategies sorted by priority."""
        all_s = cls.get_all()
        return [
            s for s in all_s
            if s.should_apply(analysis, config)
        ]
