"""Iteration 22: rho1-vs-alternatives ablation (D21 item 5, approved D22).

Question: is rho1 (independent move-pair autocorrelation, the D14
pre-flight statistic) at least as reliable an OPERATOR SELECTOR as the
classical alternatives, at equal sample budget? Pre-empts the reviewer
question "why this statistic and not autocorrelation length?".

Selectors compared (each scores an operator; argmax over
{swap, insert, inversion} = the pick):
  pair_rho1   Pearson corr of f(parent), f(child) over B independent
              sampled moves  (the D14 statistic)
  walk_rho1   lag-1 autocorrelation of fitness along one random walk of
              B steps using the operator (Weinberger 1990 estimator;
              autocorrelation length ell = -1/ln(rho) is a monotone
              transform, so its argmax is identical by construction)
  neg_mad     negative mean |f(child) - f(parent)| over B independent
              moves (ruggedness; lower absolute change = smoother)

Landscapes (closed-form or cached; ground-truth matched operator known):
  hamming n=7   -> swap       kendall n=7 -> insert
  adjacency n=7 -> inversion  LLM n=6 (Exp. K cache) -> insert
                              (validated: insert won rho1 AND the
                               matched-operator race in Exp. K)

Protocol: budgets B in {50, 100, 500}; 200 resamples per
(landscape, selector, budget); report pick accuracy (fraction of
resamples whose argmax = matched operator). Deterministic seeds.

Cost: $0, CPU, ~1-3 min. Output -> results/rho1_ablation.{csv,txt}
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

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)

OPS3 = ["swap", "insert", "inversion"]
BUDGETS = [50, 100, 500]
RESAMPLES = 200

# ---------------- landscapes with known matched operator ----------------
LANDS = {}
for obj, matched in (("hamming", "swap"), ("kendall", "insert"),
                     ("adjacency", "inversion")):
    fn = OBJECTIVES[obj]
    LANDS[f"{obj} (n=7)"] = (
        {p: fn(list(p)) for p in itertools.permutations(range(7))}, matched)

llm = {}
for r in csv.DictReader(open(os.path.join(
        ROOT, "experiments/iteration-09/results/llm_landscape.csv"))):
    llm[tuple(json.loads(r["perm"]))] = float(r["fitness"])
LANDS["LLM n=6 (Exp. K)"] = (llm, "insert")


# ---------------- selectors ----------------
def score_pair_rho1(land, keys, op, budget, rng):
    f0, f1 = [], []
    for _ in range(budget):
        p = list(keys[rng.integers(len(keys))])
        q = p.copy()
        MUTATIONS[op](q, rng)
        f0.append(land[tuple(p)])
        f1.append(land[tuple(q)])
    if np.std(f0) == 0 or np.std(f1) == 0:
        return -np.inf
    return float(np.corrcoef(f0, f1)[0, 1])


def score_walk_rho1(land, keys, op, budget, rng):
    p = list(keys[rng.integers(len(keys))])
    fs = [land[tuple(p)]]
    for _ in range(budget):
        MUTATIONS[op](p, rng)
        fs.append(land[tuple(p)])
    a, b = np.array(fs[:-1]), np.array(fs[1:])
    if np.std(a) == 0 or np.std(b) == 0:
        return -np.inf
    return float(np.corrcoef(a, b)[0, 1])


def score_neg_mad(land, keys, op, budget, rng):
    d = []
    for _ in range(budget):
        p = list(keys[rng.integers(len(keys))])
        q = p.copy()
        MUTATIONS[op](q, rng)
        d.append(abs(land[tuple(q)] - land[tuple(p)]))
    return -float(np.mean(d))


SELECTORS = {"pair_rho1": score_pair_rho1,
             "walk_rho1": score_walk_rho1,
             "neg_mad": score_neg_mad}


# ---------------- ablation ----------------
def main():
    rows, lines = [], []
    lines.append("Iteration 22 - rho1-vs-alternatives operator-selection "
                 "ablation")
    lines.append(f"budgets {BUDGETS} move-samples; {RESAMPLES} resamples; "
                 f"pick = argmax over {OPS3}\n")
    header = (f"{'landscape':<18} {'matched':<9} {'selector':<10} " +
              " ".join(f"B={b:<4}" for b in BUDGETS))
    lines.append(header)
    for lname, (land, matched) in LANDS.items():
        keys = list(land.keys())
        for sname, sfn in SELECTORS.items():
            accs = []
            for b in BUDGETS:
                correct = 0
                for r2 in range(RESAMPLES):
                    rng = np.random.default_rng(
                        hash((lname, sname, b, r2)) % (2**32))
                    scores = {op: sfn(land, keys, op, b, rng)
                              for op in OPS3}
                    if max(scores, key=scores.get) == matched:
                        correct += 1
                accs.append(correct / RESAMPLES)
            rows.append({"landscape": lname, "matched": matched,
                         "selector": sname,
                         **{f"acc_B{b}": round(a, 3)
                            for b, a in zip(BUDGETS, accs)}})
            lines.append(f"{lname:<18} {matched:<9} {sname:<10} " +
                         " ".join(f"{a:<6.2f}" for a in accs))
    # summary: mean accuracy per selector per budget across landscapes
    lines.append("\nMean pick accuracy across the 4 landscapes:")
    for sname in SELECTORS:
        means = []
        for b in BUDGETS:
            vals = [r[f"acc_B{b}"] for r in rows if r["selector"] == sname]
            means.append(np.mean(vals))
        lines.append(f"  {sname:<10} " +
                     " ".join(f"B={b}:{m:.3f}" for b, m in
                              zip(BUDGETS, means)))
    with open(os.path.join(OUT, "rho1_ablation.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    text = "\n".join(lines)
    open(os.path.join(OUT, "rho1_ablation.txt"), "w").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
