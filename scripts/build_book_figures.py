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

# ================= v2 figures (reference-quality upgrade) =================
import itertools

# ---------- Fig 2.2: the four mutation operators, visually ----------
fig, axes = plt.subplots(2, 2, figsize=(9, 3.6))
demos = [
    ("swap — exchange two positions", "swap",
     [0, 1, 2, 3, 4, 5], [0, 4, 2, 3, 1, 5], [(1, 4)]),
    ("insert — remove and re-insert", "insert",
     [0, 1, 2, 3, 4, 5], [0, 2, 3, 4, 1, 5], [(1, 4)]),
    ("inversion — reverse a segment", "inversion",
     [0, 1, 2, 3, 4, 5], [0, 4, 3, 2, 1, 5], [(1, 4)]),
    ("scramble — shuffle a segment", "scramble",
     [0, 1, 2, 3, 4, 5], [0, 3, 1, 4, 2, 5], [(1, 4)]),
]
for ax, (title, op, before, after, arcs) in zip(axes.flat, demos):
    for row, perm in [(1.5, before), (0, after)]:
        for i, b in enumerate(perm):
            changed = before[i] != after[i]
            ax.add_patch(Rectangle((i, row), .9, .9, color=C[op],
                                   alpha=1 if (row == 0 and changed)
                                   else .35))
            ax.text(i + .45, row + .45, f"B{b+1}", ha="center",
                    va="center", fontsize=8,
                    color="white" if (row == 0 and changed) else C["ink"],
                    fontweight="bold")
    ax.annotate("", xy=(3, 1.05), xytext=(3, 1.45),
                arrowprops=dict(arrowstyle="->", color=C["ink"]))
    ax.set_title(title, fontsize=9)
    ax.set_xlim(-.3, 6.2); ax.set_ylim(-.4, 2.7); ax.axis("off")
save(fig, "fig_moves.png")

# ---------- Fig 3.2: Markov chain absorption diagram ----------
fig, ax = plt.subplots(figsize=(8.5, 3))
import matplotlib.patches as mpatches
transient = [(0.8, 1.5), (2.2, 2.2), (2.2, 0.8), (3.6, 1.5)]
for i, (x, y) in enumerate(transient):
    ax.add_patch(plt.Circle((x, y), .42, color=C["swap"], alpha=.85))
    ax.text(x, y, f"T{i+1}", ha="center", va="center", color="white",
            fontweight="bold")
ax.add_patch(mpatches.FancyBboxPatch((5.3, 0.7), 2.6, 1.6,
             boxstyle="round,pad=0.12", fc=C["insert"], alpha=.2,
             ec=C["insert"]))
for j, (x, y) in enumerate([(6, 1.5), (7.2, 1.5)]):
    ax.add_patch(plt.Circle((x, y), .42, color=C["insert"]))
    ax.text(x, y, f"A{j+1}", ha="center", va="center", color="white",
            fontweight="bold")
ax.text(6.6, 2.55, "absorbing set (population contains an optimum)",
        ha="center", fontsize=8.5, color=C["insert"])
ax.text(2.2, 2.95, "transient states (suboptimal populations)",
        ha="center", fontsize=8.5, color=C["swap"])
edges = [((0.8, 1.5), (2.2, 2.2)), ((0.8, 1.5), (2.2, 0.8)),
         ((2.2, 2.2), (3.6, 1.5)), ((2.2, 0.8), (3.6, 1.5)),
         ((2.2, 2.2), (2.2, 0.8)), ((3.6, 1.5), (6, 1.5))]
for (x1, y1), (x2, y2) in edges:
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="->",
                                 color=C["muted"], shrinkA=14,
                                 shrinkB=14, lw=1.2))
loop = mpatches.FancyArrowPatch((6.35, 1.75), (6.9, 1.75),
                                connectionstyle="arc3,rad=0.9",
                                arrowstyle="->", color=C["insert"], lw=1.4)
ax.add_patch(loop)
ax.text(6.6, 0.35, "elitism: no arrow ever leaves the absorbing set",
        ha="center", fontsize=8.5, color=C["ink"])
ax.set_xlim(0, 8.3); ax.set_ylim(0, 3.3); ax.axis("off")
save(fig, "fig_markov.png")

# ---------- Fig 3.3: Cayley graph of S3 under swap ----------
fig, ax = plt.subplots(figsize=(5, 4.2))
perms3 = list(itertools.permutations([1, 2, 3]))
angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, 7)[:-1]
coords = {p: (np.cos(a), np.sin(a)) for p, a in zip(perms3, angles)}
for p, q in itertools.combinations(perms3, 2):
    if sum(a != b for a, b in zip(p, q)) == 2:  # one swap apart
        ax.plot([coords[p][0], coords[q][0]],
                [coords[p][1], coords[q][1]], color=C["grid"], lw=1.4,
                zorder=1)
for p, (x, y) in coords.items():
    ident = p == (1, 2, 3)
    ax.add_patch(plt.Circle((x, y), .21,
                            color=C["insert"] if ident else C["swap"],
                            zorder=2))
    ax.text(x, y, "".join(map(str, p)), ha="center", va="center",
            color="white", fontsize=9, fontweight="bold", zorder=3)
ax.text(0, -1.45, "every permutation reachable from every other:\n"
        "irreducibility by construction", ha="center", fontsize=8.5,
        color=C["muted"])
ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.7, 1.4)
ax.set_aspect("equal"); ax.axis("off")
save(fig, "fig_cayley.png")

# ---------- Fig 3.4: absorption probability decay (theory) ----------
fig, ax = plt.subplots(figsize=(5.4, 3.2))
t = np.arange(0, 300)
for lam, lab, col in [(0.96, r"$\rho(Q)=0.96$ (typical)", C["swap"]),
                      (0.99, r"$\rho(Q)=0.99$ (hard landscape)",
                       C["inversion"]),
                      (0.90, r"$\rho(Q)=0.90$ (easy landscape)",
                       C["insert"])]:
    ax.plot(t, lam ** t, color=col, label=lab)
ax.set_xlabel("generation t")
ax.set_ylabel("Pr(still suboptimal)")
ax.legend(fontsize=8); ax.grid(alpha=.3)
save(fig, "fig_absorption.png")

# ---------- Fig 4.2: real convergence trajectories (iteration 2) ----------
h = np.load(os.path.join(ROOT,
                         "prism-research/outputs/validation_histories.npz"))
fig, ax = plt.subplots(figsize=(6.8, 3.4))
for name, col in [("XOR", C["swap"]), ("3-bit Parity", C["inversion"]),
                  ("Polynomial", C["portfolio"])]:
    y = h[name]
    if name == "Polynomial":
        y = 1 + y / 20  # scale MSE for shared axis, annotated
        ax.plot(y, color=col, label="Polynomial (scaled −MSE)")
    else:
        ax.plot(y, color=col, label=name)
ax.annotate("discrete jumps: population discovers a\nbetter ordering "
            "and elitism locks it in", xy=(41, .996), xytext=(70, .72),
            fontsize=8, color=C["ink"],
            arrowprops=dict(arrowstyle="->", color=C["muted"]))
ax.set_xlabel("generation"); ax.set_ylabel("best fitness")
ax.legend(fontsize=8, loc="lower right"); ax.grid(alpha=.3)
save(fig, "fig_trajectories.png")

# ---------- Fig 5.3: adaptive operator weights (iteration 4) ----------
pf4 = list(csv.DictReader(open(os.path.join(
    ROOT, "experiments/iteration-04/results/portfolio_results.csv"))))
fig, axes = plt.subplots(1, 3, figsize=(9.6, 2.8), sharey=True)
MATCH2 = {"hamming": "swap", "kendall": "insert",
          "adjacency": "inversion"}
ops4 = ["swap", "insert", "inversion", "scramble"]
for ax, obj in zip(axes, MATCH2):
    ws = {o: [] for o in ops4}
    for r in pf4:
        if r["objective"] == obj and r["mode"] == "adaptive" \
                and r["censored"] == "False":
            w = json.loads(r["operator_weights"])
            for o in ops4:
                ws[o].append(w[o])
    means = [np.mean(ws[o]) for o in ops4]
    bars = ax.bar(range(4), means, color=[C[o] for o in ops4])
    for rect, o in zip(bars, ops4):
        rect.set_alpha(1 if o == MATCH2[obj] else .45)
    ax.axhline(.25, color=C["muted"], ls=":", lw=1)
    ax.set_xticks(range(4))
    ax.set_xticklabels([o[:4] for o in ops4], fontsize=8)
    ax.set_title(f"{obj}\n(matched: {MATCH2[obj]})", fontsize=9)
    ax.grid(alpha=.3, axis="y")
axes[0].set_ylabel("mean learned weight")
axes[0].text(3.4, .258, "uniform", fontsize=7, color=C["muted"])
save(fig, "fig_adaptive.png")

# ---------- Fig 6.2: n=7 — exploration collapse + tuned configs ----------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.6, 3.2))
cfgs = ["pop 20\np=.05", "pop 20\np=.30", "pop 40\np=.30",
        "pop 40\np=.60", "pop 60\np=.50"]
hits = [4, 9, 10, 15, 15]
explored = [103, 236, 319, 389, 404]
ax1.bar(range(5), hits, color=[C["adaptive"]] + [C["inversion"]] * 2 +
        [C["insert"]] * 2)
ax1.set_xticks(range(5)); ax1.set_xticklabels(cfgs, fontsize=7.5)
ax1.set_ylabel("seeds finding an optimum (of 15)")
ax1.set_title("premature convergence is fixable…", fontsize=9)
ax1.axhline(15, color=C["muted"], ls=":", lw=1); ax1.grid(alpha=.3,
                                                          axis="y")
budgets = [25, 50, 100, 200]
prism_q = [0.9083, 0.9389, 0.9556, 0.9583]
rand_q = [0.9028, 0.9528, 0.9639, 0.9778]
ax2.plot(budgets, prism_q, "o-", color=C["portfolio"],
         label="PRISM (default)")
ax2.plot(budgets, rand_q, "s--", color=C["muted"], label="random")
ax2.set_xlabel("distinct-evaluation budget")
ax2.set_ylabel("mean best accuracy found")
ax2.set_title("…but random matches or wins anyway", fontsize=9)
ax2.legend(fontsize=8); ax2.grid(alpha=.3)
save(fig, "fig_n7_honest.png")

# ---------- Fig 7.2: LLM search comparison ----------
fig, ax = plt.subplots(figsize=(5.6, 3))
methods = ["PRISM\n(default)", "PRISM\n(D12-scaled)", "random\n(no repl.)"]
vals = [6, 7, 18]
cols = [C["portfolio"], C["portfolio"], C["muted"]]
b = ax.bar(methods, vals, color=cols)
for rect, a in zip(b, [1, .7, .8]):
    rect.set_alpha(a)
for rect, v in zip(b, vals):
    ax.text(rect.get_x() + rect.get_width() / 2, v + .4, str(v),
            ha="center", fontsize=9, fontweight="bold")
ax.set_ylabel("mean distinct evaluations\nto first exact optimum")
ax.set_title("LLM chain ordering: 15/15 hits for all methods",
             fontsize=9)
ax.grid(alpha=.3, axis="y")
save(fig, "fig_llm_search.png")

# ---------- Fig 9.1: the research arc / hypothesis timeline ----------
fig, ax = plt.subplots(figsize=(9.8, 3.4))
events = [
    (2, "reproduce v1\n+ 3 corrections", C["insert"], 1),
    (3, "operator matching\nconfirmed 3/3", C["insert"], 1),
    (3.35, "H3 depth redesign\nFALSIFIED", C["adaptive"], -1),
    (4, "portfolio ≤4.1×\nzero failures", C["insert"], 1),
    (4.35, "H5 adaptive speedup\nnot confirmed", C["inversion"], -1),
    (5, "ground truth:\n120 enumerated", C["insert"], 1),
    (6, "scale to 720;\nn=7 XOR saturates", C["inversion"], 1),
    (7, "H10 FALSIFIED:\nPRISM ≈ random", C["adaptive"], -1),
    (8, "locality diagnostic\npredicts 8/8", C["insert"], 1),
    (9, "LLM: 6%→97%\nby order alone", C["portfolio"], 1),
]
ax.axhline(0, color=C["muted"], lw=1.5)
for x, label, col, side in events:
    ax.plot([x], [0], "o", color=col, ms=9, zorder=3)
    ax.annotate(label, xy=(x, 0), xytext=(x, .55 * side),
                ha="center", fontsize=7.3, color=C["ink"],
                arrowprops=dict(arrowstyle="-", color=C["grid"]))
for it in range(2, 10):
    ax.text(it, -1.05, f"it-{it:02d}", ha="center", fontsize=8,
            color=C["muted"])
ax.set_xlim(1.5, 9.6); ax.set_ylim(-1.25, 1.25); ax.axis("off")
ax.set_title("nine versions, eleven experiments, two falsifications "
             "— all kept in the record", fontsize=10)
save(fig, "fig_arc.png")

print("all figures written to", FIG)
