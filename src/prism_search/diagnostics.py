"""Landscape diagnostics implementing the PRISM pre-flight protocol."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from math import factorial, isfinite

import numpy as np

from .distances import DISTANCES, OPERATOR_DISTANCE, Distance
from .operators import MUTATION_OPERATORS
from .results import PreflightResult, Recommendation

FitnessFunction = Callable[[Sequence[int]], float]


def _pearson(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or len(left) < 2:
        raise ValueError("Correlation requires equal sequences with at least two values")
    if np.std(left) == 0.0 or np.std(right) == 0.0:
        return 0.0
    correlation = float(np.corrcoef(left, right)[0, 1])
    return correlation if isfinite(correlation) else 0.0


def fitness_distance_correlation(
    permutations: Sequence[Sequence[int]],
    fitnesses: Sequence[float],
    references: Sequence[Sequence[int]],
    *,
    distance: str | Distance = "cayley",
) -> float:
    """Compute fitness--distance correlation to the nearest reference optimum.

    For a maximization problem, a negative value indicates that higher-fitness
    candidates tend to be closer to a reference.  References may be exact
    optima or a frozen best-observed proxy, but callers should report which.
    """

    if not references:
        raise ValueError("At least one reference permutation is required")
    if len(permutations) != len(fitnesses):
        raise ValueError("Each permutation must have one fitness value")
    distance_function = DISTANCES[distance] if isinstance(distance, str) else distance
    distances = [
        min(distance_function(permutation, reference) for reference in references)
        for permutation in permutations
    ]
    return _pearson([float(value) for value in fitnesses], distances)


def preflight(
    n: int,
    fitness_fn: FitnessFunction,
    *,
    operators: Iterable[str] = ("swap", "insert", "inversion"),
    pair_samples: int = 100,
    landscape_samples: int = 200,
    seed: int | None = None,
    references: Sequence[Sequence[int]] | None = None,
    variance_tolerance: float = 1e-12,
    guiding_threshold: float = -0.15,
    deceptive_threshold: float = 0.30,
) -> PreflightResult:
    """Run PRISM's fixed-budget landscape pre-flight.

    Thresholds are conservative empirical operating bands from the PRISM
    study, not universal constants.  If exact optima are unknown, the best
    frozen pilot candidate(s) are used as explicitly labelled FDC proxies.
    Fitness calls are cached by permutation so repeated samples do not consume
    the distinct-evaluation count.
    """

    if n < 2:
        raise ValueError("n must be at least 2")
    if pair_samples < 2 or landscape_samples < 2:
        raise ValueError("pair_samples and landscape_samples must be at least 2")
    if landscape_samples > factorial(n):
        raise ValueError("landscape_samples cannot exceed the number of distinct permutations")
    operator_names = tuple(operators)
    if not operator_names:
        raise ValueError("At least one mutation operator is required")
    unknown = set(operator_names) - set(MUTATION_OPERATORS)
    if unknown:
        raise ValueError(f"Unknown mutation operator(s): {', '.join(sorted(unknown))}")

    rng = np.random.default_rng(seed)
    cache: dict[tuple[int, ...], float] = {}
    cache_hits = 0

    def evaluate(permutation: Sequence[int]) -> float:
        nonlocal cache_hits
        key = tuple(int(value) for value in permutation)
        if key in cache:
            cache_hits += 1
            return cache[key]
        value = float(fitness_fn(key))
        if not isfinite(value):
            raise ValueError(f"fitness_fn returned a non-finite value for {key}")
        cache[key] = value
        return value

    autocorrelations: dict[str, float] = {}
    for operator_name in operator_names:
        parents: list[float] = []
        children: list[float] = []
        operator = MUTATION_OPERATORS[operator_name]
        for _ in range(pair_samples):
            parent = [int(value) for value in rng.permutation(n)]
            child = parent.copy()
            operator(child, rng)
            parents.append(evaluate(parent))
            children.append(evaluate(child))
        autocorrelations[operator_name] = _pearson(parents, children)

    selected_operator = max(operator_names, key=autocorrelations.__getitem__)
    distance_name = OPERATOR_DISTANCE[selected_operator]
    sample_permutations: list[tuple[int, ...]] = []
    sampled: set[tuple[int, ...]] = set()
    while len(sample_permutations) < landscape_samples:
        permutation = tuple(int(value) for value in rng.permutation(n))
        if permutation not in sampled:
            sampled.add(permutation)
            sample_permutations.append(permutation)
    sample_fitnesses = [evaluate(permutation) for permutation in sample_permutations]

    if references is None:
        best = max(sample_fitnesses)
        frozen_references = tuple(
            permutation
            for permutation, fitness in zip(sample_permutations, sample_fitnesses, strict=True)
            if fitness == best
        )
        reference_kind = "best_observed_proxy"
    else:
        frozen_references = tuple(tuple(int(value) for value in item) for item in references)
        if not frozen_references:
            raise ValueError("references cannot be empty")
        reference_kind = "caller_supplied"

    fdc = fitness_distance_correlation(
        sample_permutations,
        sample_fitnesses,
        frozen_references,
        distance=distance_name,
    )
    variance = float(np.var(sample_fitnesses))
    best_sample_fitness = max(sample_fitnesses)
    tie_fraction = sum(value == best_sample_fitness for value in sample_fitnesses) / len(
        sample_fitnesses
    )
    recommendation: Recommendation
    if variance <= variance_tolerance:
        recommendation = "improve_evaluator"
    elif fdc <= guiding_threshold:
        recommendation = "evolution"
    elif fdc >= deceptive_threshold:
        recommendation = "avoid_local_search"
    else:
        recommendation = "uniform_sampling"

    return PreflightResult(
        autocorrelations=autocorrelations,
        selected_operator=selected_operator,
        fitness_distance_correlation=fdc,
        distance_metric=distance_name,
        fitness_variance=variance,
        top_tie_fraction=tie_fraction,
        recommendation=recommendation,
        distinct_evaluations=len(cache),
        cache_hits=cache_hits,
        reference_permutations=frozen_references,
        reference_kind=reference_kind,
        seed=seed,
    )
