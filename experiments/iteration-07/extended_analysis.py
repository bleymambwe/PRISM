"""Iteration 7: extended analysis against the cached n=7 parity landscape.

All analyses here are FREE (fitness cache from the 5040-permutation
enumeration). Reproduces:

A) Equal-budget exact-hit comparison: probability random-without-
   replacement hits an optimum within b distinct evals vs PRISM's
   observed hit rate at its actual exploration budget.
B) Hyperparameter sensitivity: hit rate and mean distinct evals for
   (pop, p_m) in {(20,.05),(20,.3),(40,.3),(40,.6),(60,.5)}.
C) Best-found-quality curves: mean best fitness at distinct-eval
   budgets {25,50,100,200} for default PRISM vs random.

Outputs -> results/n7_extended_analysis.txt
"""

import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM

RES = os.path.join(os.path.dirname(__file__), "results")
land = {r["perm"]: float(r["fitness"]) for r in
        csv.DictReader(open(os.path.join(RES, "n7_parity_landscape.csv")))}
keys = list(land.keys())
vals = np.array([land[k] for k in keys])
opt = vals.max()
optima = {p for p, v in land.items() if v == opt}
N, m = len(vals), len(optima)
out = []


def run(pop, pm, seed, gens=400):
    state = {"count": 0, "hit": None, "seen": set(), "curve": {}}

    def fit(perm, _s=state):
        k = json.dumps([int(x) for x in perm])
        if k not in _s["seen"]:
            _s["seen"].add(k)
            _s["count"] += 1
            if _s["hit"] is None and k in optima:
                _s["hit"] = _s["count"]
            best = max(land[k], _s["curve"].get(_s["count"] - 1, -1))
            _s["curve"][_s["count"]] = best
        return land[k]

    PRISM(n=7, fitness_fn=fit, seed=seed, mutation="portfolio",
          pop_size=pop, p_m=pm).evolve(generations=gens,
                                       target_fitness=opt)
    return state


# A) equal-budget hit probabilities
for b in (50, 130, 318, 384):
    prob = 1 - np.prod([(N - m - i) / (N - i) for i in range(b)])
    out.append(f"random hit prob within {b} distinct evals: {prob:.2f}")
out.append(f"expected random evals to first optimum: {(N+1)/(m+1):.0f}")

# B) sensitivity
out.append(f"\n{'config':<20} {'hits':>6} {'mean evals(hit)':>16} "
           f"{'mean explored':>14}")
for pop, pm in [(20, .05), (20, .3), (40, .3), (40, .6), (60, .5)]:
    res = [run(pop, pm, s) for s in range(15)]
    hits = [r["hit"] for r in res if r["hit"]]
    out.append(f"pop={pop} p_m={pm:<5} {len(hits):>4}/15 "
               f"{np.mean(hits) if hits else -1:>16.0f} "
               f"{np.mean([r['count'] for r in res]):>14.0f}")

# C) quality curves (default config) vs random
BUDGETS = [25, 50, 100, 200]
pr = {b: [] for b in BUDGETS}
rd = {b: [] for b in BUDGETS}
for s in range(15):
    st = run(20, 0.05, s)
    mx = max(st["curve"])
    for b in BUDGETS:
        pr[b].append(st["curve"][min(b, mx)])
    rng = np.random.default_rng(3000 + s)
    fits = vals[rng.permutation(N)]
    for b in BUDGETS:
        rd[b].append(fits[:b].max())
out.append(f"\n{'budget':>7} {'PRISM best (mean)':>18} "
           f"{'random best (mean)':>19}  optimum={opt:.4f}")
for b in BUDGETS:
    out.append(f"{b:>7} {np.mean(pr[b]):>18.4f} {np.mean(rd[b]):>19.4f}")

text = "\n".join(out)
open(os.path.join(RES, "n7_extended_analysis.txt"), "w").write(text + "\n")
print(text)
