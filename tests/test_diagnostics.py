import math

import pytest

from prism_search import fitness_distance_correlation, preflight


def fixed_points(permutation):
    return sum(index == value for index, value in enumerate(permutation))


def test_fdc_is_negative_on_a_guiding_landscape():
    permutations = [
        [0, 1, 2, 3],
        [0, 1, 3, 2],
        [1, 0, 3, 2],
        [3, 2, 1, 0],
    ]
    fitnesses = [fixed_points(item) for item in permutations]
    value = fitness_distance_correlation(
        permutations, fitnesses, [[0, 1, 2, 3]], distance="cayley"
    )
    assert value < -0.8


def test_constant_fitness_has_zero_fdc():
    value = fitness_distance_correlation([[0, 1, 2], [1, 0, 2]], [1.0, 1.0], [[0, 1, 2]])
    assert value == 0.0


def test_preflight_is_deterministic_and_auditable():
    first = preflight(
        5,
        fixed_points,
        pair_samples=20,
        landscape_samples=40,
        seed=11,
        references=[list(range(5))],
    )
    second = preflight(
        5,
        fixed_points,
        pair_samples=20,
        landscape_samples=40,
        seed=11,
        references=[list(range(5))],
    )
    assert first == second
    assert first.reference_kind == "caller_supplied"
    assert first.distance_metric in {"cayley", "ulam", "kendall"}
    assert first.distinct_evaluations > 0
    assert math.isfinite(first.fitness_distance_correlation)


def test_preflight_flags_an_uninformative_evaluator():
    result = preflight(
        4,
        lambda _permutation: 1.0,
        pair_samples=5,
        landscape_samples=10,
        seed=3,
    )
    assert result.recommendation == "improve_evaluator"
    assert result.fitness_variance == 0.0
    assert result.reference_kind == "best_observed_proxy"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"n": 1}, "at least 2"),
        ({"pair_samples": 1}, "at least 2"),
        ({"n": 3, "landscape_samples": 7}, "number of distinct"),
        ({"operators": []}, "At least one"),
        ({"operators": ["unknown"]}, "Unknown"),
        ({"references": []}, "cannot be empty"),
    ],
)
def test_preflight_validates_inputs(kwargs, message):
    arguments = {
        "n": 4,
        "fitness_fn": fixed_points,
        "pair_samples": 5,
        "landscape_samples": 10,
        "seed": 3,
    }
    arguments.update(kwargs)
    with pytest.raises(ValueError, match=message):
        preflight(**arguments)


def test_preflight_rejects_nonfinite_fitness():
    with pytest.raises(ValueError, match="non-finite"):
        preflight(
            4,
            lambda _permutation: float("nan"),
            pair_samples=5,
            landscape_samples=10,
            seed=3,
        )


def test_preflight_landscape_probe_is_distinct():
    seen = []

    def recorded_fitness(permutation):
        seen.append(tuple(permutation))
        return fixed_points(permutation)

    result = preflight(
        3,
        recorded_fitness,
        operators=["swap"],
        pair_samples=2,
        landscape_samples=6,
        seed=4,
    )
    # Pair probes may overlap the landscape probe, but every possible ordering
    # must have been evaluated exactly once because the evaluation cache is
    # keyed by permutation.
    assert result.distinct_evaluations == 6
    assert len(seen) == 6
    assert len(set(seen)) == 6


def test_fdc_validates_inputs():
    with pytest.raises(ValueError, match="reference"):
        fitness_distance_correlation([[0, 1]], [1.0], [])
    with pytest.raises(ValueError, match="fitness"):
        fitness_distance_correlation([[0, 1]], [], [[0, 1]])
