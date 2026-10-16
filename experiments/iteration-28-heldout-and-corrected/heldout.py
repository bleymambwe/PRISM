"""Study B: leave-one-family-out probe threshold, null calibration, degeneracy.

    python experiments/iteration-28-heldout-and-corrected/heldout.py [seconds]
Resumable: collects per-landscape probe FDC samples to results/probe_samples.json, then analyses.
"""

import csv
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: F401,E402
from deployable_probe import OPS, sizes_for  # noqa: E402
from prism_search.diagnostics import preflight  # noqa: E402

RES = os.path.join(common.HERE, "results")
SAMPLES = os.path.join(RES, "probe_samples.json")
G26 = os.path.join(common.HERE, "..", "iteration-26-tier0-gauntlet", "results", "gauntlet_runs.csv")
RESAMPLES = 200
GRID = [round(-0.40 + 0.05 * i, 2) for i in range(8)]
PUBLISHED_G = -0.15
MARGIN = 0.15
rng = np.random.default_rng(20261016)


def probe(table, n, size, m, label, seed0):
    pairs, land = sizes_for(m, size)
    fdcs, flat = [], []
    for s in range(RESAMPLES):
        r = preflight(n=n, fitness_fn=lambda p: table[tuple(p)], operators=OPS, pair_samples=pairs,
                      landscape_samples=land, seed=seed0 + s)
        fdcs.append(r.fitness_distance_correlation)
        flat.append(r.recommendation == "improve_evaluator")
    return {"fdc": fdcs, "flat": flat}


def collect(deadline):
    data = json.load(open(SAMPLES)) if os.path.exists(SAMPLES) else {}
    records = common.load(True)
    for i, (name, rec) in enumerate(sorted(records.items())):
        if name in data:
            continue
        if time.time() > deadline:
            return data, False
        shuffled = dict(zip(rec.table.keys(), np.random.default_rng(20261016 + i).permutation(list(rec.table.values())), strict=True))
        data[name] = {
            "family": rec.family,
            "m200": probe(rec.table, rec.n, rec.size, 200, "m200", 5_000_000),
            "null_m200": probe(shuffled, rec.n, rec.size, 200, "null", 6_000_000),
            "m20": probe(rec.table, rec.n, rec.size, 20, "m20", 7_000_000),
        }
        json.dump(data, open(SAMPLES, "w"))
        print("collected", name, flush=True)
    return data, True


def truth_labels():
    hits = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(G26, newline="", encoding="utf-8")):
        hits[r["landscape"]][r["method"]].append(int(r["hit_by_100"]))
    corr = json.load(open(os.path.join(RES, "corrected_scoring.json")))["corrected"]["B100"]
    labels, gaps = {}, {}
    for name, m in hits.items():
        u = np.mean(m["uniform"]); best = max(np.mean(m["ls_swap"]), np.mean(m["ea_portfolio"]))
        if name == common.GSM:
            u, best = corr["uniform"], max(corr["ls_swap"], corr["ea_portfolio"])
        gaps[name] = float(best - u); labels[name] = int(best - u >= MARGIN)
    return labels, gaps


def decision(entry, g):
    f = np.array(entry["m200"]["fdc"]); flat = np.array(entry["m200"]["flat"])
    return int(np.mean((f <= g) & ~flat) >= 0.5)


def balanced(y, p):
    y, p = np.array(y), np.array(p)
    if y.min() == y.max():
        return None
    return 0.5 * (np.mean(p[y == 1] == 1) + np.mean(p[y == 0] == 0))


def boot_lower(y, p, reps=2000):
    y, p = np.array(y), np.array(p); vals = []
    for _ in range(reps):
        i = rng.integers(len(y), size=len(y))
        b = balanced(y[i], p[i])
        if b is not None:
            vals.append(b - 0.5)
    return float(np.mean(y)), (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)), len(vals)) if vals else None


def analyse(data):
    labels, gaps = truth_labels()
    fams = sorted({d["family"] for d in data.values()})
    out = {"labels": labels, "gaps": gaps, "folds": {}}
    held_y, held_p, pub_p = [], [], []
    for fam in fams:
        train = [n for n in data if data[n]["family"] != fam]
        test = [n for n in data if data[n]["family"] == fam]
        ytr = [labels[n] for n in train]
        if len(set(ytr)) < 2:
            out["folds"][fam] = {"status": "undefined: single class in training set", "test": test}
            continue
        scores = {g: balanced(ytr, [decision(data[n], g) for n in train]) for g in GRID}
        best = max(GRID, key=lambda g: (scores[g], -g))  # ties go to the more negative g
        preds = {n: decision(data[n], best) for n in test}
        out["folds"][fam] = {"status": "ok", "fitted_g": best, "train_balanced": scores[best], "test": test, "preds": preds,
                             "truth": {n: labels[n] for n in test}}
        for n in test:
            held_y.append(labels[n]); held_p.append(preds[n]); pub_p.append(decision(data[n], PUBLISHED_G))
    out["pooled_heldout"] = {"n": len(held_y), "positives": int(sum(held_y)),
                             "balanced_accuracy_fitted": balanced(held_y, held_p),
                             "balanced_accuracy_published_g": balanced(held_y, pub_p)}
    if held_y:
        out["pooled_heldout"]["bootstrap_BA_minus_0.5_fitted"] = boot_lower(held_y, held_p)[1]
        out["pooled_heldout"]["bootstrap_BA_minus_0.5_published"] = boot_lower(held_y, pub_p)[1]
    null_rates = np.array([np.mean((np.array(d["null_m200"]["fdc"]) <= PUBLISHED_G) & ~np.array(d["null_m200"]["flat"])) for d in data.values()])
    idx = rng.integers(len(null_rates), size=(2000, len(null_rates)))
    mean_boot = null_rates[idx].mean(axis=1)
    out["B2_null_false_search_pays"] = {"per_landscape": dict(zip(data, null_rates.round(3).tolist(), strict=True)), "mean": float(null_rates.mean()),
                                         "ci95": [float(np.percentile(mean_boot, 2.5)), float(np.percentile(mean_boot, 97.5))],
                                         "supported_lower_bound_gt_0.10": bool(np.percentile(mean_boot, 2.5) > 0.10)}
    deg = [np.mean(np.isclose(d["m20"]["fdc"], -1.0)) for d in data.values()]
    out["B3_degenerate_fdc_minus1_at_m20"] = {"per_landscape": dict(zip(data, np.round(deg, 3).tolist(), strict=True)), "mean": float(np.mean(deg))}
    out["probe_decision_at_published_g"] = {n: decision(data[n], PUBLISHED_G) for n in data}
    json.dump(out, open(os.path.join(RES, "heldout_results.json"), "w"), indent=2)
    return out


def main():
    deadline = time.time() + (float(sys.argv[1]) if len(sys.argv) > 1 else 240.0)
    data, complete = collect(deadline)
    if not complete:
        print("wall-clock budget reached; rerun to continue")
        return
    out = analyse(data)
    print(json.dumps({k: v for k, v in out.items() if k not in ("folds",)}, indent=1)[:3500])
    for fam, f in out["folds"].items():
        print(fam, json.dumps(f))
    print("HELDOUT COMPLETE")


if __name__ == "__main__":
    main()
