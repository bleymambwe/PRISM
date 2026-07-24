"""Iteration 23, Experiment S: high-resolution hard-reasoning ordering
landscape (Benchmark #2). Approved by Bley 2026-07-22 after HTML review
brief; full spec in docs/RESEARCH_STATUS_COMPREHENSIVE_2026-07-12.md S11.

Question: do transfer + pre-flight results (Exps K, M, O, Q, Q2) hold on
a SPARSE-OPTIMUM, HIGH-RESOLUTION landscape -- competition math instead
of grade-school arithmetic -- where the earlier caveats (dense optima,
Qwen ceiling-compression) don't apply?

Same 8 reasoning modules as Experiment M (RESTATE..ANSWER). 100 MATH-500
problems (levels 3-5, SIMPLE canonical-form answers only -- integer /
a-over-b fraction / decimal -- for a frozen, deterministic, auditable
grader with no external-library reliability risk; see
_grader_test.py, 13/13 unit tests). Model: Qwen3-30B-A3B-Instruct
(3B active) via OpenRouter, same as the winning cross-family leg.

Registered hypotheses H19-H23 (see status doc S11.2); H22's numeric
forecast is written to preflight_result.json and committed to git
BEFORE the main landscape gathering begins -- that commit timestamp is
the pre-registration.

Five stages, each resumable/kill-safe, run by repeated invocation:
  python experiment_s.py [budget-seconds]
    1. PILOT      10 orderings x 20 questions (~$0.05) -> accuracy in
                   [0.20,0.60] gate. On FAIL the script stops and
                   prints the accuracy; per the approved spec, an
                   out-of-band model is swapped by hand (MODEL
                   constant) and results/ archived before rerunning,
                   not auto-resampled under the same model.
    2. PRE-FLIGHT  ~90 move-pairs x 25 questions (~$1) -> rho1/FDC,
                   H22 forecast committed to preflight_result.json.
    3. MAIN        150 random + 50 transfer-guided + 50 searcher-
                   selected orderings x 100 questions (~25,000 calls).
    4. ANALYSIS    free; landscape stats, position table, H19/H20/H23,
                   and the guided-vs-PRISM-vs-random race (H21) via
                   40-seed bootstrap replay over the frozen cache.
    5. (archival is a separate, manual git step per ARCHIVAL_PROTOCOL)

Cost guard: two independent meters (API-reported usage.cost + the
OpenRouter key-usage endpoint), hard cap $10.00 (the approved
worst-case), scoped to this experiment's own results/spend_guard.json
-- a fresh envelope, not shared with the iteration-19 cross-family cap.

Usage:
  python experiment_s.py --test          one live call, sanity check
  python experiment_s.py [budget-secs]   run/resume; prints STUDY
                                          COMPLETE when stage 4 is done
"""

import csv
import json
import math
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
HERE = os.path.dirname(__file__)
OUT = os.path.join(HERE, "results")
os.makedirs(OUT, exist_ok=True)

# Model-selection history (D16 gate, 2026-07-22). Every model tried at
# max_tokens 2000-2500 clustered at 60-76% -- too strong for this
# simple-canonical-answer-filtered MATH-500 pool (the answer-form
# filter, needed for a reliable frozen grader without an external
# library, appears to have selected somewhat easier problems within
# each level than the raw level 3-5 distribution):
#   qwen3-30b-a3b-instruct-2507  formal pilot -> 76%(n=200) -- TOO
#     STRONG, archived to results/_attempt1_qwen3-30b-a3b_too_strong/
#   qwen/qwen3-8b  formal pilot -> 70%(n=200) -- TOO STRONG (even
#     level-5-only within this pilot's cache read 60%, right at the
#     ceiling, but too few level-5 simple-answer items exist (75) to
#     build a 100-question level-5-only pool); archived to
#     results/_attempt2_qwen3-8b_too_strong/
#   mistralai/ministral-8b-2512  informal probe -> 70%(n=10) -- TOO
#     STRONG, not pursued further
#   google/gemma-3-4b-it  formal pilot -> 66.5%(n=200) -- TOO STRONG
#     (closest yet); archived to
#     results/_attempt3_gemma3-4b_too_strong/
#   meta-llama/llama-3.1-8b-instruct  first informal probe (max_tokens
#     2000) -> 17%(n=12) but ~40% of calls truncated (finish=length),
#     confounding the read. Retested at max_tokens 4000 -> 1/5 correct
#     (20%) with ZERO truncation before the probe stalled on a
#     provider-side hang (unrelated to the harness; killed after
#     several minutes with no progress). Both reads agree the true
#     rate sits right at the 20% floor -- the only candidate that
#     isn't decisively too strong. Committing to it for the formal
#     pilot with the higher token budget (see max_tokens below).
MODEL = "meta-llama/llama-3.1-8b-instruct"
URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_INFO_URL = "https://openrouter.ai/api/v1/key"
CAP_USD = 10.00  # approved worst-case ceiling for Experiment S alone
MAX_CALLS = 40000
GUARD_JSON = os.path.join(OUT, "spend_guard.json")
CACHE_CSV = os.path.join(OUT, "answer_cache.csv")
USAGE_CSV = os.path.join(OUT, "token_usage.csv")
POOL_JSON = os.path.join(OUT, "math500_pool.json")
PILOT_JSON = os.path.join(OUT, "pilot_result.json")
PREFLIGHT_JSON = os.path.join(OUT, "preflight_result.json")
ORDERINGS_JSON = os.path.join(OUT, "orderings.json")
SEARCH_STATE_JSON = os.path.join(OUT, "search_state.json")
REPORT_TXT = os.path.join(OUT, "experiment_s_report.txt")

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
OPS4 = ["swap", "insert", "inversion", "scramble"]

BUDGET_SECONDS = None
_START = time.time()
_LOCK = threading.Lock()


class Budget(Exception):
    pass


KEY = subprocess.run(
    ["gcloud", "secrets", "versions", "access", "latest",
     "--secret=OPENROUTER_API_KEY"],
    capture_output=True, text=True, shell=True).stdout.strip()

sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import MUTATIONS  # noqa: E402


def time_left():
    if BUDGET_SECONDS is None:
        return True
    return time.time() - _START < BUDGET_SECONDS


# =================================================================
# Frozen grader (verified 13/13 in _grader_test.py before this run)
# =================================================================
def extract_boxed(text):
    idx = text.rfind("\\boxed")
    if idx == -1:
        return None
    i = text.find("{", idx)
    if i == -1:
        return None
    depth = 0
    for j in range(i, len(text)):
        if text[j] == "{":
            depth += 1
        elif text[j] == "}":
            depth -= 1
            if depth == 0:
                return text[i + 1:j]
    return None


def normalize(s):
    if s is None:
        return None
    s = s.strip().strip("$")
    s = s.replace("\\left", "").replace("\\right", "")
    s = s.replace("\\!", "").replace("\\,", "").replace("\\;", "")
    s = s.replace("\\:", "").replace("\\ ", "")
    s = s.replace("\\dfrac", "\\frac").replace("\\tfrac", "\\frac")
    s = s.replace(" ", "").rstrip(".")
    s = s.replace("{,}", "").replace(",", "")
    return s


def to_number(s):
    if s is None:
        return None
    m = re.match(r"^(-?\d+)\\frac\{(-?\d+)\}\{(\d+)\}$", s)
    if m:
        whole, num, den = int(m.group(1)), int(m.group(2)), int(m.group(3))
        sign = -1 if whole < 0 else 1
        return whole + sign * num / den
    if re.match(r"^-?\\frac\{-?\d+\}\{-?\d+\}$", s):
        neg = s.startswith("-")
        body = s[1:] if neg else s
        m2 = re.match(r"^\\frac\{(-?\d+)\}\{(-?\d+)\}$", body)
        val = int(m2.group(1)) / int(m2.group(2))
        return -val if neg else val
    if re.match(r"^-?\d+/\d+$", s):
        a, b = s.split("/")
        return float(a) / float(b)
    try:
        return float(s)
    except ValueError:
        return None


ANSWER_TOKEN = re.compile(
    r"(-?\\frac\{-?\d+\}\{-?\d+\}"  # \frac{a}{b}
    r"|-?\d+\\frac\{-?\d+\}\{-?\d+\}"  # mixed number
    r"|-?\d+/\d+"  # a/b
    r"|-?\d[\d,]*\.\d+"  # decimal
    r"|-?\d[\d,]*)"  # integer (with optional , separators)
)


def grade(gold_raw, model_text):
    # Two conventions appear depending on which module lands last:
    # the ANSWER module's own "Answer: <number>" instruction (K/M/Q/Q2
    # convention), or the wrapper's \boxed{} request. Try both, boxed
    # first, then the last "Answer:"-labelled token, then the last
    # answer-shaped token anywhere in the text.
    pred_raw = extract_boxed(model_text)
    if pred_raw is None:
        after_answer = re.split(r"(?i)answer\s*:", model_text)
        if len(after_answer) > 1:
            m = ANSWER_TOKEN.search(after_answer[-1])
            pred_raw = m.group(0) if m else None
    if pred_raw is None:
        all_tokens = ANSWER_TOKEN.findall(model_text)
        pred_raw = all_tokens[-1] if all_tokens else None
    gold = normalize(gold_raw)
    pred = normalize(pred_raw) if pred_raw else None
    if pred is None:
        return 0
    if gold == pred:
        return 1
    gn, pn = to_number(gold), to_number(pred)
    if gn is not None and pn is not None and abs(gn - pn) < 1e-6:
        return 1
    return 0


# =================================================================
# MATH-500 pool: level 3-5, SIMPLE canonical answers only, seeded
# =================================================================
SIMPLE_ANSWER = re.compile(
    r"^-?\d+(\.\d+)?$"
    r"|^-?\\frac\{-?\d+\}\{\d+\}$"
    r"|^-?\d+/\d+$"
)


def load_math500_pool(n_questions=100):
    if os.path.exists(POOL_JSON):
        return json.load(open(POOL_JSON))
    r = requests.get(
        "https://huggingface.co/datasets/HuggingFaceH4/MATH-500/"
        "resolve/main/test.jsonl", timeout=60)
    rows = [json.loads(l) for l in r.text.strip().split("\n")]
    pool = [x for x in rows if x["level"] in (3, 4, 5)
           and SIMPLE_ANSWER.match(x["answer"].strip())]
    rng = np.random.default_rng(23)
    idx = rng.permutation(len(pool))[:n_questions]
    chosen = [pool[i] for i in idx]
    questions = [{"problem": x["problem"], "answer": x["answer"].strip(),
                 "level": x["level"], "unique_id": x["unique_id"]}
                for x in chosen]
    json.dump(questions, open(POOL_JSON, "w"), indent=1)
    return questions


QUESTIONS = load_math500_pool(100)
PILOT_Q = list(range(20))
PREFLIGHT_Q = list(range(25))
MAIN_Q = list(range(100))


def build_prompt(perm, problem):
    steps = "\n".join(f"{i+1}. {MODULES[m]}" for i, m in enumerate(perm))
    return (f"Solve the following mathematics problem. Work through "
            f"these steps in this exact order:\n{steps}\n\n"
            f"Problem: {problem}\n\nPut your final answer on its own "
            f"line inside \\boxed{{}}.")


# =================================================================
# Two-meter cost guard (pattern from iteration-19-crossfamily)
# =================================================================
def _guard_load():
    if os.path.exists(GUARD_JSON):
        return json.load(open(GUARD_JSON))
    return {"cap_usd": CAP_USD, "reported_usd": 0.0,
            "key_usage_baseline": None, "key_usage_latest": None,
            "updated": None}


def _guard_save(g):
    g["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    tmp = GUARD_JSON + ".tmp"
    json.dump(g, open(tmp, "w"), indent=1)
    os.replace(tmp, GUARD_JSON)


def key_usage():
    try:
        r = requests.get(KEY_INFO_URL, timeout=30,
                         headers={"Authorization": f"Bearer {KEY}"})
        if r.status_code == 200:
            return float(r.json()["data"].get("usage", 0.0))
    except Exception:
        pass
    return None


def guard_check_and_update(add_usd=0.0, poll_key=False):
    with _LOCK:
        g = _guard_load()
        if g["key_usage_baseline"] is None:
            g["key_usage_baseline"] = key_usage() or 0.0
        g["reported_usd"] = g.get("reported_usd", 0.0) + add_usd
        if poll_key:
            u = key_usage()
            if u is not None:
                g["key_usage_latest"] = u
        _guard_save(g)
        if g["reported_usd"] >= CAP_USD:
            raise Budget(f"COST CAP: reported ${g['reported_usd']:.2f} "
                        f">= ${CAP_USD}")
        if (g["key_usage_latest"] is not None
                and g["key_usage_baseline"] is not None
                and g["key_usage_latest"] - g["key_usage_baseline"]
                >= CAP_USD):
            raise Budget(
                f"COST CAP (key meter): "
                f"${g['key_usage_latest'] - g['key_usage_baseline']:.2f} "
                f">= ${CAP_USD}")
        return g["reported_usd"]


# =================================================================
# API + resumable cache
# =================================================================
class Api:
    def __init__(self):
        self.calls = 0
        self.tin = 0
        self.tout = 0
        self.cost = 0.0
        if os.path.exists(USAGE_CSV):
            r = list(csv.DictReader(open(USAGE_CSV)))[-1]
            self.calls = int(r["calls"])
            self.tin = int(r["tin"])
            self.tout = int(r["tout"])
            self.cost = float(r.get("usd_reported", 0.0) or 0.0)

    def save(self, poll_key=False):
        with open(USAGE_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=[
                "calls", "tin", "tout", "usd_reported"])
            w.writeheader()
            w.writerow({"calls": self.calls, "tin": self.tin,
                        "tout": self.tout,
                        "usd_reported": round(self.cost, 4)})
        try:  # refresh the live dashboard; never fatal to the run
            subprocess.run([sys.executable, os.path.join(
                ROOT, "scripts", "build_live_dashboard.py")],
                capture_output=True, timeout=60)
        except Exception:
            pass
        return guard_check_and_update(0.0, poll_key=poll_key)

    def ask(self, perm, qidx, retries=6):
        with _LOCK:
            if self.calls >= MAX_CALLS:
                raise Budget("call cap")
            self.calls += 1
        g = _guard_load()
        if g.get("reported_usd", 0.0) >= CAP_USD:
            raise Budget(f"COST CAP: ${g['reported_usd']:.2f}")
        q = QUESTIONS[qidx]
        body = {
            "model": MODEL,
            "messages": [{"role": "user",
                          "content": build_prompt(perm, q["problem"])}],
            "temperature": 0,
            # bumped from the spec's 1500 after calibration (2026-07-22):
            # earlier candidates truncated 20-40% of calls at 1500-2500
            # tokens on these hard problems (genuine self-doubt/
            # re-derivation looping, verified in raw output -- not a
            # harness bug); 4000 eliminated truncation entirely in the
            # Llama-3.1-8B retest (0/5, vs ~40% at 2000). A truncated
            # response is correctly graded incorrect either way, so
            # this is a calibration choice, not a correctness fix.
            "max_tokens": 4000,
            # added 2026-07-22 after the pilot's default route stalled
            # for multiple minutes per call: sorting by throughput
            # pins a real serving backend (observed: WandB, 5-28s/call)
            # instead of whatever slow/oversubscribed default route
            # OpenRouter picked. Same model weights, same pilot result
            # stands -- this only changes serving infrastructure.
            "provider": {"sort": "throughput"},
            "usage": {"include": True},
        }
        for attempt in range(retries):
            try:
                r = requests.post(URL, json=body, timeout=120,
                                  headers={"Authorization":
                                          f"Bearer {KEY}"})
                if r.status_code == 200:
                    j = r.json()
                    um = j.get("usage", {}) or {}
                    with _LOCK:
                        self.tin += um.get("prompt_tokens", 0)
                        self.tout += um.get("completion_tokens", 0)
                        self.cost += float(um.get("cost", 0.0) or 0.0)
                    if um.get("cost") is not None:
                        guard_check_and_update(float(um.get("cost") or 0.0))
                    try:
                        text = j["choices"][0]["message"]["content"] or ""
                    except (KeyError, IndexError, TypeError):
                        return 0
                    return grade(q["answer"], text)
                if r.status_code == 402:
                    raise Budget("provider out of credits (402)")
                if r.status_code in (429, 500, 502, 503):
                    time.sleep(min(2 ** attempt * 3, 45))
                    continue
                time.sleep(2)
            except Budget:
                raise
            except Exception:
                time.sleep(2 ** attempt)
        return None


API = Api()

# The cache key is (perm, qidx) only -- it does NOT encode the model.
# If MODEL is ever changed after a cache exists, silently mixing two
# models' answers under the same key would corrupt every downstream
# statistic without any visible error. Guard against that explicitly:
# record which model built the cache, and refuse to proceed on mismatch.
MODEL_LOCK_JSON = os.path.join(OUT, "model_lock.json")
if os.path.exists(CACHE_CSV) and os.path.getsize(CACHE_CSV) > len(
        "perm,qidx,correct\n"):
    if not os.path.exists(MODEL_LOCK_JSON):
        sys.exit(
            f"Cache at {CACHE_CSV} has data but no model_lock.json -- "
            f"refusing to guess which model produced it. If this cache "
            f"is from an earlier model attempt, archive or delete the "
            f"results/ contents before switching MODEL.")
    locked = json.load(open(MODEL_LOCK_JSON))["model"]
    if locked != MODEL:
        sys.exit(
            f"MODEL is {MODEL!r} but the cache was built with "
            f"{locked!r}. Archive results/ (cache, guard, usage, "
            f"pilot/preflight/orderings json) before switching models, "
            f"to avoid silently mixing two models' answers.")
else:
    json.dump({"model": MODEL, "locked_at": time.strftime(
        "%Y-%m-%d %H:%M:%S")}, open(MODEL_LOCK_JSON, "w"))

_cache = {}
if os.path.exists(CACHE_CSV):
    for r in csv.reader(open(CACHE_CSV)):
        if r and r[0] != "perm":
            _cache[(r[0], int(r[1]))] = int(r[2])
else:
    open(CACHE_CSV, "w", newline="").write("perm,qidx,correct\n")
_cache_file = open(CACHE_CSV, "a", newline="")
_cache_writer = csv.writer(_cache_file)


def ensure_evaluated(perm, qindices, workers=25):
    """Fill the cache for (perm, q) pairs not yet present. Respects the
    wall-clock budget and the cost cap; raises Budget to pause cleanly."""
    key = json.dumps(list(perm))
    jobs = [qi for qi in qindices if (key, qi) not in _cache]
    if not jobs:
        return
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(API.ask, list(perm), qi): qi for qi in jobs}
        for fut in futs:
            qi = futs[fut]
            res = fut.result()
            if res is not None:
                with _LOCK:
                    _cache_writer.writerow([key, qi, res])
                    _cache_file.flush()
                    _cache[(key, qi)] = res
            done += 1
            if done % 100 == 0:
                API.save(poll_key=True)
            if not time_left():
                raise Budget("wall clock")


def mean_fitness(perm, qindices):
    key = json.dumps(list(perm))
    vals = [_cache.get((key, qi)) for qi in qindices]
    if any(v is None for v in vals):
        return None
    return sum(vals) / len(vals)


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


# =================================================================
# Stage 1: pilot
# =================================================================
def stage_pilot():
    if os.path.exists(PILOT_JSON):
        return json.load(open(PILOT_JSON))
    attempt_key = "_pilot_attempt.json"
    seed = 2301
    orderings = []
    rng = np.random.default_rng(seed)
    seen = set()
    while len(orderings) < 10:
        p = tuple(int(x) for x in rng.permutation(N))
        if p not in seen:
            seen.add(p)
            orderings.append(p)
    for p in orderings:
        ensure_evaluated(p, PILOT_Q)
    vals = []
    for p in orderings:
        f = mean_fitness(p, PILOT_Q)
        vals.append(f)
    if any(v is None for v in vals):
        return None  # still in progress (ran out of budget mid-pilot)
    acc = float(np.mean(vals))
    passed = 0.20 <= acc <= 0.60
    result = {"accuracy": acc, "passed": passed,
             "orderings": [list(p) for p in orderings], "model": MODEL}
    json.dump(result, open(PILOT_JSON, "w"), indent=1)
    return result


# =================================================================
# Stage 2: pre-flight (forecast committed BEFORE stage 3)
# =================================================================
def stage_preflight():
    if os.path.exists(PREFLIGHT_JSON):
        return json.load(open(PREFLIGHT_JSON))
    rng = np.random.default_rng(2302)
    n_pairs = 22
    rho = {}
    all_perms_seen = {}
    for opname in OPS4:
        f0, f1 = [], []
        for _ in range(n_pairs):
            p = [int(x) for x in rng.permutation(N)]
            q = p.copy()
            MUTATIONS[opname](q, rng)
            ensure_evaluated(p, PREFLIGHT_Q)
            ensure_evaluated(q, PREFLIGHT_Q)
            fp = mean_fitness(p, PREFLIGHT_Q)
            fq = mean_fitness(q, PREFLIGHT_Q)
            if fp is None or fq is None:
                return None  # ran out of budget mid-preflight
            f0.append(fp)
            f1.append(fq)
            all_perms_seen[tuple(p)] = fp
            all_perms_seen[tuple(q)] = fq
        rho[opname] = (float(np.corrcoef(f0, f1)[0, 1])
                       if np.std(f0) > 0 and np.std(f1) > 0 else 0.0)
    best_known = max(all_perms_seen, key=all_perms_seen.get)
    fs, ds = [], []
    for p, f in all_perms_seen.items():
        fs.append(f)
        ds.append(cayley(list(p), list(best_known)))
    fdc = (float(np.corrcoef(fs, ds)[0, 1]) if np.std(fs) > 0 else 0.0)
    pick = max((o for o in OPS4 if o != "scramble"), key=lambda o: rho[o])
    forecast_search_beats_random = fdc < -0.05
    result = {
        "n_pairs_per_op": n_pairs,
        "rho1": rho,
        "fdc": fdc,
        "best_known_perm": list(best_known),
        "best_known_fitness": all_perms_seen[best_known],
        "operator_pick": pick,
        "h22_forecast_search_beats_random": forecast_search_beats_random,
        "h22_forecast_text": (
            f"argmax rho1 = {pick} ({rho[pick]:.3f}); FDC = {fdc:+.3f} "
            f"({'materially negative -> guided/search beats random'
              if forecast_search_beats_random
              else 'not materially negative -> random likely competitive'})"
        ),
        "registered_utc": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    json.dump(result, open(PREFLIGHT_JSON, "w"), indent=1)
    return result


# =================================================================
# Stage 3: main landscape (150 random + 50 guided + 50 searched)
# =================================================================
def n8_position_table():
    """pos8[module][position] from the unbiased Iteration-11 n=8 sample
    (same reconstruction as transfer_study.py / Experiment R)."""
    rng = np.random.default_rng(11)
    gate = [[int(x) for x in rng.permutation(8)] for _ in range(30)]
    base = [[int(x) for x in rng.permutation(8)] for _ in range(100)]
    ops = list(MUTATIONS)
    neigh = []
    for i, bp in enumerate(base):
        op = ops[i % 4]
        nb = bp.copy()
        MUTATIONS[op](nb, rng)
        neigh.append(nb)
    sample = sorted({tuple(p) for p in gate + base + neigh})
    cache11 = {}
    path11 = os.path.join(ROOT, "experiments/iteration-11/results/"
                          "answer_cache.csv")
    for r in csv.reader(open(path11)):
        if r and r[0] != "perm":
            cache11[(tuple(json.loads(r[0])), int(r[1]))] = int(r[2])
    pos8 = np.zeros((8, 8))
    cnt = np.zeros((8, 8))
    for p in sample:
        vals = [cache11.get((p, q)) for q in range(20)]
        if all(v is not None for v in vals):
            f = sum(vals) / 20
            for pos, mod in enumerate(p):
                pos8[mod][pos] += f
                cnt[mod][pos] += 1
    return np.divide(pos8, np.maximum(cnt, 1))


def build_ordering_sets():
    if os.path.exists(ORDERINGS_JSON):
        d = json.load(open(ORDERINGS_JSON))
        return ([tuple(p) for p in d["random_150"]],
                [tuple(p) for p in d["guided_50"]],
                d)
    rng = np.random.default_rng(2303)
    random_150 = []
    seen = set()
    while len(random_150) < 150:
        p = tuple(int(x) for x in rng.permutation(N))
        if p not in seen:
            seen.add(p)
            random_150.append(p)
    pos8 = n8_position_table()

    def score(p):
        return sum(pos8[m][i] for i, m in enumerate(p))

    rng2 = np.random.default_rng(2304)
    candidates = []
    cseen = set(seen)
    while len(candidates) < 3000:
        p = tuple(int(x) for x in rng2.permutation(N))
        if p not in cseen:
            cseen.add(p)
            candidates.append(p)
    ranked = sorted(candidates, key=score, reverse=True)
    guided_50 = ranked[:50]
    d = {"random_150": [list(p) for p in random_150],
        "guided_50": [list(p) for p in guided_50],
        "searched": []}
    json.dump(d, open(ORDERINGS_JSON, "w"), indent=1)
    return random_150, guided_50, d


def run_search_phase(random_150, guided_50):
    """Resumable, hand-rolled elitist portfolio EA (pop 40, k=3,
    p_m 0.6, elitism 1 -- D12 hyperparameters) seeded from the
    already-known 200-pool. Stops once 50 NEW orderings have been
    fully evaluated. State persists in search_state.json so the
    process survives kill/restart."""
    known_pool = list(dict.fromkeys(random_150 + guided_50))
    d = json.load(open(ORDERINGS_JSON))
    searched = [tuple(p) for p in d.get("searched", [])]

    if os.path.exists(SEARCH_STATE_JSON):
        st = json.load(open(SEARCH_STATE_JSON))
        population = [tuple(p) for p in st["population"]]
        rng = np.random.default_rng()
        rng.bit_generator.state = st["rng_state"]
        gen = st["gen"]
    else:
        rng = np.random.default_rng(2305)
        seed_idx = rng.choice(len(known_pool), 40, replace=False)
        population = [known_pool[i] for i in seed_idx]
        gen = 0

    known_set = set(random_150) | set(guided_50)
    known_set.update(searched)
    ops = list(MUTATIONS)

    def save_state():
        json.dump({"population": [list(p) for p in population],
                   "rng_state": rng.bit_generator.state, "gen": gen},
                  open(SEARCH_STATE_JSON, "w"))
        d["searched"] = [list(p) for p in searched]
        json.dump(d, open(ORDERINGS_JSON, "w"), indent=1)

    while len(searched) < 50 and time_left():
        for p in population:
            if len(searched) >= 50:
                break  # budget hit: stop feeding the EA new unknowns,
                       # do NOT let an unevaluated member reach fits{}
            if p not in known_set:
                ensure_evaluated(p, MAIN_Q)
                known_set.add(p)
                searched.append(p)
                save_state()
        if len(searched) >= 50:
            break  # exit the outer while too -- search phase is done,
                   # not "out of wall-clock" (that distinction matters:
                   # the former returns cleanly, the latter would
                   # otherwise re-raise Budget forever on resume)
        fits = {p: mean_fitness(p, MAIN_Q) for p in set(population)}
        if any(v is None for v in fits.values()):
            save_state()
            raise Budget("wall clock (mid-generation)")
        order = sorted(population, key=lambda p: fits[p], reverse=True)
        new_pop = [order[0]]  # elitism
        while len(new_pop) < 40:
            idx = rng.choice(40, 3, replace=False)
            cand = [population[i] for i in idx]
            parent = max(cand, key=lambda p: fits[p])
            if rng.random() < 0.6:
                child = list(parent)
                MUTATIONS[ops[rng.integers(4)]](child, rng)
                child = tuple(child)
            else:
                child = parent
            new_pop.append(child)
        population = new_pop
        gen += 1
        save_state()
    save_state()
    return searched if len(searched) >= 50 else None


def stage_main():
    random_150, guided_50, _ = build_ordering_sets()
    for p in random_150:
        ensure_evaluated(p, MAIN_Q)
    for p in guided_50:
        ensure_evaluated(p, MAIN_Q)
    searched = run_search_phase(random_150, guided_50)
    if searched is None:
        return None
    return random_150, guided_50, searched


# =================================================================
# Stage 4: analysis
# =================================================================
def bootstrap_ci(vals, n=4000):
    vals = np.asarray(vals, dtype=float)
    if len(vals) < 2:
        return float(vals.mean()) if len(vals) else float("nan"), \
            float("nan"), float("nan")
    rng = np.random.default_rng(99)
    means = [vals[rng.integers(0, len(vals), len(vals))].mean()
            for _ in range(n)]
    return (float(vals.mean()), float(np.percentile(means, 2.5)),
            float(np.percentile(means, 97.5)))


def race_evals_to_top1pct(fit, order_fn, threshold, rng):
    """order_fn(rng) -> a permutation (list of indices into `keys`) in
    which to evaluate; returns 1-based position of first hit."""
    keys = list(fit)
    order = order_fn(rng, keys)
    for i, k in enumerate(order):
        if fit[k] >= threshold:
            return i + 1
    return None


def stage_analyze(random_150, guided_50, searched, preflight):
    keys = random_150 + guided_50 + searched
    fit = {}
    for p in keys:
        v = mean_fitness(p, MAIN_Q)
        if v is None:
            return None
        fit[p] = v
    vals = np.array(list(fit.values()))
    best = vals.max()
    threshold = best - 0.01  # "within one question of the best"
    lines = []
    lines.append("Experiment S: MATH-500 hard-reasoning ordering "
                 "landscape (Iteration 23)")
    lines.append(f"model: {MODEL} | pool: {len(keys)} orderings "
                 f"(150 random + {len(guided_50)} guided + "
                 f"{len(searched)} searched) x 100 questions")
    lines.append(f"landscape: mean {vals.mean():.3f} std "
                 f"{vals.std():.3f} range [{vals.min():.3f},"
                 f"{best:.3f}]")

    # H19: sensitivity re-emerges
    rand_vals = np.array([fit[p] for p in random_150])
    h19_std = float(rand_vals.std())
    lines.append(f"\nH19 (sensitivity re-emerges): random-set std = "
                 f"{h19_std:.3f} (target >= 0.15; Q2 ceiling was "
                 f"0.075) -> "
                 f"{'HOLDS' if h19_std >= 0.15 else ('borderline' if h19_std >= 0.10 else 'FALSIFIED')}")

    # H20: sparsity at 1% resolution
    near_opt = int((vals >= threshold).sum())
    frac = near_opt / len(vals)
    lines.append(f"H20 (sparse optima): {near_opt}/{len(vals)} "
                 f"({frac*100:.1f}%) within one question of best "
                 f"(target <=2%) -> "
                 f"{'HOLDS' if frac <= 0.02 else ('borderline' if frac <= 0.05 else 'FALSIFIED')}")

    # H23: position-table correlation with easy-set (Exp M)
    pos8_easy = n8_position_table()
    pos_hard = np.zeros((8, 8))
    cnt = np.zeros((8, 8))
    for p in random_150 + guided_50:
        for i, m in enumerate(p):
            pos_hard[m][i] += fit[p]
            cnt[m][i] += 1
    pos_hard = np.divide(pos_hard, np.maximum(cnt, 1))
    mask = cnt.ravel() > 0
    r23 = float(np.corrcoef(pos8_easy.ravel()[mask],
                            pos_hard.ravel()[mask])[0, 1])
    lines.append(f"H23 (position rules transfer to hard set): r = "
                 f"{r23:.3f} (target >0.4) -> "
                 f"{'HOLDS' if r23 > 0.4 else ('borderline' if r23 > 0.2 else 'FALSIFIED')}")

    # H21: guided vs PRISM vs random race, 40-seed bootstrap
    def order_random(rng, ks):
        idx = rng.permutation(len(ks))
        return [ks[i] for i in idx]

    def _guided_score(p):
        return sum(pos8_easy[m][i] for i, m in enumerate(p))

    def order_guided(rng, ks):
        # BUGFIX (2026-07-24): this previously ranked by fit[p] -- the
        # TRUE fitness being raced for -- which is an oracle, not the
        # transfer-guided policy (it "wins" trivially by construction).
        # The guided policy may only use pos8_easy, the externally
        # derived score already used to build guided_50; ranking must
        # reflect what is knowable BEFORE evaluating this landscape.
        boot = [ks[i] for i in rng.integers(0, len(ks), len(ks))]
        boot_sorted = sorted(set(boot), key=_guided_score, reverse=True)
        return boot_sorted

    def order_prism(rng, ks):
        pop = [ks[i] for i in rng.integers(0, len(ks), min(20, len(ks)))]
        out = list(dict.fromkeys(pop))
        seen = set(out)
        for _ in range(30):
            best_p = max(pop, key=lambda p: fit[p])
            child = list(best_p)
            MUTATIONS[list(MUTATIONS)[rng.integers(4)]](child, rng)
            child = tuple(child)
            if child not in fit:
                continue
            if child not in seen:
                out.append(child)
                seen.add(child)
            pop = pop[1:] + [child]
        remaining = [k for k in ks if k not in seen]
        rng.shuffle(remaining)
        return out + remaining

    n_seeds = 40
    race = {}
    for name, fn in (("guided", order_guided), ("prism", order_prism),
                     ("random", order_random)):
        hits = []
        for s in range(n_seeds):
            rng = np.random.default_rng(5000 + s)
            h = race_evals_to_top1pct(fit, fn, threshold, rng)
            if h is not None:
                hits.append(h)
        race[name] = hits
    lines.append("\nH21 (three-way race to first top-1% ordering, "
                 f"40 seeds, threshold={threshold:.3f}):")
    cis = {}
    for name in ("guided", "prism", "random"):
        h = race[name]
        m, lo, hi = bootstrap_ci(h) if h else (float("nan"),) * 3
        cis[name] = (lo, hi)
        lines.append(f"  {name:<7} hit {len(h)}/{n_seeds} mean evals "
                     f"{m:.1f} 95% CI [{lo:.1f},{hi:.1f}]")
    g_lo, g_hi = cis["guided"]
    r_lo, r_hi = cis["random"]
    disjoint = (not math.isnan(g_lo) and not math.isnan(r_lo)
               and (g_hi < r_lo or r_hi < g_lo))
    lines.append(f"  guided-vs-random CIs disjoint: {disjoint} -> "
                 f"H21 {'HOLDS (headline)' if disjoint else 'does not hold (guided is a warm start, not a headline)'}")

    # H22 verdict
    lines.append(f"\nH22 (pre-flight forecast, registered "
                 f"{preflight['registered_utc']}): "
                 f"{preflight['h22_forecast_text']}")
    guided_beats_random = (not math.isnan(g_lo) and not math.isnan(r_lo)
                           and g_hi < r_lo)
    forecast_correct = (preflight["h22_forecast_search_beats_random"]
                        == guided_beats_random)
    lines.append(f"  outcome: guided decisively beats random = "
                 f"{guided_beats_random} -> forecast "
                 f"{'CORRECT' if forecast_correct else 'MISS'}")

    usd = API.cost
    lines.append(f"\nspend: {API.calls} calls, ${usd:.2f} API-reported "
                 f"of ${CAP_USD:.2f} cap")

    text = "\n".join(lines)
    open(REPORT_TXT, "w").write(text + "\n")
    print(text)
    print("STUDY COMPLETE.")


# =================================================================
# Driver
# =================================================================
def main():
    total = API.save(poll_key=True)
    print(f"[guard] reported total ${total:.2f} of ${CAP_USD} cap",
         flush=True)
    try:
        pilot = stage_pilot()
        if pilot is None:
            print("PAUSED mid-pilot; rerun to resume", flush=True)
            return
        print(f"[pilot] accuracy {pilot['accuracy']:.3f} -> "
             f"{'PASS' if pilot['passed'] else 'FAIL'}", flush=True)
        if not pilot["passed"]:
            print("PILOT FAILED band check [0.20,0.60]; model/tier "
                 "swap needed before continuing. Stopping.", flush=True)
            return

        preflight = stage_preflight()
        if preflight is None:
            print("PAUSED mid-preflight; rerun to resume", flush=True)
            return
        print(f"[preflight] {preflight['h22_forecast_text']}",
             flush=True)

        result = stage_main()
        if result is None:
            print("PAUSED mid-main-landscape; rerun to resume",
                 flush=True)
            return
        random_150, guided_50, searched = result
        print(f"[main] landscape complete: {len(random_150)} random + "
             f"{len(guided_50)} guided + {len(searched)} searched",
             flush=True)

        stage_analyze(random_150, guided_50, searched, preflight)
    except Budget as e:
        print(f"PAUSED ({e}); rerun to resume", flush=True)
    finally:
        API.save(poll_key=True)
        _cache_file.close()


def selftest():
    if not KEY:
        print("NO KEY: secret OPENROUTER_API_KEY is empty/missing.")
        return
    u = key_usage()
    print(f"key lifetime usage: ${u}" if u is not None
         else "key usage endpoint unavailable")
    q = QUESTIONS[0]
    print(f"sample question (level {q['level']}): {q['problem'][:100]}...")
    print(f"gold answer: {q['answer']}")
    res = API.ask(list(range(8)), 0)
    print(f"graded: {res}")
    API.save(poll_key=True)
    print("SELFTEST OK" if res is not None else "SELFTEST FAILED")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        selftest()
    else:
        if len(sys.argv) > 1:
            BUDGET_SECONDS = float(sys.argv[1])
        main()
