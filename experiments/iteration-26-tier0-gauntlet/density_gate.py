"""Exploratory (NOT pre-registered): does optimum density gate whether search can pay?

The gauntlet produced a pattern the pre-registration did not anticipate.  Every
landscape the protocol called "search pays" but where no method decisively beat
uniform sampling is a landscape with *many* optima; every landscape where search
did win decisively has very few.  If that separation is real, then
fitness-distance correlation under-specifies the regime, because a landscape can
be well-guided and still leave nothing to win -- uniform sampling stumbles onto
one of the many optima almost immediately.

This script tests the separation and reports it honestly as post-hoc.  It is
hypothesis-generating: it needs confirmation on landscapes not used to find it.

    python density_gate.py
"""

from __future__ import annotations

import csv
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results")
OUT_CSV = os.path.join(OUT_DIR, "density_gate.csv")


def wilson(successes: int, trials: int, z: float = 1.96) -> tuple[float, float, float]:
    if trials == 0:
        return (float("nan"),) * 3
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    margin = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return p, max(0.0, centre - margin), min(1.0, centre + margin)


def read(name: str) -> list[dict[str, str]]:
    with open(os.path.join(OUT_DIR, name), newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    runs = read("gauntlet_runs.csv")
    land = {r["landscape"]: r for r in read("landscape_summary.csv")}
    truth = {r["landscape"]: r for r in read("landscape_truth.csv")}

    # success counts at the smallest budget where the landscape is not saturated
    by_key: dict[tuple[str, str, int], list[int]] = {}
    for row in runs:
        for b in (15, 25, 50, 100):
            by_key.setdefault((row["landscape"], row["method"], b), []).append(
                int(row[f"hit_by_{b}"])
            )

    rows = []
    for name in sorted(land):
        density = float(land[name]["optimum_density"])
        fdc = float(truth[name]["true_fdc"])
        regime = truth[name]["true_regime"]

        # the informative budget: the largest budget at which uniform has not saturated
        chosen_budget = None
        for b in (15, 25, 50, 100):
            u = by_key.get((name, "uniform", b))
            if u and sum(u) / len(u) < 0.975:
                chosen_budget = b
        if chosen_budget is None:
            chosen_budget = 15

        u = by_key[(name, "uniform", chosen_budget)]
        u_point, _, u_high = wilson(sum(u), len(u))
        winners = []
        for method in sorted({r["method"] for r in runs}):
            if method == "uniform":
                continue
            values = by_key.get((name, method, chosen_budget))
            if not values:
                continue
            point, low, _ = wilson(sum(values), len(values))
            if low > u_high:
                winners.append(method)

        rows.append(
            {
                "landscape": name,
                "family": land[name]["family"],
                "size": land[name]["size"],
                "n_optima": land[name]["n_optima"],
                "optimum_density": round(density, 5),
                "distinct_values": land[name]["distinct_values"],
                "fdc": round(fdc, 4),
                "regime_call": regime,
                "informative_budget": chosen_budget,
                "uniform_success": round(u_point, 3),
                "n_decisive_winners": len(winners),
                "search_decisively_won": int(len(winners) > 0),
            }
        )

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    won = [r for r in rows if r["search_decisively_won"]]
    lost = [r for r in rows if not r["search_decisively_won"]]
    print(f"{len(won)} landscapes where search decisively won, {len(lost)} where it did not\n")

    print(f"{'landscape':<26}{'density':>10}{'FDC':>9}{'call':>20}{'search won':>12}")
    print("-" * 77)
    for row in sorted(rows, key=lambda r: r["optimum_density"]):
        print(
            f"{row['landscape']:<26}{row['optimum_density']:>10.5f}{row['fdc']:>9.3f}"
            f"{row['regime_call']:>20}{'YES' if row['search_decisively_won'] else 'no':>12}"
        )

    if won and lost:
        max_won = max(r["optimum_density"] for r in won)
        min_lost = min(r["optimum_density"] for r in lost)
        print(f"\nhighest density where search won : {max_won:.5f}")
        print(f"lowest  density where it did not : {min_lost:.5f}")
        print(
            "NO clean separation on optimum density alone -- the initial pattern does not survive."
            if max_won >= min_lost
            else "separation is clean"
        )

    if won and lost:
        worst_won_fdc = max(r["fdc"] for r in won)
        best_lost_fdc = min(r["fdc"] for r in lost)
        print(
            f"FDC alone: worst 'won' = {worst_won_fdc:+.3f}, best 'did not win' = "
            f"{best_lost_fdc:+.3f} -> does NOT separate either"
        )

    # ---- the finding that does survive: what explains the WRONG calls? ----
    predicted_search = [r for r in rows if r["regime_call"] == "search_pays"]
    false_positives = [r for r in predicted_search if not r["search_decisively_won"]]
    true_positives = [r for r in predicted_search if r["search_decisively_won"]]
    conservative = [
        r for r in rows
        if r["regime_call"] != "search_pays" and r["search_decisively_won"]
    ]

    print("\n" + "=" * 77)
    print("WHERE THE PROTOCOL WAS WRONG")
    print("=" * 77)
    print(
        f"'search pays' calls: {len(predicted_search)} "
        f"({len(true_positives)} correct, {len(false_positives)} wrong)"
    )
    for row in sorted(false_positives, key=lambda r: -r["optimum_density"]):
        print(
            f"   WRONG  {row['landscape']:<24} density={row['optimum_density']:.4f} "
            f"distinct_values={row['distinct_values']:>3} uniform_success={row['uniform_success']}"
        )
    print(f"conservative misses (said random, search won): {len(conservative)}")
    for row in conservative:
        print(f"   cons.  {row['landscape']:<24} FDC={row['fdc']:+.3f}")

    if false_positives and true_positives:
        fp_min_density = min(r["optimum_density"] for r in false_positives)
        tp_max_density = max(r["optimum_density"] for r in true_positives)
        print(
            f"\nAmong 'search pays' calls only: every wrong call has optimum density "
            f">= {fp_min_density:.4f}; every correct one has density <= {tp_max_density:.4f}."
        )
        if fp_min_density > tp_max_density:
            print(
                "   Within this subset the separation IS clean, so density is a candidate "
                "SECOND gate on the 'search pays' branch -- but it is post-hoc, rests on "
                f"{len(predicted_search)} landscapes, and needs held-out confirmation."
            )


if __name__ == "__main__":
    main()
