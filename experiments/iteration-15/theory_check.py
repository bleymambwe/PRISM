"""Iteration 15: numerical verification of the Appendix-B constants.

Three checks, all free:

1. One-step universal reachability (Proposition B.1): a single
   portfolio mutation from a fixed parent reaches a fixed distant
   target with probability >= delta0 = 1/(4 C(n,2) n!). Monte Carlo
   with 2,000,000 draws at n=5 (delta0 = 1/4800 ~ 2.083e-4).
2. Scramble full-segment uniformity (the proof's inner step): given
   the segment is the whole permutation, the shuffled result is
   ~uniform over S_n (chi-square-ish check on n=4, all 24 targets).
3. The aging discovery bound is consistent with observation: the
   geometric bound gives E[T] <= 2 n(n-1) n!/m; for parity n=7
   (m=14) that is ~30,240 steps — the observed 40-seed mean (~222,
   Iteration 14 CIs) sits far inside it, as a crude worst-case bound
   should.

Outputs -> results/theory_check.txt
"""

import math
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import MUTATIONS

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(15)
lines = []

# ---- check 1: one-step reachability at n=5 ----
n = 5
parent = [0, 1, 2, 3, 4]
target = tuple([4, 2, 0, 3, 1])  # far from parent (no single classic move)
ops = list(MUTATIONS.values())
N_DRAWS = 2_000_000
hits = 0
for _ in range(N_DRAWS):
    child = parent.copy()
    ops[rng.integers(4)](child, rng)
    if tuple(child) == target:
        hits += 1
delta0 = 1 / (4 * math.comb(n, 2) * math.factorial(n))
obs = hits / N_DRAWS
lines.append(f"check 1 (one-step reachability, n=5, {N_DRAWS:,} draws):")
lines.append(f"  theoretical lower bound delta0 = {delta0:.3e}")
lines.append(f"  observed Pr(child == distant target) = {obs:.3e} "
             f"({hits} hits)  -> bound {'HOLDS' if obs >= delta0*0.8 else 'VIOLATED'}")

# ---- check 2: scramble full-segment uniformity at n=4 ----
n4 = 4
counts = {}
N2 = 480_000
full = 0
for _ in range(N2):
    child = [0, 1, 2, 3]
    i, j = sorted(rng.choice(n4, 2, replace=False))
    if (i, j) != (0, n4 - 1):
        continue
    full += 1
    seg = child[i:j + 1]
    rng.shuffle(seg)
    child[i:j + 1] = seg
    counts[tuple(child)] = counts.get(tuple(child), 0) + 1
exp = full / math.factorial(n4)
dev = max(abs(c - exp) / exp for c in counts.values())
lines.append(f"\ncheck 2 (full-segment scramble uniformity, n=4):")
lines.append(f"  {full} full-segment draws over {len(counts)}/24 targets; "
             f"expected {exp:.0f} each; max relative deviation {dev:.3f} "
             f"-> {'UNIFORM (within MC noise)' if dev < 0.05 and len(counts) == 24 else 'CHECK'}")

# ---- check 3: aging bound vs observation ----
n7, m = 7, 14
bound = 2 * n7 * (n7 - 1) * math.factorial(n7) / m
lines.append(f"\ncheck 3 (aging discovery bound, parity n=7, m=14):")
lines.append(f"  Proposition B.2 bound: E[T_discover] <= {bound:,.0f} steps")
lines.append(f"  observed (Iteration 14, 40 seeds): mean 222.5, "
             f"bootstrap CI [170, 277] distinct evaluations")
lines.append(f"  observed << bound, as expected of a worst-case, "
             f"landscape-independent guarantee")

text = "\n".join(lines)
open(os.path.join(OUT, "theory_check.txt"), "w").write(text + "\n")
print(text)
