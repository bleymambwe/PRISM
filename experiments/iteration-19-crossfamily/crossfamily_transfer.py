"""Iteration 19, Experiment Q2: cross-FAMILY SLM transfer (Qwen + Llama legs).

Extends Experiment Q (iteration-17, Flash-Lite -> Gemma) to two more small-model
families, per benchmark #1 in `claude prism benchmark recomendation/`. The
Gemma result was asymmetric (pathology transfers decisively, optimality
marginally, positional structure not at all); these legs arbitrate whether
that asymmetry is Gemma-specific or the cross-model rule.

Design: IDENTICAL to Experiment Q — same 6 modules, same 32 GSM8K questions,
same 120 orderings (100 random seed-17 + source top-15 + bottom-5 from the
Experiment K flash-lite landscape). 3,840 cells per model, cached per
(ordering, question), resumable, budget-chunked.

Provider: OpenRouter (OpenAI-compatible chat completions). Key read from GCP
Secret Manager secret OPENROUTER_API_KEY. Reasoning/thinking disabled so the
target models answer directly (parity with Gemma/Flash-Lite runs).

Usage:
  python crossfamily_transfer.py qwen --test          # one live call, prints reply
  python crossfamily_transfer.py qwen [budget-secs]   # run/resume the qwen leg
  python crossfamily_transfer.py llama [budget-secs]  # run/resume the llama leg
When a leg's cache is complete it writes results/<leg>_transfer_report.txt
and prints STUDY COMPLETE.
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

LEGS = {
    # leg -> (openrouter model id, $/M input est., $/M output est.)
    "qwen": ("qwen/qwen3-4b-instruct-2507", 0.06, 0.24),
    "llama": ("meta-llama/llama-3.2-3b-instruct", 0.02, 0.04),
}

QUESTIONS = json.load(open(os.path.join(
    ROOT, "experiments", "iteration-09", "data", "gsm8k_subset32.json")))
URL = "https://openrouter.ai/api/v1/chat/completions"
MAX_CALLS = 6000  # hard cap per leg
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
     "--secret=OPENROUTER_API_KEY"],
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
    def __init__(self, leg):
        self.model, self.pin, self.pout = LEGS[leg]
        self.usage_csv = os.path.join(OUT, f"{leg}_token_usage.csv")
        self.calls = 0
        self.tin = 0
        self.tout = 0
        if os.path.exists(self.usage_csv):
            r = list(csv.DictReader(open(self.usage_csv)))[-1]
            self.calls, self.tin, self.tout = (int(r["calls"]),
                                               int(r["tin"]),
                                               int(r["tout"]))

    def save(self):
        with open(self.usage_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["calls", "tin", "tout",
                                              "usd_est"])
            w.writeheader()
            w.writerow({"calls": self.calls, "tin": self.tin,
                        "tout": self.tout,
                        "usd_est": round(self.tin / 1e6 * self.pin
                                         + self.tout / 1e6 * self.pout, 3)})

    def ask(self, perm, qidx, retries=6):
        import requests
        with _LOCK:
            if self.calls >= MAX_CALLS:
                raise Budget("call cap")
            self.calls += 1
        q = QUESTIONS[qidx]
        body = {
            "model": self.model,
            "messages": [{"role": "user",
                          "content": build_prompt(perm, q["question"])}],
            "temperature": 0,
            "max_tokens": 800,
            "reasoning": {"enabled": False},
        }
        for attempt in range(retries):
            try:
                r = requests.post(
                    URL, json=body, timeout=90,
                    headers={"Authorization": f"Bearer {KEY}"})
                if r.status_code == 200:
                    j = r.json()
                    um = j.get("usage", {})
                    with _LOCK:
                        self.tin += um.get("prompt_tokens", 0)
                        self.tout += um.get("completion_tokens", 0)
                    try:
                        text = j["choices"][0]["message"]["content"]
                    except (KeyError, IndexError, TypeError):
                        return 0
                    p = extract(text or "")
                    try:
                        return int(abs(float(p or "nan")
                                       - float(q["gold"])) < 1e-6)
                    except ValueError:
                        return 0
                if r.status_code in (402,):
                    raise Budget("provider says out of credits (402)")
                if r.status_code in (429, 500, 502, 503):
                    time.sleep(min(2 ** attempt * 3, 45))
                    continue
                time.sleep(2)
            except Budget:
                raise
            except Exception:
                time.sleep(2 ** attempt)
        return None


def target_orderings():
    """100 random (seed 17) + source top-15 + source bottom-5.
    Identical selection to iteration-17/slm_transfer.py."""
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


def spearman(a, b):
    ra = np.argsort(np.argsort(a))
    rb = np.argsort(np.argsort(b))
    return float(np.corrcoef(ra, rb)[0, 1])


def main(leg):
    api = Api(leg)
    cache_csv = os.path.join(OUT, f"{leg}_answer_cache.csv")
    src, rand, top15, bot5 = target_orderings()
    allp = rand + top15 + bot5
    if not os.path.exists(cache_csv):
        with open(cache_csv, "w", newline="") as f:
            csv.writer(f).writerow(["perm", "qidx", "correct"])
    cache = {}
    for r in csv.reader(open(cache_csv)):
        if r and r[0] != "perm":
            cache[(r[0], int(r[1]))] = int(r[2])
    jobs = [(json.dumps(list(p)), qi) for p in allp
            for qi in range(len(QUESTIONS))
            if (json.dumps(list(p)), qi) not in cache]
    print(f"[{leg}:{api.model}] cache {len(cache)} · to do {len(jobs)} · "
          f"calls so far {api.calls}/{MAX_CALLS}", flush=True)
    if jobs:
        f = open(cache_csv, "a", newline="")
        wr = csv.writer(f)
        done = 0

        def work(job):
            k, qi = job
            return k, qi, api.ask(json.loads(k), qi)

        try:
            with ThreadPoolExecutor(max_workers=8) as ex:
                for k, qi, res in ex.map(work, jobs):
                    if res is not None:
                        with _LOCK:
                            wr.writerow([k, qi, res])
                            f.flush()
                            cache[(k, qi)] = res
                    done += 1
                    if done % 200 == 0:
                        api.save()
                        print(f"  {done}/{len(jobs)} "
                              f"({time.time()-_START:.0f}s)", flush=True)
                    if (BUDGET_SECONDS
                            and time.time() - _START > BUDGET_SECONDS):
                        raise Budget("wall clock")
        except Budget as e:
            f.close()
            api.save()
            print(f"PAUSED ({e}); rerun to resume", flush=True)
            return
        f.close()
        api.save()

    # ---------------- analysis (mirrors iteration-17) ----------------
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
    lines = [f"MODEL: {api.model} (leg '{leg}')"]
    rand_t = np.array([tgt[p] for p in rand])
    rand_s = np.array([src[p] for p in rand])
    rng2 = np.random.default_rng(99)
    rhos = []
    for _ in range(4000):
        idx = rng2.integers(0, 100, 100)
        rhos.append(spearman(rand_s[idx], rand_t[idx]))
    lines.append("\nQ1 cross-model fitness correlation (100 random "
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
    pos_s = np.zeros((N, N))
    for k, v in src.items():
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
    lines.append(f"  target ({leg})       ANSWER row: " +
                 " ".join(f"{pos_t[5][i]:.2f}" for i in range(N)))

    top_t = np.array([tgt[p] for p in top15])
    bot_t = np.array([tgt[p] for p in bot5])
    g = np.random.default_rng(42)
    d = [top_t[g.integers(0, 15, 15)].mean()
         - rand_t[g.integers(0, 100, 100)].mean() for _ in range(10000)]
    db = [rand_t[g.integers(0, 100, 100)].mean()
          - bot_t[g.integers(0, 5, 5)].mean() for _ in range(10000)]
    lines.append("\nQ3 extreme-ordering transfer:")
    lines.append(f"  source TOP-15  -> target mean {top_t.mean():.3f} "
                 f"(min {top_t.min():.3f}); top-minus-random diff CI "
                 f"[{np.percentile(d,2.5):+.3f}, "
                 f"{np.percentile(d,97.5):+.3f}]")
    lines.append(f"  random-100     -> target mean {rand_t.mean():.3f}")
    lines.append(f"  source BOTTOM-5-> target mean {bot_t.mean():.3f} "
                 f"(max {bot_t.max():.3f}); random-minus-bottom diff CI "
                 f"[{np.percentile(db,2.5):+.3f}, "
                 f"{np.percentile(db,97.5):+.3f}]")

    lines.append("\nQ4 order sensitivity (same 32 questions):")
    lines.append(f"  flash-lite (source): mean {rand_s.mean():.3f}, "
                 f"std {rand_s.std():.3f}, range "
                 f"[{rand_s.min():.2f}, {rand_s.max():.2f}]")
    lines.append(f"  {leg} (target): mean {rand_t.mean():.3f}, "
                 f"std {rand_t.std():.3f}, range "
                 f"[{rand_t.min():.2f}, {rand_t.max():.2f}]")

    score = rand_s
    k10 = 10
    topidx = np.argsort(score)[-k10:]
    tops = []
    for _ in range(4000):
        idx = rng2.integers(0, 100, 100)
        s2, t2 = score[idx], rand_t[idx]
        tops.append(t2[np.argsort(s2)[-k10:]].mean())
    lines.append("\nQ5 warm-start (top-10% of random pool by SOURCE "
                 "fitness):")
    lines.append(f"  mean target accuracy {rand_t[topidx].mean():.3f} "
                 f"[{np.percentile(tops,2.5):.3f}, "
                 f"{np.percentile(tops,97.5):.3f}] vs random mean "
                 f"{rand_t.mean():.3f}")
    usd = api.tin / 1e6 * api.pin + api.tout / 1e6 * api.pout
    lines.append(f"\nspend: {api.calls} calls; est ~${usd:.2f}")
    text = "\n".join(lines)
    open(os.path.join(OUT, f"{leg}_transfer_report.txt"), "w").write(
        text + "\n")
    print(text)
    print("STUDY COMPLETE.")


def selftest(leg):
    api = Api(leg)
    if not KEY:
        print("NO KEY: secret OPENROUTER_API_KEY is empty/missing.")
        return
    perm = [0, 1, 2, 3, 4, 5]
    res = api.ask(perm, 0)
    q = QUESTIONS[0]
    print(f"model={api.model}  gold={q['gold']}  graded={res}")
    api.save()
    print("SELFTEST OK" if res is not None else "SELFTEST FAILED (no reply)")


if __name__ == "__main__":
    leg_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    if leg_arg not in LEGS:
        sys.exit(f"usage: crossfamily_transfer.py {{{'|'.join(LEGS)}}} "
                 f"[budget-seconds|--test]")
    if len(sys.argv) > 2 and sys.argv[2] == "--test":
        selftest(leg_arg)
    else:
        if len(sys.argv) > 2:
            BUDGET_SECONDS = float(sys.argv[2])
        main(leg_arg)
