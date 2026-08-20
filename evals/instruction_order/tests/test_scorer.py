"""Scorer tests: the bridge between the frozen grader and Inspect's Score."""

from __future__ import annotations

import pytest

pytest.importorskip("inspect_ai", reason="install with: uv sync --extra eval")

from inspect_ai.model import ModelName, ModelOutput
from inspect_ai.scorer import CORRECT, INCORRECT, Target
from inspect_ai.solver import TaskState

from evals.instruction_order.scorer import (
    INSTRUCTION_ORDER_METRICS,
    canonical_answer,
)


def make_state(completion: str, ordering_label: str = "RESTATE>ANSWER") -> TaskState:
    state = TaskState(
        model=ModelName("mockllm/model"),
        sample_id="o0000-q000",
        epoch=1,
        input="irrelevant for scoring",
        messages=[],
        metadata={"ordering_id": 0, "ordering_label": ordering_label},
    )
    state.output = ModelOutput.from_content(model="mockllm/model", content=completion)
    return state


async def score_once(completion: str, gold: str):
    return await canonical_answer()(make_state(completion), Target(gold))


@pytest.mark.anyio
async def test_correct_boxed_answer() -> None:
    score = await score_once(r"working... \boxed{18}", "18")
    assert score.value == CORRECT
    assert score.answer == "18"


@pytest.mark.anyio
async def test_wrong_answer() -> None:
    score = await score_once(r"\boxed{19}", "18")
    assert score.value == INCORRECT


@pytest.mark.anyio
async def test_answer_label_convention() -> None:
    # The GSM8K task has no \boxed wrapper, so this is the primary path there.
    score = await score_once("steps...\nAnswer: 42", "42")
    assert score.value == CORRECT


@pytest.mark.anyio
async def test_equivalent_forms_are_correct() -> None:
    score = await score_once(r"\boxed{5/4}", "1.25")
    assert score.value == CORRECT


@pytest.mark.anyio
async def test_empty_completion_scores_incorrect_with_explanation() -> None:
    # A truncated or refused generation must score 0, never raise - one bad
    # sample would otherwise abort a 23,000-sample run.
    score = await score_once("", "18")
    assert score.value == INCORRECT
    assert "no answer-shaped token" in (score.explanation or "")


@pytest.mark.anyio
async def test_ordering_label_is_carried_into_score_metadata() -> None:
    score = await score_once(r"\boxed{18}", "18")
    assert (score.metadata or {}).get("ordering_label") == "RESTATE>ANSWER"


def test_scorer_declares_the_spread_metrics() -> None:
    # Guards against someone attaching plain accuracy() and silently losing
    # the only statistics this benchmark exists to report.
    assert len(INSTRUCTION_ORDER_METRICS) == 8


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
