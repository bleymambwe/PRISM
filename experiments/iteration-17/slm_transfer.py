"""Iteration 17, Experiment Q: cross-model / SLM transfer.

Question: do instruction-ordering effects measured on one model
transfer to a different — and much SMALLER — model? This is both the
second-model replication the audit requested and the small-language-
model (SLM) application: if ordering knowledge transfers, order
optimization is free accuracy for on-device-class models.

Models:
  SOURCE  gemini-2.5-flash-lite  (Experiment K: full 720-ordering
          landscape already enumerated and committed)
  TARGET  gemma-4-26b-a4b-it     (4B ACTIVE parameters — SLM class;
          same API, temperature 0)

Design (n=6, same six modules and the same fixed 32-question GSM8K
subset as Experiment K, so fitness values are directly comparable):
  - 100 RANDOM orderings (seed 17)          -> unbiased correlation +
                                               position effects
  - TOP-15 orderings by source fitness      -> do the best transfer?
  - BOTTOM-5 orderings by source fitness    -> do the worst transfer?
  = 120 orderings x 32 questions = 3,840 calls, cached per
  (ordering, question); hard cap MAX_CALLS = 6,000; worst-case cost
  ~$0.9 even if billed at flash-lite rates (Gemma API tier is
  free-of-charge; tokens metered regardless).

Metrics:
  Q1 cross-model fitness correlation (Spearman + Pearson, random set)
  Q2 position-effect table correlation (36 cells, both models)
  Q3 top-ordering transfer: mean target accuracy of source-top-15 vs
     random-100 mean vs source-bottom-5
  Q4 order-sensitivity vs model size: fitness std + range, both models
  Q5 warm-start value on the SLM (top-10% by source score)

Usage: python slm_transfer.py [budget-seconds]
Outputs -> experiments/iteration-17/results/
"""

import csv
import json
import os
import re
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)
CACHE_CSV = os.path.join(OUT, "gemma_answer_cache.csv")
USAGE_CSV = os.path.join(OUT, "token_usage.csv")

QUESTIONS = json.load(open(os.path.join(
    ROOT, "experiments", "iteration-09", "data", "gsm8k_subset32.json")))
MODEL = "gemma-4-26b-a4b-it"
URL = (f"https://generativelanguage.googleapis.com/v1beta/models/"
       f"{MODEL}:generateContent")
MAX_CALLS = 6000
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


class Budget(Exception):
    pass


KEY = subprocess.run(
    ["gcloud", "secrets", "versions", "access", "latest",
     "--secret=GOOGLE_API_KEY"],
    capture_output=True, text=True, shell=True).stdout.strip()


def build_prompt(perm, q):
    steps = "\n".join(f"{i+1}. {MODULES[m]}" for i, m in enumerate(perm))
    return (f"Solve the following math problem. Work through these "
            f"steps in this exact order:\n{steps}\n\nProblem: {q}")


def extract(text):
    m = re.findall(r"Answer:\s*\$?(-?[\d,]+(?:\.\d+)?)", text)
    if not m:
        m = re.findall(r"(-?[\d,]+(?:\.\d+)?)", text)
    return m[-1].replace(",", "").rstrip(".") if m else None


class Api:
    def __init__(self):
        self.calls = 0
        self.tin = 0
        self.tout = 0
        if os.path.exists(USAGE_CSV):
            r = list(csv.DictReader(open(USAGE_CSV)))[-1]
            self.calls, self.tin, self.tout = (int(r["calls"]),
                                               int(r["tin"]),
                                               int(r["tout"]))

    def save(self):
        with open(USAGE_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["calls", "tin", "tout",
                                              "usd_worstcase"])
            w.writeheader()
            w.writerow({"calls": self.calls, "tin": self.tin,
                        "tout": self.tout,
                        "usd_worstcase": round(
                            self.tin / 1e6 * .10 + self.tout / 1e6 * .40,
                            3)})

    def ask(self, perm, qidx, retries=6):
        import requests
        with _LOCK:
            if self.calls >= MAX_CALLS:
                raise Budget("call cap")
            self.calls += 1
        q = QUESTIONS[qidx]
        for attempt in range(retries):
            try:
                r = requests.post(URL, params={"key": KEY}, json={
                    "contents": [{"parts": [{"text": build_prompt(
                        perm, q["question"])}]}],
                    "generationConfig": {"temperature": 0,
                                         "maxOutputTokens": 800}},
                    timeout=90)
                if r.status_code == 200:
                    j = r.json()
                    um = j.get("usageMetadata", {})
                    with _LOCK:
                        self.tin += um.get("promptTokenCount", 0)
                        self.tout += (um.get("candidatesTokenCount", 0)
                                      + um.get("thoughtsTokenCount", 0))
                    try:
                        text = (j["candidates"][0]["content"]["parts"]
                                [0]["text"])
                    except (KeyError, IndexError):
                        return 0
                    p = extract(text)
                    try:
                        return int(abs(float(p or "nan")
                                       - float(q["gold"])) < 1e-6)
                    except ValueError:
                        return 0
                if r.status_code in (429, 500, 502, 503):
                    time.sleep(min(2 ** attempt * 3, 45))
                    continue
                time.sleep(2)
            except Exception:
                time.sleep(2 ** attempt)
        return None


API = Api()


def target_orderings():
    """100 random (seed 17) + source top-15 + source bottom-5."""
    src = {tuple(json.loads(r["perm"])): float(r["fitness"])
           for r in csv.DictReader(open(os.path.join(
               ROOT, "experiments/iteration-09/results/"
                     "llm_landscape.csv")))}
    rng = np.random.default_rng(17)
    rand = []
    seen = set()
    while len(rand) < 100:
        p = tuple(int(x) for x in rng.permutation(N))
        if p not in seen:
            seen.add(p)
            rand.append(p)
    ranked = sorted(src, key=src.get)
    top15 = [p for p in ranked[::-1] if p not in seen][:15]
    bot5 = [p for p in ranked if p not in seen][:5]
    return src, rand, top15, bot5


def main():
    src, rand, top15, bot5 = target_orderings()
    allp = rand + top15 + bot5
    if not os.path.exists(CACHE_CSV):
        with open(CACHE_CSV, "w", newline="") as f:
            csv.writer(f).writerow(["perm", "qidx", "correct"])
    cache = {}
    for r in csv.reader(open(CACHE_CSV)):
        if r and r[0] != "perm":
            cache[(r[0], int(r[1]))] = int(r[2])
    jobs = [(json.dumps(list(p)), qi) for p in allp
            for qi in range(len(QUESTIONS))
            if (json.dumps(list(p)), qi) not in cache]
    print(f"cache {len(cache)} · to do {len(jobs)} · calls so far "
          f"{API.calls}/{MAX_CALLS}", flush=True)
    if jobs:
        f = open(CACHE_CSV, "a", newline="")
        wr = csv.writer(f)
        done = 0

        def work(job):
            k, qi = job
            return k, qi, API.ask(json.loads(k), qi)

        try:
            with ThreadPoolExecutor(max_workers=12) as ex:
                for k, qi, res in ex.map(work, jobs):
                    if res is not None:
                        with _LOCK:
                            wr.writerow([k, qi, res])
                            f.flush()
                            cache[(k, qi)] = res
                    done += 1
                    if done % 200 == 0:
                        API.save()
                        print(f"  {done}/{len(jobs)} "
                              f"({time.time()-_START:.0f}s)", flush=True)
                    if (BUDGET_SECONDS
                            and time.time() - _START > BUDGET_SECONDS):
                        raise Budget("wall clock")
        except Budget as e:
            f.close()
            API.save()
            print(f"PAUSED ({e}); rerun to resume", flush=True)
            return
        f.close()
        API.save()

    # ---------------- analysis ----------------
    def fit(p):
        k = json.dumps(list(p))
        vals = [cache.get((k, qi)) for qi in range(len(QUESTIONS))]
        return (sum(vals) / len(vals)
                if all(v is not None for v in vals) else None)

    tgt = {p: fit(p) for p in allp}
    missing = sum(1 for v in tgt.values() if v is None)
    if missing:
        print(f"{missing} orderings incomplete; rerun to finish")
        return
    lines = []
    rand_t = np.array([tgt[p] for p in rand])
    rand_s = np.array([src[p] for p in rand])

    def spearman(a, b):
        ra = np.argsort(np.argsort(a))
        rb = np.argsort(np.argsort(b))
        return float(np.corrcoef(ra, rb)[0, 1])

    rng2 = np.random.default_rng(99)
    rhos = []
    for _ in range(4000):
        idx = rng2.integers(0, 100, 100)
        rhos.append(spearman(rand_s[idx], rand_t[idx]))
    lines.append("Q1 cross-model fitness correlation (100 random "
                 "orderings):")
    lines.append(f"  Spearman rho = {spearman(rand_s, rand_t):.3f} "
                 f"[{np.percentile(rhos,2.5):.3f}, "
                 f"{np.percentile(rhos,97.5):.3f}] | Pearson r = "
                 f"{float(np.corrcoef(rand_s, rand_t)[0,1]):.3f}")

    pos_t = np.zeros((N, N))
    cnt = np.zeros((N, N))
    for p in rand:
        for i, m in enumerate(p):
            pos_t[m][i] += tgt[p]
            cnt[m][i] += 1
    pos_t = np.divide(pos_t, np.maximum(cnt, 1))
    land6 = src
    pos_s = np.zeros((N, N))
    for k, v in land6.items():
        for i, m in enumerate(k):
            pos_s[m][i] += v
    pos_s /= 120
    mask = cnt.ravel() > 0
    r_pos = float(np.corrcoef(pos_s.ravel()[mask],
                              pos_t.ravel()[mask])[0, 1])
    lines.append(f"\nQ2 position-effect table correlation "
                 f"({int(mask.sum())} cells): Pearson r = {r_pos:.3f}")
    lines.append("  source (flash-lite) ANSWER row: " +
                 " ".join(f"{pos_s[5][i]:.2f}" for i in range(N)))
    lines.append("  target (gemma-4B)   ANSWER row: " +
                 " ".join(f"{pos_t[5][i]:.2f}" for i in range(N)))

    top_t = np.array([tgt[p] for p in top15])
    bot_t = np.array([tgt[p] for p in bot5])
    lines.append(f"\nQ3 extreme-ordering transfer on the SLM:")
    lines.append(f"  source TOP-15 orderings  -> target mean "
                 f"{top_t.mean():.3f} (min {top_t.min():.3f})")
    lines.append(f"  random-100               -> target mean "
                 f"{rand_t.mean():.3f}")
    lines.append(f"  source BOTTOM-5 orderings-> target mean "
                 f"{bot_t.mean():.3f} (max {bot_t.max():.3f})")

    lines.append(f"\nQ4 order sensitivity vs model size (same 32 "
                 f"questions):")
    lines.append(f"  flash-lite (source): mean {rand_s.mean():.3f}, "
                 f"std {rand_s.std():.3f}, range "
                 f"[{rand_s.min():.2f}, {rand_s.max():.2f}]")
    lines.append(f"  gemma-4B active (SLM): mean {rand_t.mean():.3f}, "
                 f"std {rand_t.std():.3f}, range "
                 f"[{rand_t.min():.2f}, {rand_t.max():.2f}]")

    score = rand_s  # source fitness as the transferred score
    k10 = 10
    topidx = np.argsort(score)[-k10:]
    tops = []
    for _ in range(4000):
        idx = rng2.integers(0, 100, 100)
        s2, t2 = score[idx], rand_t[idx]
        tops.append(t2[np.argsort(s2)[-k10:]].mean())
    lines.append(f"\nQ5 warm-start on the SLM (top-10% by SOURCE "
                 f"fitness):")
    lines.append(f"  mean target accuracy {rand_t[topidx].mean():.3f} "
                 f"[{np.percentile(tops,2.5):.3f}, "
                 f"{np.percentile(tops,97.5):.3f}] vs random mean "
                 f"{rand_t.mean():.3f}")
    usd = API.tin / 1e6 * .10 + API.tout / 1e6 * .40
    lines.append(f"\nspend: {API.calls} calls; worst-case if billed "
                 f"~${usd:.2f} (Gemma API tier is free-of-charge)")
    text = "\n".join(lines)
    open(os.path.join(OUT, "slm_transfer_report.txt"), "w").write(
        text + "\n")
    print(text)
    print("STUDY COMPLETE.")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BUDGET_SECONDS = float(sys.argv[1])
    main()
