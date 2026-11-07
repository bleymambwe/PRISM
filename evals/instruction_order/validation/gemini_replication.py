"""Replicate Experiment K's 720-ordering GSM8K landscape through the eval's own code.

Uses the registered eval's prompt builder (`modules.build_prompt`), question pool,
ordering enumeration and grader (`grading.grade`) unchanged, and calls the same
model Experiment K used (Gemini 2.5 Flash-Lite, temperature 0) over plain REST.
Only the transport differs from `inspect eval`: Inspect's Google provider stalled
on this machine (no completed samples in minutes), so the generation call is made
directly. The eval's generation config is kept (max_tokens 2048, Experiment K
used 600), so this isolates what the eval changed: one prompt word ("mathematics"
for "math"), the token limit, and the canonical grader.

Kill-safe and resumable: every result is appended to a CSV and finished
(ordering, question) keys are skipped on restart.

    GOOGLE_API_KEY=... python gemini_replication.py [budget_seconds]
"""

from __future__ import annotations

import csv
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from evals.instruction_order.dataset import load_gsm8k_subset  # noqa: E402
from evals.instruction_order.grading import grade  # noqa: E402
from evals.instruction_order.modules import GSM8K_MODULES, build_prompt  # noqa: E402
from evals.instruction_order.orderings import exhaustive  # noqa: E402

MODEL = "gemini-2.5-flash-lite"
URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
OUT = Path(__file__).parent / "gemini_replication_cells.csv"
WORKERS = int(os.environ.get("WORKERS", "16"))
FIELDS = ["perm", "qidx", "correct", "in_tok", "out_tok", "finish"]


def ask(key: str, prompt: str, retries: int = 6) -> dict | None:
    for attempt in range(retries):
        try:
            r = requests.post(
                URL,
                params={"key": key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0, "maxOutputTokens": 2048},
                },
                timeout=90,
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
    budget = float(sys.argv[1]) if len(sys.argv) > 1 else 480.0
    key = os.environ["GOOGLE_API_KEY"]
    questions = load_gsm8k_subset()
    done: set[tuple[str, int]] = set()
    if OUT.exists():
        with OUT.open(newline="", encoding="utf-8") as fh:
            done = {(row["perm"], int(row["qidx"])) for row in csv.DictReader(fh)}
    todo = [
        (list(o), q)
        for o in exhaustive(len(GSM8K_MODULES))
        for q in range(len(questions))
        if (json.dumps(list(o)), q) not in done
    ]
    print(f"{len(done)} done, {len(todo)} remaining", flush=True)
    if not todo:
        print("REPLICATION COMPLETE")
        return

    start, lock = time.time(), threading.Lock()
    new_file = not OUT.exists()
    fh = OUT.open("a", newline="", encoding="utf-8")
    writer = csv.DictWriter(fh, fieldnames=FIELDS)
    if new_file:
        writer.writeheader()
    counter = {"n": 0}

    def work(item: tuple[list[int], int]) -> None:
        if time.time() - start > budget:
            return
        ordering, q = item
        prompt = build_prompt(ordering, questions[q]["problem"], GSM8K_MODULES, boxed=False)
        data = ask(key, prompt)
        if data is None:
            return
        try:
            cand = data["candidates"][0]
            text = cand["content"]["parts"][0]["text"]
            finish = cand.get("finishReason", "")
        except (KeyError, IndexError):
            text, finish = "", "EMPTY"
        usage = data.get("usageMetadata", {})
        row = {
            "perm": json.dumps(ordering),
            "qidx": q,
            "correct": int(grade(questions[q]["answer"], text)),
            "in_tok": usage.get("promptTokenCount", 0),
            "out_tok": usage.get("candidatesTokenCount", 0),
            "finish": finish,
        }
        with lock:
            writer.writerow(row)
            fh.flush()
            counter["n"] += 1

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(work, todo))
    fh.close()
    print(f"wrote {counter['n']} cells in {time.time() - start:.0f}s; "
          f"{len(todo) - counter['n']} remaining")


if __name__ == "__main__":
    main()
