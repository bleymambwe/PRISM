"""AfriMGSM few-shot exemplar ordering with PRISM (draft; see README.md).

Resumable: every distinct (language, backend, permutation, subset) score is
appended to a JSONL cache, so reruns replay finished work for free.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import random
import re
import statistics
from pathlib import Path

from prism_search import PRISM, preflight

HERE = Path(__file__).parent
RESULTS = HERE / "results"
DATASET = "masakhane/afrimgsm"
N_SHOTS = 8
NUMBER = re.compile(r"-?\d[\d,]*\.?\d*")


def load_split(language: str):
    from datasets import load_dataset  # lazy: optional dependency

    ds = load_dataset(DATASET, language)
    shots = list(ds["train"])
    test = list(ds["test"])
    order = list(range(len(test)))
    random.Random(12345).shuffle(order)  # fixed split seed, independent of run seeds
    half = len(order) // 2
    search = [test[i] for i in sorted(order[:half])]
    report = [test[i] for i in sorted(order[half:])]
    return shots, search, report


def dry_run_backend(prompt: str) -> str:
    """Deterministic stub for plumbing checks. NOT a model; never report it."""
    digest = int(hashlib.sha256(prompt.encode()).hexdigest(), 16)
    return str(digest % 40)


def load_backend(spec: str):
    if spec == "dry-run":
        return dry_run_backend
    module, _, attr = spec.partition(":")
    if not attr:
        raise SystemExit("backend must be 'dry-run' or 'package.module:function'")
    return getattr(importlib.import_module(module), attr)


def build_prompt(shots, perm, question: str) -> str:
    parts = [f"Question: {shots[i]['question']}\nAnswer: {shots[i]['answer_number']}" for i in perm]
    parts.append(f"Question: {question}\nAnswer:")
    return "\n\n".join(parts)


def extract_number(text: str) -> float | None:
    found = NUMBER.findall(text.replace(",", ""))
    try:
        return float(found[-1]) if found else None
    except ValueError:
        return None


class Scorer:
    def __init__(self, backend, shots, cache_path: Path, tag: str):
        self.backend, self.shots, self.tag = backend, shots, tag
        self.path = cache_path
        self.cache: dict[str, float] = {}
        if cache_path.exists():
            for line in cache_path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                self.cache[row["key"]] = row["acc"]

    def accuracy(self, perm, items, subset: str) -> float:
        key = f"{self.tag}|{subset}|{','.join(map(str, perm))}"
        if key in self.cache:
            return self.cache[key]
        hits = 0
        for item in items:
            pred = extract_number(self.backend(build_prompt(self.shots, perm, item["question"])))
            hits += pred is not None and abs(pred - float(item["answer_number"])) < 1e-6
        acc = hits / len(items)
        self.cache[key] = acc
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"key": key, "acc": acc}) + "\n")
        return acc


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--language", required=True, help="AfriMGSM config, e.g. swa, yor, hau")
    ap.add_argument("--backend", default="dry-run")
    ap.add_argument("--budget", type=int, default=200, help="distinct orderings evaluated per seed")
    ap.add_argument("--seeds", type=int, nargs="+", default=[0, 1, 2, 3, 4])
    ap.add_argument("--search-items", type=int, default=40, help="search-half items scored per ordering")
    ap.add_argument("--pop-size", type=int, default=10)
    args = ap.parse_args()

    RESULTS.mkdir(exist_ok=True)
    shots, search_all, report = load_split(args.language)
    if len(shots) != N_SHOTS:
        raise SystemExit(f"expected {N_SHOTS} train exemplars, got {len(shots)}")
    search = search_all[: args.search_items]
    stem = f"{args.language}_{args.backend.replace(':', '-').replace('.', '_')}"
    scorer = Scorer(load_backend(args.backend), shots, RESULTS / f"{stem}_cache.jsonl", tag=stem)

    summary = {"language": args.language, "backend": args.backend, "budget": args.budget,
               "search_items": len(search), "report_items": len(report), "seeds": {}}
    identity = tuple(range(N_SHOTS))
    for seed in args.seeds:
        fit = lambda p: scorer.accuracy(tuple(p), search, "search")  # noqa: E731
        pre = preflight(N_SHOTS, fit, seed=seed, pair_samples=20, landscape_samples=min(40, args.budget))
        result = PRISM(N_SHOTS, fit, pop_size=args.pop_size, seed=seed).search(args.budget)
        best = tuple(result.best_perm)
        rng = random.Random(seed)
        randoms = [tuple(rng.sample(range(N_SHOTS), N_SHOTS)) for _ in range(5)]
        summary["seeds"][seed] = {
            "preflight": str(pre),
            "best_permutation": best,
            "search_acc_best": fit(best),
            "report_acc_best": scorer.accuracy(best, report, "report"),
            "report_acc_identity": scorer.accuracy(identity, report, "report"),
            "report_acc_random_mean": statistics.fmean(scorer.accuracy(p, report, "report") for p in randoms),
        }
        (RESULTS / f"{stem}_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(f"seed {seed}: {summary['seeds'][seed]['best_permutation']}")


if __name__ == "__main__":
    main()
