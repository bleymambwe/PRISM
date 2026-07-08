"""Iteration 12, Experiment N: hybrid replacement + precedence surrogate.

Two queued follow-ups from Iterations 10-11, tested free on cached /
closed-form landscapes:

1. HYBRID (elitist + stagnation-triggered restart): elitist PRISM, but
   if the best-ever fitness has not improved for STAG generations, the
   population (except one elite) is re-randomized. Hypothesis H17: the
   hybrid matches elitist speed on structured landscapes AND matches
   random/aging robustness on weak-locality ones — dominating both
   D15 regimes.
2. PRECEDENCE-PAIR SURROGATE: BANANAS-style ridge over binary
   "module i before module j" features (n(n-1) dims) — the encoding
   matched to precedence structure, where the positional encoding of
   Experiment L was inert on parity. Hypothesis H18: it beats the
   positional surrogate on kendall (pure precedence) and possibly
   parity.

Methods: elitist / aging / hybrid / surrogate-pos / surrogate-prec /
random x landscapes: xor_n6, parity_n7, llm_chain_n6, kendall_n7
(closed form) x 15 seeds (40 on parity for the hybrid verdict).
Metrics: hits within 500 distinct evals; mean best@200.

Outputs -> experiments/iteration-12/results/
"""

import csv
import importlib.util
import itertools
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM, MUTATIONS

spec = importlib.util.spec_from_file_location(
    "imp", os.path.join(ROOT, "experiments", "iteration-10",
                        "improved_search.py"))
L10 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L10)

OUT = os.path.join(os.path.dirname(__file__), "results")
CAP = 500
SEEDS15 = list(range(15))


def load_all():
    lands = {k: L10.load(k) for k in
             ("xor_n6", "parity_n7", "llm_chain_n6")}
    from benchmarks.synthetic import kendall_fitness
    lands["kendall_n7"] = {p: kendall_fitness(list(p))
                           for p in itertools.permutations(range(7))}
    return lands


def run_hybrid(tr, n, seed, pop_size=20, stag=25):
    """Elitist PRISM with stagnation-triggered population restarts."""
    rng = np.random.default_rng(seed)
    ops = list(MUTATIONS.values())
    pop = [[int(x) for x in rng.permutation(n)] for _ in range(pop_size)]
    best_p, best_f = None, -np.inf
    since = 0
    while not tr.done():
        fits = [tr(p) for p in pop]
        if tr.done():
            return
        i = int(np.argmax(fits))
        if fits[i] > best_f:
            best_f, best_p = fits[i], pop[i].copy()
            since = 0
        else:
            since += 1
        if since >= stag:  # restart around the elite
            pop = [best_p.copy()] + [[int(x) for x in rng.permutation(n)]
                                     for _ in range(pop_size - 1)]
            since = 0
            continue
        new = [pop[i].copy()]
        while len(new) < pop_size:
            t = rng.choice(pop_size, 3, replace=False)
            parent = pop[t[int(np.argmax([fits[j] for j in t]))]].copy()
            if rng.random() < 0.5:
                rng.choice(ops)(parent, rng)
            new.append(parent)
        pop = new


def make_surrogate(enc_fn):
    def run(tr, n, seed, init=10, pool=200):
        rng = np.random.default_rng(seed)
        ops = list(MUTATIONS.values())
        X, y, tried, perms = [], [], set(), []
        for _ in range(init):
            p = [int(x) for x in rng.permutation(n)]
            v = tr(p)
            X.append(enc_fn(p, n)); y.append(v)
            tried.add(tuple(p)); perms.append(p)
            if tr.done():
                return
        while not tr.done():
            A = np.array(X); b = np.array(y)
            w = np.linalg.solve(A.T @ A + np.eye(A.shape[1]), A.T @ b)
            order = np.argsort(b)[::-1][:5]
            cands = []
            for oi in order:
                base = perms[oi]
                for _ in range(pool // 10):
                    c = base.copy()
                    rng.choice(ops)(c, rng)
                    if tuple(c) not in tried:
                        cands.append(c)
            for _ in range(pool // 4):
                c = [int(x) for x in rng.permutation(n)]
                if tuple(c) not in tried:
                    cands.append(c)
            if not cands:
                cands = [[int(x) for x in rng.permutation(n)]]
            preds = [enc_fn(c, n) @ w for c in cands]
            bc = cands[int(np.argmax(preds))]
            v = tr(bc)
            X.append(enc_fn(bc, n)); y.append(v)
            tried.add(tuple(bc)); perms.append(bc)
    return run


def enc_pos(p, n):
    m = np.zeros((n, n))
    for pos, mod in enumerate(p):
        m[mod][pos] = 1.0
    return m.ravel()


def enc_prec(p, n):
    """Binary precedence features: 1 if module i appears before j."""
    pos = np.empty(n, dtype=int)
    for k, mod in enumerate(p):
        pos[mod] = k
    f = np.zeros(n * n)
    for i in range(n):
        for j in range(n):
            if i != j and pos[i] < pos[j]:
                f[i * n + j] = 1.0
    return f


METHODS = {
    "elitist": L10.run_prism,
    "aging": L10.run_aging,
    "hybrid": run_hybrid,
    "surr-pos": make_surrogate(enc_pos),
    "surr-prec": make_surrogate(enc_prec),
    "random": L10.run_random,
}


def main():
    os.makedirs(OUT, exist_ok=True)
    lands = load_all()
    rows = []
    for lname, land in lands.items():
        n = len(next(iter(land)))
        opt = max(land.values())
        optima = {k for k, v in land.items() if v == opt}
        seeds = range(40) if lname == "parity_n7" else SEEDS15
        print(f"{lname}: opt {opt:.4f} ({len(optima)}/{len(land)})",
              flush=True)
        for mname, fn in METHODS.items():
            hits, b200 = [], []
            for seed in seeds:
                tr = L10.Tracker(land, optima)
                fn(tr, n, seed)
                if tr.hit:
                    hits.append(tr.hit)
                mx = max(tr.curve) if tr.curve else 1
                b200.append(tr.curve.get(min(200, mx), -1))
                rows.append({"landscape": lname, "method": mname,
                             "seed": seed,
                             "evals_to_optimum": tr.hit or -1,
                             "best@200": round(b200[-1], 4)})
            print(f"  {mname:<10} hits {len(hits):>2}/{len(list(seeds))} "
                  f" mean-evals(hit) {np.mean(hits) if hits else -1:6.1f}"
                  f"  best@200 {np.mean(b200):.4f}", flush=True)
    with open(os.path.join(OUT, "hybrid_surrogate.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    main()
