"""Stage 2 (cheap): compare ablation-ORDER search methods on the stage-1 subset table.

fitness(perm) = sum_t [loss(prefix_t) - loss(empty)]  (area under the cumulative-ablation
damage curve; higher = the order reaches damage faster). Exact optimum by DP over subsets.

Methods: identity, greedy (single-feature damage sort), random best-of-B, PRISM, Nevergrad NGOpt.
Budgets in BUDGETS, seeds 0..N_SEEDS-1. Output results/search_results.csv (resumable by key).

Usage: python search_orders.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "src"))
from prism_search import PRISM  # noqa: E402
from prism_search.integrations import nevergrad as ng  # noqa: E402

K, BUDGETS, N_SEEDS = 10, (50, 200, 1000), 20
RES = HERE / "results"


def load():
    L = np.full(2**K, np.nan)
    with (RES / "subset_losses.csv").open() as f:
        for r in csv.DictReader(f):
            L[int(r["mask"])] = float(r["loss"])
    if np.isnan(L).any():
        raise SystemExit("stage 1 incomplete: run subset_eval.py until STAGE 1 COMPLETE")
    return L - L[0]


def make_fit(D):
    def fit(perm):
        m, s = 0, 0.0
        for i in perm:
            m |= 1 << int(i)
            s += D[m]
        return s

    return fit


def exact_opt(D):
    best = np.full(2**K, -np.inf)
    best[0] = 0.0
    for m in range(1, 2**K):
        best[m] = D[m] + max(best[m ^ (1 << i)] for i in range(K) if m >> i & 1)
    return best[-1]


def main():
    D = load()
    fit, opt = make_fit(D), exact_opt(D)
    greedy = list(np.argsort(-np.array([D[1 << i] for i in range(K)])))
    out = RES / "search_results.csv"
    done = set()
    if out.exists():
        with out.open() as f:
            done = {(r["method"], r["budget"], r["seed"]) for r in csv.DictReader(f)}
    new = not out.exists()
    with out.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["method", "budget", "seed", "fitness", "gap_to_opt", "opt"])

        def emit(method, b, s, thunk):
            if (method, str(b), str(s)) in done:
                return
            val = thunk()
            w.writerow([method, b, s, val, (opt - val) / abs(opt), opt])
            f.flush()

        emit("identity", 0, 0, lambda: fit(list(range(K))))
        emit("greedy_single", 0, 0, lambda: fit(greedy))
        for b in BUDGETS:
            for s in range(N_SEEDS):
                rng = np.random.default_rng(s)
                emit("random", b, s, lambda: max(fit(rng.permutation(K)) for _ in range(b)))
                emit("prism", b, s, lambda: PRISM(K, fit, pop_size=20, seed=s).search(b).best_fitness)
                emit("nevergrad_NGOpt", b, s, lambda: ng.minimize(K, fit, budget=b, seed=s).best_fitness)
    print(f"optimum={opt:.5f}; wrote {out}")


if __name__ == "__main__":
    main()
