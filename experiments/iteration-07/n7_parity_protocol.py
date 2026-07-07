"""Iteration 7, Experiment I: the discriminating n=7 protocol.

Fixes Iteration-6 Stage B's saturation: 3-bit parity (sparse optima)
instead of XOR, k=3 deterministic trials (the canonical v4 objective),
and evaluations-to-first-optimum as the metric for both PRISM and the
random-search baseline.

Stages (budgeted + resumable; rerun until "STUDY COMPLETE"):
1. Enumerate all 5040 n=7 orderings (parity, k=3) with a
   multiprocessing pool (this machine: 4 cores; ~1-1.5 h total).
   Rows are appended as workers finish (kill-safe); torch is limited
   to 1 thread per worker so workers do not fight each other.
2. Landscape stats: exact optimum, count of optimal orderings, std.
3. Search protocol against the enumeration cache (free):
   - PRISM (portfolio, per D8), 15 seeds: count DISTINCT permutations
     evaluated until the first optimal permutation is queried.
   - Random search, 15 seeds: same metric, uniform sampling without
     replacement.
   Report means/medians and the PRISM/random ratio.

Usage: python n7_parity_protocol.py [budget-seconds] [workers]
Outputs -> experiments/iteration-07/results/
"""

import csv
import itertools
import json
import multiprocessing as mp
import os
import sys
import time

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))

OUT_DIR = os.path.join(os.path.dirname(__file__), "results")
LAND_CSV = os.path.join(OUT_DIR, "n7_parity_landscape.csv")
SEARCH_CSV = os.path.join(OUT_DIR, "n7_parity_search.csv")
N = 7
K_TRIALS = 3
SEEDS = list(range(15))
GENERATIONS = 400  # PRISM cap; cached evals make this cheap
BUDGET_SECONDS = None
_START = time.time()


def _worker_init():
    import torch
    torch.set_num_threads(1)


def eval_perm(perm):
    """Worker: deterministic parity fitness for one permutation."""
    import torch
    import torch.nn.functional as F
    from benchmarks.toy_problems_v4 import _build, _perm_seed
    X = torch.tensor([[i >> 2 & 1, i >> 1 & 1, i & 1]
                      for i in range(8)]).float()
    y = torch.tensor([[(i >> 2 & 1) ^ (i >> 1 & 1) ^ (i & 1)]
                      for i in range(8)]).float()
    accs = []
    for trial in range(K_TRIALS):
        torch.manual_seed(_perm_seed(perm, trial))
        model = _build(list(perm), 3)
        opt = torch.optim.Adam(model.parameters(), lr=0.1)
        for _ in range(100):
            opt.zero_grad()
            loss = F.mse_loss(model(X), y)
            loss.backward()
            opt.step()
        with torch.no_grad():
            accs.append(((model(X) > 0.5).float() == y)
                        .float().mean().item())
    return list(perm), sum(accs) / len(accs)


def load_landscape():
    done = {}
    if os.path.exists(LAND_CSV):
        for r in csv.DictReader(open(LAND_CSV)):
            done[r["perm"]] = float(r["fitness"])
    return done


def stage_enumerate(workers):
    done = load_landscape()
    todo = [p for p in itertools.permutations(range(N))
            if json.dumps(list(p)) not in done]
    print(f"enumeration: {len(done)}/5040 done, {len(todo)} to go, "
          f"{workers} workers", flush=True)
    if not todo:
        return done
    new_file = not os.path.exists(LAND_CSV)
    f = open(LAND_CSV, "a", newline="")
    w = csv.DictWriter(f, fieldnames=["perm", "fitness"])
    if new_file:
        w.writeheader()
    n_done = 0
    with mp.Pool(workers, initializer=_worker_init) as pool:
        for perm, fit in pool.imap_unordered(eval_perm, todo,
                                             chunksize=8):
            w.writerow({"perm": json.dumps(perm), "fitness": fit})
            f.flush()
            done[json.dumps(perm)] = fit
            n_done += 1
            if n_done % 200 == 0:
                print(f"  +{n_done} ({len(done)}/5040), "
                      f"{time.time() - _START:.0f}s", flush=True)
            if BUDGET_SECONDS and time.time() - _START > BUDGET_SECONDS:
                print("BUDGET REACHED during enumeration; rerun to "
                      "resume", flush=True)
                pool.terminate()
                f.close()
                return None
    f.close()
    return done


def stage_search(land):
    vals = np.array(list(land.values()))
    opt = float(vals.max())
    optima = {p for p, v in land.items() if v == opt}
    stats = (f"n=7 parity landscape: optimum {opt:.4f} "
             f"({len(optima)}/5040 = {len(optima)/50.40:.2f}%), "
             f"min {vals.min():.4f}, mean {vals.mean():.4f}, "
             f"std {vals.std():.4f}")
    print(stats, flush=True)

    done = set()
    if os.path.exists(SEARCH_CSV):
        for r in csv.DictReader(open(SEARCH_CSV)):
            done.add((r["method"], int(r["seed"])))
    fields = ["method", "seed", "evals_to_first_optimum", "found"]

    from core.prism import PRISM
    for seed in SEEDS:
        # PRISM with portfolio mutation; count distinct evals until an
        # optimal permutation is first queried
        if ("prism", seed) not in done:
            state = {"count": 0, "hit": None, "seen": set()}

            def counting_fitness(perm, _s=state):
                key = json.dumps([int(x) for x in perm])
                if key not in _s["seen"]:
                    _s["seen"].add(key)
                    _s["count"] += 1
                    if _s["hit"] is None and key in optima:
                        _s["hit"] = _s["count"]
                return land[key]

            PRISM(n=N, fitness_fn=counting_fitness, seed=seed,
                  mutation="portfolio").evolve(
                generations=GENERATIONS, target_fitness=opt)
            _append(SEARCH_CSV, {
                "method": "prism", "seed": seed,
                "evals_to_first_optimum":
                    state["hit"] if state["hit"] else -1,
                "found": state["hit"] is not None}, fields)
            print(f"prism seed={seed}: first optimum at distinct eval "
                  f"{state['hit']} (of {state['count']})", flush=True)
        # Random search without replacement
        if ("random", seed) not in done:
            rng = np.random.default_rng(2000 + seed)
            order = rng.permutation(len(land))
            keys = list(land.keys())
            hit = next((i + 1 for i, idx in enumerate(order)
                        if keys[idx] in optima), -1)
            _append(SEARCH_CSV, {
                "method": "random", "seed": seed,
                "evals_to_first_optimum": hit, "found": hit > 0},
                fields)
            print(f"random seed={seed}: first optimum at eval {hit}",
                  flush=True)

    rows = list(csv.DictReader(open(SEARCH_CSV)))
    p = [int(r["evals_to_first_optimum"]) for r in rows
         if r["method"] == "prism" and int(r["evals_to_first_optimum"]) > 0]
    q = [int(r["evals_to_first_optimum"]) for r in rows
         if r["method"] == "random"]
    p_miss = sum(1 for r in rows if r["method"] == "prism"
                 and int(r["evals_to_first_optimum"]) < 0)
    lines = [
        stats,
        (f"PRISM (portfolio): mean {np.mean(p):.0f}, median "
         f"{np.median(p):.0f} distinct evals to first optimum "
         f"({len(p)} hits, {p_miss} misses within cap)"),
        (f"random: mean {np.mean(q):.0f}, median {np.median(q):.0f} "
         f"evals to first optimum ({len(q)} seeds)"),
        (f"speedup (random mean / PRISM mean): "
         f"{np.mean(q) / np.mean(p):.1f}x" if p else "n/a"),
    ]
    with open(os.path.join(OUT_DIR, "n7_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[1:]), flush=True)


def _append(path, row, fields):
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if new:
            w.writeheader()
        w.writerow(row)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    workers = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    land = stage_enumerate(workers)
    if land is None:
        return
    stage_search(land)
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BUDGET_SECONDS = float(sys.argv[1])
    main()
