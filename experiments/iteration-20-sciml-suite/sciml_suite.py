"""Iteration 20: SciML pipeline-ordering suite (Benchmark #4, approved D22).

Extends Experiment P (iteration-16) from one dynamical system to six.
Question: is the preprocessing-pipeline ORDERING landscape a general
phenomenon across dynamical systems, and does the D14/D19 pre-flight
call the right method on each instance?

Design per system (identical to Experiment P; deterministic, $0):
- simulate with RK4 + 2% Gaussian noise (fixed seed per system);
- six pipeline ops applied once each in permuted order:
  TRIM, MEDIAN, SMOOTH, CLIP, SUBSAMPLE, DIFF  (DIFF = finite-difference
  derivative estimation; ops after DIFF also transform the derivatives);
- STLSQ recovery on a polynomial library (degree 2 for 3-D systems,
  degree 3 for 2-D so cubic dynamics are representable);
- fitness = max(0, 1 - ||Xi_hat - Xi_true||_F / ||Xi_true||_F);
- enumerate all 720 orderings -> landscape stats;
- D14 pre-flight (rho1 per operator + exact FDC, Cayley distance);
- protocol-selected method vs random, 40 seeds, Wilson CIs, cap 200
  distinct evaluations. Pre-flight decision rule (D14/D15/D19):
  FDC < -0.15 -> elitist PRISM with the rho1-picked operator;
  -0.15 <= FDC < +0.05 -> random is the method of record (race run
  anyway to score the forecast); FDC in [+0.05, +0.3) -> borderline,
  treated as near-zero (D19); >= +0.3 -> deceptive, no search.

Systems (ground-truth coefficient matrices known exactly):
  damped_oscillator  x' = -0.1x + 2y;      y' = -2x - 0.1y     (Exp. P)
  cubic_oscillator   x' = -0.1x^3 + 2y^3;  y' = -2x^3 - 0.1y^3 (SINDy classic)
  vanderpol          x' = y;  y' = 5(1-x^2)y - x  (mu = 5)
  lotka_volterra     x' = x - xy;          y' = xy - y  (rescaled)
  lorenz63           sigma=10, rho=28, beta=8/3 (3-D, chaotic)
  rossler            a=b=0.2, c=5.7 (3-D)

Kill-safe: one row appended per (system, ordering) to suite_landscape.csv,
resume by key; budget argument in seconds.
Usage: python sciml_suite.py [budget-seconds]
Outputs -> results/{suite_landscape.csv, suite_report.txt}
"""

import csv
import itertools
import json
import os
import sys
import time

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM, MUTATIONS

OUT = os.path.join(os.path.dirname(__file__), "results")
os.makedirs(OUT, exist_ok=True)
LAND_CSV = os.path.join(OUT, "suite_landscape.csv")
BUDGET = float(sys.argv[1]) if len(sys.argv) > 1 else None
START = time.time()


# ---------------- systems ----------------
def _rk4(rhs, x0, dt, n):
    X = np.empty((n, len(x0)))
    X[0] = x0
    for i in range(n - 1):
        k1 = rhs(X[i])
        k2 = rhs(X[i] + dt / 2 * k1)
        k3 = rhs(X[i] + dt / 2 * k2)
        k4 = rhs(X[i] + dt * k3)
        X[i + 1] = X[i] + dt / 6 * (k1 + 2 * k2 + 2 * k3 + k4)
    return X


def lib2_deg3(X):
    x, y = X[:, 0], X[:, 1]
    return np.column_stack([np.ones_like(x), x, y, x*x, x*y, y*y,
                            x**3, x*x*y, x*y*y, y**3])


LIB2_NAMES = ["1", "x", "y", "x2", "xy", "y2", "x3", "x2y", "xy2", "y3"]


def lib3_deg2(X):
    x, y, z = X[:, 0], X[:, 1], X[:, 2]
    return np.column_stack([np.ones_like(x), x, y, z, x*x, x*y, x*z,
                            y*y, y*z, z*z])


LIB3_NAMES = ["1", "x", "y", "z", "x2", "xy", "xz", "y2", "yz", "z2"]


def make_xi(names, dim, terms):
    """terms: dict state_index -> {term_name: coeff}."""
    Xi = np.zeros((len(names), dim))
    for j, tmap in terms.items():
        for t, c in tmap.items():
            Xi[names.index(t), j] = c
    return Xi


SYSTEMS = {}

SYSTEMS["damped_oscillator"] = dict(
    rhs=lambda s: np.array([-0.1*s[0] + 2*s[1], -2*s[0] - 0.1*s[1]]),
    x0=[1.0, 0.0], dt=0.01, n=1000, lib=lib2_deg3, names=LIB2_NAMES,
    xi=make_xi(LIB2_NAMES, 2, {0: {"x": -0.1, "y": 2.0},
                               1: {"x": -2.0, "y": -0.1}}), seed=1234,
    thresh=0.05)

SYSTEMS["cubic_oscillator"] = dict(
    rhs=lambda s: np.array([-0.1*s[0]**3 + 2*s[1]**3,
                            -2*s[0]**3 - 0.1*s[1]**3]),
    x0=[1.0, 0.0], dt=0.01, n=2000, lib=lib2_deg3, names=LIB2_NAMES,
    xi=make_xi(LIB2_NAMES, 2, {0: {"x3": -0.1, "y3": 2.0},
                               1: {"x3": -2.0, "y3": -0.1}}), seed=1235,
    thresh=0.05)

SYSTEMS["vanderpol"] = dict(
    rhs=lambda s: np.array([s[1], 5*(1 - s[0]**2)*s[1] - s[0]]),
    x0=[1.0, 0.0], dt=0.01, n=3000, lib=lib2_deg3, names=LIB2_NAMES,
    xi=make_xi(LIB2_NAMES, 2, {0: {"y": 1.0},
                               1: {"x": -1.0, "y": 5.0, "x2y": -5.0}}),
    seed=1236, thresh=0.1)

# NOTE (benchmark construction, 2026-07-14): the first LV config
# (x0=[1.5,1.0], thresh=0.05) orbited too close to the (1,1) equilibrium;
# the degree-3 library is collinear on that narrow range and STLSQ fails
# for EVERY ordering (fitness 0.000 flat) — a non-identifiable instance,
# not a landscape. Widened orbit restores identifiability (baseline
# rel err 0.001). Flat-landscape rows from the first config were purged.
SYSTEMS["lotka_volterra"] = dict(
    rhs=lambda s: np.array([s[0] - s[0]*s[1], s[0]*s[1] - s[1]]),
    x0=[3.0, 1.0], dt=0.01, n=4000, lib=lib2_deg3, names=LIB2_NAMES,
    xi=make_xi(LIB2_NAMES, 2, {0: {"x": 1.0, "xy": -1.0},
                               1: {"xy": 1.0, "y": -1.0}}), seed=1237,
    thresh=0.1)

SYSTEMS["lorenz63"] = dict(
    rhs=lambda s: np.array([10*(s[1]-s[0]), s[0]*(28-s[2])-s[1],
                            s[0]*s[1] - (8/3)*s[2]]),
    x0=[-8.0, 7.0, 27.0], dt=0.005, n=4000, lib=lib3_deg2,
    names=LIB3_NAMES,
    xi=make_xi(LIB3_NAMES, 3, {0: {"x": -10.0, "y": 10.0},
                               1: {"x": 28.0, "y": -1.0, "xz": -1.0},
                               2: {"xy": 1.0, "z": -8/3}}), seed=1238,
    thresh=0.2)

SYSTEMS["rossler"] = dict(
    rhs=lambda s: np.array([-s[1]-s[2], s[0]+0.2*s[1],
                            0.2 + s[2]*(s[0]-5.7)]),
    x0=[0.0, -6.0, 0.0], dt=0.02, n=4000, lib=lib3_deg2,
    names=LIB3_NAMES,
    xi=make_xi(LIB3_NAMES, 3, {0: {"y": -1.0, "z": -1.0},
                               1: {"x": 1.0, "y": 0.2},
                               2: {"1": 0.2, "xz": 1.0, "z": -5.7}}),
    seed=1239, thresh=0.1)


# ---------------- pipeline ops (identical to Experiment P) ----------------
def _apply_both(s, fn):
    s["X"] = fn(s["X"])
    if s["Xd"] is not None:
        s["Xd"] = fn(s["Xd"])


def op_trim(s):
    n = len(s["t"])
    a, b = int(0.05*n), int(0.95*n)
    for k in ("t", "X", "Xd"):
        if s[k] is not None:
            s[k] = s[k][a:b]


def _movavg(A, w):
    ker = np.ones(w)/w
    return np.column_stack([np.convolve(A[:, j], ker, mode="same")
                            for j in range(A.shape[1])])


def _medfilt(A, w):
    pad = w//2
    P = np.pad(A, ((pad, pad), (0, 0)), mode="edge")
    return np.column_stack([
        np.median(np.lib.stride_tricks.sliding_window_view(P[:, j], w),
                  axis=1) for j in range(A.shape[1])])


def op_smooth(s): _apply_both(s, lambda A: _movavg(A, 7))
def op_median(s): _apply_both(s, lambda A: _medfilt(A, 5))


def op_clip(s):
    def f(A):
        mu, sd = A.mean(axis=0), A.std(axis=0) + 1e-12
        return np.clip(A, mu - 3*sd, mu + 3*sd)
    _apply_both(s, f)


def op_subsample(s):
    for k in ("t", "X", "Xd"):
        if s[k] is not None:
            s[k] = s[k][::2]


def op_diff(s):
    s["Xd"] = np.gradient(s["X"], s["t"], axis=0)


OPS = [("TRIM", op_trim), ("MEDIAN", op_median), ("SMOOTH", op_smooth),
       ("CLIP", op_clip), ("SUBSAMPLE", op_subsample), ("DIFF", op_diff)]


def stlsq(Theta, dX, thresh, iters=10):
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


DATA = {}


def sim(name):
    if name not in DATA:
        cfg = SYSTEMS[name]
        X = _rk4(cfg["rhs"], np.array(cfg["x0"]), cfg["dt"], cfg["n"])
        t = np.arange(cfg["n"]) * cfg["dt"]
        rng = np.random.default_rng(cfg["seed"])
        Xn = X + rng.normal(0, 0.02 * X.std(axis=0), X.shape)
        DATA[name] = (t, Xn)
    return DATA[name]


def fitness(name, perm):
    cfg = SYSTEMS[name]
    t, X = sim(name)
    s = {"t": t.copy(), "X": X.copy(), "Xd": None}
    for i in perm:
        OPS[i][1](s)
    if s["Xd"] is None:
        s["Xd"] = np.gradient(s["X"], s["t"], axis=0)
    Xi = stlsq(cfg["lib"](s["X"]), s["Xd"], cfg["thresh"])
    err = np.linalg.norm(Xi - cfg["xi"]) / np.linalg.norm(cfg["xi"])
    return max(0.0, 1.0 - err)


# ---------------- enumeration (kill-safe, resumable) ----------------
def enumerate_all():
    done = {}
    if os.path.exists(LAND_CSV):
        for r in csv.DictReader(open(LAND_CSV)):
            done[(r["system"], r["perm"])] = float(r["fitness"])
    new_file = not os.path.exists(LAND_CSV)
    f = open(LAND_CSV, "a", newline="")
    w = csv.writer(f)
    if new_file:
        w.writerow(["system", "perm", "fitness"])
    count = 0
    for name in SYSTEMS:
        for p in itertools.permutations(range(6)):
            key = (name, json.dumps(list(p)))
            if key in done:
                continue
            v = fitness(name, list(p))
            w.writerow([name, key[1], round(v, 6)])
            f.flush()
            done[key] = v
            count += 1
            if BUDGET and time.time() - START > BUDGET:
                f.close()
                print(f"PAUSED (wall clock) after {count} new rows; "
                      f"rerun to resume")
                return None
    f.close()
    lands = {name: {} for name in SYSTEMS}
    for (name, pj), v in done.items():
        lands[name][tuple(json.loads(pj))] = v
    return lands


# ---------------- pre-flight + race ----------------
def cayley(p, q):
    n = len(p)
    qinv = [0]*n
    for i, v in enumerate(q):
        qinv[v] = i
    r = [qinv[v] for v in p]
    seen = [False]*n
    c = 0
    for i in range(n):
        if not seen[i]:
            c += 1
            j = i
            while not seen[j]:
                seen[j] = True
                j = r[j]
    return n - c


def wilson(k, n, z=1.96):
    p = k/n
    d = 1 + z*z/n
    c = (p + z*z/(2*n))/d
    h = z*np.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return max(0, c-h), min(1, c+h)


def analyze(lands):
    lines = ["Iteration 20 - SciML pipeline-ordering suite "
             "(6 systems x 720 orderings, deterministic, $0)\n"]
    OPS4 = ["swap", "insert", "inversion", "scramble"]
    CAP = 200
    summary = []
    for name, land in lands.items():
        vals = np.array(list(land.values()))
        opt = vals.max()
        optima = {k for k, v in land.items() if v == opt}
        best = max(land, key=land.get)
        worst = min(land, key=land.get)
        lines.append(f"== {name} ==")
        lines.append(f"  fitness: min {vals.min():.3f} mean {vals.mean():.3f}"
                     f" max {opt:.3f} std {vals.std():.3f} | optimum held by"
                     f" {len(optima)}/720")
        lines.append(f"  best  {' -> '.join(OPS[i][0] for i in best)}")
        lines.append(f"  worst {' -> '.join(OPS[i][0] for i in worst)}"
                     f" ({land[worst]:.3f})")
        # pre-flight
        rng = np.random.default_rng(20)
        keys = list(land.keys())
        rho = {}
        for opn in OPS4:
            f0, f1 = [], []
            for _ in range(4000):
                p = list(keys[rng.integers(len(keys))])
                q = p.copy()
                MUTATIONS[opn](q, rng)
                f0.append(land[tuple(p)])
                f1.append(land[tuple(q)])
            rho[opn] = (float(np.corrcoef(f0, f1)[0, 1])
                        if np.std(f0) > 0 and np.std(f1) > 0 else 0.0)
        fs, ds = [], []
        for p in keys:
            fs.append(land[p])
            ds.append(min(cayley(list(p), list(o)) for o in optima))
        fdc = (float(np.corrcoef(fs, ds)[0, 1])
               if np.std(fs) > 0 else 0.0)
        pick = max((o for o in OPS4 if o != "scramble"),
                   key=lambda o: rho[o])
        if fdc < -0.15:
            regime = "elitist search"
        elif fdc < 0.05:
            regime = "near-zero: random/aging"
        elif fdc < 0.3:
            regime = "borderline (D19): treat as near-zero"
        else:
            regime = "deceptive: no search"
        lines.append("  pre-flight: rho1 " +
                     ", ".join(f"{o}={rho[o]:.2f}" for o in OPS4) +
                     f" | FDC {fdc:+.3f} -> {regime} (operator={pick})")
        # race (always run to score the forecast)
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
                    PRISM(n=6, fitness_fn=tf, seed=seed,
                          mutation=pick).evolve(generations=1000,
                                                target_fitness=opt)
                else:
                    r2 = np.random.default_rng(7000 + seed)
                    while len(st["seen"]) < CAP and st["hit"] is None:
                        tf([int(x) for x in r2.permutation(6)])
                if st["hit"]:
                    hits += 1
                    evals.append(st["hit"])
            lo, hi = wilson(hits, 40)
            res[method] = (hits, float(np.mean(evals)) if evals else -1)
            lines.append(f"    {method:<7} hits {hits}/40 "
                         f"CI[{lo:.2f},{hi:.2f}] mean evals "
                         f"{res[method][1]:.1f}")
        summary.append((name, vals.std(),
                        f"{land[worst]:.2f}-{opt:.2f}", len(optima),
                        f"{fdc:+.2f}", pick, regime.split(":")[0],
                        f"{res['prism'][0]}/40 vs {res['random'][0]}/40"))
        lines.append("")
    lines.append("SUITE SUMMARY (system | std | range | #opt | FDC | "
                 "op | regime | prism-vs-random hits):")
    for row in summary:
        lines.append("  " + " | ".join(str(x) for x in row))
    text = "\n".join(lines)
    open(os.path.join(OUT, "suite_report.txt"), "w").write(text + "\n")
    print(text)
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    lands = enumerate_all()
    if lands is not None:
        analyze(lands)
