"""E0.1/E0.5 analysis: summarise the gauntlet and score the pre-registered claims.

Reads the (possibly sharded) gauntlet runs, produces per-landscape and
per-method summaries with Wilson intervals, decides each pre-registered
hypothesis against its registered threshold, and writes the pooled calibration
record.

    python analyze.py
"""

from __future__ import annotations

import csv
import glob
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_DIR = os.path.join(HERE, "results")

BUDGET_GRID = (15, 25, 50, 100, 200)
UNIFORM = "uniform"
PROTOCOL = "prism_protocol"
GUIDING_THRESHOLD = -0.15


def wilson(successes: int, trials: int, z: float = 1.96) -> tuple[float, float, float]:
    """Wilson score interval; returns (point, low, high)."""

    if trials == 0:
        return (float("nan"),) * 3
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return p, max(0.0, centre - margin), min(1.0, centre + margin)


def load_runs() -> list[dict[str, str]]:
    """Prefer the merged file; fall back to shards only if it is absent.

    Globbing both would count every run twice, which silently halves the width
    of every confidence interval.
    """

    merged = os.path.join(OUT_DIR, "gauntlet_runs.csv")
    paths = (
        [merged]
        if os.path.exists(merged)
        else sorted(glob.glob(os.path.join(OUT_DIR, "gauntlet_runs_shard*.csv")))
    )
    rows: list[dict[str, str]] = []
    seen: set[tuple[str, str, str]] = set()
    for path in paths:
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                key = (row["landscape"], row["method"], row["seed"])
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
    return rows


def load_truth() -> dict[str, dict[str, str]]:
    path = os.path.join(OUT_DIR, "landscape_truth.csv")
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as handle:
        return {row["landscape"]: row for row in csv.DictReader(handle)}


def main() -> None:
    runs = load_runs()
    if not runs:
        print("no gauntlet runs found")
        return
    truth = load_truth()

    # ---- aggregate: (landscape, method, budget) -> successes / values ----
    hits: dict[tuple[str, str, int], list[int]] = defaultdict(list)
    bests: dict[tuple[str, str, int], list[float]] = defaultdict(list)
    aucs: dict[tuple[str, str], list[float]] = defaultdict(list)
    evals_to_hit: dict[tuple[str, str], list[int]] = defaultdict(list)
    families: dict[str, str] = {}

    for row in runs:
        landscape, method = row["landscape"], row["method"]
        families[landscape] = row["family"]
        aucs[(landscape, method)].append(float(row["auc"]))
        if row["hit"]:
            evals_to_hit[(landscape, method)].append(int(row["hit"]))
        for b in BUDGET_GRID:
            hits[(landscape, method, b)].append(int(row[f"hit_by_{b}"]))
            bests[(landscape, method, b)].append(float(row[f"best_at_{b}"]))

    landscapes = sorted({r["landscape"] for r in runs})
    methods = sorted({r["method"] for r in runs})

    # ---- per (landscape, method, budget) summary ----
    summary_path = os.path.join(OUT_DIR, "gauntlet_summary.csv")
    with open(summary_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "landscape", "family", "method", "budget", "seeds",
                "success", "success_low", "success_high",
                "mean_best", "mean_auc", "mean_evals_to_hit", "n_hits",
            ]
        )
        for landscape in landscapes:
            for method in methods:
                for b in BUDGET_GRID:
                    key = (landscape, method, b)
                    if key not in hits:
                        continue
                    values = hits[key]
                    point, low, high = wilson(sum(values), len(values))
                    reached = evals_to_hit.get((landscape, method), [])
                    writer.writerow(
                        [
                            landscape, families[landscape], method, b, len(values),
                            round(point, 4), round(low, 4), round(high, 4),
                            round(sum(bests[key]) / len(bests[key]), 6),
                            round(sum(aucs[(landscape, method)]) / len(aucs[(landscape, method)]), 6),
                            round(sum(reached) / len(reached), 2) if reached else "",
                            len(reached),
                        ]
                    )

    # ---- head-to-head against uniform, and the calibration record ----
    verdicts: list[dict[str, object]] = []
    calibration_rows: list[dict[str, object]] = []
    for landscape in landscapes:
        for b in (50, 100):
            u = hits.get((landscape, UNIFORM, b))
            if not u:
                continue
            _, u_low, u_high = wilson(sum(u), len(u))
            winners = []
            for method in methods:
                if method == UNIFORM:
                    continue
                values = hits.get((landscape, method, b))
                if not values:
                    continue
                point, low, high = wilson(sum(values), len(values))
                if low > u_high:
                    winners.append((method, round(point, 3)))
            verdicts.append(
                {
                    "landscape": landscape,
                    "budget": b,
                    "uniform": round(sum(u) / len(u), 3),
                    "decisive_winners": ";".join(f"{m}={p}" for m, p in winners),
                    "n_winners": len(winners),
                }
            )

        record = truth.get(landscape)
        if record:
            fdc = float(record["true_fdc"])
            forecast = record["true_regime"]
            u100 = hits.get((landscape, UNIFORM, 100), [])
            search_won = any(
                wilson(sum(hits[(landscape, m, 100)]), len(hits[(landscape, m, 100)]))[1]
                > wilson(sum(u100), len(u100))[2]
                for m in methods
                if m != UNIFORM and (landscape, m, 100) in hits
            ) if u100 else False
            predicted_search = forecast == "search_pays"
            calibration_rows.append(
                {
                    "source": "gauntlet_landscape",
                    "item": landscape,
                    "forecast": forecast,
                    "predicted_search_wins": int(predicted_search),
                    "observed_search_wins": int(search_won),
                    "correct": int(predicted_search == search_won),
                    "conservative_miss": int(
                        predicted_search != search_won and not predicted_search
                    ),
                    "statistic": round(fdc, 4),
                }
            )

    with open(os.path.join(OUT_DIR, "head_to_head.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(verdicts[0].keys()))
        writer.writeheader()
        writer.writerows(verdicts)

    # ---- fold in the 18 NAS-Bench forecasts registered in Iteration 21 ----
    nas_path = os.path.join(
        ROOT, "experiments/iteration-21-nasbench-search/results/nasbench_confirmation.csv"
    )
    if os.path.exists(nas_path):
        with open(nas_path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                predicted = row["level"] == "HIGH"
                observed = row["search_wins"] == "True"
                calibration_rows.append(
                    {
                        "source": "nasbench_slice",
                        "item": f"{row['dataset']}|{row['distribution']}",
                        "forecast": "search_pays" if predicted else "random_competitive",
                        "predicted_search_wins": int(predicted),
                        "observed_search_wins": int(observed),
                        "correct": int(predicted == observed),
                        "conservative_miss": int(predicted != observed and not predicted),
                        "statistic": round(float(row["fdc"]), 4),
                    }
                )

    with open(os.path.join(OUT_DIR, "calibration.csv"), "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(calibration_rows[0].keys()))
        writer.writeheader()
        writer.writerows(calibration_rows)

    # ---- score the pre-registered hypotheses ----
    results = score_hypotheses(hits, evals_to_hit, truth, landscapes, methods)
    with open(os.path.join(OUT_DIR, "hypothesis_outcomes.json"), "w", encoding="utf-8") as handle:
        json.dump(results, handle, indent=2)

    _print_report(runs, landscapes, methods, hits, verdicts, calibration_rows, results)


def score_hypotheses(hits, evals_to_hit, truth, landscapes, methods) -> dict[str, object]:
    out: dict[str, object] = {}

    # H27: on 'search pays' landscapes, some method decisively beats uniform @100
    search_pays = [
        name for name in landscapes
        if truth.get(name, {}).get("true_regime") == "search_pays"
    ]
    h27_detail = {}
    for name in search_pays:
        u = hits.get((name, UNIFORM, 100), [])
        if not u:
            continue
        u_high = wilson(sum(u), len(u))[2]
        winners = [
            m for m in methods
            if m != UNIFORM and (name, m, 100) in hits
            and wilson(sum(hits[(name, m, 100)]), len(hits[(name, m, 100)]))[1] > u_high
        ]
        h27_detail[name] = winners
    out["H27"] = {
        "landscapes_called_search_pays": search_pays,
        "decisive_winners_by_landscape": h27_detail,
        "supported": any(v for v in h27_detail.values()),
    }

    # H28: no method decisively beats uniform on the LLM landscape @50
    name = "llm_gsm8k_n6"
    u = hits.get((name, UNIFORM, 50), [])
    h28_winners = []
    if u:
        u_high = wilson(sum(u), len(u))[2]
        h28_winners = [
            m for m in methods
            if m != UNIFORM and (name, m, 50) in hits
            and wilson(sum(hits[(name, m, 50)]), len(hits[(name, m, 50)]))[1] > u_high
        ]
    out["H28"] = {
        "uniform_success_at_50": round(sum(u) / len(u), 4) if u else None,
        "decisive_winners": h28_winners,
        "supported": len(h28_winners) == 0,
    }

    # H29: precedence surrogate top-2 by evals-to-optimum on kendall_n7
    name = "kendall_n7"
    ranking = sorted(
        (
            (m, sum(v) / len(v))
            for (ln, m), v in evals_to_hit.items()
            if ln == name and v and m != UNIFORM
        ),
        key=lambda item: item[1],
    )
    out["H29"] = {
        "ranking_by_mean_evals_to_optimum": [(m, round(v, 2)) for m, v in ranking[:5]],
        "supported": any(m == "surrogate_precedence" for m, _ in ranking[:2]),
    }

    # H30: protocol within 10pp of uniform @100 everywhere
    gaps = {}
    for name in landscapes:
        u = hits.get((name, UNIFORM, 100), [])
        p = hits.get((name, PROTOCOL, 100), [])
        if u and p:
            gaps[name] = round(sum(p) / len(p) - sum(u) / len(u), 4)
    out["H30"] = {
        "protocol_minus_uniform_at_100": gaps,
        "worst": min(gaps.values()) if gaps else None,
        "supported": all(v >= -0.10 for v in gaps.values()) if gaps else None,
    }

    # H31: regime accuracy >= 0.90 at m=200 where |FDC - threshold| >= 0.10
    complexity = _read("sample_complexity.csv")
    clear = [
        r for r in complexity
        if int(r["probe_m"]) == 200 and float(r["margin_to_threshold"]) >= 0.10
    ]
    if clear:
        worst = min(float(r["regime_agreement"]) for r in clear)
        out["H31"] = {
            "clear_margin_landscapes": len(clear),
            "mean_regime_agreement_at_m200": round(
                sum(float(r["regime_agreement"]) for r in clear) / len(clear), 4
            ),
            "worst_landscape": min(clear, key=lambda r: float(r["regime_agreement"]))["landscape"],
            "worst_agreement": worst,
            "supported": worst >= 0.90,
        }

    # H32: operator agreement >= 0.90 at m>=100 on typed synthetics
    typed = [
        r for r in complexity
        if r["family"] == "synthetic"
        and r["landscape"] != "deceptive_n7"
        and int(r["probe_m"]) >= 100
    ]
    if typed:
        by_m: dict[int, list[float]] = {}
        for r in typed:
            by_m.setdefault(int(r["probe_m"]), []).append(float(r["operator_agreement"]))
        at_100 = [float(r["operator_agreement"]) for r in typed if int(r["probe_m"]) == 100]
        out["H32"] = {
            "typed_synthetics": sorted({r["landscape"] for r in typed}),
            "operator_agreement_by_m": {m: round(sum(v) / len(v), 4) for m, v in sorted(by_m.items())},
            "worst_at_m100": min(at_100) if at_100 else None,
            "supported": bool(at_100) and min(at_100) >= 0.90,
        }

    # H33: LLM regime call unstable below q=16 (agreement < 0.80 at q=8)
    resolution = _read("resolution_curves.csv")
    flagship = [
        r for r in resolution
        if r["landscape"] == "llm_gsm8k_n6" and int(r["q_subset"]) == 8
    ]
    if flagship:
        agreement = float(flagship[0]["regime_agreement"])
        others = {
            r["landscape"]: float(r["regime_agreement"])
            for r in resolution
            if int(r["q_subset"]) == 8
        }
        out["H33"] = {
            "flagship_agreement_at_q8": agreement,
            "all_landscapes_at_q8": others,
            "supported": agreement < 0.80,
        }
    return out


def _read(name: str) -> list[dict[str, str]]:
    path = os.path.join(OUT_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _print_report(runs, landscapes, methods, hits, verdicts, calibration_rows, results) -> None:
    print(f"\n{len(runs)} runs | {len(landscapes)} landscapes | {len(methods)} methods\n")
    print("=" * 78)
    print("PRE-REGISTERED HYPOTHESES")
    print("=" * 78)
    for key in ("H27", "H28", "H29", "H30", "H31", "H32", "H33"):
        if key not in results:
            continue
        block = results[key]
        verdict = block.get("supported")
        label = {True: "HOLDS", False: "FALSIFIED", None: "no data"}[verdict]
        print(f"\n{key}: {label}")
        for field, value in block.items():
            if field == "supported":
                continue
            print(f"   {field}: {value}")

    correct = sum(r["correct"] for r in calibration_rows)
    total = len(calibration_rows)
    conservative = sum(r["conservative_miss"] for r in calibration_rows)
    print("\n" + "=" * 78)
    print("POOLED CALIBRATION")
    print("=" * 78)
    print(f"   {correct}/{total} forecasts correct ({correct / total:.1%})")
    print(f"   misses: {total - correct}, of which conservative: {conservative}")


if __name__ == "__main__":
    main()
