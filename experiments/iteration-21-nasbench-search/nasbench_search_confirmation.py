"""Iteration 21: NAS-Bench-201 within-slice search confirmation
(Benchmark #5, approved D22; completes the ANASOD boundary diagnostic's
"budget-matched search confirmation remains" item).

PRE-REGISTERED DESIGN (written before any race ran; the selection basis
is the ALREADY-COMMITTED iteration-19 slice metrics, computed 2026-07-11
before this experiment existed):

  Eligible slices: n_placements >= 60 AND range >= 1.0 accuracy point
  Structure score: (-fdc) + rho_swap   (both from the committed CSV)
  Per dataset: top-3 scores = HIGH-structure, bottom-3 = LOW-structure.

  FORECAST (H24): on HIGH slices the swap-mutation elitist searcher beats
  uniform random-without-replacement (hit-rate gap >= 20 points at budget
  30, or disjoint 95% Wilson CIs). On LOW slices searcher ~ random
  (neither criterion met, in either direction).

Race protocol per slice: fitness = table lookup (mean of the repeated
last-epoch validation accuracies, identical to iteration-19); target =
the slice optimum (ties included); budget = 30 DISTINCT architectures;
40 seeds each for searcher and random. Searcher = elitist EA, pop 20,
tournament k=3, one same-multiset edge swap per mutation, p_m = 0.6
(D12 regime), elitism 1 — the PRISM searcher semantics on multiset
placements. Cost: $0 (all lookups).

Data backend: simple-hpo-bench==0.2.0 compact NATS-Bench tables (same
caveat as iteration-19: last-epoch, compact redistribution).

Usage: python nasbench_search_confirmation.py
Outputs -> results/nasbench_confirmation.{csv,txt}
"""

import csv
import os
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = os.path.dirname(__file__)
ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
SLICE_CSV = os.path.join(ROOT, "experiments", "iteration-19", "results",
                         "slice_metrics.csv")

OPS = ("none", "skip_connect", "nor_conv_1x1", "nor_conv_3x3",
       "avg_pool_3x3")
BUDGET = 30
SEEDS = 40
MIN_PLACEMENTS = 60
MIN_RANGE = 1.0


def load_tables():
    import hpo_benchmarks
    root = Path(hpo_benchmarks.__file__).parent / "datasets" / "nasbench201"
    mapping = {"cifar10.pkl": "cifar10-valid", "cifar100.pkl": "cifar100",
               "imagenet.pkl": "ImageNet16-120"}
    out = {}
    for fn, ds in mapping.items():
        raw = pickle.load((root / fn).open("rb"))
        out[ds] = {tuple(OPS[int(i)] for i in enc):
                   float(np.mean(m["val_acc"])) for enc, m in raw.items()}
    return out


def distribution(ops):
    from collections import Counter
    c = Counter(ops)
    return tuple(c[o] for o in OPS)


def pick_slices():
    """Pre-registered selection from the committed iteration-19 CSV."""
    rows = []
    for r in csv.DictReader(open(SLICE_CSV)):
        try:
            npl = int(r["n_placements"])
            rng_ = float(r["range"])
            fdc = float(r["fdc"])
            rho = float(r["rho_swap"])
        except ValueError:
            continue
        if npl >= MIN_PLACEMENTS and rng_ >= MIN_RANGE and \
                np.isfinite(fdc) and np.isfinite(rho):
            rows.append({"dataset": r["dataset"],
                         "distribution": r["distribution"],
                         "n_placements": npl, "range": rng_,
                         "fdc": fdc, "rho_swap": rho,
                         "score": (-fdc) + rho})
    picks = {}
    for ds in ("cifar10-valid", "cifar100", "ImageNet16-120"):
        sub = sorted((r for r in rows if r["dataset"] == ds),
                     key=lambda r: r["score"])
        picks[ds] = {"HIGH": sub[-3:], "LOW": sub[:3]}
    return picks


def swap_mutate(ops, rng):
    """One same-multiset edge swap (skip identical-op pairs)."""
    ops = list(ops)
    idx = [(i, j) for i in range(5) for j in range(i + 1, 6)
           if ops[i] != ops[j]]
    if not idx:
        return tuple(ops)
    i, j = idx[rng.integers(len(idx))]
    ops[i], ops[j] = ops[j], ops[i]
    return tuple(ops)


def race(slice_scores, seed, method):
    """Return distinct-evals-to-optimum or None (budget exhausted)."""
    keys = list(slice_scores)
    best = max(slice_scores.values())
    optima = {k for k, v in slice_scores.items()
              if abs(v - best) < 1e-12}
    rng = np.random.default_rng(seed)
    seen = {}

    def evaluate(k):
        if k not in seen and len(seen) < BUDGET:
            seen[k] = slice_scores[k]
        return slice_scores[k]

    if method == "random":
        order = rng.permutation(len(keys))
        for oi in order:
            k = keys[oi]
            evaluate(k)
            if k in optima:
                return len(seen)
            if len(seen) >= BUDGET:
                return None
        return None
    # elitist swap EA, pop 20, tournament 3, p_m 0.6, elitism 1
    pop = [keys[i] for i in rng.integers(0, len(keys), 20)]
    fit = [evaluate(p) for p in pop]
    for p in pop:
        if p in optima:
            return len(seen)
    for _ in range(1000):
        if len(seen) >= BUDGET:
            return None
        newpop = [pop[int(np.argmax(fit))]]  # elite
        while len(newpop) < 20:
            cand = rng.integers(0, 20, 3)
            parent = pop[max(cand, key=lambda c: fit[c])]
            child = (swap_mutate(parent, rng)
                     if rng.random() < 0.6 else parent)
            newpop.append(child)
        pop = newpop
        fit = []
        for p in pop:
            v = evaluate(p)
            fit.append(v)
            if p in optima and len(seen) <= BUDGET:
                return len(seen)
    return None


def wilson(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0, c - h), min(1, c + h)


def main():
    tables = load_tables()
    picks = pick_slices()
    lines = ["Iteration 21 - NAS-Bench-201 within-slice search "
             "confirmation (pre-registered H24)",
             f"budget {BUDGET} distinct archs, {SEEDS} seeds, "
             f"eligibility n>={MIN_PLACEMENTS} & range>={MIN_RANGE}pt, "
             "score=(-FDC)+rho_swap\n"]
    rows = []
    verdicts = {"HIGH": [], "LOW": []}
    for ds, groups_sel in picks.items():
        table = tables[ds]
        groups = defaultdict(dict)
        for ops, v in table.items():
            groups[";".join(map(str, distribution(ops)))][ops] = v
        lines.append(f"== {ds} ==")
        for level in ("HIGH", "LOW"):
            for meta in groups_sel[level]:
                sl = groups[meta["distribution"]]
                res = {}
                for method in ("prism", "random"):
                    hits, evals = 0, []
                    for s in range(SEEDS):
                        r = race(sl, 10_000 + s, method)
                        if r is not None:
                            hits += 1
                            evals.append(r)
                    lo, hi = wilson(hits, SEEDS)
                    res[method] = (hits, lo, hi,
                                   float(np.mean(evals)) if evals else -1)
                hp, hr = res["prism"][0], res["random"][0]
                disjoint = (res["prism"][1] > res["random"][2] or
                            res["random"][1] > res["prism"][2])
                search_wins = (hp - hr) >= 8 or (disjoint and hp > hr)
                ok = (search_wins if level == "HIGH" else not search_wins)
                verdicts[level].append(ok)
                rows.append({
                    "dataset": ds, "level": level,
                    "distribution": meta["distribution"],
                    "n_placements": meta["n_placements"],
                    "range": meta["range"], "fdc": meta["fdc"],
                    "rho_swap": meta["rho_swap"],
                    "prism_hits": hp, "random_hits": hr,
                    "prism_mean_evals": round(res["prism"][3], 1),
                    "random_mean_evals": round(res["random"][3], 1),
                    "search_wins": search_wins,
                    "forecast_correct": ok})
                lines.append(
                    f"  {level} {meta['distribution']:<11} "
                    f"n={meta['n_placements']:<3} range="
                    f"{meta['range']:.1f} FDC={meta['fdc']:+.2f} "
                    f"rho={meta['rho_swap']:+.2f} | prism {hp}/{SEEDS} "
                    f"(mean {res['prism'][3]:.1f}) vs random "
                    f"{hr}/{SEEDS} (mean {res['random'][3]:.1f}) "
                    f"-> {'SEARCH WINS' if search_wins else '~ random'} "
                    f"[forecast {'OK' if ok else 'MISS'}]")
        lines.append("")
    nh, nl = len(verdicts["HIGH"]), len(verdicts["LOW"])
    lines.append(f"H24 scorecard: HIGH forecasts correct "
                 f"{sum(verdicts['HIGH'])}/{nh}; LOW forecasts correct "
                 f"{sum(verdicts['LOW'])}/{nl}")
    with open(os.path.join(OUT, "nasbench_confirmation.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    text = "\n".join(lines)
    open(os.path.join(OUT, "nasbench_confirmation.txt"), "w").write(
        text + "\n")
    print(text)
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    main()
