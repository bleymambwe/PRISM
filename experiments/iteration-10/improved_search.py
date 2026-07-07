"""Iteration 10, Experiment L: literature-driven algorithm improvements.

Three candidate improvements, each grounded in a paper from
research-opportunity-mapping-2026-07-06/papers and mapped to a
*measured* PRISM weakness:

1. AGING EVOLUTION (Real et al. 2019, "Regularized Evolution",
   paper 05): kill the OLDEST genome instead of the worst; no
   permanent elite. Targets Experiment I's diagnosis — premature
   convergence at n>=7 (default PRISM explored only ~103 distinct
   orderings). Aging forces turnover without hyperparameter surgery.
2. SURROGATE-GUIDED SEARCH (White et al., BANANAS, paper 14): fit a
   cheap predictor on all evaluated orderings; propose candidates by
   mutating the best known; evaluate only the top-predicted. Our
   encoding: flattened one-hot (module x position) matrix + ridge
   regression — motivated by Experiment K's strong position effects.
   Targets the n=7 result that local moves alone cannot beat random.
3. (Noted, not tested here) ZERO-COST / MULTI-FIDELITY GATES
   (Abdelfattah et al., paper 15): k=1 screening before k=3
   confirmation for expensive neural evaluations — relevant at GPU
   scale, no-op on cached landscapes.

Protocol: methods {prism-portfolio (baseline), aging, surrogate,
random} x landscapes {n=6 XOR, n=7 parity, LLM chain} x 15 seeds,
all against cached enumerations (zero new evaluation cost).
Metrics: distinct evaluations to first exact optimum (capped at 500)
and best-found fitness at budgets {25, 50, 100, 200}.

Outputs -> experiments/iteration-10/results/
"""

import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM, MUTATIONS

OUT = os.path.join(os.path.dirname(__file__), "results")
CAP = 500
BUDGETS = [25, 50, 100, 200]
SEEDS = list(range(15))

LANDSCAPES = {
    "xor_n6": ("experiments/iteration-06/results/n6_landscape.csv",
               None, "perm", "fitness"),
    "parity_n7": ("experiments/iteration-07/results/"
                  "n7_parity_landscape.csv", None, "perm", "fitness"),
    "llm_chain_n6": ("experiments/iteration-09/results/"
                     "llm_landscape.csv", None, "perm", "fitness"),
}


def load(name):
    path, prob, pk, fk = LANDSCAPES[name]
    land = {}
    for r in csv.DictReader(open(os.path.join(ROOT, path))):
        if prob and r.get("problem") != prob:
            continue
        land[tuple(json.loads(r[pk]))] = float(r[fk])
    return land


class Tracker:
    """Counts distinct evaluations; records first-optimum hit and
    best-at-budget curve."""

    def __init__(self, land, optima):
        self.land = land
        self.optima = optima
        self.seen = set()
        self.count = 0
        self.hit = None
        self.curve = {}
        self.best = -np.inf

    def __call__(self, perm):
        k = tuple(int(x) for x in perm)
        v = self.land[k]
        if k not in self.seen and self.count < CAP:
            self.seen.add(k)
            self.count += 1
            if self.hit is None and k in self.optima:
                self.hit = self.count
            self.best = max(self.best, v)
            self.curve[self.count] = self.best
        return v

    def done(self):
        return self.count >= CAP or self.hit is not None


def run_prism(tr, n, seed):
    PRISM(n=n, fitness_fn=tr, seed=seed, mutation="portfolio").evolve(
        generations=2000,
        target_fitness=max(tr.land.values()))


def run_aging(tr, n, seed, pop_size=20, sample=10):
    """Regularized evolution: tournament on a sample, mutate the best,
    append child, remove the OLDEST (no permanent elite)."""
    rng = np.random.default_rng(seed)
    ops = list(MUTATIONS.values())
    pop = []
    for _ in range(pop_size):
        p = [int(x) for x in rng.permutation(n)]
        pop.append((p, tr(p)))
        if tr.done():
            return
    while not tr.done():
        idx = rng.choice(len(pop), size=sample, replace=False)
        parent = max((pop[i] for i in idx), key=lambda t: t[1])[0]
        child = parent.copy()
        rng.choice(ops)(child, rng)
        pop.append((child, tr(child)))
        pop.pop(0)  # oldest dies


def run_surrogate(tr, n, seed, init=10, pool=200):
    """BANANAS-style: one-hot positional encoding + ridge regression;
    propose mutations of the best known; evaluate the top-predicted
    unevaluated candidate."""
    rng = np.random.default_rng(seed)
    ops = list(MUTATIONS.values())

    def enc(p):
        m = np.zeros((n, n))
        for pos, mod in enumerate(p):
            m[mod][pos] = 1.0
        return m.ravel()

    X, y, tried = [], [], set()
    for _ in range(init):
        p = [int(x) for x in rng.permutation(n)]
        v = tr(p)
        X.append(enc(p)); y.append(v); tried.add(tuple(p))
        if tr.done():
            return
    while not tr.done():
        A = np.array(X); b = np.array(y)
        lam = 1.0
        w = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]),
                            A.T @ b)
        # candidate pool: mutations of the top-5 known + randoms
        order = np.argsort(b)[::-1][:5]
        seeds_ = [list(np.array(X[i].reshape(n, n).argmax(axis=1)))
                  for i in order]
        # decode: X rows are (module,position); argmax per module gives
        # position; rebuild perm as position->module
        cands = []
        for s in seeds_:
            posmap = s  # module -> position
            perm = [0] * n
            for mod, pos in enumerate(posmap):
                perm[pos] = mod
            for _ in range(pool // 10):
                c = perm.copy()
                rng.choice(ops)(c, rng)
                if tuple(c) not in tried:
                    cands.append(c)
        for _ in range(pool // 4):
            c = [int(x) for x in rng.permutation(n)]
            if tuple(c) not in tried:
                cands.append(c)
        if not cands:
            c = [int(x) for x in rng.permutation(n)]
            cands = [c]
        preds = [enc(c) @ w for c in cands]
        best_c = cands[int(np.argmax(preds))]
        v = tr(best_c)
        X.append(enc(best_c)); y.append(v); tried.add(tuple(best_c))


def run_random(tr, n, seed):
    rng = np.random.default_rng(seed)
    keys = list(tr.land.keys())
    order = rng.permutation(len(keys))
    for i in order:
        tr(list(keys[i]))
        if tr.done():
            return


METHODS = {"prism": run_prism, "aging": run_aging,
           "surrogate": run_surrogate, "random": run_random}


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for lname in LANDSCAPES:
        land = load(lname)
        n = len(next(iter(land)))
        opt = max(land.values())
        optima = {k for k, v in land.items() if v == opt}
        print(f"{lname}: {len(land)} orderings, optimum {opt:.4f} "
              f"({len(optima)})", flush=True)
        for mname, fn in METHODS.items():
            hits, curves = [], []
            for seed in SEEDS:
                tr = Tracker(land, optima)
                fn(tr, n, seed)
                # extend curve to CAP
                mx = max(tr.curve) if tr.curve else 0
                hits.append(tr.hit if tr.hit else -1)
                curves.append({b: tr.curve[min(b, mx)] for b in BUDGETS})
                rows.append({"landscape": lname, "method": mname,
                             "seed": seed,
                             "evals_to_optimum": tr.hit or -1,
                             **{f"best@{b}": round(curves[-1][b], 4)
                                for b in BUDGETS}})
            ok = [h for h in hits if h > 0]
            print(f"  {mname:<10} hits {len(ok):>2}/15  "
                  f"mean-evals {np.mean(ok) if ok else -1:6.1f}  "
                  f"best@50 {np.mean([c[50] for c in curves]):.4f}  "
                  f"best@200 {np.mean([c[200] for c in curves]):.4f}",
                  flush=True)
    with open(os.path.join(OUT, "improved_search.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    main()
