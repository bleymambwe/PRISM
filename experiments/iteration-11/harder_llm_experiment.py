"""Iteration 11, Experiment M: the harder LLM instance.

n = 8 reasoning modules -> 8! = 40,320 orderings (NOT enumerable in
budget). This is the first PRISM application run entirely on
sample-based statistics — the regime every real problem lives in.

Modules (first 20 questions of the fixed seed-42 GSM8K subset, same
model/settings as Experiment K so results are comparable):
RESTATE, IDENTIFY, ESTIMATE, PLAN, SIMPLIFY, COMPUTE, CHECK, ANSWER.

Staged protocol (all resumable via the per-(ordering,question) cache):
1. VARIANCE GATE: 30 random orderings; stop if std <= 0.02.
2. SAMPLED D14 PRE-FLIGHT: 100 random base orderings + 1 one-move
   neighbor each (25 per operator) -> rho1 per operator; approximate
   FDC = corr(fitness, Cayley distance to the BEST-KNOWN ordering).
   Prints the D14/D15 decision (operator, replacement policy, whether
   search should beat random).
3. SEARCH: PRISM (configured per the pre-flight; D12 scale-aware
   pop 40 / p_m 0.5) vs random sampling, 4 seeds each, budget = 120
   distinct orderings per run. Metric: best-found at budgets
   {30, 60, 120} + mean rank of final best.

BUDGET: hard cap MAX_CALLS = 28000 API calls (~$6 at Flash-Lite
prices); the script refuses new calls beyond it. Actual token usage is
accumulated from usageMetadata and reported.

Usage: python harder_llm_experiment.py [budget-seconds]
Outputs -> experiments/iteration-11/results/
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
sys.path.insert(0, os.path.join(ROOT, "prism-research"))

HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "results")
CACHE_CSV = os.path.join(OUT, "answer_cache.csv")
USAGE_CSV = os.path.join(OUT, "token_usage.csv")
QFILE = os.path.join(ROOT, "experiments", "iteration-09", "data",
                     "gsm8k_subset32.json")
N_Q = 20
QUESTIONS = json.load(open(QFILE))[:N_Q]
MODEL = "gemini-2.5-flash-lite"
URL = (f"https://generativelanguage.googleapis.com/v1beta/models/"
       f"{MODEL}:generateContent")
MAX_CALLS = 28000
BUDGET_SECONDS = None
_START = time.time()
_LOCK = threading.Lock()

MODULES = [
    "RESTATE: Restate the problem briefly in your own words.",
    "IDENTIFY: List the known quantities and what is being asked.",
    "ESTIMATE: Make a rough order-of-magnitude estimate of the answer.",
    "PLAN: Devise a short step-by-step strategy before calculating.",
    "SIMPLIFY: Note any way to simplify the problem before solving.",
    "COMPUTE: Carry out the calculations step by step.",
    "CHECK: Verify the result against the problem statement.",
    "ANSWER: State the final answer on its own line as "
    "'Answer: <number>'.",
]
N = 8


class Budget(Exception):
    pass


def get_key():
    r = subprocess.run(["gcloud", "secrets", "versions", "access",
                        "latest", "--secret=GOOGLE_API_KEY"],
                       capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        sys.exit("secret access failed")
    return r.stdout.strip()


KEY = get_key()


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
        self.tok_in = 0
        self.tok_out = 0
        if os.path.exists(USAGE_CSV):
            for r in csv.DictReader(open(USAGE_CSV)):
                self.calls = int(r["calls"])
                self.tok_in = int(r["tok_in"])
                self.tok_out = int(r["tok_out"])

    def save(self):
        with open(USAGE_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["calls", "tok_in",
                                              "tok_out", "usd_est"])
            w.writeheader()
            usd = self.tok_in / 1e6 * 0.10 + self.tok_out / 1e6 * 0.40
            w.writerow({"calls": self.calls, "tok_in": self.tok_in,
                        "tok_out": self.tok_out,
                        "usd_est": round(usd, 3)})

    def ask(self, perm, qidx, retries=5):
        import requests
        with _LOCK:
            if self.calls >= MAX_CALLS:
                raise Budget("API call cap reached")
            self.calls += 1
        q = QUESTIONS[qidx]
        for attempt in range(retries):
            try:
                r = requests.post(URL, params={"key": KEY}, json={
                    "contents": [{"parts": [{"text": build_prompt(
                        perm, q["question"])}]}],
                    "generationConfig": {"temperature": 0,
                                         "maxOutputTokens": 650}},
                    timeout=60)
                if r.status_code == 200:
                    j = r.json()
                    um = j.get("usageMetadata", {})
                    with _LOCK:
                        self.tok_in += um.get("promptTokenCount", 0)
                        self.tok_out += um.get(
                            "candidatesTokenCount", 0)
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
                    time.sleep(min(2 ** attempt * 2, 30))
                    continue
                time.sleep(2)
            except Exception:
                time.sleep(2 ** attempt)
        return None


API = Api()


def load_cache():
    c = {}
    if os.path.exists(CACHE_CSV):
        for r in csv.reader(open(CACHE_CSV)):
            if r and r[0] != "perm":
                c[(r[0], int(r[1]))] = int(r[2])
    return c


CACHE = None


def fitness_many(perms):
    """Evaluate orderings (list of lists) via cache + threads.
    Returns dict key->fitness for fully-answered orderings."""
    jobs = [(json.dumps([int(x) for x in p]), qi)
            for p in perms for qi in range(N_Q)
            if (json.dumps([int(x) for x in p]), qi) not in CACHE]
    if jobs:
        f = open(CACHE_CSV, "a", newline="")
        wr = csv.writer(f)
        done = 0

        def work(job):
            k, qi = job
            return k, qi, API.ask(json.loads(k), qi)

        with ThreadPoolExecutor(max_workers=16) as ex:
            for k, qi, res in ex.map(work, jobs):
                if res is not None:
                    with _LOCK:
                        wr.writerow([k, qi, res])
                        f.flush()
                        CACHE[(k, qi)] = res
                done += 1
                if done % 300 == 0:
                    API.save()
                    print(f"  {done}/{len(jobs)} calls "
                          f"({API.calls} total, "
                          f"{time.time()-_START:.0f}s)", flush=True)
                if BUDGET_SECONDS and time.time() - _START > BUDGET_SECONDS:
                    f.close()
                    API.save()
                    raise Budget("wall clock")
        f.close()
        API.save()
    out = {}
    for p in perms:
        k = json.dumps([int(x) for x in p])
        vals = [CACHE.get((k, qi)) for qi in range(N_Q)]
        if all(v is not None for v in vals):
            out[k] = sum(vals) / N_Q
    return out


def fitness_one(perm):
    return fitness_many([perm])[json.dumps([int(x) for x in perm])]


def cayley(p, q):
    n = len(p)
    qinv = [0] * n
    for i, v in enumerate(q):
        qinv[v] = i
    r = [qinv[v] for v in p]
    seen = [False] * n
    c = 0
    for i in range(n):
        if not seen[i]:
            c += 1
            j = i
            while not seen[j]:
                seen[j] = True
                j = r[j]
    return n - c


def main():
    global CACHE
    os.makedirs(OUT, exist_ok=True)
    if not os.path.exists(CACHE_CSV):
        with open(CACHE_CSV, "w", newline="") as f:
            csv.writer(f).writerow(["perm", "qidx", "correct"])
    CACHE = load_cache()
    print(f"cache {len(CACHE)} answers · api calls so far {API.calls} "
          f"(cap {MAX_CALLS})", flush=True)
    rng = np.random.default_rng(11)
    from core.prism import PRISM, MUTATIONS

    try:
        # ---- Stage 1: gate ----
        gate = [[int(x) for x in rng.permutation(N)] for _ in range(30)]
        fits = fitness_many(gate)
        v = np.array(list(fits.values()))
        print(f"STAGE 1: mean {v.mean():.3f} min {v.min():.3f} max "
              f"{v.max():.3f} std {v.std():.4f} -> "
              f"{'PROCEED' if v.std() > .02 else 'STOP'}", flush=True)
        if v.std() <= .02:
            return

        # ---- Stage 2: sampled pre-flight ----
        base = [[int(x) for x in rng.permutation(N)]
                for _ in range(100)]
        ops = list(MUTATIONS)
        pairs = []
        for i, b in enumerate(base):
            op = ops[i % 4]
            nb = b.copy()
            MUTATIONS[op](nb, rng)
            pairs.append((op, b, nb))
        allp = base + [p[2] for p in pairs]
        fits = fitness_many(allp + gate)
        rho = {}
        for op in ops:
            f0 = [fits[json.dumps(b)] for o, b, nb in pairs if o == op]
            f1 = [fits[json.dumps(nb)] for o, b, nb in pairs if o == op]
            rho[op] = float(np.corrcoef(f0, f1)[0, 1])
        best_k = max(fits, key=fits.get)
        best_p = json.loads(best_k)
        fs, ds = [], []
        for k, fv in fits.items():
            fs.append(fv)
            ds.append(cayley(json.loads(k), best_p))
        afdc = float(np.corrcoef(fs, ds)[0, 1])
        chosen = max((o for o in ops if o != "scramble"),
                     key=lambda o: rho[o])
        pre = (f"STAGE 2 pre-flight ({len(fits)} sampled orderings): "
               f"rho1 " +
               ", ".join(f"{o}={rho[o]:.2f}" for o in ops) +
               f" | approx-FDC(best-known) {afdc:.3f}\n"
               f"  D14 decision: operator={chosen}; "
               f"{'search should beat random' if afdc < -0.15 else 'random likely competitive'}"
               f" | best sampled fitness {fits[best_k]:.3f}")
        print(pre, flush=True)
        open(os.path.join(OUT, "preflight.txt"), "w").write(pre + "\n")

        # ---- Stage 3: search comparison ----
        EVAL_BUDGET = 120
        rows_path = os.path.join(OUT, "search_results.csv")
        done = set()
        if os.path.exists(rows_path):
            for r in csv.DictReader(open(rows_path)):
                done.add((r["method"], int(r["seed"])))
        for seed in range(4):
            for method in ("prism", "random"):
                if (method, seed) in done:
                    continue
                seen = {}

                def track_fit(perm, _s=seen):
                    k = json.dumps([int(x) for x in perm])
                    if k not in _s:
                        if len(_s) >= EVAL_BUDGET:
                            return 0.0
                        _s[k] = fitness_one(perm)
                    return _s[k]

                if method == "prism":
                    PRISM(n=N, fitness_fn=track_fit, seed=seed,
                          mutation=chosen, pop_size=40,
                          p_m=0.5).evolve(generations=300)
                else:
                    r2 = np.random.default_rng(4000 + seed)
                    perms, ks = [], set()
                    while len(perms) < EVAL_BUDGET:
                        p = [int(x) for x in r2.permutation(N)]
                        k = json.dumps(p)
                        if k not in ks:
                            ks.add(k)
                            perms.append(p)
                    fits2 = fitness_many(perms)  # batched, parallel
                    for p in perms:
                        track_fit(p)
                curve = {}
                best = -1
                for i, (k, fv) in enumerate(seen.items(), 1):
                    best = max(best, fv)
                    curve[i] = best
                mx = max(curve)
                row = {"method": method, "seed": seed,
                       **{f"best@{b}": round(curve[min(b, mx)], 4)
                          for b in (30, 60, 120)},
                       "best_perm": max(seen, key=seen.get)}
                new = not os.path.exists(rows_path)
                with open(rows_path, "a", newline="") as f:
                    w = csv.DictWriter(f, fieldnames=list(row.keys()))
                    if new:
                        w.writeheader()
                    w.writerow(row)
                print(f"{method} seed={seed}: " +
                      " ".join(f"best@{b}={row[f'best@{b}']}"
                               for b in (30, 60, 120)), flush=True)

        rows = list(csv.DictReader(open(rows_path)))
        lines = []
        for b in (30, 60, 120):
            p = np.mean([float(r[f"best@{b}"]) for r in rows
                         if r["method"] == "prism"])
            q = np.mean([float(r[f"best@{b}"]) for r in rows
                         if r["method"] == "random"])
            lines.append(f"best@{b}: PRISM {p:.4f} vs random {q:.4f} "
                         f"({p-q:+.4f})")
        usd = API.tok_in / 1e6 * .10 + API.tok_out / 1e6 * .40
        lines.append(f"spend: {API.calls} calls, ~${usd:.2f}")
        summary = "\n".join(lines)
        open(os.path.join(OUT, "summary.txt"), "w").write(summary + "\n")
        print(summary, flush=True)
        print("STUDY COMPLETE.")
    except Budget as e:
        usd = API.tok_in / 1e6 * .10 + API.tok_out / 1e6 * .40
        print(f"PAUSED ({e}); {API.calls} calls, ~${usd:.2f}; rerun to "
              f"resume", flush=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        BUDGET_SECONDS = float(sys.argv[1])
    main()
