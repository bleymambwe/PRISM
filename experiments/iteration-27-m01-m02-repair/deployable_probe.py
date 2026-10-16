"""M01 repair: reliability of the DEPLOYED probe, with every evaluation charged.

The rejected submission's 91% agreement came from an estimator that read the true
optimum set (an oracle) and used up to 7m raw accesses.  This script measures the
production ``prism_search.diagnostics.preflight`` (reference = best point of its
own sample) and a cross-fit variant (reference chosen on one half of the sample,
FDC computed on the other half).  Both are charged for every distinct evaluation.

    python experiments/iteration-27-m01-m02-repair/deployable_probe.py [seconds]

Truth is ``landscape_truth.csv`` (exact optima; rho1 from 20,000 sampled pairs, so
the reference operator is itself an estimate).  Run from the repository root.
"""

from __future__ import annotations

import csv
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "iteration-26-tier0-gauntlet"))
sys.path.insert(0, "src")

import _compat  # noqa: F401,E402
from landscapes import load_all  # noqa: E402
from prism_search.diagnostics import _pearson, fitness_distance_correlation, preflight  # noqa: E402
from prism_search.distances import OPERATOR_DISTANCE  # noqa: E402
from prism_search.operators import MUTATION_OPERATORS  # noqa: E402

TRUTH = os.path.join(HERE, "..", "iteration-26-tier0-gauntlet", "results", "landscape_truth.csv")
OUT = os.path.join(HERE, "results", "deployable_probe.csv")
OPS = ("swap", "insert", "inversion")
PROBE_SIZES = (20, 50, 100, 200, 500)
RESAMPLES = 200
GUIDE, DECEPTIVE = -0.15, 0.30
REGIME_OF_REC = {
    "evolution": "search_pays",
    "uniform_sampling": "random_competitive",
    "avoid_local_search": "do_not_search",
    "improve_evaluator": "improve_evaluator",
}
FIELDS = ["landscape", "family", "n", "size", "variant", "m_target", "resamples", "mean_distinct_evals",
          "operator_agreement", "regime_agreement", "frac_search_pays", "true_operator", "true_regime"]


def regime(value: float) -> str:
    return "search_pays" if value <= GUIDE else "do_not_search" if value >= DECEPTIVE else "random_competitive"


def sizes_for(m: int, size: int) -> tuple[int, int]:
    """Same pair/landscape ratio as the protocol: charged cost is about 1.25 x probe."""

    probe = max(4, int(m / 1.25))
    return max(2, probe // 8), max(2, min(probe // 2, size // 2))


def crossfit(table, n, pairs, landscape, seed):
    """Reference from half A of the landscape sample, FDC on half B; all charged."""

    rng = np.random.default_rng(seed)
    cache: dict[tuple[int, ...], float] = {}

    def f(p):
        k = tuple(int(x) for x in p)
        if k not in cache:
            cache[k] = float(table[k])
        return cache[k]

    rhos = {}
    for name in OPS:
        op = MUTATION_OPERATORS[name]
        a, b = [], []
        for _ in range(pairs):
            parent = [int(v) for v in rng.permutation(n)]
            child = parent.copy()
            op(child, rng)
            a.append(f(parent))
            b.append(f(child))
        rhos[name] = _pearson(a, b)
    picked = max(OPS, key=rhos.__getitem__)
    seen, sample = set(), []
    while len(sample) < landscape:
        p = tuple(int(v) for v in rng.permutation(n))
        if p not in seen:
            seen.add(p)
            sample.append(p)
    fits = [f(p) for p in sample]
    half = max(1, len(sample) // 2)
    ref_a, ref_b = sample[:half], sample[half:]
    fa, fb = fits[:half], fits[half:]
    if len(ref_b) < 2:
        return picked, "random_competitive", len(cache)
    best = max(fa)
    refs = [p for p, v in zip(ref_a, fa, strict=True) if v == best]
    fdc = fitness_distance_correlation(ref_b, fb, refs, distance=OPERATOR_DISTANCE[picked])
    return picked, regime(fdc), len(cache)


def main() -> None:
    deadline = time.time() + (float(sys.argv[1]) if len(sys.argv) > 1 else 240.0)
    truth = {}
    with open(TRUTH, newline="", encoding="utf-8") as h:
        for r in csv.DictReader(h):
            truth[r["landscape"]] = r
    records = load_all()
    done = set()
    if os.path.exists(OUT):
        with open(OUT, newline="", encoding="utf-8") as h:
            done = {(r["landscape"], r["variant"], int(r["m_target"])) for r in csv.DictReader(h)}
    fresh = not os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8") as h:
        w = csv.DictWriter(h, fieldnames=FIELDS)
        if fresh:
            w.writeheader()
        for name, rec in records.items():
            t = truth[name]
            for variant in ("deployed_proxy", "crossfit"):
                for m in PROBE_SIZES:
                    if (name, variant, m) in done:
                        continue
                    if time.time() > deadline:
                        print("wall-clock budget reached")
                        return
                    pairs, land = sizes_for(m, rec.size)
                    op_hit = rg_hit = sp = 0
                    spent = []
                    for s in range(RESAMPLES):
                        seed = 1_000_003 * (m + 1) + s
                        if variant == "deployed_proxy":
                            res = preflight(
                                n=rec.n, fitness_fn=lambda p, tb=rec.table: tb[tuple(p)], operators=OPS,
                                pair_samples=pairs, landscape_samples=land, seed=seed,
                            )
                            picked, label, cost = res.selected_operator, REGIME_OF_REC[res.recommendation], res.distinct_evaluations
                        else:
                            picked, label, cost = crossfit(rec.table, rec.n, pairs, land, seed)
                        op_hit += picked == t["true_operator"]
                        rg_hit += label == t["true_regime"]
                        sp += label == "search_pays"
                        spent.append(cost)
                    w.writerow({
                        "landscape": name, "family": rec.family, "n": rec.n, "size": rec.size, "variant": variant,
                        "m_target": m, "resamples": RESAMPLES, "mean_distinct_evals": round(float(np.mean(spent)), 1),
                        "operator_agreement": round(op_hit / RESAMPLES, 4), "regime_agreement": round(rg_hit / RESAMPLES, 4),
                        "frac_search_pays": round(sp / RESAMPLES, 4), "true_operator": t["true_operator"],
                        "true_regime": t["true_regime"],
                    })
                    h.flush()
            print("done", name, flush=True)
    print("DEPLOYABLE PROBE COMPLETE")


if __name__ == "__main__":
    main()
