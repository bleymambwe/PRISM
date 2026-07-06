"""Iteration 3, Experiments C & D: operator-landscape matching + stress.

C: mutation operators {swap, insert, inversion, scramble} x typed
   landscapes {hamming (A), kendall (P), adjacency (R)} x
   n in {6, 8, 10, 12, 14, 16}, 15 seeds. Hypothesis H1 (from other.md /
   Cicirello 2022): matched operators (swap-A, insert-P, inversion-R)
   have the lowest hitting times on their landscape type.

D: deceptive landscape (optimum fitness 2.0), operators {swap,
   inversion}, n in {6, 8, 10}, 15 seeds. Hypothesis H2: heavy censoring
   / near-random-search behavior.

Protocol v2 (first run was killed mid-way; see iteration note):
- MAX_GENS lowered 20000 -> 10000. Successful operators hit in <1000
  generations, so ranking is unaffected; censored-at-cap is recorded as
  a qualitative failure either way.
- Rows are appended to the CSV immediately (kill-safe) with a status
  column: ok | censored | skipped.
- Early abort: if >= 14/15 seeds censor at size n for an (objective,
  operator) pair, larger sizes for that pair are recorded as
  status=skipped (treated as censored in analysis) instead of burning
  15 x MAX_GENS generations to confirm the same failure.
- Resumable: already-recorded (objective, operator, n, seed) rows are
  skipped on rerun, so the study survives repeated interruption.

Baseline for comparison: Iteration-2 swap results
(prism-research/outputs/scaling_results.csv, git tag iteration-02).

Outputs -> experiments/iteration-03/results/operator_study_results.csv
"""

import csv
import os
import sys
import time

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM, MUTATIONS
from benchmarks.synthetic import OBJECTIVES

OUT_DIR = os.path.join(os.path.dirname(__file__), "results")
CSV_PATH = os.path.join(OUT_DIR, "operator_study_results.csv")
FIELDS = ["objective", "operator", "n", "seed", "hit_generation",
          "censored", "status"]
SEEDS = list(range(15))
MAX_GENS = 10000
ABORT_THRESHOLD = 14  # censored seeds at one size that abort larger sizes
BUDGET_SECONDS = None  # set via argv[1]; exit cleanly when exceeded
_START = time.time()


class BudgetExceeded(Exception):
    pass


def check_budget():
    if BUDGET_SECONDS and time.time() - _START > BUDGET_SECONDS:
        raise BudgetExceeded


def load_done():
    """Rows already recorded, keyed for resume."""
    done = {}
    if os.path.exists(CSV_PATH):
        for r in csv.DictReader(open(CSV_PATH)):
            key = (r["objective"], r["operator"], int(r["n"]),
                   int(r["seed"]))
            done[key] = r
    return done


def append_row(row):
    new_file = not os.path.exists(CSV_PATH)
    with open(CSV_PATH, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new_file:
            w.writeheader()
        w.writerow(row)


def run_block(objective, ns, operators, target, done):
    fitness_fn = OBJECTIVES[objective]
    for op in operators:
        aborted = False
        for n in ns:
            if aborted:
                for seed in SEEDS:
                    if (objective, op, n, seed) in done:
                        continue
                    append_row({"objective": objective, "operator": op,
                                "n": n, "seed": seed,
                                "hit_generation": MAX_GENS,
                                "censored": True, "status": "skipped"})
                print(f"{objective:<10} {op:<10} n={n:<3} skipped "
                      f"(fully censored at smaller n)", flush=True)
                continue
            hits, censored = [], 0
            for seed in SEEDS:
                key = (objective, op, n, seed)
                if key in done:
                    r = done[key]
                    c = r["censored"] == "True"
                    censored += c
                    hits.append(int(r["hit_generation"]))
                    continue
                check_budget()
                prism = PRISM(n=n, fitness_fn=fitness_fn, seed=seed,
                              mutation=op)
                res = prism.evolve(generations=MAX_GENS,
                                   target_fitness=target)
                c = res.hit_generation is None
                censored += c
                hit = MAX_GENS if c else res.hit_generation
                hits.append(hit)
                append_row({"objective": objective, "operator": op,
                            "n": n, "seed": seed, "hit_generation": hit,
                            "censored": c,
                            "status": "censored" if c else "ok"})
            print(f"{objective:<10} {op:<10} n={n:<3} mean "
                  f"{np.mean(hits):8.1f} median {np.median(hits):8.1f} "
                  f"censored {censored}/{len(SEEDS)}", flush=True)
            if censored >= ABORT_THRESHOLD:
                aborted = True


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    done = load_done()
    if done:
        print(f"Resuming: {len(done)} rows already recorded", flush=True)
    t0 = time.time()

    try:
        print("=== Experiment C: operator x landscape ===", flush=True)
        for objective in ("hamming", "kendall", "adjacency"):
            run_block(objective, [6, 8, 10, 12, 14, 16],
                      list(MUTATIONS), target=1.0, done=done)

        print("=== Experiment D: deceptive landscape ===", flush=True)
        run_block("deceptive", [6, 8, 10], ["swap", "inversion"],
                  target=2.0, done=done)
    except BudgetExceeded:
        print(f"BUDGET REACHED after {time.time() - t0:.0f}s; "
              "rerun to resume", flush=True)
        return

    print(f"STUDY COMPLETE. Wall time {time.time() - t0:.0f}s")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BUDGET_SECONDS = float(sys.argv[1])
    main()
