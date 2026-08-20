"""Create reproducible Remotion graph extracts from committed experiment artifacts."""

from __future__ import annotations

import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
OUT = ROOT / "src" / "data" / "graphExtracts.json"
MANIFEST = ROOT / "public" / "data" / "graph-manifest.json"


def rows(relative: str) -> list[dict[str, str]]:
    with (REPO / relative).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def number(value: object, default: float | None = None) -> float | None:
    try:
        parsed = float(str(value))
        return parsed if math.isfinite(parsed) else default
    except (TypeError, ValueError):
        return default


def points_from(relative: str, x: str, y: str, series: str | None = None) -> list[dict]:
    output = []
    for row in rows(relative):
        xv, yv = number(row.get(x)), number(row.get(y))
        if xv is None or yv is None:
            continue
        point = {"x": xv, "y": yv}
        if series:
            point["series"] = row.get(series, "series")
        output.append(point)
    return output


def histogram(values: list[float], bins: int = 28) -> list[dict]:
    if not values:
        return []
    lo, hi = min(values), max(values)
    if hi == lo:
        return [{"x": lo, "y": len(values), "label": f"{lo:.3f}"}]
    counts = Counter(min(bins - 1, int((v - lo) / (hi - lo) * bins)) for v in values)
    return [
        {"x": lo + (i + 0.5) * (hi - lo) / bins, "y": counts.get(i, 0), "label": f"bin {i + 1}"}
        for i in range(bins)
    ]


def add(store: dict, ident: str, kind: str, title: str, x_label: str, y_label: str, sample: str, pts: list[dict], artifact: str, summary: str, transforms: list[str] | None = None) -> None:
    store[ident] = {
        "id": ident,
        "kind": kind,
        "title": title,
        "xLabel": x_label,
        "yLabel": y_label,
        "sample": sample,
        "points": pts,
        "source": {
            "artifact": artifact,
            "rowCount": len(rows(artifact.split(";")[0])) if artifact.split(";")[0].endswith(".csv") and (REPO / artifact.split(";")[0]).exists() else len(pts),
            "filters": [],
            "transforms": transforms or ["numeric fields parsed without smoothing"],
            "xAxis": x_label,
            "yAxis": y_label,
        },
        "summary": summary,
    }


def build() -> dict:
    graphs: dict[str, dict] = {}
    add(graphs, "overview-headlines", "bar", "Ordering can matter without guaranteeing search advantage", "evidence panel", "reported range", "three audited observations", [
        {"x": 0, "y": 90.6, "label": "LLM accuracy swing"},
        {"x": 1, "y": 23.1, "label": "SINDy error swing"},
        {"x": 2, "y": 1.0, "label": "random-competitive boundary"},
    ], "PRISM_Remotion_Kokoro_Production_Brief.md", "Headline ranges introduce the distinction between order sensitivity and optimizer advantage.", ["reported summary values only"])

    growth = []
    for n in range(2, 17):
        growth.extend([
            {"x": n, "y": 5**n, "series": "5^n"},
            {"x": n, "y": math.factorial(n), "series": "n factorial"},
        ])
    add(graphs, "T1-search-space", "line", "Search-space growth", "number of slots or items n", "candidate count (log scale)", "n=2…16", growth, "Paper Table 1", "Factorial permutation growth remains rapid even though the component set is fixed.", ["exact combinatorial formulas", "logarithmic y-axis requested"])

    scaling = points_from("prism-research/outputs/scaling_summary.csv", "n", "mean_hit", "objective")
    add(graphs, "T4-scaling", "scatter", "Empirical hitting-time scaling", "permutation size n", "mean hit generation", "14 aggregate cells from 210 runs", scaling, "prism-research/outputs/scaling_summary.csv", "Matched smooth synthetic cases are consistent with the proposed cubic-log trend over the tested range.")

    validation = rows("prism-research/outputs/validation_results.csv")
    add(graphs, "A-validation", "bar", "Historical reproduction outcomes", "task", "best recorded fitness", "five tasks", [
        {"x": i, "y": number(r["best_fitness"], 0), "label": r["problem"]} for i, r in enumerate(validation)
    ], "prism-research/outputs/validation_results.csv", "Headline values reproduce, while the variance audit narrows interpretation.")

    operator = points_from("experiments/iteration-03/results/operator_summary.csv", "n", "mean_hit", "operator")
    add(graphs, "CD-operators", "scatter", "Operator × landscape hitting time", "permutation size n", "mean generations; cap marked separately", "78 aggregate cells from 1,170 runs", operator, "experiments/iteration-03/results/operator_summary.csv", "Matched operators lead while mismatch and deception censor under realistic budgets.")

    flat_rows = rows("experiments/iteration-03/results/toy_v3_results.csv")
    flat = [{"x": i, "y": 0.5, "label": r["problem"]} for i, r in enumerate(flat_rows)]
    add(graphs, "E-flat", "scatter", "Failed all-positions neural redesign", "attempted task", "accuracy", "two task summaries; all stage-one orders reported at 0.500", flat, "experiments/iteration-03/results/toy_v3_results.csv", "The redesigned plain stack has zero useful ordering variance.", ["0.500 reconstructed from recorded stage-one summary", "no connecting trend line"])

    portfolio = points_from("experiments/iteration-04/results/portfolio_summary.csv", "n", "overhead_vs_matched", "mode")
    add(graphs, "F-portfolio", "scatter", "Portfolio overhead versus matched operator", "permutation size n", "overhead ratio", "36 aggregate cells from 540 runs", portfolio, "experiments/iteration-04/results/portfolio_summary.csv", "Uniform portfolio avoids censoring at bounded overhead.")

    v4 = rows("experiments/iteration-05/results/v4_landscape.csv")
    v4_points = [{"x": i, "y": number(r["fitness"], 0), "series": r["problem"]} for i, r in enumerate(v4)]
    add(graphs, "G-landscape", "scatter", "Exact v4 neural landscapes", "enumerated ordering rank", "deterministic fitness", "240 rows: 120 orders for each task", v4_points, "experiments/iteration-05/results/v4_landscape.csv", "XOR and parity have different optimum densities and search difficulty.", ["raw enumerated points sorted only for display"])

    n6 = [number(r["fitness"], 0) for r in rows("experiments/iteration-06/results/n6_landscape.csv")]
    add(graphs, "H-scaleup", "histogram", "Six-block XOR exact landscape", "fitness bin", "ordering count", "720 exact orderings", histogram([v for v in n6 if v is not None]), "experiments/iteration-06/results/n6_landscape.csv", "Dense optima make method comparisons saturate.", ["28-bin histogram of raw fitness"])

    n7 = [number(r["fitness"], 0) for r in rows("experiments/iteration-07/results/n7_parity_landscape.csv")]
    add(graphs, "I-audit", "histogram", "Sparse n=7 parity landscape", "fitness bin", "ordering count", "5,040 exact orderings; 40-seed audit", histogram([v for v in n7 if v is not None], 36), "experiments/iteration-07/results/n7_parity_landscape.csv", "Only fourteen orderings are optimal and audited evolution does not beat random.", ["36-bin histogram of all raw fitness values"])

    locality_rows = rows("experiments/iteration-08/results/locality.csv")
    locality_points = []
    for i, r in enumerate(locality_rows):
        for field in ("rho1_swap", "rho1_insert", "rho1_inversion", "rho1_scramble", "fdc"):
            value = number(r[field])
            if value is not None:
                locality_points.append({"x": i, "y": value, "label": r["landscape"], "series": field})
    add(graphs, "J-locality", "scatter", "Operator-specific locality and F D C", "landscape", "correlation", "eight enumerated landscapes", locality_points, "experiments/iteration-08/results/locality.csv", "Rho one selects neighborhoods while FDC distinguishes guidance from deception.")

    llm = [number(r["fitness"], 0) for r in rows("experiments/iteration-09/results/llm_landscape.csv")]
    add(graphs, "K-llm", "histogram", "Six-module LLM ordering accuracy", "accuracy bin", "ordering count", "720 exact orderings × 32 questions", histogram([v for v in llm if v is not None], 30), "experiments/iteration-09/results/llm_landscape.csv", "Accuracy spans 0.063–0.969 across fixed-wording orderings.", ["30-bin histogram of raw cached fitness"])

    l_rows = rows("experiments/iteration-10/results/improved_search.csv")
    l_points = []
    for i, r in enumerate(l_rows):
        value = number(r.get("evals_to_optimum"))
        if value is not None:
            l_points.append({"x": i, "y": value, "series": r["method"], "label": r["landscape"]})
    add(graphs, "L-methods", "scatter", "Replacement and surrogate variants", "recorded run", "distinct evaluations to optimum", "180 runs", l_points, "experiments/iteration-10/results/improved_search.csv", "Aging improves robustness but does not manufacture locality.")

    m_rows = rows("experiments/iteration-11/results/search_results.csv")
    m_points = [{"x": i, "y": number(r.get("best@120"), 0), "series": r["method"]} for i, r in enumerate(m_rows)]
    add(graphs, "M-eight-module", "bar", "Eight-module sampled search", "method-seed run", "best accuracy by 120 evaluations", "eight search rows; 222 diagnostic orders", m_points, "experiments/iteration-11/results/search_results.csv", "Both methods saturate on a coarse twenty-question evaluator.")

    n_rows = rows("experiments/iteration-12/results/hybrid_surrogate.csv")
    n_points = []
    for i, r in enumerate(n_rows):
        value = number(r.get("evals_to_optimum"))
        if value is not None:
            n_points.append({"x": i, "y": value, "series": r["method"], "label": r["landscape"]})
    add(graphs, "N-surrogate", "scatter", "Encoding-matched surrogate comparison", "recorded run", "distinct evaluations to optimum", "510 runs", n_points, "experiments/iteration-12/results/hybrid_surrogate.csv", "Precedence features produce the decisive Kendall result.")

    add(graphs, "O-transfer", "scatter", "Cross-task versus cross-size transfer", "source score", "target score", "120 neural pairs; 222 LLM candidates", [
        {"x": 0, "y": -0.004, "label": "XOR to parity", "series": "neural"},
        {"x": 1, "y": 0.665, "label": "n=6 to n=8", "series": "LLM"},
    ], "experiments/iteration-16/results/transfer.txt", "Transfer is absent across neural tasks but strong within the LLM instruction family.", ["reported correlation summaries only"])

    sciml = [number(r["fitness"], 0) for r in rows("experiments/iteration-16/results/sciml_landscape.csv")]
    add(graphs, "P-sciml", "histogram", "SINDy pipeline-order landscape", "fitness bin", "pipeline count", "720 exact pipelines", histogram([v for v in sciml if v is not None], 30), "experiments/iteration-16/results/sciml_landscape.csv", "Order changes recovery error greatly even though random is the better executor.")

    add(graphs, "Q-progress", "bar", "Gemma transfer progress at the paper cut", "progress state", "target cells", "212 of 3,840 cells", [
        {"x": 0, "y": 212, "label": "cached"}, {"x": 1, "y": 3628, "label": "remaining"}
    ], "experiments/iteration-17 paper-cut record", "The target experiment is registered but incomplete at Iteration 18.", ["paper-cut progress values only"])

    add(graphs, "R-guided", "bar", "Transfer-guided low-budget evaluation", "budget or group", "reported score", "222 candidates; 12 perfect", [
        {"x": 0, "y": 5, "label": "guided perfect-hit budget"},
        {"x": 1, "y": 0.248, "label": "random probability by five"},
        {"x": 2, "y": 0.900, "label": "transferred top decile"},
        {"x": 3, "y": 0.725, "label": "pool mean"},
    ], "experiments/iteration-18/results/transfer_guided_selection.txt", "Guided ranking yields an early hit, but dense optima make random success plausible.", ["reported summary values only"])

    # Post-paper extracts.
    add(graphs, "EP-S-math", "bar", "MATH-500 method comparison", "method", "mean evaluations to near-best", "250 orders; 31,998 calls", [
        {"x": 0, "y": 32.9, "label": "guided"}, {"x": 1, "y": 37.8, "label": "PRISM"}, {"x": 2, "y": 43.6, "label": "random"}
    ], "experiments/iteration-23-experiment-s/results/experiment_s_report.txt", "Intervals overlap and the sensitivity hypothesis is falsified.", ["reported audited means only"])

    rho = rows("experiments/iteration-22-rho1-ablation/results/rho1_ablation.csv")
    rho_points = []
    for r in rho:
        for budget in (50, 100, 500):
            value = number(r.get(f"acc_B{budget}"))
            if value is not None:
                rho_points.append({"x": budget, "y": value, "series": r["selector"]})
    add(graphs, "EP-I22-rho", "scatter", "Rho-one estimator accuracy", "sample budget", "operator-pick accuracy", "12 aggregate rows; 200 resamples", rho_points, "experiments/iteration-22-rho1-ablation/results/rho1_ablation.csv", "Independent pairs lead at the protocol's low budget.")

    nas = rows("experiments/iteration-21-nasbench-search/results/nasbench_confirmation.csv")
    add(graphs, "EP-I21-nasbench", "bar", "NAS-Bench forecast confirmation", "registered slice", "forecast correct", "18 slices; 40 seeds each", [
        {"x": i, "y": 1 if str(r["forecast_correct"]).lower() in ("1", "true", "yes") else 0, "series": r["level"]} for i, r in enumerate(nas)
    ], "experiments/iteration-21-nasbench-search/results/nasbench_confirmation.csv", "Thirteen of eighteen pre-registered calls are correct.")

    suite = rows("experiments/iteration-20-sciml-suite/results/d23_fdc_comparison.csv")
    add(graphs, "EP-I20-sciml", "bar", "Six-system SciML search margins", "system", "PRISM minus random hits", "six systems; 720 exact orders each", [
        {"x": i, "y": number(r["margin"], 0), "label": r["system"]} for i, r in enumerate(suite)
    ], "experiments/iteration-20-sciml-suite/results/d23_fdc_comparison.csv", "Swap-aligned FDC under-calls insert-friendly systems.")

    add(graphs, "EP-Q-gemma", "bar", "Gemma transfer groups", "source group", "target mean accuracy", "120 target orders", [
        {"x": 0, "y": 0.565, "label": "source top 15"}, {"x": 1, "y": 0.442, "label": "random 100"}, {"x": 2, "y": 0.150, "label": "source bottom 5"}
    ], "experiments/iteration-17/results/slm_transfer_report.txt", "Extremes transfer while fine-grained rank correlation crosses zero.", ["reported bootstrap means only"])

    add(graphs, "EP-Q2-family", "bar", "Cross-family rank transfer", "target model", "Spearman correlation", "120 orders per model", [
        {"x": 0, "y": 0.158, "label": "Gemma"}, {"x": 1, "y": 0.375, "label": "Llama"}, {"x": 2, "y": 0.250, "label": "Qwen"}
    ], "experiments/iteration-19-crossfamily/results/*_transfer_report.txt", "Transfer depends on capability and compresses near ceiling.", ["reported correlations only"])

    t_summary = json.loads((REPO / "experiments/iteration-24-prompt-optimizer-baselines/results/T_RESULTS_SUMMARY.json").read_text(encoding="utf-8"))
    add(graphs, "EP-T-opro", "bar", "PRISM versus OPRO at budget 25", "method", "best accuracy", "five shared seeds", [
        {"x": 0, "y": 0.500, "label": "PRISM"}, {"x": 1, "y": 0.507, "label": "OPRO"}
    ], "experiments/iteration-24-prompt-optimizer-baselines/results/T_RESULTS_SUMMARY.json", "Wording raises mean level while ordering variance persists; final search result is a tie.", ["audited reported means; interval shown in narration"])
    return graphs


def main() -> None:
    graphs = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(graphs, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    manifest = [
        {"id": graph["id"], **graph["source"], "displayedSummary": graph["summary"]}
        for graph in graphs.values()
    ]
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(graphs)} graph extracts and manifest entries")


if __name__ == "__main__":
    main()
