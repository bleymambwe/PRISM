"""M02 repair: run the PRISM protocol at its TRUE total budget for each B.

The rejected submission read B=15/25/100 results off the prefix of a B=200 run.
The protocol sizes its probe from the total budget, so that prefix is a different
policy.  Here every (landscape, B, seed) is its own run with the budget supplied.

    python experiments/iteration-27-m01-m02-repair/fresh_budget.py [seconds]

Resumable: finished keys are skipped.  Run from the repository root.
"""

from __future__ import annotations

import csv
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "iteration-26-tier0-gauntlet"))
sys.path.insert(0, "src")

import _compat  # noqa: F401,E402
from landscapes import load_all  # noqa: E402
from optimizers import (  # noqa: E402
    _EXECUTOR_FOR_RECOMMENDATION,
    _OPERATOR_NAMES,
    BudgetExhausted,
    Oracle,
    _evolutionary,
    ea_portfolio,
    ls_swap,
)
from prism_search.diagnostics import preflight  # noqa: E402

OUT = os.path.join(HERE, "results", "fresh_budget_runs.csv")
SEEDS = 40
BUDGETS = (15, 25, 50, 100, 200)
FLOOR_FRACTION = 0.25  # pre-registered, not tuned
FIELDS = ["landscape", "method", "B", "seed", "budget", "hit", "hit_by_B", "probe_spent", "recommendation"]


def _probe_sizes(budget: int) -> tuple[int, int]:
    probe = max(4, int(0.2 * budget))
    return max(2, probe // 8), max(2, min(probe // 2, budget - 1))


def run(table, optima, n, B, seed, variant):
    """Mirror of optimizers.prism_protocol, instrumented, with the real budget."""

    oracle = Oracle(table, optima, B)
    rng = np.random.default_rng(seed)
    probe_spent, recommendation = 0, ""
    try:
        pairs, landscape = _probe_sizes(B)
        projected = 6 * pairs + landscape
        if variant == "floor" and projected > FLOOR_FRACTION * B:
            recommendation = "skipped_probe"
            ls_swap(oracle, n, rng)
        else:
            sub_seed = int(rng.integers(0, 2**31 - 1))
            result = preflight(
                n=n, fitness_fn=oracle, operators=_OPERATOR_NAMES,
                pair_samples=pairs, landscape_samples=landscape, seed=sub_seed,
            )
            probe_spent = oracle.count
            recommendation = result.recommendation
            executor = _EXECUTOR_FOR_RECOMMENDATION[result.recommendation]
            if executor is ea_portfolio:
                _evolutionary(oracle, n, rng, operator=result.selected_operator, aging=False)
            else:
                executor(oracle, n, rng)
    except BudgetExhausted:
        probe_spent = probe_spent or oracle.count
    return oracle, probe_spent, recommendation


def main() -> None:
    deadline = time.time() + (float(sys.argv[1]) if len(sys.argv) > 1 else 240.0)
    records = load_all()
    done = set()
    if os.path.exists(OUT):
        with open(OUT, newline="", encoding="utf-8") as h:
            done = {(r["landscape"], r["method"], int(r["B"]), int(r["seed"])) for r in csv.DictReader(h)}
    fresh = not os.path.exists(OUT)
    todo = [
        (name, variant, B, seed)
        for name in records for variant in ("protocol", "floor")
        for B in BUDGETS for seed in range(SEEDS)
        if (name, f"prism_{variant}", B, seed) not in done
    ]
    print(f"{len(done)} done; {len(todo)} remaining")
    count = 0
    with open(OUT, "a", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=FIELDS)
        if fresh:
            w.writeheader()
        for name, variant, B, seed in todo:
            if time.time() > deadline:
                break
            rec = records[name]
            budget = min(B, rec.size)
            o, spent, recmd = run(rec.table, rec.optima, rec.n, budget, seed, variant)
            w.writerow({
                "landscape": name, "method": f"prism_{variant}", "B": B, "seed": seed,
                "budget": budget, "hit": o.hit if o.hit is not None else "",
                "hit_by_B": int(o.hit is not None and o.hit <= budget),
                "probe_spent": spent, "recommendation": recmd,
            })
            h.flush()
            count += 1
    print(f"completed {count}; {len(todo) - count} remaining")
    if count == len(todo):
        print("FRESH BUDGET COMPLETE")


if __name__ == "__main__":
    main()
