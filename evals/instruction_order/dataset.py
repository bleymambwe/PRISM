"""Build the (ordering x question) sample grid.

Every sample is one ordering applied to one question. The ordering travels in
`Sample.metadata` so the scorer never has to reconstruct it and the metrics can
group by it afterwards.

Question pools are committed JSON in `data/`, not fetched at run time. The
register requires external assets to be pinned, and a benchmark whose questions
can change underneath it cannot support a landscape claim. `load_math500` is
the one network path, and it pins an explicit Hugging Face revision.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from inspect_ai.dataset import MemoryDataset, Sample

from evals.instruction_order.grading import SIMPLE_ANSWER
from evals.instruction_order.modules import MODULE_SETS, build_prompt, ordering_label
from evals.instruction_order.orderings import Design, build_orderings

DATA_DIR = Path(__file__).parent / "data"

#: Pinned so the dataset can never silently move under a published result.
#: The register requires external assets to carry an explicit revision. Resolved
#: from the Hugging Face API on 2026-08-20 (dataset last modified 2025-12-15).
#: Changing this changes what the eval measures - bump the task version with it.
MATH500_REPO = "HuggingFaceH4/MATH-500"
MATH500_REVISION = "6e4ed1a2a79af7d8630a6b768ec859cb5af4d3be"


def load_gsm8k_subset(limit: int | None = None) -> list[dict[str, str]]:
    """The frozen 32-question GSM8K subset used for the exhaustive map."""
    records = json.loads((DATA_DIR / "gsm8k_subset32.json").read_text(encoding="utf-8"))
    pool = [{"problem": record["question"], "answer": _gsm8k_gold(record)} for record in records]
    return pool[:limit] if limit else pool


def load_math500(limit: int = 100, levels: Sequence[int] = (3, 4, 5)) -> list[dict[str, str]]:
    """MATH-500 restricted to levels 3-5 with simple canonical answers.

    Filtered to the answer forms `grading.grade` handles exactly, which is what
    makes the frozen grader safe to rely on. Requires `datasets`; install with
    the `eval-math500` extra.
    """
    try:
        from datasets import load_dataset
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ImportError(
            "load_math500 needs the `datasets` package: uv sync --extra eval-math500"
        ) from exc

    rows = load_dataset(MATH500_REPO, split="test", revision=MATH500_REVISION)
    pool = [
        {"problem": row["problem"], "answer": row["answer"]}
        for row in rows
        if row.get("level") in levels and SIMPLE_ANSWER.match(str(row.get("answer", "")).strip())
    ]
    if len(pool) < limit:
        raise ValueError(
            f"only {len(pool)} MATH-500 items match levels {levels} with simple answers; "
            f"asked for {limit}"
        )
    return pool[:limit]


def _gsm8k_gold(record: dict[str, Any]) -> str:
    """GSM8K stores the answer after a `####` marker at the end of the rationale."""
    if record.get("gold") not in (None, ""):
        return str(record["gold"]).strip()
    match = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", record["answer"])
    if not match:
        raise ValueError(f"no #### answer marker in record: {record['answer'][-80:]!r}")
    return match.group(1).replace(",", "")


def build_dataset(
    module_set: str,
    questions: list[dict[str, str]],
    *,
    design: Design = "random",
    orderings: int = 50,
    seed: int = 7,
    operator: str = "swap",
    boxed: bool = True,
) -> MemoryDataset:
    """Cross every ordering with every question into one flat sample list."""
    modules = MODULE_SETS[module_set]
    ordering_set = build_orderings(
        len(modules), design=design, count=orderings, seed=seed, operator=operator
    )

    samples: list[Sample] = []
    for ordering_index, ordering in enumerate(ordering_set):
        label = ordering_label(ordering, modules)
        for question_index, question in enumerate(questions):
            samples.append(
                Sample(
                    input=build_prompt(ordering, question["problem"], modules, boxed=boxed),
                    target=question["answer"],
                    id=f"o{ordering_index:04d}-q{question_index:03d}",
                    metadata={
                        # `ordering_id` is what the metrics group by. Keep it an
                        # int so grouping stays cheap on 20k+ samples.
                        "ordering_id": ordering_index,
                        "ordering": list(ordering),
                        "ordering_label": label,
                        "question_id": question_index,
                        "module_set": module_set,
                    },
                )
            )
    return MemoryDataset(samples, name=f"instruction-order-{module_set}-{design}")
