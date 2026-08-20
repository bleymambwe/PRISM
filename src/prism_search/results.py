"""Immutable result records returned by PRISM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

Recommendation = Literal[
    "evolution",
    "uniform_sampling",
    "avoid_local_search",
    "improve_evaluator",
]


@dataclass(frozen=True)
class PrismResult:
    """Result of a PRISM executor run.

    ``evaluations`` is the number of fitness-function calls.  For
    :meth:`prism_search.PRISM.search`, these are distinct evaluations because
    the executor caches candidates.  The legacy generation-based
    :meth:`prism_search.PRISM.evolve` method may reevaluate candidates.
    """

    best_perm: list[int]
    best_fitness: float
    history: list[float] = field(default_factory=list)
    hit_generation: int | None = None
    generations_run: int = 0
    evaluations: int = 0
    operator_weights: dict[str, float] | None = None
    cache_hits: int = 0
    termination_reason: str = "completed"


@dataclass(frozen=True)
class PreflightResult:
    """Diagnostics and conservative executor recommendation from a pre-flight."""

    autocorrelations: dict[str, float]
    selected_operator: str
    fitness_distance_correlation: float
    distance_metric: str
    fitness_variance: float
    top_tie_fraction: float
    recommendation: Recommendation
    distinct_evaluations: int
    cache_hits: int
    reference_permutations: tuple[tuple[int, ...], ...]
    reference_kind: str
    seed: int | None
