"""Metrics that report a spread across orderings rather than one accuracy.

The scientific quantity here is not "how well does the model do" but "how much
does the answer depend on an arbitrary presentation choice". A single mean
accuracy would hide exactly the effect the benchmark exists to measure, so each
metric below collapses the sample grid to per-ordering accuracies first and
then reports a statistic over *those*.

`worst_ordering_accuracy` is the one to read first: it is what a user gets when
they write a perfectly reasonable prompt and happen to pick a bad order.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Callable

from inspect_ai.scorer import Metric, SampleScore, Value, metric, value_to_float

__all__ = [
    "best_ordering_accuracy",
    "ordering_accuracies",
    "ordering_count",
    "ordering_mean",
    "ordering_range",
    "ordering_std",
    "worst_ordering_accuracy",
]


def ordering_accuracies(scores: list[SampleScore]) -> list[float]:
    """Per-ordering accuracy, in ordering_id order.

    Samples whose metadata lacks an `ordering_id` are ignored rather than
    lumped together - a missing id means the sample did not come from this
    dataset builder, and averaging it in would corrupt every statistic.
    """
    to_float = value_to_float()
    buckets: dict[int, list[float]] = defaultdict(list)
    for sample_score in scores:
        metadata = sample_score.sample_metadata or {}
        ordering_id = metadata.get("ordering_id")
        if ordering_id is None:
            continue
        buckets[int(ordering_id)].append(to_float(sample_score.score.value))
    return [statistics.fmean(buckets[key]) for key in sorted(buckets)]


def _over_orderings(reduce: Callable[[list[float]], float], minimum: int = 1) -> Metric:
    def metric_fn(scores: list[SampleScore]) -> Value:
        accuracies = ordering_accuracies(scores)
        if len(accuracies) < minimum:
            return 0.0
        return float(reduce(accuracies))

    return metric_fn


@metric
def ordering_mean() -> Metric:
    """Mean accuracy across orderings (equal weight per ordering)."""
    return _over_orderings(statistics.fmean)


@metric
def ordering_std() -> Metric:
    """Population SD of per-ordering accuracy - the headline sensitivity number.

    Population rather than sample SD because the ordering set *is* the set of
    conditions being compared, not a sample drawn from a larger population of
    conditions we want to infer about.
    """
    return _over_orderings(statistics.pstdev, minimum=2)


@metric
def ordering_range() -> Metric:
    """Best minus worst ordering accuracy."""
    return _over_orderings(lambda values: max(values) - min(values), minimum=2)


@metric
def worst_ordering_accuracy() -> Metric:
    """Accuracy of the worst ordering - the realistic downside of a bad guess."""
    return _over_orderings(min)


@metric
def best_ordering_accuracy() -> Metric:
    """Accuracy of the best ordering - the ceiling ordering search could reach."""
    return _over_orderings(max)


@metric
def ordering_count() -> Metric:
    """How many orderings actually contributed, for auditing partial runs."""
    return _over_orderings(len)
