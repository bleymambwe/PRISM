"""Ordering-design tests: determinism, distinctness, and the cost guard."""

from __future__ import annotations

import math

import pytest

from evals.instruction_order.modules import GSM8K_MODULES, build_prompt, ordering_label
from evals.instruction_order.orderings import (
    MAX_EXHAUSTIVE_N,
    build_orderings,
    diverse_orderings,
    exhaustive,
    random_orderings,
)
from prism_search import cayley_distance


def test_exhaustive_is_complete_and_distinct() -> None:
    orderings = exhaustive(6)
    assert len(orderings) == math.factorial(6) == 720
    assert len(set(orderings)) == 720


def test_exhaustive_refuses_above_the_guard() -> None:
    # 8! = 40,320 orderings would be a five-figure API bill by accident.
    with pytest.raises(ValueError, match="exhaustive enumeration refused"):
        exhaustive(MAX_EXHAUSTIVE_N + 1)


def test_random_orderings_are_seeded() -> None:
    assert random_orderings(6, 20, seed=7) == random_orderings(6, 20, seed=7)


def test_different_seeds_give_different_sets() -> None:
    assert random_orderings(6, 20, seed=7) != random_orderings(6, 20, seed=8)


def test_random_orderings_are_distinct() -> None:
    orderings = random_orderings(6, 100, seed=3)
    assert len(set(orderings)) == 100


def test_random_orderings_are_valid_permutations() -> None:
    for ordering in random_orderings(8, 30, seed=1):
        assert sorted(ordering) == list(range(8))


def test_cannot_ask_for_more_orderings_than_exist() -> None:
    with pytest.raises(ValueError, match="only 6 exist"):
        random_orderings(3, 7, seed=1)


def test_count_below_two_is_rejected() -> None:
    # One ordering cannot produce a spread, which is the whole measurement.
    with pytest.raises(ValueError, match="at least 2"):
        random_orderings(6, 1, seed=1)


def test_diverse_is_more_spread_out_than_random() -> None:
    count, seed = 12, 5
    diverse = diverse_orderings(6, count, seed=seed, operator="swap")
    plain = random_orderings(6, count, seed=seed)

    def mean_nearest_neighbour(orderings: list[tuple[int, ...]]) -> float:
        return sum(
            min(cayley_distance(a, b) for j, b in enumerate(orderings) if j != i)
            for i, a in enumerate(orderings)
        ) / len(orderings)

    assert mean_nearest_neighbour(diverse) >= mean_nearest_neighbour(plain)


def test_diverse_rejects_unknown_operator() -> None:
    with pytest.raises(ValueError, match="unknown operator"):
        diverse_orderings(6, 5, seed=1, operator="teleport")


def test_build_orderings_dispatches() -> None:
    assert len(build_orderings(6, design="exhaustive")) == 720
    assert len(build_orderings(6, design="random", count=9, seed=2)) == 9
    assert len(build_orderings(6, design="diverse", count=9, seed=2)) == 9
    with pytest.raises(ValueError, match="unknown design"):
        build_orderings(6, design="spiral")  # type: ignore[arg-type]


def test_prompt_lists_modules_in_the_given_order() -> None:
    prompt = build_prompt((5, 0, 1, 2, 3, 4), "2+2?", GSM8K_MODULES, boxed=False)
    assert "1. ANSWER:" in prompt
    assert "2. RESTATE:" in prompt
    assert "Problem: 2+2?" in prompt
    assert "\\boxed" not in prompt


def test_prompt_boxed_wrapper_is_opt_in() -> None:
    assert "\\boxed" in build_prompt(range(6), "2+2?", GSM8K_MODULES, boxed=True)


def test_prompt_rejects_a_non_permutation() -> None:
    with pytest.raises(ValueError, match="must be a permutation"):
        build_prompt((0, 0, 1, 2, 3, 4), "2+2?", GSM8K_MODULES, boxed=False)


def test_ordering_label_is_readable_and_unique_per_ordering() -> None:
    assert ordering_label((0, 1, 2, 3, 4, 5), GSM8K_MODULES).startswith("RESTATE>IDENTIFY")
    assert ordering_label((0, 1, 2, 3, 4, 5), GSM8K_MODULES) != ordering_label(
        (1, 0, 2, 3, 4, 5), GSM8K_MODULES
    )
