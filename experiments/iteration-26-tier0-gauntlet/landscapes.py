"""Unified loader for every exactly enumerated PRISM landscape.

Tier 0, E0.1-E0.3.  Each landscape is a complete lookup table mapping a
permutation tuple to its fitness, so any optimizer can be replayed against it
at zero API cost.  That is the whole reason the baseline gauntlet is free:
the expensive evaluations were already paid for and committed.

Sources are the committed result CSVs; nothing here re-runs a model.  The
closed-form synthetic objectives come from ``prism-research/benchmarks``.

Landscape families
------------------
llm        exhaustive language-model instruction-ordering landscapes
neural     enumerated XOR / parity module-ordering benchmarks
synthetic  closed-form typed landscapes (A-type, P-type, R-type, deceptive)
sciml      scientific-pipeline ordering suites
"""

from __future__ import annotations

import csv
import itertools
import json
import os
import sys
from dataclasses import dataclass

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "prism-research"))

from benchmarks.synthetic import OBJECTIVES  # noqa: E402

Landscape = dict[tuple[int, ...], float]


@dataclass(frozen=True)
class LandscapeRecord:
    """One enumerated landscape plus the facts a fair replay needs."""

    name: str
    family: str
    n: int
    table: Landscape
    source: str

    @property
    def size(self) -> int:
        return len(self.table)

    @property
    def best(self) -> float:
        return max(self.table.values())

    @property
    def optima(self) -> frozenset[tuple[int, ...]]:
        top = self.best
        return frozenset(k for k, v in self.table.items() if v == top)

    @property
    def optimum_density(self) -> float:
        return len(self.optima) / self.size

    def as_fitness_fn(self):
        table = self.table
        return lambda perm: table[tuple(int(x) for x in perm)]


def _read_csv(path: str) -> list[dict[str, str]]:
    with open(os.path.join(ROOT, path), newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _from_csv(
    path: str,
    *,
    perm_key: str = "perm",
    fitness_key: str = "fitness",
    filter_key: str | None = None,
    filter_value: str | None = None,
) -> Landscape:
    table: Landscape = {}
    for row in _read_csv(path):
        if filter_key is not None and row.get(filter_key) != filter_value:
            continue
        table[tuple(json.loads(row[perm_key]))] = float(row[fitness_key])
    return table


# (name, family, relative path, filter column, filter value)
_CSV_SOURCES: tuple[tuple[str, str, str, str | None, str | None], ...] = (
    (
        "llm_gsm8k_n6",
        "llm",
        "experiments/iteration-09/results/llm_landscape.csv",
        None,
        None,
    ),
    (
        "parity_n7",
        "neural",
        "experiments/iteration-07/results/n7_parity_landscape.csv",
        None,
        None,
    ),
    (
        "xor_n6",
        "neural",
        "experiments/iteration-06/results/n6_landscape.csv",
        None,
        None,
    ),
    (
        "xor_n5",
        "neural",
        "experiments/iteration-05/results/v4_landscape.csv",
        "problem",
        "XOR-v4",
    ),
    (
        "parity_n5",
        "neural",
        "experiments/iteration-05/results/v4_landscape.csv",
        "problem",
        "Parity-v4",
    ),
)

_SCIML_PATH = "experiments/iteration-20-sciml-suite/results/suite_landscape.csv"
_SCIML_SYSTEMS = (
    "damped_oscillator",
    "cubic_oscillator",
    "vanderpol",
    "lorenz63",
    "rossler",
    "lotka_volterra",
)

_SYNTHETIC_N = 7


def load_all(include: tuple[str, ...] | None = None) -> dict[str, LandscapeRecord]:
    """Load every enumerated landscape, keyed by name.

    ``include`` optionally restricts to a subset of family names.
    """

    records: dict[str, LandscapeRecord] = {}

    for name, family, path, fkey, fval in _CSV_SOURCES:
        table = _from_csv(path, filter_key=fkey, filter_value=fval)
        if not table:
            raise RuntimeError(f"landscape {name} loaded empty from {path}")
        n = len(next(iter(table)))
        records[name] = LandscapeRecord(name, family, n, table, path)

    for system in _SCIML_SYSTEMS:
        table = _from_csv(_SCIML_PATH, filter_key="system", filter_value=system)
        if not table:
            raise RuntimeError(f"sciml system {system} loaded empty")
        n = len(next(iter(table)))
        records[f"sciml_{system}"] = LandscapeRecord(
            f"sciml_{system}", "sciml", n, table, _SCIML_PATH
        )

    for objective, function in OBJECTIVES.items():
        table = {
            perm: float(function(list(perm)))
            for perm in itertools.permutations(range(_SYNTHETIC_N))
        }
        records[f"{objective}_n{_SYNTHETIC_N}"] = LandscapeRecord(
            f"{objective}_n{_SYNTHETIC_N}",
            "synthetic",
            _SYNTHETIC_N,
            table,
            "prism-research/benchmarks/synthetic.py",
        )

    if include is not None:
        records = {k: v for k, v in records.items() if v.family in include}
    return records


def summarize(records: dict[str, LandscapeRecord]) -> list[dict[str, object]]:
    """One row per landscape: the ground-truth facts a reviewer will ask for."""

    rows: list[dict[str, object]] = []
    for record in sorted(records.values(), key=lambda r: (r.family, r.name)):
        values = list(record.table.values())
        spread = max(values) - min(values)
        rows.append(
            {
                "landscape": record.name,
                "family": record.family,
                "n": record.n,
                "size": record.size,
                "best": round(record.best, 6),
                "worst": round(min(values), 6),
                "spread": round(spread, 6),
                "n_optima": len(record.optima),
                "optimum_density": round(record.optimum_density, 6),
                "distinct_values": len(set(values)),
                "source": record.source,
            }
        )
    return rows


if __name__ == "__main__":
    loaded = load_all()
    print(f"{len(loaded)} landscapes loaded\n")
    header = f"{'landscape':<22}{'fam':<10}{'n':>3}{'size':>7}{'#opt':>6}{'density':>9}{'values':>8}"
    print(header)
    print("-" * len(header))
    for row in summarize(loaded):
        print(
            f"{row['landscape']:<22}{row['family']:<10}{row['n']:>3}{row['size']:>7}"
            f"{row['n_optima']:>6}{row['optimum_density']:>9.4f}{row['distinct_values']:>8}"
        )
