"""Iteration 9, Experiment K: LLM reasoning-chain ordering (GSM8K).

The flagship application, run under the full D13/D14 methodology.

Problem: 6 fixed reasoning-module instructions; a permutation orders
them in the prompt. Fitness(ordering) = accuracy of Gemini 2.5
Flash-Lite (temperature 0) on a fixed 32-question GSM8K subset.
6! = 720 orderings — small enough to ENUMERATE COMPLETELY, giving the
same exact-ground-truth methodology as the neural benchmarks
(~23k API calls ~ $2.5-3 at Flash-Lite prices).

Staged protocol (budgeted + resumable; the per-(ordering,question)
answer cache is the unit of persistence, so any interruption resumes):

1. VARIANCE GATE: 30 random orderings. If fitness std <= 0.02 (less
   than one question), ordering does not matter for this model/task —
   stop and report the negative result (do not spend the full budget).
2. ENUMERATION: all 720 orderings x 32 questions.
3. D14 PRE-FLIGHT on the enumerated landscape: rho1 per operator + FDC.
4. SEARCH COMPARISON (free, cached): PRISM (portfolio; D12 settings)
   vs random-without-replacement, evals-to-first-optimum + quality at
   budgets.

API key: Google Cloud Secret Manager (GOOGLE_API_KEY), fetched at run
time (D10). Concurrency 6, exponential backoff on 429/5xx.

Usage: python llm_chain_experiment.py [budget-seconds]
Outputs -> experiments/iteration-09/results/
"""

import csv
import itertools
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, os.path.join(ROOT, "prism-research"))

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "results")
CACHE_CSV = os.path.join(OUT, "answer_cache.csv")   # perm,qidx,correct
QUESTIONS = json.load(open(os.path.join(HERE, "data",
                                        "gsm8k_subset32.json")))
MODEL = "gemini-2.5-flash-lite"
URL = (f"https://generativelanguage.googleapis.com/v1beta/models/"
       f"{MODEL}:generateContent")
BUDGET_SECONDS = None
_START = time.time()
_LOCK = threading.Lock()

MODULES = [
    "RESTATE: Restate the problem briefly in your own words.",
    "IDENTIFY: List the known quantities and what is being asked.",
    "PLAN: Devise a short step-by-step strategy before calculating.",
    "COMPUTE: Carry out the calculations step by step.",
    "CHECK: Verify the result against the problem statement.",
    "ANSWER: State the final answer on its own line as "
    "'Answer: <number>'.",
]
N = 6


class BudgetExceeded(Exception):
    pass


def get_key():
    r = subprocess.run(["gcloud", "secrets", "versions", "access",
                        "latest", "--secret=GOOGLE_API_KEY"],
                       capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        sys.exit("secret access failed: " + r.stderr[:200])
    return r.stdout.strip()


KEY = get_key()


def build_prompt(perm, question):
    steps = "\n".join(f"{i+1}. {MODULES[m]}"
                      for i, m in enumerate(perm))
    return (f"Solve the following math problem. Work through these "
            f"steps in this exact order:\n{steps}\n\n"
            f"Problem: {question}")


def extract_answer(text):
    m = re.findall(r"Answer:\s*\$?(-?[\d,]+(?:\.\d+)?)", text)
    if not m:
        m = re.findall(r"(-?[\d,]+(?:\.\d+)?)", text)
    if not m:
        return None
    return m[-1].replace(",", "").rstrip(".")


def ask(perm, qidx, retries=5):
    q = QUESTIONS[qidx]
    for attempt in range(retries):
        try:
            r = requests.post(
                URL, params={"key": KEY},
                json={"contents": [{"parts": [{"text": build_prompt(
                    perm, q["question"])}]}],
                    "generationConfig": {"temperature": 0,
                                         "maxOutputTokens": 600}},
                timeout=60)
            if r.status_code == 200:
                try:
                    text = (r.json()["candidates"][0]["content"]
                            ["parts"][0]["text"])
                except (KeyError, IndexError):
                    return 0  # empty/blocked response counts as wrong
                pred = extract_answer(text)
                try:
                    return int(abs(float(pred or "nan")
                                   - float(q["gold"])) < 1e-6)
                except ValueError:
                    return 0
            if r.status_code in (429, 500, 502, 503):
                time.sleep(min(2 ** attempt * 2, 30))
                continue
            print(f"  API {r.status_code}: {r.text[:120]}", flush=True)
            time.sleep(2)
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return None  # persistent failure: leave uncached, retry next run


def load_cache():
    cache = {}
    if os.path.exists(CACHE_CSV):
        for r in csv.reader(open(CACHE_CSV)):
            if r and r[0] != "perm":
                cache[(r[0], int(r[1]))] = int(r[2])
    return cache


def eval_orderings(perms, cache):
    """Fill the answer cache for the given orderings; returns fitness
    per ordering or raises BudgetExceeded."""
    jobs = [(json.dumps(list(p)), qi)
            for p in perms for qi in range(len(QUESTIONS))
            if (json.dumps(list(p)), qi) not in cache]
    if jobs:
        f = open(CACHE_CSV, "a", newline="")
        wr = csv.writer(f)
        if os.path.getsize(CACHE_CSV) == 0 if os.path.exists(CACHE_CSV) else True:
            pass
        done_ct = 0

        def work(job):
            key, qi = job
            res = ask(json.loads(key), qi)
            return key, qi, res

        with ThreadPoolExecutor(max_workers=20) as ex:
            for key, qi, res in ex.map(work, jobs):
                if res is not None:
                    with _LOCK:
                        wr.writerow([key, qi, res])
                        f.flush()
                        cache[(key, qi)] = res
                done_ct += 1
                if done_ct % 200 == 0:
                    print(f"  {done_ct}/{len(jobs)} calls, "
                          f"{time.time()-_START:.0f}s", flush=True)
                if BUDGET_SECONDS and time.time() - _START > BUDGET_SECONDS:
                    f.close()
                    raise BudgetExceeded
        f.close()
    fits = {}
    for p in perms:
        key = json.dumps(list(p))
        vals = [cache.get((key, qi)) for qi in range(len(QUESTIONS))]
        if all(v is not None for v in vals):
            fits[key] = sum(vals) / len(vals)
    return fits


def main():
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(CACHE_CSV):
        with open(CACHE_CSV, "w", newline="") as f:
            csv.writer(f).writerow(["perm", "qidx", "correct"])
    cache = load_cache()
    print(f"cache: {len(cache)} answers", flush=True)
    rng = np.random.default_rng(7)

    try:
        # ---- Stage 1: variance gate ----
        gate_perms = [[int(x) for x in rng.permutation(N)]
                      for _ in range(30)]
        fits = eval_orderings(gate_perms, cache)
        vals = np.array(list(fits.values()))
        std = vals.std()
        line = (f"STAGE 1 (variance gate): 30 orderings, mean acc "
                f"{vals.mean():.3f}, min {vals.min():.3f}, max "
                f"{vals.max():.3f}, std {std:.4f} -> "
                f"{'PROCEED' if std > 0.02 else 'STOP: order does not matter'}")
        print(line, flush=True)
        with open(os.path.join(OUT, "stage1_gate.txt"), "w") as f:
            f.write(line + "\n")
        if std <= 0.02:
            print("STUDY COMPLETE (negative result at gate).")
            return

        # ---- Stage 2: full enumeration ----
        all_perms = [list(p) for p in itertools.permutations(range(N))]
        fits = eval_orderings(all_perms, cache)
        print(f"enumeration: {len(fits)}/720 orderings complete",
              flush=True)
        if len(fits) < 720:
            print("BUDGET REACHED; rerun to resume")
            return
        with open(os.path.join(OUT, "llm_landscape.csv"), "w",
                  newline="") as f:
            w = csv.writer(f)
            w.writerow(["perm", "fitness"])
            for k, v in fits.items():
                w.writerow([k, v])
        print("STAGE 2 complete: landscape written. Run "
              "analyze_llm_landscape.py next.", flush=True)
    except BudgetExceeded:
        print(f"BUDGET REACHED after {time.time()-_START:.0f}s; "
              "rerun to resume", flush=True)
        return
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BUDGET_SECONDS = float(sys.argv[1])
    main()
