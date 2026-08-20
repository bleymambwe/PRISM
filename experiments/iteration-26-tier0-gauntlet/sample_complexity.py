"""E0.2 estimator sample complexity: how big must the pre-flight probe be?

The protocol's decision rule is a threshold crossing on two estimated
statistics.  A threshold rule on a noisy estimate is only as good as the
estimate's concentration, so the question a reviewer asks is: *how many probe
evaluations buy a regime call that is right with probability at least 1 - delta?*

Analytic statement
------------------
Both statistics are Pearson correlations of bounded variables.  For a probe of
m independent draws the Fisher transform z = artanh(r) is approximately normal
with standard error 1/sqrt(m - 3).  A regime call flips only when the estimate
crosses a decision boundary tau, so for a landscape whose true statistic rho
sits a margin away from that boundary,

    P(flip) ~= Phi( -|artanh(rho) - artanh(tau)| * sqrt(m - 3) )

which inverts to the probe size that buys a target confidence:

    m >= 3 + ( z_{1-delta} / (artanh(rho) - artanh(tau)) )^2

``predicted_flip_rate`` records the left-hand side so the empirical flip rate
can be checked against it directly.

Implementation note: distance-to-nearest-optimum is precomputed once per
(landscape, distance) rather than inside each resample, and the mutation moves
are inlined with a fast generator.  Both are performance-only changes; the
sampling distributions are unchanged.

    python sample_complexity.py [seconds]
"""

from __future__ import annotations

import csv
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "src")

from landscapes import load_all  # noqa: E402
from prism_search.distances import DISTANCES, OPERATOR_DISTANCE  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results")
OUT_CSV = os.path.join(OUT_DIR, "sample_complexity.csv")
TRUTH_CSV = os.path.join(OUT_DIR, "landscape_truth.csv")

OPERATORS = ("swap", "insert", "inversion")
PROBE_SIZES = (20, 50, 100, 200, 500)
RESAMPLES = 200
GUIDING_THRESHOLD = -0.15
DECEPTIVE_THRESHOLD = 0.30
FULL_PAIRS = 20000

FIELDS = [
    "landscape",
    "family",
    "n",
    "probe_m",
    "resamples",
    "operator_agreement",
    "regime_agreement",
    "mean_abs_fdc_error",
    "mean_abs_rho1_error",
    "true_operator",
    "true_fdc",
    "true_regime",
    "margin_to_threshold",
    "predicted_flip_rate",
]


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    if a.std() == 0 or b.std() == 0:
        return 0.0
    value = float(np.corrcoef(a, b)[0, 1])
    return value if math.isfinite(value) else 0.0


def _move(perm: np.ndarray, operator: str, rng: np.random.Generator) -> tuple[int, ...]:
    """Apply one mutation.  Semantics match ``prism_search.operators``."""

    n = perm.shape[0]
    i = int(rng.integers(n))
    j = int(rng.integers(n - 1))
    if j >= i:
        j += 1
    out = perm.copy()
    if operator == "swap":
        out[i], out[j] = out[j], out[i]
    elif operator == "insert":
        value = out[i]
        rest = np.delete(out, i)
        out = np.insert(rest, j, value)
    else:  # inversion
        lo, hi = (i, j) if i < j else (j, i)
        out[lo : hi + 1] = out[lo : hi + 1][::-1]
    return tuple(int(x) for x in out)


def rho1_estimate(
    keys: list[tuple[int, ...]],
    fitness: dict[tuple[int, ...], float],
    operator: str,
    rng: np.random.Generator,
    pairs: int,
) -> float:
    idx = rng.integers(len(keys), size=pairs)
    parents = np.empty(pairs)
    children = np.empty(pairs)
    for slot, index in enumerate(idx):
        parent = keys[int(index)]
        parents[slot] = fitness[parent]
        children[slot] = fitness[_move(np.array(parent), operator, rng)]
    return _pearson(parents, children)


def regime_of(value: float) -> str:
    if value <= GUIDING_THRESHOLD:
        return "search_pays"
    if value >= DECEPTIVE_THRESHOLD:
        return "do_not_search"
    return "random_competitive"


def _fisher(value: float) -> float:
    return math.atanh(max(min(value, 0.999999), -0.999999))


def predicted_flip_rate(true_fdc: float, m: int) -> float:
    """Normal-approximation flip probability at the nearer decision boundary."""

    gap = min(
        abs(_fisher(true_fdc) - _fisher(b))
        for b in (GUIDING_THRESHOLD, DECEPTIVE_THRESHOLD)
    )
    if m <= 4:
        return 0.5
    return 0.5 * math.erfc(gap * math.sqrt(m - 3) / math.sqrt(2.0))


def main() -> None:
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 1800.0
    deadline = time.time() + seconds
    os.makedirs(OUT_DIR, exist_ok=True)

    records = load_all()
    done: set[tuple[str, int]] = set()
    if os.path.exists(OUT_CSV):
        with open(OUT_CSV, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                done.add((row["landscape"], int(row["probe_m"])))
    fresh = not os.path.exists(OUT_CSV)
    truth_rows = []

    with open(OUT_CSV, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if fresh:
            writer.writeheader()

        for name, record in records.items():
            keys = list(record.table.keys())
            fitness = record.table
            optima = list(record.optima)
            fits = np.array([fitness[k] for k in keys])

            # distance to the nearest true optimum, precomputed once per distance
            distance_columns: dict[str, np.ndarray] = {}
            for distance_name, function in DISTANCES.items():
                distance_columns[distance_name] = np.array(
                    [min(function(list(k), list(o)) for o in optima) for k in keys]
                )

            true_rhos = {
                op: rho1_estimate(keys, fitness, op, np.random.default_rng(7), FULL_PAIRS)
                for op in OPERATORS
            }
            true_operator = max(OPERATORS, key=true_rhos.__getitem__)
            true_distance = OPERATOR_DISTANCE[true_operator]
            true_fdc = _pearson(fits, distance_columns[true_distance])
            true_regime = regime_of(true_fdc)
            margin = min(
                abs(true_fdc - GUIDING_THRESHOLD), abs(true_fdc - DECEPTIVE_THRESHOLD)
            )
            truth_rows.append(
                {
                    "landscape": name,
                    "family": record.family,
                    "n": record.n,
                    **{f"rho1_{op}": round(true_rhos[op], 4) for op in OPERATORS},
                    "true_operator": true_operator,
                    "distance": true_distance,
                    "true_fdc": round(true_fdc, 4),
                    "true_regime": true_regime,
                    "margin_to_threshold": round(margin, 4),
                }
            )

            rng = np.random.default_rng(20260813)
            for m in PROBE_SIZES:
                if (name, m) in done:
                    continue
                if time.time() > deadline:
                    print("wall-clock budget reached")
                    _write_truth(truth_rows)
                    return
                op_hits = regime_hits = 0
                fdc_errors: list[float] = []
                rho_errors: list[float] = []
                for _ in range(RESAMPLES):
                    rhos = {
                        op: rho1_estimate(keys, fitness, op, rng, m) for op in OPERATORS
                    }
                    picked = max(OPERATORS, key=rhos.__getitem__)
                    op_hits += int(picked == true_operator)
                    rho_errors.append(abs(rhos[picked] - true_rhos[picked]))

                    sample = rng.choice(len(keys), size=min(m, len(keys)), replace=False)
                    estimate = _pearson(
                        fits[sample], distance_columns[OPERATOR_DISTANCE[picked]][sample]
                    )
                    regime_hits += int(regime_of(estimate) == true_regime)
                    fdc_errors.append(abs(estimate - true_fdc))

                writer.writerow(
                    {
                        "landscape": name,
                        "family": record.family,
                        "n": record.n,
                        "probe_m": m,
                        "resamples": RESAMPLES,
                        "operator_agreement": round(op_hits / RESAMPLES, 4),
                        "regime_agreement": round(regime_hits / RESAMPLES, 4),
                        "mean_abs_fdc_error": round(float(np.mean(fdc_errors)), 4),
                        "mean_abs_rho1_error": round(float(np.mean(rho_errors)), 4),
                        "true_operator": true_operator,
                        "true_fdc": round(true_fdc, 4),
                        "true_regime": true_regime,
                        "margin_to_threshold": round(margin, 4),
                        "predicted_flip_rate": round(predicted_flip_rate(true_fdc, m), 4),
                    }
                )
                handle.flush()
            print(f"  {name}: done ({true_operator}, FDC {true_fdc:+.3f}, {true_regime})")

    _write_truth(truth_rows)
    print("SAMPLE COMPLEXITY COMPLETE")


def _write_truth(rows) -> None:
    if not rows:
        return
    with open(TRUTH_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
