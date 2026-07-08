"""Iteration 14, part A: the statistics pass (publication gaps 3 & 4).

Free — everything runs against cached/closed-form landscapes.

A1. Headline comparisons at 40 seeds with Wilson 95% CIs for hit rates
    and bootstrap 95% CIs for best@200, on all four landscapes x six
    methods (elitist, aging, hybrid, surr-pos, surr-prec, random).
A2. Pre-flight sampling-error bounds: at realistic pre-flight sample
    sizes (100 move-pairs per operator; 200/500 points for FDC),
    bootstrap the probability that (a) argmax rho1 picks the correct
    matched operator and (b) FDC's sign/regime call is stable, on
    every enumerated landscape.

Outputs -> experiments/iteration-14/results/{headline_cis.csv,
preflight_error.csv, summary.txt}
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
from core.prism import MUTATIONS

spec = importlib.util.spec_from_file_location(
    "l12", os.path.join(ROOT, "experiments", "iteration-12",
                        "hybrid_surrogate.py"))
L12 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(L12)

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)
SEEDS = 40
RNG = np.random.default_rng(14)
lines = []


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def boot_ci(vals, stat=np.mean, B=4000):
    vals = np.asarray(vals, dtype=float)
    if len(vals) == 0:
        return (float("nan"), float("nan"))
    idx = RNG.integers(0, len(vals), (B, len(vals)))
    s = stat(vals[idx], axis=1)
    return float(np.percentile(s, 2.5)), float(np.percentile(s, 97.5))


# ---------------- A1: headline CIs ----------------
lands = L12.load_all()
rows = []
for lname, land in lands.items():
    n = len(next(iter(land)))
    opt = max(land.values())
    optima = {k for k, v in land.items() if v == opt}
    lines.append(f"\n== {lname} (optimum {opt:.4f}, "
                 f"{len(optima)}/{len(land)}) ==")
    for mname, fn in L12.METHODS.items():
        hits, evals, b200 = 0, [], []
        for seed in range(SEEDS):
            tr = L12.L10.Tracker(land, optima)
            fn(tr, n, seed)
            if tr.hit:
                hits += 1
                evals.append(tr.hit)
            mx = max(tr.curve) if tr.curve else 1
            b200.append(tr.curve.get(min(200, mx), -1))
        lo, hi = wilson(hits, SEEDS)
        elo, ehi = boot_ci(evals)
        blo, bhi = boot_ci(b200)
        rows.append({"landscape": lname, "method": mname,
                     "hits": hits, "n_seeds": SEEDS,
                     "hit_rate": round(hits / SEEDS, 3),
                     "wilson_lo": round(lo, 3),
                     "wilson_hi": round(hi, 3),
                     "mean_evals_hit": round(float(np.mean(evals)), 1)
                     if evals else -1,
                     "evals_ci": f"[{elo:.0f},{ehi:.0f}]"
                     if evals else "-",
                     "best200": round(float(np.mean(b200)), 4),
                     "best200_ci": f"[{blo:.4f},{bhi:.4f}]"})
        lines.append(
            f"  {mname:<10} hits {hits:>2}/40 "
            f"CI[{lo:.2f},{hi:.2f}]  evals "
            f"{np.mean(evals) if evals else -1:6.1f} "
            f"{'[%.0f,%.0f]' % (elo, ehi) if evals else '':<12} "
            f"best@200 {np.mean(b200):.4f} [{blo:.4f},{bhi:.4f}]")
with open(os.path.join(OUT, "headline_cis.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

# ---------------- A2: pre-flight sampling error ----------------
NEURAL = {k: L12.L10.load(k) for k in ("xor_n6", "parity_n7",
                                       "llm_chain_n6")}
from benchmarks.synthetic import OBJECTIVES
SYN = {f"{o}_n7": {p: OBJECTIVES[o](list(p))
                   for p in itertools.permutations(range(7))}
       for o in ("hamming", "kendall", "adjacency", "deceptive")}
ALL = {**NEURAL, **SYN}
MATCHED = {"hamming_n7": "swap", "kendall_n7": "insert",
           "adjacency_n7": "inversion"}
OPS = ["swap", "insert", "inversion", "scramble"]


def rho1_sample(land, keys, op, n_pairs, rng):
    opf = MUTATIONS[op]
    f0, f1 = [], []
    for _ in range(n_pairs):
        p = list(keys[rng.integers(len(keys))])
        q = p.copy()
        opf(q, rng)
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


def fdc_sample(land, keys, n_pts, rng, optima):
    idx = rng.choice(len(keys), min(n_pts, len(keys)), replace=False)
    fs, ds = [], []
    for i in idx:
        p = keys[i]
        fs.append(land[p])
        ds.append(min(cayley(list(p), list(o)) for o in optima))
    return float(np.corrcoef(fs, ds)[0, 1])


rows2 = []
lines.append("\n== pre-flight sampling error (200 resamples each) ==")
for lname, land in ALL.items():
    keys = list(land.keys())
    opt = max(land.values())
    optima = [k for k, v in land.items() if v == opt][:50]
    B = 200
    picks, fdcs = [], []
    for b in range(B):
        rng = np.random.default_rng(1000 + b)
        rhos = {op: rho1_sample(land, keys, op, 100, rng)
                for op in OPS}
        picks.append(max((o for o in OPS if o != "scramble"),
                         key=lambda o: rhos[o]))
        fdcs.append(fdc_sample(land, keys, 200, rng, optima))
    fdcs = np.array(fdcs)
    # regime call: negative (<-0.15) / near-zero / positive (>0.05)
    full_fdc = fdc_sample(land, keys, len(keys),
                          np.random.default_rng(0), optima)
    regime = ("neg" if full_fdc < -0.15 else
              "pos" if full_fdc > 0.05 else "zero")
    calls = np.where(fdcs < -0.15, "neg",
                     np.where(fdcs > 0.05, "pos", "zero"))
    stable = float(np.mean(calls == regime))
    pick_counts = {o: picks.count(o) for o in OPS if o != "scramble"}
    top_pick = max(pick_counts, key=pick_counts.get)
    agree = pick_counts[top_pick] / B
    correct = (f"{pick_counts.get(MATCHED[lname], 0)/B:.2f} correct"
               if lname in MATCHED else "n/a")
    rows2.append({"landscape": lname,
                  "modal_operator_pick": top_pick,
                  "pick_agreement@100pairs": round(agree, 2),
                  "matched_pick_rate": correct,
                  "fdc_full": round(full_fdc, 3),
                  "fdc_sample_ci": f"[{np.percentile(fdcs,2.5):.2f},"
                                   f"{np.percentile(fdcs,97.5):.2f}]",
                  "regime": regime,
                  "regime_call_stability@200pts": round(stable, 2)})
    lines.append(f"  {lname:<14} pick={top_pick}({agree:.2f}) "
                 f"{correct:<14} FDC {full_fdc:+.2f} "
                 f"CI[{np.percentile(fdcs,2.5):+.2f},"
                 f"{np.percentile(fdcs,97.5):+.2f}] "
                 f"regime={regime} stable={stable:.2f}")
with open(os.path.join(OUT, "preflight_error.csv"), "w",
          newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows2[0].keys()))
    w.writeheader()
    w.writerows(rows2)

text = "\n".join(lines)
open(os.path.join(OUT, "summary.txt"), "w").write(text + "\n")
print(text)
print("\nSTATS PASS COMPLETE.")
