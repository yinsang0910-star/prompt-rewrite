# -*- coding: utf-8 -*-
"""Decorator API for programmatic prompt optimization.

Usage:
    from prompt_rewrite import optimize

    @optimize
    def my_prompt() -> str:
        return "Write a function to sort a list"

    print(my_prompt())  # returns the optimized version

    @optimize(style="chat_ml")
    def system_prompt() -> str:
        return "You are a helpful assistant"
"""

from __future__ import annotations

import functools
from typing import Callable, Optional, overload

from prompt_rewrite.core.pipeline import RewritePipeline
from prompt_rewrite.core.types import RewriteConfig


def optimize(
    func: Optional[Callable[..., str]] = None,
    *,
    style: str = "instruction",
    lang: str = "auto",
    no_cot: bool = False,
) -> Callable:
    """Decorator that rewrites the return value of a function as an optimized prompt.

    Can be used bare (@optimize) or with arguments (@optimize(style="chat_ml")).
    """
    def decorator(fn: Callable[..., str]) -> Callable[..., str]:
        config = RewriteConfig(
            language=lang,
            output_style=style,
            inject_chain_of_thought=not no_cot,
        )
        pipeline = RewritePipeline(config=config)

        @functools.wraps(fn)
        def wrapper(*args, **kwargs) -> str:
            raw = fn(*args, **kwargs)
            if not isinstance(raw, str):
                return raw
            result = pipeline.run(raw)
            return result.rewritten

        wrapper._prs_pipeline = pipeline  # type: ignore[attr-defined]
        return wrapper

    if func is not None:
        # @optimize without parentheses
        return decorator(func)
    # @optimize(...) with arguments
    return decorator
