"""Inspect scorer wrapping the frozen canonical-answer grader."""

from __future__ import annotations

from inspect_ai.scorer import (
    CORRECT,
    INCORRECT,
    Score,
    Scorer,
    Target,
    accuracy,
    scorer,
    stderr,
)
from inspect_ai.solver import TaskState

from evals.instruction_order.grading import extract_prediction, grade
from evals.instruction_order.metrics import (
    best_ordering_accuracy,
    ordering_count,
    ordering_mean,
    ordering_range,
    ordering_std,
    worst_ordering_accuracy,
)

#: `accuracy`/`stderr` describe the flat sample grid; the ordering_* metrics
#: describe the spread across conditions and are the ones worth reading.
INSTRUCTION_ORDER_METRICS = [
    accuracy(),
    stderr(),
    ordering_mean(),
    ordering_std(),
    ordering_range(),
    worst_ordering_accuracy(),
    best_ordering_accuracy(),
    ordering_count(),
]


@scorer(metrics=INSTRUCTION_ORDER_METRICS)
def canonical_answer() -> Scorer:
    """Exact match on canonical numeric form, no model grader.

    A model-graded scorer would put a second, noisier order-sensitive system in
    the measurement path - the benchmark would then be measuring the grader's
    sensitivity as much as the solver's.
    """

    async def score(state: TaskState, target: Target) -> Score:
        completion = state.output.completion
        prediction = extract_prediction(completion)
        correct = grade(target.text, completion)
        return Score(
            value=CORRECT if correct else INCORRECT,
            answer=prediction,
            explanation=(
                f"gold={target.text!r} extracted={prediction!r}"
                if prediction is not None
                else "no answer-shaped token found in completion"
            ),
            metadata={"ordering_label": (state.metadata or {}).get("ordering_label")},
        )

    return score
