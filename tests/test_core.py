import math

import pytest

from prism_search import PRISM


def fixed_points(permutation):
    return sum(index == value for index, value in enumerate(permutation))


def test_evolve_is_seeded_and_returns_valid_result():
    first = PRISM(6, fixed_points, pop_size=10, p_m=0.5, seed=42).evolve(20)
    second = PRISM(6, fixed_points, pop_size=10, p_m=0.5, seed=42).evolve(20)
    assert first == second
    assert sorted(first.best_perm) == list(range(6))
    assert first.evaluations == 200
    assert len(first.history) == 20
    assert first.termination_reason == "generations"


def test_evolve_stops_on_target():
    result = PRISM(5, fixed_points, pop_size=6, seed=1).evolve(generations=20, target_fitness=-1)
    assert result.hit_generation == 0
    assert result.generations_run == 1
    assert result.termination_reason == "target_reached"


def test_search_honors_distinct_evaluation_budget():
    calls = []

    def recorded_fitness(permutation):
        calls.append(tuple(permutation))
        return fixed_points(permutation)

    result = PRISM(6, recorded_fitness, pop_size=8, mutation="portfolio", seed=7).search(30)
    assert result.evaluations == 30
    assert len(calls) == 30
    assert len(set(calls)) == 30
    assert result.termination_reason == "budget_exhausted"


def test_search_caps_budget_at_complete_space():
    result = PRISM(3, fixed_points, pop_size=4, seed=5).search(20)
    assert result.evaluations <= math.factorial(3)
    assert result.termination_reason in {"budget_exhausted", "proposal_space_saturated"}


def test_adaptive_mode_reports_normalized_weights():
    result = PRISM(5, fixed_points, pop_size=6, p_m=1.0, mutation="adaptive", seed=9).evolve(10)
    assert result.operator_weights is not None
    assert set(result.operator_weights) == {"swap", "insert", "inversion", "scramble"}
    assert sum(result.operator_weights.values()) == pytest.approx(1.0, abs=1e-5)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"n": 1}, "n must"),
        ({"pop_size": 1}, "pop_size"),
        ({"p_m": 2}, "p_m"),
        ({"k": 0}, "k must"),
        ({"k": 21}, "k must"),
        ({"elitism": 20}, "elitism"),
        ({"mutation": "unknown"}, "Unknown mutation"),
    ],
)
def test_constructor_validates_parameters(kwargs, message):
    arguments = {"n": 6, "fitness_fn": fixed_points}
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=message):
        PRISM(**arguments)


def test_constructor_rejects_population_larger_than_space():
    with pytest.raises(ValueError, match="number of distinct"):
        PRISM(3, fixed_points, pop_size=7)


def test_methods_validate_parameters():
    optimizer = PRISM(5, fixed_points, pop_size=5, seed=0)
    with pytest.raises(ValueError, match="generations"):
        optimizer.evolve(0)
    with pytest.raises(ValueError, match="at least pop_size"):
        optimizer.search(4)
    with pytest.raises(ValueError, match="max_proposal_attempts"):
        optimizer.search(5, max_proposal_attempts=0)


def test_nonfinite_fitness_is_rejected():
    with pytest.raises(ValueError, match="non-finite"):
        PRISM(5, lambda _permutation: float("inf"), pop_size=5).evolve(1)
