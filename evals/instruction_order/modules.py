"""The fixed reasoning modules whose order is permuted.

Wording is frozen. The whole point of the benchmark is that nothing changes
between conditions except the order of these strings, so any edit here breaks
comparability with the published landscapes in arXiv:2608.08344 and must be
accompanied by a task-version bump.

`GSM8K_MODULES` is the six-module set from Experiment K, whose 6! = 720
orderings were enumerated exhaustively. `MATH500_MODULES` is the eight-module
set from Experiment S, which adds ESTIMATE and SIMPLIFY and is far too large
(8! = 40,320) to enumerate.
"""

from __future__ import annotations

from collections.abc import Sequence

GSM8K_MODULES: tuple[str, ...] = (
    "RESTATE: Restate the problem briefly in your own words.",
    "IDENTIFY: List the known quantities and what is being asked.",
    "PLAN: Devise a short step-by-step strategy before calculating.",
    "COMPUTE: Carry out the calculations step by step.",
    "CHECK: Verify the result against the problem statement.",
    "ANSWER: State the final answer on its own line as 'Answer: <number>'.",
)

MATH500_MODULES: tuple[str, ...] = (
    "RESTATE: Restate the problem briefly in your own words.",
    "IDENTIFY: List the known quantities and what is being asked.",
    "ESTIMATE: Make a rough order-of-magnitude estimate of the answer.",
    "PLAN: Devise a short step-by-step strategy before calculating.",
    "SIMPLIFY: Note any way to simplify the problem before solving.",
    "COMPUTE: Carry out the calculations step by step.",
    "CHECK: Verify the result against the problem statement.",
    "ANSWER: State the final answer on its own line as 'Answer: <number>'.",
)

MODULE_SETS: dict[str, tuple[str, ...]] = {
    "gsm8k": GSM8K_MODULES,
    "math500": MATH500_MODULES,
}


#: Short labels, used for readable ordering identifiers such as
#: ``PLAN>RESTATE>...``. Derived from the module text so the two never drift.
def short_labels(modules: Sequence[str]) -> tuple[str, ...]:
    return tuple(module.split(":", 1)[0] for module in modules)


def build_prompt(
    ordering: Sequence[int],
    problem: str,
    modules: Sequence[str],
    *,
    boxed: bool,
) -> str:
    """Render the numbered instruction list for one ordering.

    `boxed` reproduces the Experiment S wrapper, which asks for a \\boxed{}
    answer in addition to whatever the ANSWER module says. Experiment K (GSM8K)
    relied on the ANSWER module alone, so the two experiments need different
    wrappers to stay faithful to their published landscapes. The grader accepts
    both conventions either way.
    """
    if sorted(ordering) != list(range(len(modules))):
        raise ValueError(
            f"ordering must be a permutation of 0..{len(modules) - 1}, got {list(ordering)}"
        )
    steps = "\n".join(
        f"{position + 1}. {modules[index]}" for position, index in enumerate(ordering)
    )
    prompt = (
        "Solve the following mathematics problem. Work through these steps "
        f"in this exact order:\n{steps}\n\nProblem: {problem}"
    )
    if boxed:
        prompt += "\n\nPut your final answer on its own line inside \\boxed{}."
    return prompt


def ordering_label(ordering: Sequence[int], modules: Sequence[str]) -> str:
    """Human-readable ordering id, e.g. ``PLAN>RESTATE>COMPUTE>...``."""
    labels = short_labels(modules)
    return ">".join(labels[index] for index in ordering)
