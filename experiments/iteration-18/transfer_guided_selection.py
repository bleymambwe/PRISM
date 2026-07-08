"""Iteration 18, Experiment R: transfer-guided evaluation on cached LLM data.

Question: does the n=6 instruction-order landscape merely correlate with
n=8 fitness, or can it guide a low-budget n=8 evaluation policy?

This experiment uses only committed caches:
  - Iteration 9: full n=6 LLM ordering landscape.
  - Iteration 11: n=8 sampled answer cache.

Protocol:
  1. Reconstruct the unbiased n=8 gate + pre-flight sample from Iteration 11.
  2. Score each n=8 ordering using the n=6 position-effect table.
  3. Compare evaluating candidates in source-score order against a
     random-without-replacement baseline over the same candidate pool.

Outputs -> experiments/iteration-18/results/transfer_guided_selection.txt
"""

import csv
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def ci(xs):
    return float(np.percentile(xs, 2.5)), float(np.percentile(xs, 97.5))


def load_n6_position_effects():
    landscape_path = os.path.join(
        ROOT, "experiments", "iteration-09", "results", "llm_landscape.csv"
    )
    land6 = {
        tuple(json.loads(r["perm"])): float(r["fitness"])
        for r in csv.DictReader(open(landscape_path, newline=""))
    }
    pos6 = np.zeros((6, 6))
    for perm, fitness in land6.items():
        for pos, module in enumerate(perm):
            pos6[module][pos] += fitness
    pos6 /= 120
    return pos6


def reconstruct_iteration11_sample():
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
    return sorted({tuple(p) for p in gate + base + neigh})


def load_n8_fitness(sample):
    cache_path = os.path.join(
        ROOT, "experiments", "iteration-11", "results", "answer_cache.csv"
    )
    cache = {}
    for r in csv.reader(open(cache_path, newline="")):
        if r and r[0] != "perm":
            cache[(tuple(json.loads(r[0])), int(r[1]))] = int(r[2])

    fit8 = {}
    for perm in sample:
        vals = [cache.get((perm, qidx)) for qidx in range(20)]
        if all(v is not None for v in vals):
            fit8[perm] = sum(vals) / 20
    return fit8


def score_n8_from_n6(pos6, perm):
    # Experiment M n=8 modules:
    # 0 RESTATE, 1 IDENTIFY, 2 ESTIMATE, 3 PLAN, 4 SIMPLIFY,
    # 5 COMPUTE, 6 CHECK, 7 ANSWER.
    # Shared n=6 modules are RESTATE, IDENTIFY, PLAN, COMPUTE, CHECK, ANSWER.
    m8_to_m6 = {0: 0, 1: 1, 3: 2, 5: 3, 6: 4, 7: 5}
    score = 0.0
    for pos, module in enumerate(perm):
        if module in m8_to_m6:
            rel = pos / 7
            n6_pos = min(5, int(round(rel * 5)))
            score += pos6[m8_to_m6[module]][n6_pos]
    return score


def main():
    pos6 = load_n6_position_effects()
    sample = reconstruct_iteration11_sample()
    fit8 = load_n8_fitness(sample)
    rows = []
    for perm, fitness in fit8.items():
        rows.append((perm, score_n8_from_n6(pos6, perm), fitness))

    scores = np.array([r[1] for r in rows])
    actuals = np.array([r[2] for r in rows])
    order = np.argsort(scores)[::-1]
    guided_actuals = actuals[order]
    guided_best = np.maximum.accumulate(guided_actuals)

    rng = np.random.default_rng(1800)
    budgets = [1, 3, 5, 10, 20, 30, 50, 100, min(200, len(rows))]
    budgets = [b for b in budgets if b <= len(rows)]
    random_trials = 10000

    lines = []
    lines.append("Experiment R: n=6 -> n=8 transfer-guided evaluation")
    lines.append(f"candidate pool: {len(rows)} complete unbiased n=8 orderings")
    lines.append(
        f"source-score vs n=8 fitness: Spearman rho={spearman(scores, actuals):.3f}, "
        f"Pearson r={float(np.corrcoef(scores, actuals)[0, 1]):.3f}"
    )
    lines.append(
        f"fitness range in pool: [{actuals.min():.3f}, {actuals.max():.3f}], "
        f"mean={actuals.mean():.3f}, perfect_count={int((actuals == 1.0).sum())}"
    )
    lines.append("")
    lines.append("budget,guided_best,random_best_mean,random_best_ci95,random_p_hit_1.0")

    for budget in budgets:
        rand_best = []
        rand_hit = []
        for _ in range(random_trials):
            idx = rng.choice(len(rows), size=budget, replace=False)
            best = float(actuals[idx].max())
            rand_best.append(best)
            rand_hit.append(best >= 1.0)
        lo, hi = ci(rand_best)
        lines.append(
            f"{budget},{guided_best[budget - 1]:.3f},"
            f"{np.mean(rand_best):.3f},[{lo:.3f},{hi:.3f}],"
            f"{np.mean(rand_hit):.3f}"
        )

    top10 = max(1, len(rows) // 10)
    top_actuals = guided_actuals[:top10]
    lines.append("")
    lines.append(
        f"top-10% by transferred score: mean={top_actuals.mean():.3f}, "
        f"min={top_actuals.min():.3f}, max={top_actuals.max():.3f}"
    )
    lines.append(
        "interpretation: promoted only if guided evaluation reaches high-quality "
        "orderings at materially lower budget than random in this cached pool."
    )

    text = "\n".join(lines)
    out_path = os.path.join(OUT, "transfer_guided_selection.txt")
    with open(out_path, "w", newline="") as f:
        f.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
