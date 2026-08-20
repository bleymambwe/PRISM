"""Instruction-order sensitivity tasks.

Measures how much a model's mathematical accuracy depends on the *order* of a
fixed set of reasoning instructions whose wording never changes. Implements the
instruction-ordering landscape of arXiv:2608.08344, where 720 orderings of six
fixed modules spanned 6.3%-96.9% accuracy on a GSM8K subset.

Run:
    uv run inspect eval evals/instruction_order/task.py@instruction_order_gsm8k \\
        --model openai/gpt-4o-mini --limit 200

The default is deliberately cheap (50 orderings x 32 questions = 1,600 calls).
`instruction_order_gsm8k_exhaustive` reproduces the paper's full 720-ordering
map and costs ~23,000 calls - opt in knowingly.
"""

from __future__ import annotations

from inspect_ai import Task, task
from inspect_ai.model import GenerateConfig
from inspect_ai.solver import generate

from evals.instruction_order.dataset import build_dataset, load_gsm8k_subset, load_math500
from evals.instruction_order.orderings import Design
from evals.instruction_order.scorer import canonical_answer

#: Temperature 0 throughout. Sampling noise and ordering effects are the same
#: size in these landscapes, so anything above 0 makes the two inseparable.
DETERMINISTIC = GenerateConfig(temperature=0.0, max_tokens=2048)


@task
def instruction_order_gsm8k(
    orderings: int = 50,
    questions: int = 32,
    design: Design = "random",
    seed: int = 7,
    operator: str = "swap",
) -> Task:
    """Six fixed reasoning modules, permuted, on a frozen GSM8K subset.

    Args:
        orderings: How many distinct module orderings to compare.
        questions: Questions per ordering (max 32, the frozen subset size).
        design: `random`, `diverse` (PRISM maximin), or `exhaustive`.
        seed: Seed for the ordering design.
        operator: Distance alignment for `diverse` - swap, insert or precedence.
    """
    return Task(
        dataset=build_dataset(
            "gsm8k",
            load_gsm8k_subset(questions),
            design=design,
            orderings=orderings,
            seed=seed,
            operator=operator,
            boxed=False,  # Experiment K relied on the ANSWER module alone.
        ),
        solver=generate(),
        scorer=canonical_answer(),
        config=DETERMINISTIC,
    )


@task
def instruction_order_gsm8k_exhaustive(questions: int = 32) -> Task:
    """All 720 orderings of the six modules - the paper's exhaustive map.

    ~23,000 model calls. This is the replication target, not a routine run.
    """
    return instruction_order_gsm8k(design="exhaustive", questions=questions)


@task
def instruction_order_math500(
    orderings: int = 50,
    questions: int = 100,
    design: Design = "random",
    seed: int = 7,
    operator: str = "swap",
) -> Task:
    """Eight fixed modules on MATH-500 levels 3-5 (harder, sparser optima).

    Needs the `eval-math500` extra for `datasets`. 8! = 40,320 orderings, so
    `exhaustive` is refused here by design.
    """
    return Task(
        dataset=build_dataset(
            "math500",
            load_math500(questions),
            design=design,
            orderings=orderings,
            seed=seed,
            operator=operator,
            boxed=True,  # Experiment S added a \boxed{} wrapper.
        ),
        solver=generate(),
        scorer=canonical_answer(),
        config=DETERMINISTIC,
    )
