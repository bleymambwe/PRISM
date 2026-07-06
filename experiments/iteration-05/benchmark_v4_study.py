"""Iteration 5, Experiment G: noise-controlled benchmark v4.

Stages (all resumable; enumeration rows appended per permutation):
1. Determinism check (evaluate one permutation twice, must be equal).
2. Exact enumeration of all 120 permutations per task -> ground-truth
   optimum + landscape statistics.
3. Stage-1 style variance report from the enumerated landscape.
4. PRISM search (10 seeds, portfolio mutation per D8, 60 generations)
   against a fitness cache built from the enumeration -> exact hit
   rate and regret.

Usage: python benchmark_v4_study.py [budget-seconds]
Rerun until "STUDY COMPLETE".

Outputs -> experiments/iteration-05/results/
- v4_landscape.csv   fitness of every permutation, both tasks
- v4_search.csv      per-seed PRISM results (hit, regret, generations)
- v4_summary.txt     landscape stats + hit rates
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
from benchmarks.toy_problems_v4 import PROBLEMS_V4

OUT_DIR = os.path.join(os.path.dirname(__file__), "results")
LAND_CSV = os.path.join(OUT_DIR, "v4_landscape.csv")
SEARCH_CSV = os.path.join(OUT_DIR, "v4_search.csv")
SEEDS = list(range(10))
GENERATIONS = 60
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


def load_landscape():
    done = {}
    if os.path.exists(LAND_CSV):
        for r in csv.DictReader(open(LAND_CSV)):
            done[(r["problem"], r["perm"])] = float(r["fitness"])
    return done


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    land = load_landscape()
    fields = ["problem", "perm", "fitness"]

    # Stage 1: determinism check
    for name, fn in PROBLEMS_V4:
        a, b = fn([0, 1, 2, 3, 4]), fn([0, 1, 2, 3, 4])
        assert a == b, f"{name} not deterministic: {a} vs {b}"
    print("determinism check: OK", flush=True)

    # Stage 2: enumeration (resumable)
    try:
        for name, fn in PROBLEMS_V4:
            for perm in itertools.permutations(range(5)):
                key = (name, json.dumps(list(perm)))
                if key in land:
                    continue
                check_budget()
                fit = fn(list(perm))
                land[key] = fit
                append(LAND_CSV, {"problem": name, "perm": key[1],
                                  "fitness": fit}, fields)
            n_done = sum(1 for k in land if k[0] == name)
            print(f"{name}: enumerated {n_done}/120", flush=True)
    except BudgetExceeded:
        print(f"BUDGET REACHED during enumeration "
              f"({len(land)}/240 rows); rerun to resume", flush=True)
        return

    # Stage 3+4: landscape stats and cached PRISM search
    summary = []
    sfields = ["problem", "seed", "best_fitness", "optimum_fitness",
               "hit_optimum", "regret", "hit_generation"]
    search_done = set()
    if os.path.exists(SEARCH_CSV):
        for r in csv.DictReader(open(SEARCH_CSV)):
            search_done.add((r["problem"], int(r["seed"])))

    for name, _ in PROBLEMS_V4:
        fits = {k[1]: v for k, v in land.items() if k[0] == name}
        vals = np.array(list(fits.values()))
        opt = float(vals.max())
        n_opt = int((vals == opt).sum())
        summary.append(
            f"{name}: optimum {opt:.4f} ({n_opt}/120 permutations), "
            f"min {vals.min():.4f}, mean {vals.mean():.4f}, "
            f"std {vals.std():.4f} (order matters: "
            f"{'YES' if vals.std() > 0.01 else 'NO'})")

        cache = {p: f for p, f in fits.items()}

        def cached_fitness(perm, _c=cache):
            return _c[json.dumps([int(x) for x in perm])]

        hits, regrets = [], []
        for seed in SEEDS:
            if (name, seed) in search_done:
                continue
            res = PRISM(n=5, fitness_fn=cached_fitness, seed=seed,
                        mutation="portfolio").evolve(
                generations=GENERATIONS, target_fitness=opt)
            hit = res.best_fitness >= opt
            regret = opt - res.best_fitness
            hits.append(hit)
            regrets.append(regret)
            append(SEARCH_CSV, {
                "problem": name, "seed": seed,
                "best_fitness": res.best_fitness,
                "optimum_fitness": opt,
                "hit_optimum": hit, "regret": round(regret, 4),
                "hit_generation": res.hit_generation
                if res.hit_generation is not None else -1,
            }, sfields)
        rows = [r for r in csv.DictReader(open(SEARCH_CSV))
                if r["problem"] == name]
        hr = np.mean([r["hit_optimum"] == "True" for r in rows])
        mr = np.mean([float(r["regret"]) for r in rows])
        summary.append(
            f"{name}: PRISM (portfolio, 60 gens, {len(rows)} seeds) "
            f"hit rate {hr:.2f}, mean regret {mr:.4f}")

    with open(os.path.join(OUT_DIR, "v4_summary.txt"), "w") as f:
        f.write("\n".join(summary) + "\n")
    print("\n".join(summary))
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BUDGET_SECONDS = float(sys.argv[1])
    main()
