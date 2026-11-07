"""Full-size runs of the registered tasks over plain REST, using the eval's own samples.

The Inspect runs on this machine process roughly 45 samples a minute (about eight
hours for one 23,040-sample model), so full-size validation goes through the same
`build_dataset` samples, the same temperature-0 / 2048-token config and the same
`grading.grade`, with only the HTTP transport replaced. Each row is one
(ordering, question) sample. Kill-safe and resumable.

    OPENAI_API_KEY=... python openai_direct.py <gsm8k_exhaustive|math500> <model> [budget_seconds]
"""

from __future__ import annotations

import csv
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from evals.instruction_order.dataset import build_dataset, load_gsm8k_subset, load_math500  # noqa: E402
from evals.instruction_order.grading import grade  # noqa: E402

WORKERS = int(os.environ.get("WORKERS", "32"))
FIELDS = ["sample_id", "ordering_id", "ordering", "question_id", "correct", "in_tok", "out_tok", "finish"]


def samples_for(task: str):
    if task == "gsm8k_exhaustive":
        ds = build_dataset("gsm8k", load_gsm8k_subset(32), design="exhaustive", boxed=False)
    elif task == "math500":
        ds = build_dataset("math500", load_math500(100), design="random", orderings=50,
                           seed=7, operator="swap", boxed=True)
    else:
        raise SystemExit(f"unknown task {task}")
    return list(ds)


def ask(key: str, model: str, prompt: str, retries: int = 6):
    for attempt in range(retries):
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}"},
                json={"model": model, "temperature": 0, "max_tokens": 2048,
                      "messages": [{"role": "user", "content": prompt}]},
                timeout=120,
            )
            if r.status_code == 200:
                return r.json()
            if r.status_code in (429, 500, 502, 503):
                time.sleep(min(2**attempt * 2, 30))
                continue
            time.sleep(2)
        except requests.RequestException:
            time.sleep(2**attempt)
    return None


def main() -> None:
    task, model = sys.argv[1], sys.argv[2]
    budget = float(sys.argv[3]) if len(sys.argv) > 3 else 480.0
    key = os.environ["OPENAI_API_KEY"]
    out = Path(__file__).parent / f"cells_{task}_{model.replace('.', '').replace('/', '_')}.csv"
    samples = samples_for(task)
    done: set[str] = set()
    if out.exists():
        with out.open(newline="", encoding="utf-8") as fh:
            done = {row["sample_id"] for row in csv.DictReader(fh)}
    todo = [s for s in samples if s.id not in done]
    print(f"{task} {model}: {len(done)} done, {len(todo)} remaining", flush=True)
    if not todo:
        print("RUN COMPLETE")
        return
    start, lock, n = time.time(), threading.Lock(), [0]
    new = not out.exists()
    fh = out.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(fh, fieldnames=FIELDS)
    if new:
        writer.writeheader()

    def work(s) -> None:
        if time.time() - start > budget:
            return
        data = ask(key, model, s.input)
        if data is None:
            return
        try:
            choice = data["choices"][0]
            text, finish = choice["message"]["content"] or "", choice.get("finish_reason", "")
        except (KeyError, IndexError):
            text, finish = "", "EMPTY"
        usage = data.get("usage", {})
        row = {
            "sample_id": s.id, "ordering_id": s.metadata["ordering_id"],
            "ordering": ">".join(map(str, s.metadata["ordering"])),
            "question_id": s.metadata["question_id"],
            "correct": int(grade(str(s.target), text)),
            "in_tok": usage.get("prompt_tokens", 0), "out_tok": usage.get("completion_tokens", 0),
            "finish": finish,
        }
        with lock:
            writer.writerow(row)
            fh.flush()
            n[0] += 1

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(work, todo))
    fh.close()
    print(f"wrote {n[0]} in {time.time() - start:.0f}s; {len(todo) - n[0]} remaining")


if __name__ == "__main__":
    main()
