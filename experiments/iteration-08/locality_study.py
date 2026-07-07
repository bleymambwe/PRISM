"""Iteration 8, Experiment J: landscape locality as the predictor.

Question: does landscape locality — measured before running any search —
predict when PRISM beats random sampling? Iteration 7 showed PRISM >>
random on synthetic landscapes but PRISM ~ random on the n=7 neural
landscape; this study quantifies the difference.

Two standard metrics per (landscape, operator):

1. One-step move autocorrelation rho1: Pearson correlation between
   f(pi) and f(op(pi)) over sampled (pi, move) pairs. High rho1 =
   smooth under that operator's move set.
2. Fitness-distance correlation (FDC, Jones & Forrest 1995):
   correlation between fitness and Cayley distance (minimum swaps =
   n - #cycles) to the nearest global optimum. FDC near -1 = fitness
   guides search toward optima; near 0 = needle in haystack;
   positive = deceptive.

Landscapes (all exact, no new training):
- Neural (cached enumerations): XOR-v4 n=5, Parity-v4 n=5, XOR-v4 n=6,
  Parity-v4 n=7.
- Synthetic (closed-form, computed over all 5040 n=7 permutations):
  hamming, kendall, adjacency, deceptive.

H11: synthetic landscapes show high rho1 (under the matched operator)
and strongly negative FDC; neural landscapes show weaker locality, with
n=7 parity the weakest — matching the observed PRISM-vs-random
outcomes.

Outputs -> experiments/iteration-08/results/locality.csv + .txt
Runtime: ~1-2 min (everything cached or closed-form).
"""

import csv
import itertools
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import MUTATIONS
from benchmarks.synthetic import OBJECTIVES

OUT_DIR = os.path.join(os.path.dirname(__file__), "results")
RNG = np.random.default_rng(42)
N_PAIRS = 4000

CACHES = {
    "XOR-v4 (n=5)": ("experiments/iteration-05/results/v4_landscape.csv",
                     "XOR-v4"),
    "Parity-v4 (n=5)": ("experiments/iteration-05/results/v4_landscape.csv",
                        "Parity-v4"),
    "XOR-v4 (n=6)": ("experiments/iteration-06/results/n6_landscape.csv",
                     None),
    "Parity-v4 (n=7)": ("experiments/iteration-07/results/"
                        "n7_parity_landscape.csv", None),
}
# Observed outcome labels for the verdict table
OBSERVED = {
    "XOR-v4 (n=5)": "PRISM hit rate 1.00 (8/120 optima)",
    "Parity-v4 (n=5)": "hit rate 0.40 (2/120)",
    "XOR-v4 (n=6)": "hit rate 0.90 (33/720)",
    "Parity-v4 (n=7)": "PRISM ~ random (14/5040)",
    "hamming (n=7)": "matched PRISM >> random",
    "kendall (n=7)": "all operators >> random",
    "adjacency (n=7)": "matched PRISM >> random",
    "deceptive (n=7)": "everything fails",
}


def load_neural():
    out = {}
    for name, (path, prob) in CACHES.items():
        land = {}
        for r in csv.DictReader(open(os.path.join(ROOT, path))):
            if prob and r.get("problem") != prob:
                continue
            land[tuple(json.loads(r["perm"]))] = float(r["fitness"])
        out[name] = land
    return out


def synth_landscapes(n=7):
    out = {}
    for obj in ("hamming", "kendall", "adjacency", "deceptive"):
        fn = OBJECTIVES[obj]
        out[f"{obj} (n=7)"] = {p: fn(list(p))
                               for p in itertools.permutations(range(n))}
    return out


def rho1(land, op_name):
    """One-step autocorrelation under an operator's move."""
    keys = list(land.keys())
    op = MUTATIONS[op_name]
    f0, f1 = [], []
    for _ in range(N_PAIRS):
        p = list(keys[RNG.integers(len(keys))])
        q = p.copy()
        op(q, RNG)
        f0.append(land[tuple(p)])
        f1.append(land[tuple(q)])
    return float(np.corrcoef(f0, f1)[0, 1])


def cayley(p, q):
    """Min swaps between permutations = n - number of cycles of p q^-1."""
    n = len(p)
    qinv = [0] * n
    for i, v in enumerate(q):
        qinv[v] = i
    r = [qinv[v] for v in p]
    seen = [False] * n
    cycles = 0
    for i in range(n):
        if not seen[i]:
            cycles += 1
            j = i
            while not seen[j]:
                seen[j] = True
                j = r[j]
    return n - cycles


def fdc(land):
    """Fitness-distance correlation to the nearest global optimum."""
    vals = np.array(list(land.values()))
    opt = vals.max()
    optima = [p for p, v in land.items() if v == opt]
    keys = list(land.keys())
    if len(keys) > 1500:
        idx = RNG.choice(len(keys), 1500, replace=False)
        keys = [keys[i] for i in idx]
    fs, ds = [], []
    for p in keys:
        fs.append(land[p])
        ds.append(min(cayley(list(p), list(o)) for o in optima))
    return float(np.corrcoef(fs, ds)[0, 1])


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    lands = {**load_neural(), **synth_landscapes()}
    rows, lines = [], []
    ops = list(MUTATIONS)
    header = (f"{'landscape':<18} " +
              " ".join(f"rho1({o[:4]})" for o in ops) +
              f" {'FDC':>7}  observed outcome")
    lines.append(header)
    for name, land in lands.items():
        rs = {op: rho1(land, op) for op in ops}
        f = fdc(land)
        rows.append({"landscape": name, **{f"rho1_{o}": round(rs[o], 3)
                                           for o in ops},
                     "fdc": round(f, 3), "observed": OBSERVED[name]})
        lines.append(f"{name:<18} " +
                     " ".join(f"{rs[o]:>10.3f}" for o in ops) +
                     f" {f:>7.3f}  {OBSERVED[name]}")
    with open(os.path.join(OUT_DIR, "locality.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    text = "\n".join(lines)
    open(os.path.join(OUT_DIR, "locality.txt"), "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
