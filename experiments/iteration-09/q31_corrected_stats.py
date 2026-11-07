"""Recompute the manuscript's GSM8K-landscape statistics after the Q31 correction.

Runs the Iteration-14 40-seed replay (same methods, same seeds, same Tracker)
and exact Ulam/Cayley FDC on both the original landscape and
results/llm_landscape_q31corrected.csv (written by q31_requery.py), so each
corrected number sits next to a reproduction of the published one.

Needs the pre-port `prism-research/` tree on the path (PYTHONPATH), as the
Iteration-12/14 scripts do.

Output -> results/q31_corrected_stats.txt
"""

import bisect
import csv
import importlib.util
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
RES = os.path.join(HERE, "results")

spec = importlib.util.spec_from_file_location(
    "l12", os.path.join(ROOT, "experiments", "iteration-12",
                        "hybrid_surrogate.py"))
L12 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L12)

SEEDS = 40
RNG = np.random.default_rng(14)


def boot_ci(vals, B=4000):
    vals = np.asarray(vals, dtype=float)
    idx = RNG.integers(0, len(vals), (B, len(vals)))
    s = vals[idx].mean(axis=1)
    return float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


def ulam(p, q):
    pos = {v: i for i, v in enumerate(q)}
    tails = []
    for x in (pos[v] for v in p):
        i = bisect.bisect_left(tails, x)
        tails[i:i + 1] = [x]
    return len(p) - len(tails)


def cayley(p, q):
    pos = {v: i for i, v in enumerate(q)}
    a = [pos[v] for v in p]
    seen, cycles = [False] * len(p), 0
    for i in range(len(p)):
        if not seen[i]:
            cycles += 1
            j = i
            while not seen[j]:
                seen[j] = True
                j = a[j]
    return len(p) - cycles


def load(name):
    return {tuple(json.loads(r["perm"])): float(r["fitness"])
            for r in csv.DictReader(open(os.path.join(RES, name)))}


lines = []
for label, name in [("original", "llm_landscape.csv"),
                    ("q31-corrected", "llm_landscape_q31corrected.csv")]:
    land = load(name)
    vals = np.array(list(land.values()))
    opt = vals.max()
    optima = {k for k, v in land.items() if v == opt}
    lines.append(f"== {label}: min {vals.min():.4f} max {opt:.4f} "
                 f"mean {vals.mean():.4f} std {vals.std():.4f} "
                 f"optima {len(optima)}/{len(land)} "
                 f"({len(optima) / len(land):.1%})")
    for dname, d in (("ulam", ulam), ("cayley", cayley)):
        dist = np.array([min(d(k, o) for o in optima) for k in land])
        lines.append(f"  FDC {dname}: "
                     f"{np.corrcoef(vals, dist)[0, 1]:.3f}")
    for mname in ("elitist", "random"):
        evals = []
        for seed in range(SEEDS):
            tr = L12.L10.Tracker(land, optima)
            L12.METHODS[mname](tr, 6, seed)
            if tr.hit:
                evals.append(tr.hit)
        lo, hi = boot_ci(evals)
        lines.append(f"  {mname:<8} hits {len(evals)}/{SEEDS} "
                     f"evals-to-optimum {np.mean(evals):.1f} "
                     f"[{lo:.0f},{hi:.0f}]")

text = "\n".join(lines)
print(text)
open(os.path.join(RES, "q31_corrected_stats.txt"), "w").write(text + "\n")
