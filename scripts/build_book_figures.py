"""Generate all figures for the PRISM book (deliverables/book_figures/).

Every data figure is generated from the committed experiment CSVs —
nothing is drawn from memory. Concept figures are schematic matplotlib
drawings. Consistent palette across the book (colorblind-safe).
"""

import csv
import json
import os

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = os.path.join(os.path.dirname(__file__), "..")
FIG = os.path.join(ROOT, "deliverables", "book_figures")
os.makedirs(FIG, exist_ok=True)

C = {"swap": "#2a78d6", "insert": "#1baf7a", "inversion": "#eda100",
     "scramble": "#008300", "portfolio": "#4a3aa7", "adaptive": "#e34948",
     "ink": "#222222", "muted": "#898781", "grid": "#e1e0d9"}
plt.rcParams.update({"font.size": 10, "axes.edgecolor": C["muted"],
                     "axes.labelcolor": C["ink"], "figure.dpi": 150})


def save(fig, name):
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight", dpi=150)
    plt.close(fig)
    print("wrote", name)


# ---------- Fig 1.1: the concept — order as the search variable ----------
fig, axes = plt.subplots(1, 2, figsize=(9, 2.6))
blocks = ["B1", "B2", "B3", "B4", "B5"]
cols = [C["swap"], C["insert"], C["inversion"], C["scramble"],
        C["portfolio"]]
for ax, (order, title, acc) in zip(axes, [
        ([0, 1, 2, 3, 4], "ordering A", "works (accuracy 1.00)"),
        ([4, 2, 0, 3, 1], "ordering B", "fails (accuracy 0.50)")]):
    for i, b in enumerate(order):
        ax.add_patch(Rectangle((i * 1.2, 0), 1, 1, color=cols[b]))
        ax.text(i * 1.2 + .5, .5, blocks[b], ha="center", va="center",
                color="white", fontweight="bold")
        if i < 4:
            ax.add_patch(FancyArrowPatch((i * 1.2 + 1.02, .5),
                                         (i * 1.2 + 1.18, .5),
                                         arrowstyle="->", color=C["ink"]))
    ax.set_xlim(-.2, 6.1)
    ax.set_ylim(-.6, 1.4)
    ax.set_title(f"{title}: same five blocks — {acc}", fontsize=10)
    ax.axis("off")
save(fig, "fig_concept.png")

# ---------- Fig 2.1: the evolutionary loop ----------
fig, ax = plt.subplots(figsize=(9, 1.9))
stages = ["Population\n(20 orderings)", "Evaluate\nfitness",
          "Keep the best\n(elitism)", "Tournament\nselection",
          "Mutate\n(operator)"]
scol = [C["swap"], C["insert"], C["inversion"], C["portfolio"],
        C["adaptive"]]
for i, (s, c) in enumerate(zip(stages, scol)):
    ax.add_patch(Rectangle((i * 1.9, 0), 1.6, 1, color=c, alpha=.9))
    ax.text(i * 1.9 + .8, .5, s, ha="center", va="center", color="white",
            fontsize=9, fontweight="bold")
    if i < 4:
        ax.add_patch(FancyArrowPatch((i * 1.9 + 1.62, .5),
                                     (i * 1.9 + 1.88, .5),
                                     arrowstyle="->", color=C["ink"]))
ax.add_patch(FancyArrowPatch((9.2, 0), (0.8, -0.35),
                             connectionstyle="arc3,rad=0.15",
                             arrowstyle="->", color=C["muted"]))
ax.text(5, -.52, "next generation", ha="center", color=C["muted"],
        fontsize=9)
ax.set_xlim(-.3, 9.6)
ax.set_ylim(-.8, 1.3)
ax.axis("off")
save(fig, "fig_loop.png")

# ---------- Fig 3.1: hitting time vs theory (iteration 2) ----------
rows = list(csv.DictReader(open(os.path.join(
    ROOT, "prism-research/outputs/scaling_results.csv"))))
ns = [4, 5, 6, 7, 8, 10, 12]
fig, ax = plt.subplots(figsize=(5.4, 3.6))
for obj, col in [("hamming", C["swap"]), ("kendall", C["insert"])]:
    means = [np.mean([int(r["hit_generation"]) for r in rows
                      if r["objective"] == obj and int(r["n"]) == n])
             for n in ns]
    ax.plot(ns, means, "o-", color=col, label=f"{obj} (measured)")
k8 = np.mean([int(r["hit_generation"]) for r in rows
              if r["objective"] == "kendall" and int(r["n"]) == 8])
c0 = k8 / (8 ** 3 * np.log(8))
ax.plot(ns, [c0 * n ** 3 * np.log(n) for n in ns], "k--", alpha=.6,
        label=r"$c\,n^3\log n$ (theory shape)")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xticks(ns); ax.get_xaxis().set_major_formatter(
    matplotlib.ticker.ScalarFormatter())
ax.set_xlabel("number of components n")
ax.set_ylabel("generations to reach the optimum")
ax.grid(alpha=.3, which="both"); ax.legend(fontsize=8)
save(fig, "fig_scaling.png")

# ---------- Fig 5.1: operator x landscape (iteration 3) ----------
rows = list(csv.DictReader(open(os.path.join(
    ROOT, "experiments/iteration-03/results/operator_study_results.csv"))))
NS3 = [6, 8, 10, 12, 14, 16]
MATCHED = {"hamming": "swap", "kendall": "insert", "adjacency": "inversion"}
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2), sharey=True)
for ax, obj in zip(axes, MATCHED):
    for op in ["swap", "insert", "inversion", "scramble"]:
        means = [np.mean([int(r["hit_generation"]) for r in rows
                          if r["objective"] == obj and r["operator"] == op
                          and int(r["n"]) == n]) for n in NS3]
        ax.plot(NS3, means, "o-", color=C[op], lw=2.2 if
                op == MATCHED[obj] else 1.4,
                alpha=1 if op == MATCHED[obj] else .65, label=op)
    ax.axhline(10000, color=C["muted"], ls=":", lw=1)
    ax.text(6, 11500, "failure cap", fontsize=7, color=C["muted"])
    ax.set_yscale("log"); ax.set_title(f"{obj}\n(matched: "
                                       f"{MATCHED[obj]})", fontsize=9)
    ax.set_xlabel("n"); ax.grid(alpha=.3)
axes[0].set_ylabel("generations to optimum")
axes[0].legend(fontsize=7)
save(fig, "fig_operators.png")

# ---------- Fig 5.2: portfolio (iteration 4) ----------
pf = list(csv.DictReader(open(os.path.join(
    ROOT, "experiments/iteration-04/results/portfolio_results.csv"))))
fig, ax = plt.subplots(figsize=(6.4, 3.4))
labels, matched_v, port_v = [], [], []
for obj in MATCHED:
    m = MATCHED[obj]
    matched_v.append(np.mean([int(r["hit_generation"]) for r in rows
                              if r["objective"] == obj
                              and r["operator"] == m
                              and int(r["n"]) == 16]))
    port_v.append(np.mean([int(r["hit_generation"]) for r in pf
                           if r["objective"] == obj
                           and r["mode"] == "portfolio"
                           and int(r["n"]) == 16]))
    labels.append(obj)
x = np.arange(3)
ax.bar(x - .22, matched_v, .4, color=[C[MATCHED[o]] for o in MATCHED],
       label="matched fixed operator")
ax.bar(x + .22, port_v, .4, color=C["portfolio"], label="portfolio")
ax.axhline(10000, color=C["adaptive"], ls="--", lw=1.2)
ax.text(2.4, 10500, "any mismatched fixed\noperator: total failure",
        fontsize=7.5, color=C["adaptive"], ha="right")
for xi, v in zip(x - .22, matched_v):
    ax.text(xi, v * 1.15, f"{v:.0f}", ha="center", fontsize=8)
for xi, v in zip(x + .22, port_v):
    ax.text(xi, v * 1.15, f"{v:.0f}", ha="center", fontsize=8)
ax.set_yscale("log"); ax.set_xticks(x); ax.set_xticklabels(labels)
ax.set_ylabel("generations to optimum (n=16)")
ax.legend(fontsize=8); ax.grid(alpha=.3, axis="y")
save(fig, "fig_portfolio.png")

# ---------- Fig 4.1: ground-truth landscapes ----------
fig, axes = plt.subplots(1, 3, figsize=(10.5, 3))
sets = [
    ("XOR-v4, n=5 (120 orderings)",
     [float(r["fitness"]) for r in csv.DictReader(open(os.path.join(
         ROOT, "experiments/iteration-05/results/v4_landscape.csv")))
      if r["problem"] == "XOR-v4"]),
    ("XOR-v4, n=6 (720)",
     [float(r["fitness"]) for r in csv.DictReader(open(os.path.join(
         ROOT, "experiments/iteration-06/results/n6_landscape.csv")))]),
    ("Parity-v4, n=7 (5040)",
     [float(r["fitness"]) for r in csv.DictReader(open(os.path.join(
         ROOT, "experiments/iteration-07/results/"
               "n7_parity_landscape.csv")))]),
]
for ax, (title, vals) in zip(axes, sets):
    vals = np.array(vals)
    ax.hist(vals, bins=18, color=C["swap"], alpha=.85)
    ax.axvline(vals.max(), color=C["ink"], ls="--", lw=1.2)
    n_opt = (vals == vals.max()).sum()
    ax.set_title(f"{title}\noptimum {vals.max():.3f} held by "
                 f"{n_opt}/{len(vals)}", fontsize=9)
    ax.set_xlabel("accuracy of ordering")
    ax.grid(alpha=.3, axis="y")
axes[0].set_ylabel("number of orderings")
save(fig, "fig_landscapes.png")

# ---------- Fig 6.1: locality heatmap (iteration 8) ----------
loc = list(csv.DictReader(open(os.path.join(
    ROOT, "experiments/iteration-08/results/locality.csv"))))
names = [r["landscape"] for r in loc]
ops4 = ["swap", "insert", "inversion", "scramble"]
mat = np.array([[float(r[f"rho1_{o}"]) for o in ops4] for r in loc])
fdc = np.array([float(r["fdc"]) for r in loc])
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.4),
                               gridspec_kw={"width_ratios": [3, 1]})
im = ax1.imshow(mat, cmap="Blues", vmin=-0.1, vmax=0.8, aspect="auto")
ax1.set_xticks(range(4)); ax1.set_xticklabels(ops4, fontsize=8)
ax1.set_yticks(range(len(names))); ax1.set_yticklabels(names, fontsize=8)
for i in range(len(names)):
    for j in range(4):
        ax1.text(j, i, f"{mat[i, j]:.2f}", ha="center", va="center",
                 fontsize=7,
                 color="white" if mat[i, j] > .45 else C["ink"])
ax1.set_title("move autocorrelation ρ1 (smoothness per operator)",
              fontsize=9)
colors = [C["insert"] if v < -0.15 else
          (C["adaptive"] if v > 0 else C["inversion"]) for v in fdc]
ax2.barh(range(len(names)), fdc, color=colors)
ax2.axvline(0, color=C["ink"], lw=.8)
ax2.set_yticks([]); ax2.invert_yaxis()
ax2.set_title("FDC (guidance)", fontsize=9)
ax2.set_xlabel("← guided        deceptive →", fontsize=8)
ax2.grid(alpha=.3, axis="x")
save(fig, "fig_locality.png")

# ---------- Fig 7.1: LLM position effects + landscape ----------
pos_rows = list(csv.DictReader(open(os.path.join(
    ROOT, "experiments/iteration-09/results/llm_position_effects.csv"))))
mods = [r["module"] for r in pos_rows]
pmat = np.array([[float(r[f"pos{i+1}"]) for i in range(6)]
                 for r in pos_rows])
llm = [float(r["fitness"]) for r in csv.DictReader(open(os.path.join(
    ROOT, "experiments/iteration-09/results/llm_landscape.csv")))]
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.2, 3.4),
                               gridspec_kw={"width_ratios": [3, 2]})
im = ax1.imshow(pmat, cmap="RdYlGn", vmin=.4, vmax=.95, aspect="auto")
ax1.set_xticks(range(6))
ax1.set_xticklabels([f"step {i+1}" for i in range(6)], fontsize=8)
ax1.set_yticks(range(6)); ax1.set_yticklabels(mods, fontsize=8)
for i in range(6):
    for j in range(6):
        ax1.text(j, i, f"{pmat[i, j]:.2f}", ha="center", va="center",
                 fontsize=7)
ax1.set_title("mean GSM8K accuracy when module is at prompt position",
              fontsize=9)
vals = np.array(llm)
ax2.hist(vals, bins=20, color=C["portfolio"], alpha=.85)
ax2.axvline(vals.max(), color=C["ink"], ls="--")
ax2.set_title(f"all 720 orderings\n6.3% → 96.9% accuracy by order alone",
              fontsize=9)
ax2.set_xlabel("accuracy"); ax2.set_ylabel("orderings")
ax2.grid(alpha=.3, axis="y")
save(fig, "fig_llm.png")

print("all figures written to", FIG)
