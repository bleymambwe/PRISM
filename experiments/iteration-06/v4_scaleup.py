"""Iteration 6, Experiment H: scaling benchmark v4 beyond n=5.

Two protocols, per the Iteration-5 handover:

Stage A — n=6, exact ground truth (still enumerable):
  All 720 orderings of blocks {0..5} on XOR-v4 (k=3 trials,
  deterministic). Then PRISM (portfolio, 80 generations, 10 seeds)
  against the enumeration cache -> exact hit rate + regret.

Stage B — n=7, regret vs baseline (enumeration infeasible in budget):
  XOR objective with k=1 trials (still deterministic; cheaper).
  PRISM (portfolio) vs random search at the same evaluation budget
  (800 distinct-permutation evaluations via shared memo cache),
  4 seeds each. Report best-found and the PRISM-minus-random gap.

Resumable and budgeted: python v4_scaleup.py [budget-seconds]
Rerun until "STUDY COMPLETE".

Outputs -> experiments/iteration-06/results/
"""

import csv
import itertools
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM
from benchmarks.toy_problems_v4 import make_xor_fitness

OUT_DIR = os.path.join(os.path.dirname(__file__), "results")
N6_CSV = os.path.join(OUT_DIR, "n6_landscape.csv")
N6_SEARCH = os.path.join(OUT_DIR, "n6_search.csv")
N7_CSV = os.path.join(OUT_DIR, "n7_search.csv")
BUDGET_SECONDS = None
_START = time.time()


class BudgetExceeded(Exception):
    pass


def check_budget():
    if BUDGET_SECONDS and time.time() - _START > BUDGET_SECONDS:
        raise BudgetExceeded


def append(path, row, fields):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow(row)


def stage_a():
    fit = make_xor_fitness(k_trials=3)
    done = {}
    if os.path.exists(N6_CSV):
        for r in csv.DictReader(open(N6_CSV)):
            done[r["perm"]] = float(r["fitness"])
    total = 720
    for perm in itertools.permutations(range(6)):
        key = json.dumps(list(perm))
        if key in done:
            continue
        check_budget()
        f = fit(list(perm))
        done[key] = f
        append(N6_CSV, {"perm": key, "fitness": f}, ["perm", "fitness"])
    print(f"n=6 enumeration: {len(done)}/{total}", flush=True)
    if len(done) < total:
        return None

    vals = np.array(list(done.values()))
    opt = float(vals.max())
    n_opt = int((vals == opt).sum())
    stats = (f"n=6 XOR-v4: optimum {opt:.4f} ({n_opt}/720), "
             f"min {vals.min():.4f}, mean {vals.mean():.4f}, "
             f"std {vals.std():.4f}")
    print(stats, flush=True)

    cache = dict(done)

    def cached(perm, _c=cache):
        return _c[json.dumps([int(x) for x in perm])]

    sdone = set()
    if os.path.exists(N6_SEARCH):
        for r in csv.DictReader(open(N6_SEARCH)):
            sdone.add(int(r["seed"]))
    for seed in range(10):
        if seed in sdone:
            continue
        res = PRISM(n=6, fitness_fn=cached, seed=seed,
                    mutation="portfolio").evolve(
            generations=80, target_fitness=opt)
        append(N6_SEARCH, {
            "seed": seed, "best_fitness": res.best_fitness,
            "optimum": opt, "hit": res.best_fitness >= opt,
            "regret": round(opt - res.best_fitness, 4),
            "hit_generation": res.hit_generation
            if res.hit_generation is not None else -1,
        }, ["seed", "best_fitness", "optimum", "hit", "regret",
            "hit_generation"])
    rows = list(csv.DictReader(open(N6_SEARCH)))
    hr = np.mean([r["hit"] == "True" for r in rows])
    mr = np.mean([float(r["regret"]) for r in rows])
    line = (f"n=6 PRISM (portfolio, 80 gens, {len(rows)} seeds): "
            f"hit rate {hr:.2f}, mean regret {mr:.4f}")
    print(line, flush=True)
    return [stats, line]


def stage_b():
    base_fit = make_xor_fitness(k_trials=1)
    EVAL_BUDGET = 800
    done = set()
    if os.path.exists(N7_CSV):
        for r in csv.DictReader(open(N7_CSV)):
            done.add((r["method"], int(r["seed"])))
    fields = ["method", "seed", "best_fitness", "distinct_evals"]

    for seed in range(4):
        for method in ("prism", "random"):
            if (method, seed) in done:
                continue
            check_budget()
            cache = {}

            def memo_fit(perm, _c=cache):
                key = tuple(int(x) for x in perm)
                if key not in _c:
                    if len(_c) >= EVAL_BUDGET:
                        # budget exhausted: return worst-case, do not
                        # count new evaluations
                        return 0.0
                    _c[key] = base_fit(list(key))
                return _c[key]

            if method == "prism":
                res = PRISM(n=7, fitness_fn=memo_fit, seed=seed,
                            mutation="portfolio").evolve(
                    generations=200)
                best = res.best_fitness
            else:
                rng = np.random.default_rng(1000 + seed)
                best = -1.0
                while len(cache) < EVAL_BUDGET:
                    best = max(best, memo_fit(list(rng.permutation(7))))
            append(N7_CSV, {"method": method, "seed": seed,
                            "best_fitness": round(best, 4),
                            "distinct_evals": len(cache)}, fields)
            print(f"n=7 {method} seed={seed}: best {best:.4f} "
                  f"({len(cache)} distinct evals)", flush=True)

    rows = list(csv.DictReader(open(N7_CSV)))
    p = [float(r["best_fitness"]) for r in rows if r["method"] == "prism"]
    q = [float(r["best_fitness"]) for r in rows if r["method"] == "random"]
    line = (f"n=7 XOR (k=1, budget {EVAL_BUDGET} evals): PRISM mean best "
            f"{np.mean(p):.4f} vs random {np.mean(q):.4f} "
            f"(gap {np.mean(p) - np.mean(q):+.4f}, {len(p)} seeds)")
    print(line, flush=True)
    return [line]


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    summary = []
    try:
        a = stage_a()
        if a is None:
            print("BUDGET REACHED (stage A incomplete); rerun to resume")
            return
        summary += a
        b = stage_b()
        summary += b
    except BudgetExceeded:
        print(f"BUDGET REACHED after {time.time() - _START:.0f}s; "
              "rerun to resume", flush=True)
        return
    with open(os.path.join(OUT_DIR, "scaleup_summary.txt"), "w") as f:
        f.write("\n".join(summary) + "\n")
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BUDGET_SECONDS = float(sys.argv[1])
    main()
