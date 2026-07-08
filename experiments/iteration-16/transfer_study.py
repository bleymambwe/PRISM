"""Iteration 16, Experiment O: does ordering knowledge TRANSFER?

Three transfer questions, all answerable free from committed data:

O1. CROSS-TASK (same components, different task): correlate the
    enumerated XOR-v4 and Parity-v4 landscapes over the same 120
    orderings at n=5. High correlation would mean orderings learned on
    one task warm-start another.

O2. CROSS-SIZE (same task family, more components): do the n=6 LLM
    position effects predict n=8 ordering fitness? Score every
    RANDOMLY-SAMPLED n=8 ordering (the reproducible gate+pre-flight
    orderings from Experiment M — search-visited orderings are
    excluded to avoid selection bias) by summing the n=6
    position-effect table over the six shared modules at their nearest
    relative positions; Spearman-correlate with actual n=8 fitness.

O3. WARM-START VALUE: if O2 correlates, quantify the head start — mean
    fitness of the top-10% n=8 orderings under the n=6-derived score
    vs the random mean.

Outputs -> experiments/iteration-16/results/transfer.txt
"""

import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)
lines = []


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


# ---------------- O1: cross-task, n=5 ----------------
xor5, par5 = {}, {}
for r in csv.DictReader(open(os.path.join(
        ROOT, "experiments/iteration-05/results/v4_landscape.csv"))):
    key = tuple(json.loads(r["perm"]))
    if r["problem"] == "XOR-v4":
        xor5[key] = float(r["fitness"])
    elif r["problem"] == "Parity-v4":
        par5[key] = float(r["fitness"])
keys = sorted(xor5)
a = np.array([xor5[k] for k in keys])
b = np.array([par5[k] for k in keys])
pear = float(np.corrcoef(a, b)[0, 1])
spear = spearman(a, b)
top_a = set(np.argsort(a)[-12:])
top_b = set(np.argsort(b)[-12:])
overlap = len(top_a & top_b) / 12
lines.append("O1 cross-task transfer (XOR-v4 vs Parity-v4, 120 shared "
             "orderings, n=5):")
lines.append(f"  Pearson r = {pear:.3f} | Spearman rho = {spear:.3f} | "
             f"top-10% overlap = {overlap:.2f} (chance ~0.10)")

# ---------------- O2: cross-size LLM transfer ----------------
# n=6 position effects (module x position mean fitness)
land6 = {tuple(json.loads(r["perm"])): float(r["fitness"])
         for r in csv.DictReader(open(os.path.join(
             ROOT, "experiments/iteration-09/results/llm_landscape.csv")))}
pos6 = np.zeros((6, 6))
for k, v in land6.items():
    for i, m in enumerate(k):
        pos6[m][i] += v
pos6 /= 120  # each (module, position) appears 5! times

# n=8 fitness for the REPRODUCIBLE random sample (gate 30 + pre-flight
# 100 base + 100 neighbors, regenerated exactly as Experiment M did)
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import MUTATIONS
rng = np.random.default_rng(11)
gate = [[int(x) for x in rng.permutation(8)] for _ in range(30)]
base = [[int(x) for x in rng.permutation(8)] for _ in range(100)]
ops = list(MUTATIONS)
neigh = []
for i, bp in enumerate(base):
    op = ops[i % 4]
    nb = bp.copy()
    MUTATIONS[op](nb, rng)
    neigh.append(nb)
sample = {tuple(p) for p in gate + base + neigh}

cache = {}
for r in csv.reader(open(os.path.join(
        ROOT, "experiments/iteration-11/results/answer_cache.csv"))):
    if r and r[0] != "perm":
        cache[(tuple(json.loads(r[0])), int(r[1]))] = int(r[2])
fit8 = {}
for p in sample:
    vals = [cache.get((p, q)) for q in range(20)]
    if all(v is not None for v in vals):
        fit8[p] = sum(vals) / 20

# n=6-derived score for an n=8 ordering: shared modules 0..5 map to the
# same indices in Experiment M's module list (RESTATE, IDENTIFY at 0,1;
# PLAN=3, COMPUTE=5, CHECK=6, ANSWER=7 in M's list map to n=6 modules
# 2,3,4,5 respectively; ESTIMATE=2, SIMPLIFY=4 are new).
M8_TO_M6 = {0: 0, 1: 1, 3: 2, 5: 3, 6: 4, 7: 5}  # n8 module -> n6 module
scores, actuals = [], []
for p, f in fit8.items():
    sc = 0.0
    for pos, mod in enumerate(p):
        if mod in M8_TO_M6:
            rel = pos / 7  # relative position 0..1
            j = min(5, int(round(rel * 5)))  # nearest n=6 position
            sc += pos6[M8_TO_M6[mod]][j]
    scores.append(sc)
    actuals.append(f)
scores = np.array(scores)
actuals = np.array(actuals)
rho = spearman(scores, actuals)
r_p = float(np.corrcoef(scores, actuals)[0, 1])
lines.append(f"\nO2 cross-size transfer (LLM n=6 position effects -> "
             f"n=8 fitness, {len(fit8)} unbiased random orderings):")
lines.append(f"  Spearman rho = {rho:.3f} | Pearson r = {r_p:.3f}")

# ---------------- O3: warm-start value ----------------
k = max(1, len(scores) // 10)
top_idx = np.argsort(scores)[-k:]
lines.append(f"\nO3 warm-start value (top-10% by n=6-derived score, "
             f"k={k}):")
lines.append(f"  mean n=8 accuracy of score-selected orderings: "
             f"{actuals[top_idx].mean():.3f}")
lines.append(f"  mean n=8 accuracy of all random orderings:      "
             f"{actuals.mean():.3f}")
lines.append(f"  best possible in sample:                        "
             f"{actuals.max():.3f}")

# ---------------- D18 CIs (bootstrap over the random sample) ----------------
rng2 = np.random.default_rng(99)
B = 4000
rhos, tops = [], []
nS = len(scores)
for _ in range(B):
    idx = rng2.integers(0, nS, nS)
    s2, a2 = scores[idx], actuals[idx]
    rhos.append(spearman(s2, a2))
    tops.append(a2[np.argsort(s2)[-k:]].mean())
lines.append(f"\nD18 CIs (4000 bootstrap resamples):")
lines.append(f"  O2 Spearman rho 95% CI: [{np.percentile(rhos,2.5):.3f}, "
             f"{np.percentile(rhos,97.5):.3f}]")
lines.append(f"  O3 warm-start top-10% mean 95% CI: "
             f"[{np.percentile(tops,2.5):.3f}, "
             f"{np.percentile(tops,97.5):.3f}] vs random mean "
             f"{actuals.mean():.3f}")

text = "\n".join(lines)
open(os.path.join(OUT, "transfer.txt"), "w").write(text + "\n")
print(text)
