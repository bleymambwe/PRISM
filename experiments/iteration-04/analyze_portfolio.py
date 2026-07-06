"""Iteration 4: analysis of Experiment F vs Iteration-3 baselines.

Produces:
- portfolio_summary.csv     per (objective, mode, n) aggregates
- portfolio_vs_fixed.txt    matched / portfolio / adaptive / worst-fixed
                            comparison with overhead ratios
- adaptive_weights.txt      mean final operator weights per landscape
- portfolio_study.png       hitting time vs n, portfolio modes overlaid
                            on fixed-operator baselines
"""

import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(__file__)
RES = os.path.join(HERE, "results")
IT3 = os.path.join(HERE, "..", "iteration-03", "results",
                   "operator_study_results.csv")
MATCHED = {"hamming": "swap", "kendall": "insert", "adjacency": "inversion"}
NS = [6, 8, 10, 12, 14, 16]
MAX_GENS = 10000


def load(path, key_field):
    rows = list(csv.DictReader(open(path)))
    for r in rows:
        r["n"] = int(r["n"])
        r["hit_generation"] = int(r["hit_generation"])
        r["censored"] = r["censored"] == "True"
        r["group"] = r[key_field]
    return rows


def mean_hit(rows, obj, group, n):
    sub = [r for r in rows if r["objective"] == obj
           and r["group"] == group and r["n"] == n]
    if not sub:
        return None, 0, 0
    return (float(np.mean([r["hit_generation"] for r in sub])),
            sum(r["censored"] for r in sub), len(sub))


def main():
    pf = load(os.path.join(RES, "portfolio_results.csv"), "mode")
    fx = load(IT3, "operator")

    summary, lines, weight_lines = [], [], []
    for obj in MATCHED:
        m_op = MATCHED[obj]
        lines.append(f"\n=== {obj} (matched fixed operator: {m_op}) ===")
        lines.append(f"{'n':<4} {'matched':>9} {'portfolio':>10} "
                     f"{'adaptive':>9} {'worst-fixed':>12} "
                     f"{'pf/matched':>11} {'ad/matched':>11}")
        for n in NS:
            m, mc, _ = mean_hit(fx, obj, m_op, n)
            p, pc, _ = mean_hit(pf, obj, "portfolio", n)
            a, ac, _ = mean_hit(pf, obj, "adaptive", n)
            worst = max(
                (mean_hit(fx, obj, op, n)[0] or 0)
                for op in ("swap", "insert", "inversion", "scramble"))
            lines.append(
                f"{n:<4} {m:>9.0f} {p:>9.0f}{'*' if pc else ' '} "
                f"{a:>8.0f}{'*' if ac else ' '} {worst:>12.0f} "
                f"{p / m:>11.1f} {a / m:>11.1f}")
            for mode, val, cens in (("portfolio", p, pc),
                                    ("adaptive", a, ac)):
                summary.append({"objective": obj, "mode": mode, "n": n,
                                "mean_hit": round(val, 1),
                                "matched_mean": round(m, 1),
                                "overhead_vs_matched": round(val / m, 2),
                                "censored": cens})
        # adaptive final weights (uncensored runs)
        wsum = {}
        for r in pf:
            if (r["objective"] == obj and r["group"] == "adaptive"
                    and not r["censored"]):
                for op, w in json.loads(r["operator_weights"]).items():
                    wsum.setdefault(op, []).append(w)
        means = {op: np.mean(v) for op, v in wsum.items()}
        top = max(means, key=means.get)
        weight_lines.append(
            f"{obj:<10} mean final weights: "
            + ", ".join(f"{op}={means[op]:.3f}" for op in means)
            + f" -> top: {top} "
            + ("(= matched)" if top == m_op else f"(matched is {m_op})"))

    with open(os.path.join(RES, "portfolio_summary.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary[0].keys()))
        w.writeheader()
        w.writerows(summary)
    with open(os.path.join(RES, "portfolio_vs_fixed.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(RES, "adaptive_weights.txt"), "w") as f:
        f.write("\n".join(weight_lines) + "\n")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5), sharey=True)
    for ax, obj in zip(axes, MATCHED):
        m_op = MATCHED[obj]
        for group, rows, style, color in (
                (m_op + " (matched fixed)", fx, "o-", "#2E86AB"),
                ("portfolio", pf, "s--", "#A23B72"),
                ("adaptive", pf, "d--", "#F18F01")):
            g = group.split(" ")[0] if "fixed" in group else group
            means = [mean_hit(rows, obj, g, n)[0] for n in NS]
            ax.plot(NS, means, style, color=color, label=group)
        ax.axhline(MAX_GENS, color="gray", ls=":", lw=1)
        ax.set_yscale("log")
        ax.set_title(f"{obj} landscape")
        ax.set_xlabel("n")
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Mean generations to optimum")
    plt.tight_layout()
    plt.savefig(os.path.join(RES, "portfolio_study.png"), dpi=150,
                bbox_inches="tight")

    print("\n".join(lines))
    print()
    print("\n".join(weight_lines))


if __name__ == "__main__":
    main()
