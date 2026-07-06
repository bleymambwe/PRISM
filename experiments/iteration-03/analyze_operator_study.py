"""Iteration 3: analysis of operator_study_results.csv.

Produces:
- operator_summary.csv   mean/median/censoring per (objective, operator, n)
- operator_ranking.txt   per-landscape operator ranking at each n + H1 verdict
- operator_scaling.txt   log-log exponents per (objective, operator) where
                         >= 4 sizes are (mostly) uncensored
- operator_study.png     hitting time vs n, one panel per landscape
"""

import csv
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.join(os.path.dirname(__file__), "results")
MAX_GENS = 10000
MATCHED = {"hamming": "swap", "kendall": "insert", "adjacency": "inversion"}


def main():
    rows = list(csv.DictReader(open(
        os.path.join(HERE, "operator_study_results.csv"))))
    for r in rows:
        r["n"] = int(r["n"])
        r["hit_generation"] = int(r["hit_generation"])
        r["censored"] = r["censored"] == "True"

    objectives = sorted({r["objective"] for r in rows})
    summary, ranking_lines, scaling_lines = [], [], []

    for obj in objectives:
        obj_rows = [r for r in rows if r["objective"] == obj]
        operators = sorted({r["operator"] for r in obj_rows})
        ns = sorted({r["n"] for r in obj_rows})
        ranking_lines.append(f"\n=== {obj} (matched operator per "
                             f"literature: {MATCHED.get(obj, 'n/a')}) ===")
        for n in ns:
            stats = {}
            for op in operators:
                sub = [r for r in obj_rows
                       if r["operator"] == op and r["n"] == n]
                hits = [r["hit_generation"] for r in sub]
                cens = sum(r["censored"] for r in sub)
                stats[op] = (np.mean(hits), cens, len(sub))
                summary.append({
                    "objective": obj, "operator": op, "n": n,
                    "mean_hit": round(float(np.mean(hits)), 1),
                    "median_hit": float(np.median(hits)),
                    "censored": cens, "runs": len(sub),
                })
            order = sorted(stats, key=lambda o: stats[o][0])
            desc = " < ".join(
                f"{o}({stats[o][0]:.0f}{'*' if stats[o][1] else ''})"
                for o in order)
            ranking_lines.append(f"n={n:<3} {desc}")
        # H1 verdict at largest informative n
        big = max(ns)
        best = min(operators, key=lambda o: np.mean(
            [r["hit_generation"] for r in obj_rows
             if r["operator"] == o and r["n"] == big]))
        m = MATCHED.get(obj)
        if m:
            verdict = "MATCHES" if best == m else f"DIFFERS (best={best})"
            ranking_lines.append(
                f"H1 at n={big}: literature-matched '{m}' vs empirical "
                f"best '{best}' -> {verdict}")

        # scaling exponents for operators with <=20% censoring overall
        for op in operators:
            pts = []
            for n in ns:
                sub = [r for r in obj_rows
                       if r["operator"] == op and r["n"] == n]
                unc = [r["hit_generation"] for r in sub
                       if not r["censored"]]
                if len(unc) >= 0.8 * len(sub) and np.mean(unc) > 0:
                    pts.append((n, np.mean(unc)))
            if len(pts) >= 4:
                xs, ys = zip(*pts)
                a, _ = np.polyfit(np.log(xs), np.log(ys), 1)
                scaling_lines.append(
                    f"{obj:<10} {op:<10} exponent {a:5.2f} over n={list(xs)}")

    with open(os.path.join(HERE, "operator_summary.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    with open(os.path.join(HERE, "operator_ranking.txt"), "w") as f:
        f.write("\n".join(ranking_lines) + "\n")
    with open(os.path.join(HERE, "operator_scaling.txt"), "w") as f:
        f.write("\n".join(scaling_lines) + "\n")

    # plot
    typed = [o for o in objectives if o in MATCHED]
    fig, axes = plt.subplots(1, len(typed), figsize=(5 * len(typed), 4.5),
                             sharey=True)
    colors = {"swap": "#2E86AB", "insert": "#A23B72",
              "inversion": "#F18F01", "scramble": "#5B7553"}
    for ax, obj in zip(np.atleast_1d(axes), typed):
        obj_rows = [r for r in rows if r["objective"] == obj]
        ns = sorted({r["n"] for r in obj_rows})
        for op in sorted({r["operator"] for r in obj_rows}):
            means = [np.mean([r["hit_generation"] for r in obj_rows
                              if r["operator"] == op and r["n"] == n])
                     for n in ns]
            ax.plot(ns, means, "o-", color=colors[op],
                    label=op + (" (matched)" if MATCHED[obj] == op else ""))
        ax.axhline(MAX_GENS, color="gray", ls=":", lw=1)
        ax.set_yscale("log")
        ax.set_title(f"{obj} landscape")
        ax.set_xlabel("n")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    np.atleast_1d(axes)[0].set_ylabel("Mean generations to optimum "
                                      "(cap 20000)")
    plt.tight_layout()
    plt.savefig(os.path.join(HERE, "operator_study.png"), dpi=150,
                bbox_inches="tight")

    print("\n".join(ranking_lines))
    print()
    print("\n".join(scaling_lines))


if __name__ == "__main__":
    main()
