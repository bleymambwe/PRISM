import pytest

from prism_search.integrations.saelens import make_sae_fitness, preflight_sae


def test_sae_fitness_adapts_and_validates_permutations():
    fitness = make_sae_fitness(lambda permutation: sum(i == v for i, v in enumerate(permutation)), 4)
    assert fitness((0, 1, 2, 3)) == 4
    with pytest.raises(ValueError, match="Expected a permutation"):
        fitness((0, 0, 1, 2))


def test_sae_preflight_uses_callback():
    result = preflight_sae(
        4,
        lambda permutation: sum(i == v for i, v in enumerate(permutation)),
        pair_samples=4,
        landscape_samples=8,
        seed=3,
    )
    assert result.distinct_evaluations >= 8
    assert result.reference_kind == "best_observed_proxy"


def _identity_score(permutation):
    return sum(i == v for i, v in enumerate(permutation))


def test_sae_fitness_rejects_bad_inputs():
    with pytest.raises(ValueError, match="at least 2"):
        make_sae_fitness(_identity_score, 1)
    fitness = make_sae_fitness(_identity_score, 3)
    with pytest.raises(ValueError, match="Expected a permutation"):
        fitness((0, 1))
    with pytest.raises(ValueError, match="Expected a permutation"):
        fitness((0, 1, 3))


def test_sae_fitness_returns_float_and_propagates_callback_errors():
    assert isinstance(make_sae_fitness(_identity_score, 3)((0, 1, 2)), float)

    def boom(_permutation):
        raise RuntimeError("hook failed")

    with pytest.raises(RuntimeError, match="hook failed"):
        make_sae_fitness(boom, 3)((0, 1, 2))


def test_nevergrad_helpers_validate_without_optimizer():
    ng_mod = pytest.importorskip("nevergrad")  # noqa: F841
    from prism_search.integrations import nevergrad as bridge

    assert bridge._as_permutation([2, 0, 1], 3) == (2, 0, 1)
    with pytest.raises(ValueError, match="invalid permutation"):
        bridge._as_permutation([0, 0, 1], 3)
    assert bridge._is_permutation([1, 0], 2)
    assert not bridge._is_permutation([1, 1], 2)
    with pytest.raises(ValueError, match="at least 2"):
        bridge.permutation_parameter(1)
    with pytest.raises(ValueError, match="budget"):
        bridge.minimize(3, _identity_score, budget=0)
    with pytest.raises(ValueError, match="Unknown Nevergrad optimizer"):
        bridge.minimize(3, _identity_score, budget=5, optimizer="NoSuchOptimizer")


def test_nevergrad_minimize_returns_valid_permutation():
    pytest.importorskip("nevergrad")
    from prism_search.integrations.nevergrad import minimize

    result = minimize(5, _identity_score, budget=60, optimizer="RandomSearch", seed=1)
    assert sorted(result.best_perm) == list(range(5))
    assert result.best_fitness == _identity_score(result.best_perm)
    assert result.evaluations >= 1
