"""Merge sharded gauntlet outputs into a single canonical runs file.

Shards partition by landscape, so rows cannot collide; this still de-duplicates
on ``(landscape, method, seed)`` in case a shard was rerun with a different
partition count.

    python merge_shards.py
"""

from __future__ import annotations

import csv
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "results")
TARGET = os.path.join(OUT_DIR, "gauntlet_runs.csv")


def main() -> None:
    shards = sorted(glob.glob(os.path.join(OUT_DIR, "gauntlet_runs_shard*.csv")))
    if not shards:
        print("no shard files found")
        return

    seen: set[tuple[str, str, str]] = set()
    rows: list[dict[str, str]] = []
    fieldnames: list[str] | None = None

    for path in shards:
        with open(path, newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fieldnames = fieldnames or list(reader.fieldnames or [])
            count = 0
            for row in reader:
                key = (row["landscape"], row["method"], row["seed"])
                if key in seen:
                    continue
                seen.add(key)
                rows.append(row)
                count += 1
        print(f"  {os.path.basename(path)}: +{count}")

    if not fieldnames:
        print("shards had no header")
        return

    rows.sort(key=lambda r: (r["landscape"], r["method"], int(r["seed"])))
    with open(TARGET, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    landscapes = {r["landscape"] for r in rows}
    methods = {r["method"] for r in rows}
    seeds = {r["seed"] for r in rows}
    expected = len(landscapes) * len(methods) * len(seeds)
    print(
        f"merged {len(rows)} rows -> {TARGET}\n"
        f"  {len(landscapes)} landscapes x {len(methods)} methods x {len(seeds)} seeds "
        f"= {expected} expected"
    )
    if len(rows) != expected:
        print(f"  INCOMPLETE: {expected - len(rows)} runs still missing")
    else:
        print("  COMPLETE")


if __name__ == "__main__":
    main()
