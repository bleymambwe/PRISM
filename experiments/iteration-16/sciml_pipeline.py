"""Iteration 16, Experiment P: SciML application — preprocessing-
pipeline ordering for sparse equation discovery (SINDy-style).

Motivation (papers 49-50 in the collection: SINDy, PySR): equation
discovery from noisy data requires a preprocessing pipeline — trim,
smooth, denoise, subsample, differentiate, clip — and practitioners
know its ORDER matters (smooth-then-differentiate vs
differentiate-then-smooth is the classic example). Nobody maps that
landscape. We do, exhaustively, and run the full PRISM Protocol on it.

Setup (deterministic, numpy-only, zero cost):
- Ground truth: damped 2-D oscillator  x' = -0.1x + 2y,
  y' = -2x - 0.1y; RK4, dt = 0.01, 1000 steps; Gaussian noise
  (sigma = 2% of signal std, fixed seed).
- Six pipeline operations, each applied exactly once, in permuted
  order (720 orderings, all enumerated):
    TRIM       drop first/last 5% of samples
    MEDIAN     median filter (window 5) on states (and derivs if present)
    SMOOTH     moving average (window 7) likewise
    CLIP       clip beyond 3 sigma likewise
    SUBSAMPLE  keep every 2nd sample
    DIFF       central finite differences -> derivative estimates
               (ops before DIFF shape the data it sees; ops after DIFF
               also transform the derivatives)
- Recovery: STLSQ (sequential thresholded least squares, threshold
  0.05, 10 iterations) on the library [1, x, y, x^2, xy, y^2].
- Fitness = max(0, 1 - ||Xi_hat - Xi_true||_F / ||Xi_true||_F).

Protocol: enumerate -> landscape stats -> D14 pre-flight ->
protocol-selected method vs random, 40 seeds, Wilson/bootstrap CIs.

Outputs -> experiments/iteration-16/results/sciml_{landscape.csv,report.txt}
"""

import csv
import itertools
import json
import os
import sys

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM, MUTATIONS

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)
lines = []

# ---------------- ground-truth system + noisy data (fixed) ----------------
A_TRUE = np.array([[-0.1, 2.0], [-2.0, -0.1]])  # linear dynamics


def rhs(s):
    return s @ A_TRUE.T


def simulate():
    rng = np.random.default_rng(1234)
    dt, N = 0.01, 1000
    X = np.empty((N, 2))
    X[0] = [1.0, 0.0]
    for i in range(N - 1):
        k1 = rhs(X[i])
        k2 = rhs(X[i] + dt / 2 * k1)
        k3 = rhs(X[i] + dt / 2 * k2)
        k4 = rhs(X[i] + dt * k3)
        X[i + 1] = X[i] + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    t = np.arange(N) * dt
    noise = rng.normal(0, 0.02 * X.std(axis=0), X.shape)
    return t, X + noise


T0, X0 = simulate()

# library: [1, x, y, x^2, xy, y^2]; true coefficients (2 x 6)
XI_TRUE = np.zeros((2, 6))
XI_TRUE[0, 1], XI_TRUE[0, 2] = -0.1, 2.0
XI_TRUE[1, 1], XI_TRUE[1, 2] = -2.0, -0.1


def library(X):
    x, y = X[:, 0], X[:, 1]
    return np.column_stack([np.ones_like(x), x, y, x * x, x * y, y * y])


def stlsq(Theta, dX, thresh=0.05, iters=10):
    Xi = np.linalg.lstsq(Theta, dX, rcond=None)[0]
    for _ in range(iters):
        small = np.abs(Xi) < thresh
        Xi[small] = 0
        for j in range(dX.shape[1]):
            big = ~small[:, j]
            if big.any():
                Xi[big, j] = np.linalg.lstsq(Theta[:, big], dX[:, j],
                                             rcond=None)[0]
    return Xi


# ---------------- pipeline operations ----------------
def _apply_both(state, fn):
    state["X"] = fn(state["X"])
    if state["Xd"] is not None:
        state["Xd"] = fn(state["Xd"])


def op_trim(s):
    n = len(s["t"])
    a, b = int(0.05 * n), int(0.95 * n)
    for k2 in ("t", "X", "Xd"):
        if s[k2] is not None:
            s[k2] = s[k2][a:b]


def _movavg(A, w):
    ker = np.ones(w) / w
    return np.column_stack([np.convolve(A[:, j], ker, mode="same")
                            for j in range(A.shape[1])])


def op_smooth(s):
    _apply_both(s, lambda A: _movavg(A, 7))


def _medfilt(A, w):
    pad = w // 2
    P = np.pad(A, ((pad, pad), (0, 0)), mode="edge")
    return np.column_stack([
        np.median(np.lib.stride_tricks.sliding_window_view(
            P[:, j], w), axis=1) for j in range(A.shape[1])])


def op_median(s):
    _apply_both(s, lambda A: _medfilt(A, 5))


def op_clip(s):
    def f(A):
        mu, sd = A.mean(axis=0), A.std(axis=0) + 1e-12
        return np.clip(A, mu - 3 * sd, mu + 3 * sd)
    _apply_both(s, f)


def op_subsample(s):
    for k2 in ("t", "X", "Xd"):
        if s[k2] is not None:
            s[k2] = s[k2][::2]


def op_diff(s):
    s["Xd"] = np.gradient(s["X"], s["t"], axis=0)


OPS = [("TRIM", op_trim), ("MEDIAN", op_median), ("SMOOTH", op_smooth),
       ("CLIP", op_clip), ("SUBSAMPLE", op_subsample), ("DIFF", op_diff)]


def fitness(perm):
    s = {"t": T0.copy(), "X": X0.copy(), "Xd": None}
    for i in perm:
        OPS[i][1](s)
    if s["Xd"] is None:
        s["Xd"] = np.gradient(s["X"], s["t"], axis=0)
    Xi = stlsq(library(s["X"]), s["Xd"])  # shape (6 terms, 2 states)
    err = np.linalg.norm(Xi - XI_TRUE.T) / np.linalg.norm(XI_TRUE)
    return max(0.0, 1.0 - err)


# ---------------- enumerate ----------------
land_path = os.path.join(OUT, "sciml_landscape.csv")
land = {}
if os.path.exists(land_path):
    for r in csv.DictReader(open(land_path)):
        land[tuple(json.loads(r["perm"]))] = float(r["fitness"])
if len(land) < 720:
    with open(land_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["perm", "fitness"])
        for p in itertools.permutations(range(6)):
            v = fitness(list(p))
            land[p] = v
            w.writerow([json.dumps(list(p)), round(v, 6)])
vals = np.array(list(land.values()))
opt = vals.max()
optima = {k for k, v in land.items() if v == opt}
best = max(land, key=land.get)
worst = min(land, key=land.get)
lines.append("Experiment P — SciML pipeline-ordering landscape "
             "(720 orderings, deterministic):")
lines.append(f"  fitness (1 - relative coefficient error): "
             f"min {vals.min():.3f}, mean {vals.mean():.3f}, "
             f"max {opt:.3f}, std {vals.std():.3f}")
lines.append(f"  optimum held by {len(optima)}/720 orderings")
lines.append(f"  best ordering:  {' -> '.join(OPS[i][0] for i in best)}")
lines.append(f"  worst ordering: {' -> '.join(OPS[i][0] for i in worst)} "
             f"(fitness {land[worst]:.3f})")
dpos = np.zeros(6)
for kk, vv in land.items():
    dpos[kk.index(5)] += vv
dpos /= 120
lines.append("  mean fitness by DIFF position: " +
             " ".join(f"p{i+1}:{dpos[i]:.3f}" for i in range(6)))

# ---------------- D14 pre-flight ----------------
rng = np.random.default_rng(16)
keys = list(land.keys())
OPS4 = ["swap", "insert", "inversion", "scramble"]
rho = {}
for opname in OPS4:
    f0, f1 = [], []
    for _ in range(4000):
        p = list(keys[rng.integers(len(keys))])
        q = p.copy()
        MUTATIONS[opname](q, rng)
        f0.append(land[tuple(p)])
        f1.append(land[tuple(q)])
    rho[opname] = float(np.corrcoef(f0, f1)[0, 1])


def cayley(p, q):
    n = len(p)
    qinv = [0] * n
    for i, v in enumerate(q):
        qinv[v] = i
    r = [qinv[v] for v in p]
    seen = [False] * n
    c = 0
    for i in range(n):
        if not seen[i]:
            c += 1
            j = i
            while not seen[j]:
                seen[j] = True
                j = r[j]
    return n - c


fs, ds = [], []
for p in keys:
    fs.append(land[p])
    ds.append(min(cayley(list(p), list(o)) for o in optima))
fdc = float(np.corrcoef(fs, ds)[0, 1])
pick = max((o for o in OPS4 if o != "scramble"), key=lambda o: rho[o])
lines.append(f"\nD14 pre-flight: rho1 " +
             ", ".join(f"{o}={rho[o]:.2f}" for o in OPS4) +
             f" | FDC {fdc:+.3f}")
lines.append(f"  decision: operator={pick}; "
             f"{'elitist search (FDC<-0.15)' if fdc < -0.15 else 'random/aging regime' if fdc < 0.05 else 'DECEPTIVE - no search'}")

# ---------------- protocol-selected method vs random, 40 seeds ----------------
def wilson(k2, n2, z=1.96):
    p = k2 / n2
    d = 1 + z * z / n2
    c = (p + z * z / (2 * n2)) / d
    h = z * np.sqrt(p * (1 - p) / n2 + z * z / (4 * n2 * n2)) / d
    return max(0, c - h), min(1, c + h)


CAP = 200
res = {}
for method in ("prism", "random"):
    hits, evals = 0, []
    for seed in range(40):
        st = {"seen": {}, "hit": None}

        def tf(perm, _s=st):
            kk = tuple(int(x) for x in perm)
            if kk not in _s["seen"] and len(_s["seen"]) < CAP:
                _s["seen"][kk] = land[kk]
                if _s["hit"] is None and kk in optima:
                    _s["hit"] = len(_s["seen"])
            return land.get(kk, 0.0)

        if method == "prism":
            PRISM(n=6, fitness_fn=tf, seed=seed, mutation=pick).evolve(
                generations=1000, target_fitness=opt)
        else:
            r2 = np.random.default_rng(7000 + seed)
            while len(st["seen"]) < CAP and st["hit"] is None:
                tf([int(x) for x in r2.permutation(6)])
        if st["hit"]:
            hits += 1
            evals.append(st["hit"])
    lo, hi = wilson(hits, 40)
    res[method] = (hits, np.mean(evals) if evals else -1, lo, hi)
    lines.append(f"  {method:<7} hits {hits}/40 CI[{lo:.2f},{hi:.2f}] "
                 f"mean evals-to-optimum "
                 f"{np.mean(evals) if evals else -1:.1f}")

text = "\n".join(lines)
open(os.path.join(OUT, "sciml_report.txt"), "w").write(text + "\n")
print(text)
