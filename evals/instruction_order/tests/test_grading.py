"""Grader regression suite.

CASES is the case list from `experiments/iteration-23-experiment-s/_grader_test.py`,
carried over unchanged. These pin the grader's behaviour to what produced the
published landscapes: if one of these flips, the eval is no longer measuring
what the paper measured.
"""

from __future__ import annotations

import pytest

from evals.instruction_order.grading import (
    SIMPLE_ANSWER,
    extract_boxed,
    extract_prediction,
    grade,
    normalize,
    to_number,
)

CASES = [
    ("9", r"Let's work through this. The answer is \boxed{9}.", True),
    ("\\frac{14}{3}", r"So x = \boxed{\frac{14}{3}}", True),
    ("\\frac{14}{3}", r"So x = \boxed{\dfrac{14}{3}}", True),
    ("-125", r"\boxed{-125}", True),
    ("1.25", r"The result is \boxed{1.25}", True),
    ("1.25", r"\boxed{5/4}", True),
    ("720", r"\boxed{720}", True),
    ("9", r"\boxed{10}", False),
    ("\\frac{3}{56}", r"\boxed{\frac{6}{112}}", True),
    ("2", r"Answer: 2", True),
    ("13535", r"no boxed here, just prose", False),
    ("4", r"\boxed{4.0}", True),
    ("-125", r"\boxed{125}", False),
    ("10", "...math steps...\n8. ANSWER:\nAnswer: 10", True),
    ("850", "so r_1 satisfies ...\n\nAnswer: 850", True),
    ("66200", "Total: 66,200\n\nAnswer: 66,200", True),
    ("14", "we get x=14 which is wrong\nAnswer: 15", False),
    ("2", "Step 8. ANSWER: The final answer is 2.", True),
]


@pytest.mark.parametrize(("gold", "completion", "expected"), CASES)
def test_grade_matches_frozen_cases(gold: str, completion: str, expected: bool) -> None:
    assert grade(gold, completion) is expected


def test_extract_boxed_balances_braces() -> None:
    assert extract_boxed(r"\boxed{\frac{1}{2}}") == r"\frac{1}{2}"


def test_extract_boxed_takes_the_last_one() -> None:
    assert extract_boxed(r"first \boxed{1} then \boxed{2}") == "2"


def test_extract_boxed_returns_none_without_a_box() -> None:
    assert extract_boxed("no box at all") is None


def test_boxed_wins_over_answer_label() -> None:
    # A model that writes a wrong scratch "Answer:" then boxes the right value
    # must be graded on the box.
    assert extract_prediction(r"Answer: 3 ... final \boxed{4}") == "4"


def test_answer_label_wins_over_stray_numbers() -> None:
    assert extract_prediction("we had 5 apples and 7 pears\nAnswer: 12") == "12"


def test_falls_back_to_last_numeric_token() -> None:
    assert extract_prediction("no marker, the total comes to 42") == "42"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (r"\dfrac{1}{2}", r"\frac{1}{2}"),
        ("$1{,}000$", "1000"),
        ("  3.5. ", "3.5"),
        (r"\left(5\right)", "(5)"),
    ],
)
def test_normalize(raw: str, expected: str) -> None:
    assert normalize(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("5/4", 1.25),
        (r"\frac{14}{3}", 14 / 3),
        (r"-\frac{1}{2}", -0.5),
        (r"2\frac{1}{2}", 2.5),
        ("-7", -7.0),
        ("not a number", None),
    ],
)
def test_to_number(raw: str, expected: float | None) -> None:
    assert to_number(raw) == expected


def test_no_prediction_is_incorrect_not_an_error() -> None:
    assert grade("5", "") is False


@pytest.mark.parametrize("answer", ["7", "-7", "3.5", r"\frac{1}{2}", "3/4"])
def test_simple_answer_accepts_gradeable_forms(answer: str) -> None:
    assert SIMPLE_ANSWER.match(answer)


@pytest.mark.parametrize("answer", [r"\sqrt{2}", "x+1", r"(3,\frac{\pi}{2})", "12\\%"])
def test_simple_answer_rejects_ungradeable_forms(answer: str) -> None:
    # These are exactly the answers the pool filter must drop; letting one
    # through would score a correct model as wrong.
    assert not SIMPLE_ANSWER.match(answer)
