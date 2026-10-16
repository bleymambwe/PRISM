"""SAELens-facing hooks without a hard SAELens dependency.

SAELens experiments expose different activation and reconstruction APIs across
versions. PRISM therefore accepts a narrow evaluator callback rather than
importing SAELens internals. The callback can wrap feature ordering,
ablation, reconstruction, or downstream task scoring.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from ..diagnostics import preflight
from ..results import PreflightResult

SAEEvaluator = Callable[[tuple[int, ...]], float]


def make_sae_fitness(evaluator: SAEEvaluator, n: int) -> Callable[[Sequence[int]], float]:
    """Adapt a SAELens experiment callback to PRISM's fitness protocol."""

    if n < 2:
        raise ValueError("n must be at least 2")

    def fitness(permutation: Sequence[int]) -> float:
        values = tuple(int(value) for value in permutation)
        if len(values) != n or set(values) != set(range(n)):
            raise ValueError(f"Expected a permutation of range({n}), got {values!r}")
        return float(evaluator(values))

    return fitness


def preflight_sae(
    n: int,
    evaluator: SAEEvaluator,
    **kwargs: object,
) -> PreflightResult:
    """Run PRISM diagnostics around a SAELens-backed evaluator callback."""

    return preflight(n, make_sae_fitness(evaluator, n), **kwargs)
