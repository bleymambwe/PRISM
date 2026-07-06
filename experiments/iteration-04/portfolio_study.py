"""Iteration 4, Experiment F: operator-portfolio PRISM.

Modes {portfolio, adaptive} x landscapes {hamming, kendall, adjacency}
x n in {6, 8, 10, 12, 14, 16}, 15 seeds, cap 10000 generations —
identical protocol to Iteration-3 Experiment C so results merge
directly with the fixed-operator baselines
(experiments/iteration-03/results/operator_study_results.csv).

Hypotheses: H4 (uniform portfolio succeeds everywhere with ~2-4x
overhead vs matched operator), H5 (adaptive closes part of the gap).

Kill-safe / resumable / budgeted:
    python portfolio_study.py [budget-seconds]
Rerun until it prints STUDY COMPLETE.

Outputs -> experiments/iteration-04/results/portfolio_results.csv
(also records evaluations, since adaptive pays one extra evaluation per
mutation event, and final adaptive operator weights).
"""

import csv
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM
from benchmarks.synthetic import OBJECTIVES

OUT_DIR = os.path.join(os.path.dirname(__file__), "results")
CSV_PATH = os.path.join(OUT_DIR, "portfolio_results.csv")
FIELDS = ["objective", "mode", "n", "seed", "hit_generation",
          "censored", "evaluations", "operator_weights", "status"]
SEEDS = list(range(15))
NS = [6, 8, 10, 12, 14, 16]
MODES = ["portfolio", "adaptive"]
LANDSCAPES = ["hamming", "kendall", "adjacency"]
MAX_GENS = 10000
BUDGET_SECONDS = None
_START = time.time()


class BudgetExceeded(Exception):
    pass


def check_budget():
    if BUDGET_SECONDS and time.time() - _START > BUDGET_SECONDS:
        raise BudgetExceeded


def load_done():
    done = set()
    if os.path.exists(CSV_PATH):
        for r in csv.DictReader(open(CSV_PATH)):
            done.add((r["objective"], r["mode"], int(r["n"]),
                      int(r["seed"])))
    return done


def append_row(row):
    new_file = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    done = load_done()
    if done:
        print(f"Resuming: {len(done)} rows already recorded", flush=True)
    t0 = time.time()

    try:
        for obj in LANDSCAPES:
            fitness_fn = OBJECTIVES[obj]
            for mode in MODES:
                for n in NS:
                    hits, censored = [], 0
                    for seed in SEEDS:
                        if (obj, mode, n, seed) in done:
                            continue
                        check_budget()
                        res = PRISM(n=n, fitness_fn=fitness_fn,
                                    seed=seed, mutation=mode).evolve(
                            generations=MAX_GENS, target_fitness=1.0)
                        c = res.hit_generation is None
                        censored += c
                        hit = MAX_GENS if c else res.hit_generation
                        hits.append(hit)
                        append_row({
                            "objective": obj, "mode": mode, "n": n,
                            "seed": seed, "hit_generation": hit,
                            "censored": c,
                            "evaluations": res.evaluations,
                            "operator_weights": json.dumps(
                                res.operator_weights),
                            "status": "censored" if c else "ok",
                        })
                    if hits:
                        print(f"{obj:<10} {mode:<10} n={n:<3} mean "
                              f"{np.mean(hits):8.1f} censored "
                              f"{censored}/{len(hits)}", flush=True)
    except BudgetExceeded:
        print(f"BUDGET REACHED after {time.time() - t0:.0f}s; "
              "rerun to resume", flush=True)
        return

    print(f"STUDY COMPLETE. Wall time {time.time() - t0:.0f}s")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BUDGET_SECONDS = float(sys.argv[1])
    main()
