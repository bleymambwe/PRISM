"""Deterministic canonical-form answer grader.

Ported verbatim in behaviour from `experiments/iteration-23-experiment-s`
(`grade` plus its `_grader_test.py` case list, which is reproduced in
`tests/test_grading.py`). Deliberately dependency-free: an external symbolic
equivalence library would make the score non-reproducible across versions,
which is the one thing a landscape study cannot tolerate.

Scope: integers, decimals, `a/b`, `\\frac{a}{b}`, and mixed numbers. Answers
outside those forms are not gradeable here, which is why the question pools are
filtered to simple canonical answers before they ever reach this function.
"""

from __future__ import annotations

import re

__all__ = ["extract_boxed", "extract_prediction", "grade", "normalize", "to_number"]

#: Ordered alternation - the longer LaTeX forms must be tried before the bare
#: integer branch or `\frac{14}{3}` would match as `14`.
ANSWER_TOKEN = re.compile(
    r"(-?\\frac\{-?\d+\}\{-?\d+\}"  # \frac{a}{b}
    r"|-?\d+\\frac\{-?\d+\}\{-?\d+\}"  # mixed number
    r"|-?\d+/\d+"  # a/b
    r"|-?\d[\d,]*\.\d+"  # decimal
    r"|-?\d[\d,]*)"  # integer, optional thousands separators
)

#: Answer forms this grader can handle. Used to filter question pools.
SIMPLE_ANSWER = re.compile(r"^-?\d+(\.\d+)?$|^-?\\frac\{-?\d+\}\{\d+\}$|^-?\d+/\d+$")


def extract_boxed(text: str) -> str | None:
    """Return the contents of the last ``\\boxed{...}``, brace-balanced."""
    index = text.rfind("\\boxed")
    if index == -1:
        return None
    start = text.find("{", index)
    if start == -1:
        return None
    depth = 0
    for position in range(start, len(text)):
        if text[position] == "{":
            depth += 1
        elif text[position] == "}":
            depth -= 1
            if depth == 0:
                return text[start + 1 : position]
    return None


def normalize(value: str | None) -> str | None:
    """Strip LaTeX spacing, delimiters and separators to a comparable form."""
    if value is None:
        return None
    value = value.strip().strip("$")
    value = value.replace("\\left", "").replace("\\right", "")
    value = value.replace("\\!", "").replace("\\,", "").replace("\\;", "")
    value = value.replace("\\:", "").replace("\\ ", "")
    value = value.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    value = value.replace(" ", "").rstrip(".")
    value = value.replace("{,}", "")  # thousands separator written as braces
    return value.replace(",", "")


def to_number(value: str | None) -> float | None:
    """Best-effort numeric value, so `5/4` and `1.25` compare equal."""
    if value is None:
        return None
    mixed = re.match(r"^(-?\d+)\\frac\{(-?\d+)\}\{(\d+)\}$", value)
    if mixed:
        whole, numerator, denominator = (int(g) for g in mixed.groups())
        sign = -1 if whole < 0 else 1
        return whole + sign * numerator / denominator
    if re.match(r"^-?\\frac\{-?\d+\}\{-?\d+\}$", value):
        negative = value.startswith("-")
        body = value[1:] if negative else value
        parts = re.match(r"^\\frac\{(-?\d+)\}\{(-?\d+)\}$", body)
        if parts is None:  # pragma: no cover - guarded by the outer match
            return None
        result = int(parts.group(1)) / int(parts.group(2))
        return -result if negative else result
    if re.match(r"^-?\d+/\d+$", value):
        numerator, denominator = value.split("/")
        return float(numerator) / float(denominator)
    try:
        return float(value)
    except ValueError:
        return None


def extract_prediction(model_text: str) -> str | None:
    """Pull the predicted answer out of a completion.

    Three conventions appear, depending on which module lands last and which
    wrapper was used: a ``\\boxed{}`` answer, an ``Answer:``-labelled token, or
    (when the model ignores both) the last answer-shaped token anywhere. Tried
    in that order of reliability.
    """
    boxed = extract_boxed(model_text)
    if boxed is not None:
        return boxed
    labelled = re.split(r"(?i)answer\s*:", model_text)
    if len(labelled) > 1:
        match = ANSWER_TOKEN.search(labelled[-1])
        if match:
            return match.group(0)
    tokens = ANSWER_TOKEN.findall(model_text)
    return tokens[-1] if tokens else None


def grade(gold_raw: str, model_text: str) -> bool:
    """True when the completion's answer matches the gold answer."""
    gold = normalize(gold_raw)
    prediction = normalize(extract_prediction(model_text))
    if prediction is None:
        return False
    if gold == prediction:
        return True
    gold_number, prediction_number = to_number(gold), to_number(prediction)
    if gold_number is not None and prediction_number is not None:
        return abs(gold_number - prediction_number) < 1e-6
    return False
