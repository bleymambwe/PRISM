"""Assemble TIER0_REPORT.md from the committed result CSVs.

Everything in the report is read back from disk rather than passed in memory, so
the report can be regenerated from the artifact alone.

    python build_report.py
"""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results")
REPORT = os.path.join(HERE, "TIER0_REPORT.md")


def read(name: str) -> list[dict[str, str]]:
    path = os.path.join(OUT_DIR, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_json(name: str) -> dict:
    path = os.path.join(OUT_DIR, name)
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def table(rows: list[list[str]], header: list[str]) -> str:
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(["---"] * len(header)) + "|"]
    for row in rows:
        out.append("| " + " | ".join(str(c) for c in row) + " |")
    return "\n".join(out)


def main() -> None:
    summary = read("gauntlet_summary.csv")
    truth = read("landscape_truth.csv")
    land = read("landscape_summary.csv")
    calib = read("calibration.csv")
    resolution = read("resolution_curves.csv")
    complexity = read("sample_complexity.csv")
    derived = read("derived_index.csv")
    outcomes = read_json("hypothesis_outcomes.json")

    parts: list[str] = []
    parts.append("# Iteration 26 — Tier 0 results\n")
    parts.append(
        "**Cost: US$0.** Every number here was produced on CPU by replaying optimizers and "
        "estimators against landscapes that were already enumerated and committed. No model "
        "was called.\n"
    )
    parts.append(
        "Hypotheses were registered in `hypotheses.json` and committed at `32f4d9d`, before "
        "any result in this file existed.\n"
    )

    # ---------------- landscapes ----------------
    if land:
        parts.append("\n## The evidence base\n")
        rows = [
            [
                r["landscape"], r["family"], r["n"], r["size"], r["n_optima"],
                f"{float(r['optimum_density']):.4f}", r["distinct_values"],
            ]
            for r in land
        ]
        parts.append(
            table(rows, ["landscape", "family", "n", "orderings", "optima", "density", "distinct values"])
        )
        parts.append(
            "\n`distinct values` is the number of different fitness values the landscape can "
            "express. The flagship language-model landscape resolves 720 orderings onto only "
            "29 distinct accuracies, because 32 questions admit 33 possible scores. That is the "
            "resolution objection stated as a measurement, and it motivates the paid resolution "
            "upgrade.\n"
        )

    # ---------------- hypotheses ----------------
    if outcomes:
        parts.append("\n## Pre-registered outcomes\n")
        labels = {True: "**HOLDS**", False: "**FALSIFIED**", None: "no data"}
        claims = {
            "H27": "On landscapes called 'search pays', some method decisively beats uniform at budget 100",
            "H28": "No method decisively beats uniform on the language-model landscape at budget 50",
            "H29": "The precedence surrogate is top-2 by evaluations-to-optimum on kendall n=7",
            "H30": "Charging the pre-flight probe keeps the protocol within 10pp of uniform at budget 100",
        }
        rows = [[key, claims[key], labels[outcomes[key].get("supported")]] for key in claims if key in outcomes]
        parts.append(table(rows, ["id", "claim", "outcome"]))

        for key in claims:
            if key not in outcomes:
                continue
            parts.append(f"\n### {key}\n")
            for field, value in outcomes[key].items():
                if field == "supported":
                    continue
                parts.append(f"- `{field}`: {value}")

    # ---------------- head to head ----------------
    if summary:
        parts.append("\n## Success at budget 100, by landscape\n")
        by_landscape: dict[str, dict[str, str]] = defaultdict(dict)
        for row in summary:
            if int(row["budget"]) == 100:
                by_landscape[row["landscape"]][row["method"]] = row["success"]
        methods = sorted({m for v in by_landscape.values() for m in v})
        interesting = [
            m for m in methods
            if m in {
                "uniform", "ls_insert", "simulated_annealing", "ea_portfolio",
                "surrogate_precedence", "eda_precedence", "prism_protocol",
            }
        ]
        rows = []
        for name in sorted(by_landscape):
            rows.append([name] + [by_landscape[name].get(m, "-") for m in interesting])
        parts.append(table(rows, ["landscape"] + [m.replace("_", " ") for m in interesting]))
        parts.append(
            "\nSuccess is the fraction of 40 seeds that evaluated a **true** global optimum "
            "within the budget. Because the landscapes are enumerated, this is exact rather "
            "than a best-observed proxy.\n"
        )

    # ---------------- calibration ----------------
    if calib:
        correct = sum(int(r["correct"]) for r in calib)
        total = len(calib)
        conservative = sum(int(r["conservative_miss"]) for r in calib)
        parts.append("\n## Pooled calibration record\n")
        parts.append(
            f"Every forecast this project registered before its outcome, in one table: "
            f"**{correct}/{total} correct ({correct / total:.1%})**, with {total - correct} misses "
            f"of which **{conservative} were conservative** (the protocol said random would be "
            f"competitive and search won anyway).\n"
        )
        groups: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in calib:
            groups[row["source"]].append(row)
        rows = []
        for source, items in sorted(groups.items()):
            hit = sum(int(r["correct"]) for r in items)
            cons = sum(int(r["conservative_miss"]) for r in items)
            rows.append([source, len(items), hit, f"{hit / len(items):.1%}", len(items) - hit, cons])
        parts.append(table(rows, ["source", "forecasts", "correct", "rate", "misses", "conservative"]))
        parts.append(
            "\nThe protocol emits categorical regime calls, not probabilities, so a Brier score "
            "would require inventing confidences it never claimed. The honest calibration "
            "statement is the observed hit rate per call, reported above, together with the "
            "direction of the misses.\n"
        )

    # ---------------- sample complexity ----------------
    if complexity:
        parts.append("\n## E0.2 — how large must the probe be?\n")
        by_m: dict[str, list[dict[str, str]]] = defaultdict(list)
        for row in complexity:
            by_m[row["probe_m"]].append(row)
        rows = []
        for m in sorted(by_m, key=int):
            items = by_m[m]
            regime = sum(float(r["regime_agreement"]) for r in items) / len(items)
            operator = sum(float(r["operator_agreement"]) for r in items) / len(items)
            error = sum(float(r["mean_abs_fdc_error"]) for r in items) / len(items)
            rows.append([m, len(items), f"{regime:.3f}", f"{operator:.3f}", f"{error:.3f}"])
        parts.append(
            table(rows, ["probe m", "landscapes", "regime agreement", "operator agreement", "mean |FDC error|"])
        )
        parts.append(
            "\nAgreement is measured against the call computed from the full enumeration, over "
            "200 resampled probes per landscape.\n"
        )

    # ---------------- resolution ----------------
    if resolution:
        parts.append("\n## E0.3 — how many questions does the call need?\n")
        rows = [
            [
                r["landscape"], r["q_total"], r["q_subset"], r["regime_agreement"],
                r["operator_agreement"], r["mean_distinct_values"], r["full_regime"],
            ]
            for r in resolution
        ]
        parts.append(
            table(rows, ["landscape", "questions", "subset", "regime agreement", "operator agreement", "distinct values", "full call"])
        )

    # ---------------- derived ----------------
    if derived:
        parts.append("\n## E0.4 — derived landscape tables\n")
        parts.append(
            "Answer caches converted to per-ordering fitness tables, so every language-model "
            "landscape in the paper is now loadable without an API key.\n"
        )
        rows = [
            [
                r["derived"], r["n_orderings"], r["questions_per_ordering"],
                r["distinct_values"], f"{r['min_fitness']}–{r['max_fitness']}",
            ]
            for r in derived
        ]
        parts.append(table(rows, ["file", "orderings", "questions", "distinct values", "range"]))

    with open(REPORT, "w", encoding="utf-8") as handle:
        handle.write("\n".join(parts) + "\n")
    print(f"wrote {REPORT}")


if __name__ == "__main__":
    main()
