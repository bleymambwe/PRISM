"""Iteration 3, Experiment E: all-positions-matter toy benchmarks.

Iteration-2 finding: the original toy benchmarks read only positions
0-2 of the length-5 permutation (effective space 60, not 120). Here the
network has 5 permuted layers, so every position is functional:
layer i's type = layer_types[perm[i]].

Hypothesis H3: fitness variance across random orderings is at least as
large as the v2 benchmarks' (the whole permutation is now functional).

Protocol: stage 1 = fitness std over 10 random permutations (compare to
v2 stage-1 values: XOR 0.100, parity 0.179); stage 2 = PRISM search,
seed 42, 60 generations (reduced from 150: v2 searches converged by gen
41 and each v3 evaluation is ~1.7x deeper; budget noted as a protocol
difference). XOR and 3-bit parity only (the informative v2 problems).

Outputs -> experiments/iteration-03/results/
"""

import csv
import json
import os
import sys
import time

import numpy as np
import torch
import torch.nn as nn

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import PRISM
from benchmarks.toy_problems import _make_layer, _train_classify

OUT_DIR = os.path.join(os.path.dirname(__file__), "results")
GLOBAL_SEED = 42
GENERATIONS = 60

_X2 = torch.tensor([[0., 0.], [0., 1.], [1., 0.], [1., 1.]])
_Y_XOR = torch.tensor([[0.], [1.], [1.], [0.]])


def xor_fitness_v3(permutation):
    """XOR with 5 permuted layers: all positions matter."""
    types = ["linear", "deep", "tanh", "sigmoid", "medium"]
    layers = [_make_layer(2, 4, types[permutation[0]]), nn.ReLU()]
    for i in range(1, 5):
        layers += [_make_layer(4, 4, types[permutation[i]]), nn.ReLU()]
    layers.append(nn.Linear(4, 1))
    return _train_classify(nn.Sequential(*layers), _X2, _Y_XOR, steps=50)


def parity_fitness_v3(permutation):
    """3-bit parity with 5 permuted layers: all positions matter."""
    types = ["linear", "deep", "tanh", "very_deep", "sigmoid"]
    layers = [_make_layer(3, 6, types[permutation[0]]), nn.ReLU()]
    for i in range(1, 5):
        layers += [_make_layer(6, 6, types[permutation[i]]), nn.ReLU()]
    layers.append(nn.Linear(6, 1))
    X = torch.tensor([[i >> 2 & 1, i >> 1 & 1, i & 1]
                      for i in range(8)]).float()
    y = torch.tensor([[(i >> 2 & 1) ^ (i >> 1 & 1) ^ (i & 1)]
                      for i in range(8)]).float()
    return _train_classify(nn.Sequential(*layers), X, y, steps=100)


PROBLEMS_V3 = [("XOR-v3", xor_fitness_v3),
               ("Parity-v3", parity_fitness_v3)]
V2_STAGE1_STD = {"XOR-v3": 0.100, "Parity-v3": 0.179}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    np.random.seed(GLOBAL_SEED)
    torch.manual_seed(GLOBAL_SEED)
    rng = np.random.default_rng(GLOBAL_SEED)
    rows = []

    for name, fn in PROBLEMS_V3:
        perms = [list(rng.permutation(5)) for _ in range(10)]
        fits = [fn(p) for p in perms]
        std = float(np.std(fits))
        print(f"{name}: stage-1 std {std:.4f} "
              f"(v2 reference {V2_STAGE1_STD[name]:.3f}), "
              f"range [{min(fits):.3f}, {max(fits):.3f}]", flush=True)

        start = time.time()
        res = PRISM(n=5, fitness_fn=fn, seed=GLOBAL_SEED).evolve(
            generations=GENERATIONS)
        runtime = time.time() - start
        print(f"{name}: best={res.best_fitness:.4f} "
              f"perm={res.best_perm} runtime={runtime:.0f}s", flush=True)
        rows.append({
            "problem": name, "stage1_std": std,
            "stage1_std_v2": V2_STAGE1_STD[name],
            "best_fitness": res.best_fitness,
            "best_perm": json.dumps(res.best_perm),
            "generations": GENERATIONS,
            "runtime_sec": round(runtime, 1),
        })

    with open(os.path.join(OUT_DIR, "toy_v3_results.csv"), "w",
              newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("done")


if __name__ == "__main__":
    main()
