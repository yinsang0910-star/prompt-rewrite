"""Rewrite strategies — each implements a specific prompt engineering technique."""

from prompt_rewrite.strategies.base import RewriteStrategy, StrategyRegistry
from prompt_rewrite.strategies.role_enhancer import RoleEnhancer
from prompt_rewrite.strategies.structure_formatter import StructureFormatter
from prompt_rewrite.strategies.chain_of_thought import ChainOfThoughtInjector
from prompt_rewrite.strategies.constraint_injector import ConstraintInjector
from prompt_rewrite.strategies.output_formatter import OutputFormatter
from prompt_rewrite.strategies.example_formatter import ExampleFormatter
from prompt_rewrite.strategies.context_optimizer import ContextOptimizer
from prompt_rewrite.strategies.refusal_guard import RefusalGuard

# Register all strategies
for _s in [
    RoleEnhancer,
    StructureFormatter,
    ChainOfThoughtInjector,
    ConstraintInjector,
    OutputFormatter,
    ExampleFormatter,
    ContextOptimizer,
    RefusalGuard,
]:
    StrategyRegistry.register(_s)

__all__ = [
    "RewriteStrategy",
    "StrategyRegistry",
    "RoleEnhancer",
    "StructureFormatter",
    "ChainOfThoughtInjector",
    "ConstraintInjector",
    "OutputFormatter",
    "ExampleFormatter",
    "ContextOptimizer",
    "RefusalGuard",
]
