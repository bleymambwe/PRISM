"""E0.1 baseline gauntlet: replay every optimizer against every enumerated landscape.

Kill-safe and resumable, per this machine's constraints: every completed run is
appended to CSV immediately, already-recorded ``(landscape, method, seed)`` keys
are skipped on restart, and the process stops cleanly when its wall-clock budget
expires.

    python gauntlet.py [seconds] [shard] [num_shards]

Repeat until it prints GAUNTLET COMPLETE.  Shards partition the work by
landscape and write to separate CSVs, so several processes can run at once
without contending for the same file; ``merge_shards.py`` combines them.

One run is executed per (landscape, method, seed) at the maximum budget; every
smaller budget in the grid is read off the best-so-far curve, so the whole budget
sweep costs no extra evaluations.
"""

from __future__ import annotations

import csv
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from landscapes import load_all, summarize  # noqa: E402
from optimizers import METHODS, run_method  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results")
RUNS_CSV = os.path.join(OUT_DIR, "gauntlet_runs.csv")
SUMMARY_CSV = os.path.join(OUT_DIR, "landscape_summary.csv")

SEEDS = 40
MAX_BUDGET = 200
BUDGET_GRID = (15, 25, 50, 100, 200)

FIELDS = [
    "landscape",
    "family",
    "n",
    "method",
    "seed",
    "budget",
    "evaluated",
    "hit",
    "best",
    "optimum",
    "regret",
    "auc",
    *[f"best_at_{b}" for b in BUDGET_GRID],
    *[f"hit_by_{b}" for b in BUDGET_GRID],
]


def _load_done(path: str) -> set[tuple[str, str, int]]:
    if not os.path.exists(path):
        return set()
    done: set[tuple[str, str, int]] = set()
    with open(path, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            done.add((row["landscape"], row["method"], int(row["seed"])))
    return done


def main() -> None:
    seconds = float(sys.argv[1]) if len(sys.argv) > 1 else 240.0
    shard = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    num_shards = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    deadline = time.time() + seconds
    os.makedirs(OUT_DIR, exist_ok=True)

    runs_csv = (
        RUNS_CSV
        if num_shards == 1
        else os.path.join(OUT_DIR, f"gauntlet_runs_shard{shard}.csv")
    )

    records = load_all()
    if num_shards > 1:
        names = sorted(records)
        mine = {name for i, name in enumerate(names) if i % num_shards == shard}
        records = {k: v for k, v in records.items() if k in mine}
        print(f"shard {shard}/{num_shards}: {sorted(records)}")

    if not os.path.exists(SUMMARY_CSV):
        rows = summarize(records)
        with open(SUMMARY_CSV, "w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    done = _load_done(runs_csv)
    fresh = not os.path.exists(runs_csv)

    todo = [
        (name, method, seed)
        for name in records
        for method in METHODS
        for seed in range(SEEDS)
        if (name, method, seed) not in done
    ]
    total = len(records) * len(METHODS) * SEEDS
    print(f"{len(done)}/{total} runs already recorded; {len(todo)} remaining")

    completed = 0
    with open(runs_csv, "a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if fresh:
            writer.writeheader()

        for name, method, seed in todo:
            if time.time() > deadline:
                break
            record = records[name]
            budget = min(MAX_BUDGET, record.size)
            oracle = run_method(
                method, record.table, record.optima, record.n, budget, seed
            )
            curve = oracle.curve
            auc = sum(curve) / len(curve) if curve else float("nan")
            row: dict[str, object] = {
                "landscape": name,
                "family": record.family,
                "n": record.n,
                "method": method,
                "seed": seed,
                "budget": budget,
                "evaluated": oracle.count,
                "hit": oracle.hit if oracle.hit is not None else "",
                "best": round(oracle.best, 8),
                "optimum": round(record.best, 8),
                "regret": round(record.best - oracle.best, 8),
                "auc": round(auc, 8),
            }
            for b in BUDGET_GRID:
                capped = min(b, budget)
                row[f"best_at_{b}"] = round(oracle.best_at(capped), 8)
                row[f"hit_by_{b}"] = int(
                    oracle.hit is not None and oracle.hit <= capped
                )
            writer.writerow(row)
            handle.flush()
            completed += 1

    remaining = len(todo) - completed
    print(f"completed {completed} runs this chunk; {remaining} remaining")
    if remaining == 0:
        print("GAUNTLET COMPLETE")


if __name__ == "__main__":
    main()
