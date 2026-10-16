"""Nevergrad bridge for permutation-valued PRISM objectives.

Nevergrad minimizes objectives, while PRISM conventionally maximizes fitness.
This module provides a small, dependency-optional bridge that keeps that
conversion explicit and validates that returned candidates are permutations.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np

FitnessFunction = Callable[[Sequence[int]], float]


@dataclass(frozen=True)
class NevergradResult:
    """Best permutation found through Nevergrad's ask/tell/minimize API."""

    best_perm: tuple[int, ...]
    best_fitness: float
    evaluations: int


def _require_nevergrad() -> Any:
    try:
        import nevergrad as ng
    except ImportError as exc:  # pragma: no cover - exercised by installation tests
        raise ImportError(
            "The Nevergrad integration requires the optional dependency. "
            "Install it with `pip install prism-search[nevergrad]`."
        ) from exc
    return ng


def _as_permutation(candidate: Any, n: int) -> tuple[int, ...]:
    values = tuple(int(value) for value in np.asarray(candidate).reshape(-1))
    if len(values) != n or set(values) != set(range(n)):
        raise ValueError(f"Nevergrad produced an invalid permutation: {values!r}")
    return values


def permutation_parameter(n: int) -> Any:
    """Return a Nevergrad parameter constrained to permutations of ``range(n)``.

    The integer array representation is used because it is stable across
    Nevergrad releases. The cheap constraint rejects duplicate or out-of-range
    candidates before they reach the expensive objective.
    """

    if n < 2:
        raise ValueError("n must be at least 2")
    ng = _require_nevergrad()
    parameter = ng.p.Array(shape=(n,)).set_bounds(0, n - 1).set_integer_casting()
    parameter.register_cheap_constraint(
        lambda value: _is_permutation(value, n),
    )
    return parameter


def _is_permutation(candidate: Any, n: int) -> bool:
    try:
        return _as_permutation(candidate, n) == tuple(range(n)) or sorted(
            _as_permutation(candidate, n)
        ) == list(range(n))
    except (TypeError, ValueError):
        return False


def minimize(
    n: int,
    fitness_fn: FitnessFunction,
    *,
    budget: int,
    optimizer: str = "NGOpt",
    seed: int | None = None,
) -> NevergradResult:
    """Minimize a negative PRISM fitness through a Nevergrad optimizer.

    ``fitness_fn`` remains a maximization function. The adapter negates it for
    Nevergrad and returns the result in PRISM's original fitness convention.
    """

    if budget < 1:
        raise ValueError("budget must be at least 1")
    ng = _require_nevergrad()
    parameter = permutation_parameter(n)
    optimizer_cls = getattr(ng.optimizers, optimizer, None)
    if optimizer_cls is None:
        raise ValueError(f"Unknown Nevergrad optimizer: {optimizer!r}")
    searcher = optimizer_cls(parametrization=parameter, budget=budget)
    if seed is not None:
        searcher.parametrization.random_state.seed(seed)

    def loss(candidate: Any) -> float:
        try:
            permutation = _as_permutation(candidate, n)
        except ValueError:
            return float("inf")
        return -float(fitness_fn(permutation))

    recommendation = searcher.minimize(loss)
    best_perm = _as_permutation(recommendation.value, n)
    # Re-evaluate the returned candidate through the caller's fitness function
    # instead of relying on Nevergrad's internal ``loss`` attribute, which has
    # varied between releases.
    best_fitness = float(fitness_fn(best_perm))
    return NevergradResult(
        best_perm=best_perm,
        best_fitness=best_fitness,
        evaluations=searcher.budget if searcher.budget is not None else budget,
    )
