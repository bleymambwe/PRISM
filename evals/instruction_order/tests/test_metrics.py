"""Spread-metric tests.

Skipped unless `inspect_ai` is installed, so the pure-Python grader and
ordering suites still run in the base environment.
"""

from __future__ import annotations

import pytest

pytest.importorskip("inspect_ai", reason="install with: uv sync --extra eval")

from inspect_ai.scorer import CORRECT, INCORRECT, SampleScore, Score

from evals.instruction_order.metrics import (
    best_ordering_accuracy,
    ordering_accuracies,
    ordering_count,
    ordering_mean,
    ordering_range,
    ordering_std,
    worst_ordering_accuracy,
)


def make_scores(per_ordering: list[list[bool]]) -> list[SampleScore]:
    """Build a flat sample grid from per-ordering correctness patterns."""
    scores: list[SampleScore] = []
    for ordering_id, results in enumerate(per_ordering):
        for question_id, correct in enumerate(results):
            scores.append(
                SampleScore(
                    score=Score(value=CORRECT if correct else INCORRECT),
                    sample_id=f"o{ordering_id}-q{question_id}",
                    sample_metadata={"ordering_id": ordering_id, "question_id": question_id},
                )
            )
    return scores


#: Ordering 0 gets 4/4, ordering 1 gets 2/4, ordering 2 gets 0/4.
GRID = make_scores([[True] * 4, [True, True, False, False], [False] * 4])


def test_ordering_accuracies_groups_by_ordering() -> None:
    assert ordering_accuracies(GRID) == [1.0, 0.5, 0.0]


def test_ordering_mean_weights_orderings_equally() -> None:
    assert ordering_mean()(GRID) == pytest.approx(0.5)


def test_ordering_range_is_best_minus_worst() -> None:
    assert ordering_range()(GRID) == pytest.approx(1.0)


def test_worst_and_best() -> None:
    assert worst_ordering_accuracy()(GRID) == pytest.approx(0.0)
    assert best_ordering_accuracy()(GRID) == pytest.approx(1.0)


def test_ordering_std_is_population_sd() -> None:
    # pstdev([1.0, 0.5, 0.0]) = sqrt(1/6)
    assert ordering_std()(GRID) == pytest.approx((1 / 6) ** 0.5)


def test_ordering_count() -> None:
    assert ordering_count()(GRID) == pytest.approx(3.0)


def test_identical_orderings_have_zero_spread() -> None:
    flat = make_scores([[True, False]] * 5)
    assert ordering_std()(flat) == pytest.approx(0.0)
    assert ordering_range()(flat) == pytest.approx(0.0)


def test_samples_without_ordering_metadata_are_ignored() -> None:
    # A stray sample from another dataset must not be folded into a bucket.
    polluted = [*GRID, SampleScore(score=Score(value=CORRECT), sample_id="x", sample_metadata={})]
    assert ordering_accuracies(polluted) == [1.0, 0.5, 0.0]


def test_spread_metrics_need_two_orderings() -> None:
    single = make_scores([[True, False]])
    assert ordering_std()(single) == 0.0
    assert ordering_range()(single) == 0.0
    # Point statistics are still meaningful with one ordering.
    assert ordering_mean()(single) == pytest.approx(0.5)


def test_empty_scores_do_not_raise() -> None:
    assert ordering_std()([]) == 0.0
    assert ordering_mean()([]) == 0.0
