"""Exact ANASOD--PRISM boundary diagnostic for NAS-Bench-201.

The script accepts either a compact CSV (recommended) or the official
NAS-Bench-201 .pth archive through nas_201_api.  It never trains a network.
It exhaustively groups all 5**6 cells by operation multiset and measures:

* distribution sufficiency: eta^2 (between-distribution variance / total);
* placement residual: within-distribution SD and range;
* PRISM pre-flight: lag-1 swap autocorrelation and exact FDC to the nearest
  best placement (shortest-path distance in the slice's swap graph).

This is a diagnostic experiment, not a test whose null is "ANASOD is wrong".
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import pickle
from collections import Counter, defaultdict, deque
from pathlib import Path

import numpy as np

OPS = ("none", "skip_connect", "nor_conv_1x1", "nor_conv_3x3", "avg_pool_3x3")
EDGES = ((0, 1), (0, 2), (1, 2), (0, 3), (1, 3), (2, 3))
DATASETS = ("cifar10-valid", "cifar100", "ImageNet16-120")


def arch_string(ops: tuple[str, ...]) -> str:
    """Return the canonical NAS-Bench-201 string for edge-order OPS."""
    return (
        f"|{ops[0]}~0|+|{ops[1]}~0|{ops[2]}~1|+"
        f"|{ops[3]}~0|{ops[4]}~1|{ops[5]}~2|"
    )


def parse_arch(text: str) -> tuple[str, ...]:
    """Parse a canonical cell string into the fixed six-edge order."""
    by_edge: dict[tuple[int, int], str] = {}
    for dst, node in enumerate(text.split("+"), start=1):
        for token in node.strip().strip("|").split("|"):
            op, src = token.split("~")
            by_edge[(int(src), dst)] = op
    result = tuple(by_edge[e] for e in EDGES)
    if len(result) != 6 or any(op not in OPS for op in result):
        raise ValueError(f"invalid NAS-Bench-201 architecture: {text}")
    return result


def distribution(ops: tuple[str, ...]) -> tuple[int, ...]:
    counts = Counter(ops)
    return tuple(counts[op] for op in OPS)


def swap_neighbors(ops: tuple[str, ...]):
    seen = set()
    for i in range(5):
        for j in range(i + 1, 6):
            if ops[i] == ops[j]:
                continue
            child = list(ops)
            child[i], child[j] = child[j], child[i]
            child = tuple(child)
            if child not in seen:
                seen.add(child)
                yield child


def pearson(x, y) -> float:
    if len(x) < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def exact_distances(keys, optima) -> dict[tuple[str, ...], int]:
    """Multi-source BFS gives distance to the nearest tied optimum."""
    allowed = set(keys)
    dist = {key: 0 for key in optima}
    queue = deque(optima)
    while queue:
        parent = queue.popleft()
        for child in swap_neighbors(parent):
            if child in allowed and child not in dist:
                dist[child] = dist[parent] + 1
                queue.append(child)
    if len(dist) != len(allowed):
        raise RuntimeError("swap graph unexpectedly disconnected")
    return dist


def analyze_slice(scores: dict[tuple[str, ...], float]) -> dict:
    keys = sorted(scores)
    values = np.array([scores[k] for k in keys], dtype=float)
    best = float(values.max())
    optima = [k for k in keys if math.isclose(scores[k], best, abs_tol=1e-12)]
    # Include both directions of every move. That is the exact expectation for
    # a uniformly sampled placement followed by a uniformly sampled valid swap;
    # it also prevents arbitrary tuple ordering from orienting the correlation.
    pairs = [(a, b) for a in keys for b in swap_neighbors(a) if b in scores]
    rho = pearson([scores[a] for a, b in pairs], [scores[b] for a, b in pairs])
    dists = exact_distances(keys, optima)
    fdc = pearson([dists[k] for k in keys], [scores[k] for k in keys])
    return {
        "n_placements": len(keys),
        "mean": float(values.mean()),
        "sd": float(values.std(ddof=0)),
        "range": float(values.max() - values.min()),
        "best": best,
        "n_optima": len(optima),
        "swap_edges": len(pairs),
        "rho_swap": rho,
        "fdc": fdc,
    }


def eta_squared(groups: dict[tuple[int, ...], dict[tuple[str, ...], float]]) -> float:
    all_values = np.array([v for group in groups.values() for v in group.values()])
    grand = float(all_values.mean())
    total = float(np.sum((all_values - grand) ** 2))
    between = sum(len(g) * (np.mean(list(g.values())) - grand) ** 2 for g in groups.values())
    return float(between / total) if total else float("nan")


def load_csv(path: Path) -> dict[str, dict[tuple[str, ...], float]]:
    """Load columns arch plus any of the three canonical dataset names."""
    output = {d: {} for d in DATASETS}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "arch" not in reader.fieldnames:
            raise ValueError("CSV must contain an 'arch' column")
        present = [d for d in DATASETS if d in reader.fieldnames]
        if not present:
            raise ValueError(f"CSV needs at least one score column from {DATASETS}")
        for row in reader:
            ops = parse_arch(row["arch"])
            for dataset in present:
                if row[dataset] != "":
                    output[dataset][ops] = float(row[dataset])
    return {d: scores for d, scores in output.items() if scores}


def load_pth(path: Path) -> dict[str, dict[tuple[str, ...], float]]:
    try:
        from nas_201_api import NASBench201API
    except ImportError as exc:
        raise SystemExit("Install the API first: pip install nas-bench-201") from exc
    api = NASBench201API(str(path), verbose=False)
    output = {d: {} for d in DATASETS}
    for index, text in enumerate(api):
        ops = parse_arch(str(text))
        for dataset in DATASETS:
            info = api.get_more_info(index, dataset, hp="200", is_random=False)
            output[dataset][ops] = float(info["valid-accuracy"])
    return output


def load_simple_hpo() -> dict[str, dict[tuple[str, ...], float]]:
    """Load the compact simple-hpo-bench NATS-Bench last-epoch tables.

    Keys are six base-5 operation indices in the same edge order used here;
    val_acc contains the available repeated runs, which we average.
    """
    try:
        import hpo_benchmarks
    except ImportError as exc:
        raise SystemExit("Install compact tables first: pip install simple-hpo-bench") from exc
    root = Path(hpo_benchmarks.__file__).parent / "datasets" / "nasbench201"
    mapping = {
        "cifar10.pkl": "cifar10-valid",
        "cifar100.pkl": "cifar100",
        "imagenet.pkl": "ImageNet16-120",
    }
    output = {}
    for filename, dataset in mapping.items():
        with (root / filename).open("rb") as handle:
            raw = pickle.load(handle)
        scores = {}
        for encoded, metrics in raw.items():
            ops = tuple(OPS[int(index)] for index in encoded)
            scores[ops] = float(np.mean(metrics["val_acc"]))
        output[dataset] = scores
    return output


def run(tables, outdir: Path) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    summary = {}
    rows = []
    example_dist = (0, 0, 2, 4, 0)  # paper Figure 1: 2 conv1x1, 4 conv3x3
    for dataset, table in tables.items():
        groups = defaultdict(dict)
        for ops, score in table.items():
            groups[distribution(ops)][ops] = score
        complete = len(table) == 5**6
        analyzed = {}
        for dist, scores in sorted(groups.items()):
            result = analyze_slice(scores)
            analyzed[dist] = result
            rows.append({"dataset": dataset, "distribution": ";".join(map(str, dist)), **result})
        summary[dataset] = {
            "n_architectures": len(table),
            "n_distributions": len(groups),
            "complete_nb201": complete,
            "eta_squared_distribution": eta_squared(groups),
            "weighted_within_variance_fraction": 1.0 - eta_squared(groups),
            "example_2conv1x1_4conv3x3": analyzed.get(example_dist),
            "median_slice_sd": float(np.median([r["sd"] for r in analyzed.values()])),
            "max_slice_range": float(max(r["range"] for r in analyzed.values())),
        }
    with (outdir / "slice_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(rows[0])
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    (outdir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def make_fixture(path: Path):
    """Small deterministic fixture used only to verify the pipeline."""
    dist = ("nor_conv_3x3",) * 4 + ("nor_conv_1x1",) * 2
    placements = sorted(set(itertools.permutations(dist)))
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("arch", "cifar10-valid"))
        writer.writeheader()
        for ops in placements:
            # Deliberately structured position effect; not an empirical result.
            score = 90 + 2 * (ops[0] == "nor_conv_3x3") + (ops[5] == "nor_conv_1x1")
            writer.writerow({"arch": arch_string(ops), "cifar10-valid": score})


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--csv", type=Path)
    source.add_argument("--pth", type=Path)
    source.add_argument("--simple-hpo", action="store_true")
    source.add_argument("--make-fixture", type=Path)
    parser.add_argument("--outdir", type=Path, default=Path(__file__).parent / "results")
    args = parser.parse_args()
    if args.make_fixture:
        make_fixture(args.make_fixture)
        return
    if args.csv:
        tables = load_csv(args.csv)
    elif args.pth:
        tables = load_pth(args.pth)
    else:
        tables = load_simple_hpo()
    print(json.dumps(run(tables, args.outdir), indent=2))


if __name__ == "__main__":
    main()
