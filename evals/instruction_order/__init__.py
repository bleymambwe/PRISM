"""Instruction-order sensitivity benchmark for Inspect AI.

Implements the language-model instruction-ordering landscape of
arXiv:2608.08344. See `task.py` for the registered tasks.

Only the pure-Python helpers are re-exported here; importing the tasks pulls in
`inspect_ai`, so `task.py` is imported directly by the eval runner instead.
"""

from __future__ import annotations

from evals.instruction_order.grading import extract_prediction, grade
from evals.instruction_order.modules import (
    GSM8K_MODULES,
    MATH500_MODULES,
    build_prompt,
    ordering_label,
)
from evals.instruction_order.orderings import (
    build_orderings,
    diverse_orderings,
    exhaustive,
    random_orderings,
)

__all__ = [
    "GSM8K_MODULES",
    "MATH500_MODULES",
    "build_orderings",
    "build_prompt",
    "diverse_orderings",
    "exhaustive",
    "extract_prediction",
    "grade",
    "ordering_label",
    "random_orderings",
]

__version__ = "0.1.0"
