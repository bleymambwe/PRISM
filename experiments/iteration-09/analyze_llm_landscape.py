"""Iteration 9, stages 3-4: analysis of the enumerated LLM landscape.

Free (runs against llm_landscape.csv). Produces:
- D14 pre-flight: rho1 per operator + FDC -> predicted operator and
  whether search should beat random
- Landscape stats: optimum, |optima|, distribution, position effects
  (mean accuracy by position of each module)
- Search comparison: PRISM (portfolio; D12 n>=7 settings scaled for
  n=6: pop 20/40, p_m 0.05/0.5) vs random-without-replacement:
  evals-to-first-optimum (15 seeds) + best-found quality at budgets
- Verdict: did the pre-flight predict the outcome?

Outputs -> results/llm_analysis.txt + llm_position_effects.csv
"""

import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM, MUTATIONS

RES = os.path.join(os.path.dirname(__file__), "results")
RNG = np.random.default_rng(42)
MODULE_NAMES = ["RESTATE", "IDENTIFY", "PLAN", "COMPUTE", "CHECK",
                "ANSWER"]
N = 6

land = {tuple(json.loads(r["perm"])): float(r["fitness"])
        for r in csv.DictReader(open(os.path.join(RES,
                                                  "llm_landscape.csv")))}
keys = list(land.keys())
vals = np.array([land[k] for k in keys])
opt = vals.max()
optima = {k for k, v in land.items() if v == opt}
out = []


def rho1(op_name, n_pairs=4000):
    op = MUTATIONS[op_name]
    f0, f1 = [], []
    for _ in range(n_pairs):
        p = list(keys[RNG.integers(len(keys))])
        q = p.copy()
        op(q, RNG)
        f0.append(land[tuple(p)])
        f1.append(land[tuple(q)])
    return float(np.corrcoef(f0, f1)[0, 1])


def cayley(p, q):
    n = len(p)
    qinv = [0] * n
    for i, v in enumerate(q):
        qinv[v] = i
    r = [qinv[v] for v in p]
    seen = [False] * n
    c = 0
    for i in range(n):
        if not seen[i]:
            c += 1
            j = i
            while not seen[j]:
                seen[j] = True
                j = r[j]
    return n - c


def fdc():
    fs, ds = [], []
    for p in keys:
        fs.append(land[p])
        ds.append(min(cayley(list(p), list(o)) for o in optima))
    return float(np.corrcoef(fs, ds)[0, 1])


def search(pop, pm, seed, gens=400):
    state = {"count": 0, "hit": None, "seen": set(), "curve": {}}

    def fit(perm, _s=state):
        k = tuple(int(x) for x in perm)
        if k not in _s["seen"]:
            _s["seen"].add(k)
            _s["count"] += 1
            if _s["hit"] is None and k in optima:
                _s["hit"] = _s["count"]
            _s["curve"][_s["count"]] = max(
                land[k], _s["curve"].get(_s["count"] - 1, -1))
        return land[k]

    PRISM(n=N, fitness_fn=fit, seed=seed, mutation="portfolio",
          pop_size=pop, p_m=pm).evolve(generations=gens,
                                       target_fitness=opt)
    return state


# --- landscape stats ---
out.append(f"LLM chain landscape (720 orderings, 32 GSM8K questions, "
           f"Gemini 2.5 Flash-Lite):")
out.append(f"  optimum {opt:.4f} ({len(optima)}/720 = "
           f"{len(optima)/7.20:.1f}%), min {vals.min():.4f}, mean "
           f"{vals.mean():.4f}, std {vals.std():.4f}")

# position effects: mean fitness when module m is at position i
pos = np.zeros((N, N))
for k in keys:
    for i, m in enumerate(k):
        pos[m][i] += land[k]
pos /= 120  # each (module, position) appears 5!=120 times
with open(os.path.join(RES, "llm_position_effects.csv"), "w",
          newline="") as f:
    w = csv.writer(f)
    w.writerow(["module"] + [f"pos{i+1}" for i in range(N)])
    for m in range(N):
        w.writerow([MODULE_NAMES[m]] + [round(pos[m][i], 3)
                                        for i in range(N)])
out.append("  position effects (mean acc by module position):")
for m in range(N):
    out.append(f"    {MODULE_NAMES[m]:<9} " +
               " ".join(f"{pos[m][i]:.3f}" for i in range(N)))

# --- D14 pre-flight ---
rs = {op: rho1(op) for op in MUTATIONS}
f = fdc()
best_op = max((o for o in rs if o != "scramble"), key=lambda o: rs[o])
out.append("\nD14 pre-flight:")
out.append("  rho1: " + ", ".join(f"{o}={rs[o]:.3f}" for o in rs))
out.append(f"  FDC: {f:.3f}")
out.append(f"  predicted operator: {best_op}; search should "
           f"{'beat' if f < -0.15 else 'roughly match'} random")

# --- search comparison ---
out.append("\nSearch comparison (15 seeds):")
for pop, pm, label in [(20, 0.05, "default"), (40, 0.5, "D12-scaled")]:
    res = [search(pop, pm, s) for s in range(15)]
    hits = [r["hit"] for r in res if r["hit"]]
    out.append(f"  PRISM {label} (pop={pop}, p_m={pm}): "
               f"{len(hits)}/15 hits, mean evals-to-optimum "
               f"{np.mean(hits) if hits else -1:.0f}, mean explored "
               f"{np.mean([r['count'] for r in res]):.0f}")
rnd_hits = []
for s in range(15):
    order = np.random.default_rng(5000 + s).permutation(len(keys))
    rnd_hits.append(next(i + 1 for i, idx in enumerate(order)
                         if keys[idx] in optima))
out.append(f"  random: 15/15 hits, mean evals-to-optimum "
           f"{np.mean(rnd_hits):.0f} (expected "
           f"{(len(keys)+1)/(len(optima)+1):.0f})")

# quality at budgets
budgets = [15, 30, 60, 120]
out.append(f"\n  best-found quality (mean over 15 seeds):")
out.append(f"  {'budget':>7} {'PRISM default':>14} {'PRISM D12':>10} "
           f"{'random':>8}")
curves = {"default": [search(20, .05, s)["curve"] for s in range(15)],
          "D12": [search(40, .5, s)["curve"] for s in range(15)]}
for b in budgets:
    row = []
    for label in ("default", "D12"):
        cs = curves[label]
        row.append(np.mean([c[min(b, max(c))] for c in cs]))
    rnd = []
    for s in range(15):
        order = np.random.default_rng(6000 + s).permutation(len(keys))
        rnd.append(max(land[keys[i]] for i in order[:b]))
    out.append(f"  {b:>7} {row[0]:>14.4f} {row[1]:>10.4f} "
               f"{np.mean(rnd):>8.4f}")

text = "\n".join(out)
open(os.path.join(RES, "llm_analysis.txt"), "w").write(text + "\n")
print(text)
