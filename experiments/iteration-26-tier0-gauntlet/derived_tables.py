"""E0.4 derived tables: turn answer caches into per-ordering landscapes.

The transfer studies shipped raw answer caches (``perm, qidx, correct``) rather
than per-ordering fitness tables, so the appendix's reproducibility claim was
one groupby short of literally true.  This closes that gap: every landscape the
paper discusses becomes a committed CSV that a reader can load without an API
key and without re-spending the original budget.

    python derived_tables.py
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results")
INDEX_CSV = os.path.join(OUT_DIR, "derived_index.csv")

# source cache -> derived landscape
DERIVATIONS: tuple[tuple[str, str], ...] = (
    (
        "experiments/iteration-09/results/answer_cache.csv",
        "experiments/iteration-09/results/derived_landscape.csv",
    ),
    (
        "experiments/iteration-11/results/answer_cache.csv",
        "experiments/iteration-11/results/n8_landscape.csv",
    ),
    (
        "experiments/iteration-17/results/gemma_answer_cache.csv",
        "experiments/iteration-17/results/gemma_landscape.csv",
    ),
    (
        "experiments/iteration-19-crossfamily/results/qwen_answer_cache.csv",
        "experiments/iteration-19-crossfamily/results/qwen_landscape.csv",
    ),
    (
        "experiments/iteration-19-crossfamily/results/llama_answer_cache.csv",
        "experiments/iteration-19-crossfamily/results/llama_landscape.csv",
    ),
    (
        "experiments/iteration-23-experiment-s/results/answer_cache.csv",
        "experiments/iteration-23-experiment-s/results/math500_landscape.csv",
    ),
)


def derive(source: str, target: str) -> dict[str, object] | None:
    source_path = os.path.join(ROOT, source)
    if not os.path.exists(source_path):
        print(f"  SKIP {source} (missing)")
        return None

    totals: dict[str, list[int]] = defaultdict(list)
    with open(source_path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            totals[row["perm"]].append(int(row["correct"]))

    target_path = os.path.join(ROOT, target)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(target_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["perm", "fitness", "n_questions"])
        for perm in sorted(totals, key=lambda p: json.loads(p)):
            answers = totals[perm]
            writer.writerow([perm, sum(answers) / len(answers), len(answers)])

    fitnesses = [sum(v) / len(v) for v in totals.values()]
    counts = {len(v) for v in totals.values()}
    n = len(json.loads(next(iter(totals))))
    row = {
        "source": source,
        "derived": target,
        "n": n,
        "n_orderings": len(totals),
        "questions_per_ordering": min(counts) if len(counts) == 1 else f"{min(counts)}-{max(counts)}",
        "min_fitness": round(min(fitnesses), 6),
        "max_fitness": round(max(fitnesses), 6),
        "distinct_values": len(set(fitnesses)),
    }
    print(
        f"  {target}: {row['n_orderings']} orderings, "
        f"{row['questions_per_ordering']} questions, "
        f"{row['distinct_values']} distinct values, "
        f"range {row['min_fitness']}-{row['max_fitness']}"
    )
    return row


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    rows = []
    for source, target in DERIVATIONS:
        row = derive(source, target)
        if row is not None:
            rows.append(row)
    if rows:
        with open(INDEX_CSV, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    print(f"DERIVED {len(rows)} landscape tables")


if __name__ == "__main__":
    main()
