"""E0.3 evaluator resolution: how many questions does the regime call need?

Every language-model landscape in this project is an average over a finite
question set, so its fitness has a granularity of 1/q.  With q = 32 the
flagship landscape can only take 33 distinct values, and in fact takes 29.
That is the quantitative form of the reviewer objection "32 questions is noise".

This script rebuilds the landscape from the committed answer caches using only
q of the questions, recomputes the pre-flight statistics and the regime call,
and measures how often that call matches the one made with the full question
set.  It also reports how many distinct fitness values survive at each q, which
is the resolution figure the protocol's own "improve the evaluator" branch
should be keyed to.

CPU-only; re-derives everything from cached model responses, spending nothing.

    python resolution.py [seconds]
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "src")

from prism_search.distances import DISTANCES, OPERATOR_DISTANCE  # noqa: E402
from prism_search.operators import MUTATION_OPERATORS  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results")
OUT_CSV = os.path.join(OUT_DIR, "resolution_curves.csv")

OPERATORS = ("swap", "insert", "inversion")
GUIDING_THRESHOLD = -0.15
DECEPTIVE_THRESHOLD = 0.30
RESAMPLES = 60
PAIRS = 1200
POINTS = 400
# At small question counts many orderings tie at the top, so the exact
# "distance to the nearest optimum" becomes quadratic in the tie count.  We cap
# the reference set at a sample of this many optima -- applied identically at
# every question count, so comparisons across q remain fair.
MAX_REFERENCES = 25

# name -> (cache path, question counts to test)
CACHES: dict[str, str] = {
    "llm_gsm8k_n6": "experiments/iteration-09/results/answer_cache.csv",
    "llm_gsm8k_n8": "experiments/iteration-11/results/answer_cache.csv",
    "llm_gemma_n6": "experiments/iteration-17/results/gemma_answer_cache.csv",
    "llm_llama_n6": "experiments/iteration-19-crossfamily/results/llama_answer_cache.csv",
    "llm_qwen_n6": "experiments/iteration-19-crossfamily/results/qwen_answer_cache.csv",
    "llm_math500_n8": "experiments/iteration-23-experiment-s/results/answer_cache.csv",
}

FIELDS = [
    "landscape",
    "n",
    "n_orderings",
    "q_total",
    "q_subset",
    "resamples",
    "regime_agreement",
    "operator_agreement",
    "mean_distinct_values",
    "mean_abs_fdc_error",
    "full_regime",
    "full_operator",
    "full_fdc",
    "full_distinct_values",
]


def _pearson(a, b) -> float:
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    value = float(np.corrcoef(a, b)[0, 1])
    return value if math.isfinite(value) else 0.0


def load_cache(path: str) -> tuple[dict[tuple[int, ...], dict[int, int]], list[int]]:
    per_perm: dict[tuple[int, ...], dict[int, int]] = defaultdict(dict)
    questions: set[int] = set()
    with open(os.path.join(ROOT, path), newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            perm = tuple(json.loads(row["perm"]))
            qidx = int(row["qidx"])
            per_perm[perm][qidx] = int(row["correct"])
            questions.add(qidx)
    return dict(per_perm), sorted(questions)


def build_table(
    per_perm: dict[tuple[int, ...], dict[int, int]], subset: list[int]
) -> dict[tuple[int, ...], float]:
    table: dict[tuple[int, ...], float] = {}
    for perm, answers in per_perm.items():
        values = [answers[q] for q in subset if q in answers]
        if values:
            table[perm] = sum(values) / len(values)
    return table


def _move(perm: np.ndarray, operator: str, rng) -> tuple[int, ...]:
    """Apply one mutation.  Semantics match ``prism_search.operators``."""

    n = perm.shape[0]
    i = int(rng.integers(n))
    j = int(rng.integers(n - 1))
    if j >= i:
        j += 1
    out = perm.copy()
    if operator == "swap":
        out[i], out[j] = out[j], out[i]
    elif operator == "insert":
        value = out[i]
        out = np.insert(np.delete(out, i), j, value)
    else:
        lo, hi = (i, j) if i < j else (j, i)
        out[lo : hi + 1] = out[lo : hi + 1][::-1]
    return tuple(int(x) for x in out)


def diagnose(table: dict[tuple[int, ...], float], rng) -> tuple[str, str, float]:
    keys = list(table)
    arrays = [np.array(k) for k in keys]
    rhos = {}
    for operator in OPERATORS:
        parents, children = [], []
        for _ in range(PAIRS):
            index = int(rng.integers(len(keys)))
            child_key = _move(arrays[index], operator, rng)
            if child_key not in table:
                continue
            parents.append(table[keys[index]])
            children.append(table[child_key])
        rhos[operator] = _pearson(parents, children) if parents else 0.0
    operator = max(OPERATORS, key=rhos.__getitem__)
    distance = DISTANCES[OPERATOR_DISTANCE[operator]]

    best = max(table.values())
    optima = [k for k, v in table.items() if v == best]
    if len(optima) > MAX_REFERENCES:
        picked = rng.choice(len(optima), MAX_REFERENCES, replace=False)
        optima = [optima[int(i)] for i in picked]
    if len(keys) > POINTS:
        idx = rng.choice(len(keys), POINTS, replace=False)
        chosen = [keys[int(i)] for i in idx]
    else:
        chosen = keys
    fits = [table[k] for k in chosen]
    dists = [min(distance(list(k), list(o)) for o in optima) for k in chosen]
    value = _pearson(fits, dists)

    if value <= GUIDING_THRESHOLD:
        regime = "search_pays"
    elif value >= DECEPTIVE_THRESHOLD:
        regime = "do_not_search"
    else:
        regime = "random_competitive"
    return regime, operator, value


def main() -> None:
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 900.0
    deadline = time.time() + seconds
    os.makedirs(OUT_DIR, exist_ok=True)

    done: set[tuple[str, int]] = set()
    if os.path.exists(OUT_CSV):
        with open(OUT_CSV, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                done.add((row["landscape"], int(row["q_subset"])))
    fresh = not os.path.exists(OUT_CSV)

    with open(OUT_CSV, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if fresh:
            writer.writeheader()

        for name, path in CACHES.items():
            full_path = os.path.join(ROOT, path)
            if not os.path.exists(full_path):
                print(f"  {name}: cache missing, skipped")
                continue
            per_perm, questions = load_cache(path)
            q_total = len(questions)
            n = len(next(iter(per_perm)))
            rng = np.random.default_rng(20260813)

            full_table = build_table(per_perm, questions)
            full_regime, full_operator, full_fdc = diagnose(full_table, rng)
            full_distinct = len(set(full_table.values()))
            print(
                f"  {name}: {len(full_table)} orderings, {q_total} questions, "
                f"{full_distinct} distinct values, regime={full_regime}"
            )

            subsets = [q for q in (4, 8, 16, 32, 64, 100) if q < q_total]
            for q in subsets:
                if (name, q) in done:
                    continue
                if time.time() > deadline:
                    print("wall-clock budget reached")
                    return
                regime_hits = 0
                operator_hits = 0
                distincts = []
                errors = []
                for _ in range(RESAMPLES):
                    subset = [
                        questions[int(i)]
                        for i in rng.choice(q_total, q, replace=False)
                    ]
                    table = build_table(per_perm, subset)
                    regime, operator, value = diagnose(table, rng)
                    regime_hits += int(regime == full_regime)
                    operator_hits += int(operator == full_operator)
                    distincts.append(len(set(table.values())))
                    errors.append(abs(value - full_fdc))
                writer.writerow(
                    {
                        "landscape": name,
                        "n": n,
                        "n_orderings": len(full_table),
                        "q_total": q_total,
                        "q_subset": q,
                        "resamples": RESAMPLES,
                        "regime_agreement": round(regime_hits / RESAMPLES, 4),
                        "operator_agreement": round(operator_hits / RESAMPLES, 4),
                        "mean_distinct_values": round(float(np.mean(distincts)), 2),
                        "mean_abs_fdc_error": round(float(np.mean(errors)), 4),
                        "full_regime": full_regime,
                        "full_operator": full_operator,
                        "full_fdc": round(full_fdc, 4),
                        "full_distinct_values": full_distinct,
                    }
                )
                handle.flush()

    print("RESOLUTION COMPLETE")


if __name__ == "__main__":
    main()
