"""Iteration 24, Experiment T: prompt-optimizer baselines. Approved D27.
Full design + pre-registered hypotheses: PLAN.md, hypotheses.json
(committed 2026-07-24 before any evaluation, commit c970894).

Answers the D21-required reviewer objection "why does ORDER matter vs.
just writing better instructions?" with two tracks:

  TRACK A (H25, complementarity): OPRO rewrites the 8 modules' WORDING at
    fixed canonical order; then we sweep ORDERINGS on the optimized
    wording and ask whether ordering still moves accuracy.
  TRACK B (H26, efficiency): OPRO proposes ORDERINGS (wording frozen)
    head-to-head vs the PRISM portfolio searcher on the same 8! space,
    same 30-question fitness, same seeds, same 25-eval budget.

Models: target (scored) = meta-llama/llama-3.1-8b-instruct via OpenRouter
(provider sort=throughput, temp 0, max_tokens 4000) -- reused from Exp. S.
Optimizer (proposes, never scored) = gemini-2.5-flash-lite via Google API.
OPRO is hand-implemented and auditable (not pip-installed).

Cache key = (wording_id, perm_json, qidx). wording_id "orig"/"opt"/hash
distinguishes prompt content so Track A's optimized-wording calls never
collide with original-wording rows. Own $5 two-meter cost guard.

Usage:
  python prompt_optimizer_baselines.py --selftest     # 1 target + 1 opt call
  python prompt_optimizer_baselines.py [budget-secs]  # run/resume all stages
Prints STUDY COMPLETE when stage C (analysis) finishes.
"""

import csv
import hashlib
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

# ---- models ----
TARGET_MODEL = "meta-llama/llama-3.1-8b-instruct"
TARGET_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_INFO_URL = "https://openrouter.ai/api/v1/key"
OPT_MODEL = "gemini-2.5-flash-lite"
OPT_URL = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{OPT_MODEL}:generateContent")

CAP_USD = 5.00           # dedicated OpenRouter (target) cap for Exp. T
MAX_TARGET_CALLS = 30000
GUARD_JSON = os.path.join(OUT, "spend_guard.json")
CACHE_CSV = os.path.join(OUT, "answer_cache.csv")
USAGE_CSV = os.path.join(OUT, "token_usage.csv")
WORDINGS_JSON = os.path.join(OUT, "wordings_registry.json")
STATE_JSON = os.path.join(OUT, "state.json")
TRAJ_JSON = os.path.join(OUT, "a1_trajectory.json")
BESTWORD_JSON = os.path.join(OUT, "best_wording.json")
SWEEP_JSON = os.path.join(OUT, "sweep_orderings.json")
BSTATE_JSON = os.path.join(OUT, "b_state.json")
OPTLOG_CSV = os.path.join(OUT, "optimizer_calls.csv")
REPORT_TXT = os.path.join(OUT, "experiment_t_report.txt")

POOL = json.load(open(os.path.join(
    ROOT, "experiments", "iteration-23-experiment-s", "results",
    "math500_pool.json")))
TRAIN_Q = list(range(0, 60))
HELDOUT_Q = list(range(60, 100))
TRACKB_Q = list(range(60, 90))     # 30-question subset of held-out

LABELS = ["RESTATE", "IDENTIFY", "ESTIMATE", "PLAN",
          "SIMPLIFY", "COMPUTE", "CHECK", "ANSWER"]
ORIG_WORDINGS = [
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
CANON = list(range(8))

BUDGET_SECONDS = None
_START = time.time()
_LOCK = threading.Lock()


class Budget(Exception):
    pass


class Pause(Exception):
    pass


OR_KEY = subprocess.run(
    ["gcloud", "secrets", "versions", "access", "latest",
     "--secret=OPENROUTER_API_KEY"],
    capture_output=True, text=True, shell=True).stdout.strip()
GOOGLE_KEY = subprocess.run(
    ["gcloud", "secrets", "versions", "access", "latest",
     "--secret=GOOGLE_API_KEY"],
    capture_output=True, text=True, shell=True).stdout.strip()

sys.path.insert(0, os.path.join(ROOT, "prism-research"))
from core.prism import MUTATIONS  # noqa: E402
OPS4 = list(MUTATIONS)


def time_left():
    return BUDGET_SECONDS is None or time.time() - _START < BUDGET_SECONDS


# =================================================================
# Frozen grader (verbatim from Experiment S; 18/18 unit tests)
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
    r"(-?\\frac\{-?\d+\}\{-?\d+\}"
    r"|-?\d+\\frac\{-?\d+\}\{-?\d+\}"
    r"|-?\d+/\d+"
    r"|-?\d[\d,]*\.\d+"
    r"|-?\d[\d,]*)"
)


def grade(gold_raw, model_text):
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


def build_prompt(perm, problem, wordings):
    steps = "\n".join(f"{i+1}. {wordings[m]}" for i, m in enumerate(perm))
    return (f"Solve the following mathematics problem. Work through "
            f"these steps in this exact order:\n{steps}\n\n"
            f"Problem: {problem}\n\nPut your final answer on its own "
            f"line inside \\boxed{{}}.")


# =================================================================
# wording registry (wording_id -> 8-module wording list)
# =================================================================
def _load_json(path, default):
    if os.path.exists(path):
        try:
            return json.load(open(path))
        except Exception:
            return default
    return default


def _save_json(path, obj):
    tmp = path + ".tmp"
    json.dump(obj, open(tmp, "w"), indent=1)
    os.replace(tmp, path)


_registry = _load_json(WORDINGS_JSON, {})
if "orig" not in _registry:
    _registry["orig"] = ORIG_WORDINGS
    _save_json(WORDINGS_JSON, _registry)


def register_wording(wid, wordings):
    if wid not in _registry:
        _registry[wid] = wordings
        _save_json(WORDINGS_JSON, _registry)


def wording_hash(wordings):
    h = hashlib.md5("||".join(wordings).encode()).hexdigest()[:10]
    return h


# =================================================================
# cost guard (two meters, OpenRouter target only)
# =================================================================
def _guard_load():
    return _load_json(GUARD_JSON, {
        "cap_usd": CAP_USD, "reported_usd": 0.0,
        "key_usage_baseline": None, "key_usage_latest": None})


def key_usage():
    try:
        r = requests.get(KEY_INFO_URL, timeout=30,
                         headers={"Authorization": f"Bearer {OR_KEY}"})
        if r.status_code == 200:
            return float(r.json()["data"].get("usage", 0.0))
    except Exception:
        pass
    return None


def guard_update(add=0.0, poll=False):
    with _LOCK:
        g = _guard_load()
        if g["key_usage_baseline"] is None:
            g["key_usage_baseline"] = key_usage() or 0.0
        g["reported_usd"] = g.get("reported_usd", 0.0) + add
        if poll:
            u = key_usage()
            if u is not None:
                g["key_usage_latest"] = u
        g["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _save_json(GUARD_JSON, g)
        if g["reported_usd"] >= CAP_USD:
            raise Budget(f"COST CAP reported ${g['reported_usd']:.2f}")
        if (g["key_usage_latest"] is not None
                and g["key_usage_latest"] - g["key_usage_baseline"]
                >= CAP_USD):
            raise Budget("COST CAP (key meter)")
        return g["reported_usd"]


# =================================================================
# target model (Llama via OpenRouter) + resumable cache
# =================================================================
class Api:
    def __init__(self):
        self.calls = 0
        self.cost = 0.0
        if os.path.exists(USAGE_CSV):
            r = list(csv.DictReader(open(USAGE_CSV)))[-1]
            self.calls = int(r["calls"])
            self.cost = float(r.get("usd_reported", 0) or 0)

    def save(self, poll=False):
        with open(USAGE_CSV, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["calls", "usd_reported"])
            w.writeheader()
            w.writerow({"calls": self.calls,
                        "usd_reported": round(self.cost, 4)})
        try:
            subprocess.run([sys.executable, os.path.join(
                ROOT, "scripts", "build_live_dashboard.py")],
                capture_output=True, timeout=60)
        except Exception:
            pass
        return guard_update(0.0, poll=poll)

    def ask(self, wordings, perm, qidx, retries=6):
        with _LOCK:
            if self.calls >= MAX_TARGET_CALLS:
                raise Budget("call cap")
            self.calls += 1
        g = _guard_load()
        if g.get("reported_usd", 0.0) >= CAP_USD:
            raise Budget("cost cap pre-check")
        q = POOL[qidx]
        body = {"model": TARGET_MODEL,
                "messages": [{"role": "user",
                              "content": build_prompt(perm, q["problem"],
                                                      wordings)}],
                "temperature": 0, "max_tokens": 4000,
                "provider": {"sort": "throughput"},
                "usage": {"include": True}}
        for attempt in range(retries):
            try:
                r = requests.post(TARGET_URL, json=body, timeout=120,
                                  headers={"Authorization":
                                           f"Bearer {OR_KEY}"})
                if r.status_code == 200:
                    j = r.json()
                    um = j.get("usage", {}) or {}
                    with _LOCK:
                        self.cost += float(um.get("cost", 0.0) or 0.0)
                    if um.get("cost") is not None:
                        guard_update(float(um.get("cost") or 0.0))
                    try:
                        text = j["choices"][0]["message"]["content"] or ""
                    except (KeyError, IndexError, TypeError):
                        return 0
                    return grade(q["answer"], text)
                if r.status_code == 402:
                    raise Budget("provider out of credits")
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

_cache = {}
if os.path.exists(CACHE_CSV):
    for r in csv.reader(open(CACHE_CSV)):
        if r and r[0] != "wording_id":
            _cache[(r[0], r[1], int(r[2]))] = int(r[3])
else:
    open(CACHE_CSV, "w", newline="").write("wording_id,perm,qidx,correct\n")
_cf = open(CACHE_CSV, "a", newline="")
_cw = csv.writer(_cf)


def ensure(wid, wordings, perm, qindices, workers=25):
    key = json.dumps(list(perm))
    todo = [qi for qi in qindices if (wid, key, qi) not in _cache]
    if not todo:
        return
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(API.ask, wordings, list(perm), qi): qi
                for qi in todo}
        done = 0
        for fut in futs:
            qi = futs[fut]
            res = fut.result()
            if res is not None:
                with _LOCK:
                    _cw.writerow([wid, key, qi, res])
                    _cf.flush()
                    _cache[(wid, key, qi)] = res
            done += 1
            if done % 100 == 0:
                API.save(poll=True)
            if not time_left():
                raise Pause()


def acc(wid, perm, qindices):
    key = json.dumps(list(perm))
    vals = [_cache.get((wid, key, qi)) for qi in qindices]
    if any(v is None for v in vals):
        return None
    return sum(vals) / len(vals)


# =================================================================
# optimizer model (Gemini Flash-Lite)
# =================================================================
def opt_call(meta_prompt, retries=4):
    for attempt in range(retries):
        try:
            r = requests.post(OPT_URL, params={"key": GOOGLE_KEY},
                              json={"contents": [{"parts": [
                                  {"text": meta_prompt}]}],
                                  "generationConfig": {
                                      "temperature": 1.0,
                                      "maxOutputTokens": 900}},
                              timeout=90)
            if r.status_code == 200:
                j = r.json()
                try:
                    txt = j["candidates"][0]["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    txt = ""
                with open(OPTLOG_CSV, "a", newline="") as f:
                    csv.writer(f).writerow(
                        [time.strftime("%H:%M:%S"), len(meta_prompt),
                         len(txt)])
                return txt
            if r.status_code in (429, 500, 503):
                time.sleep(2 ** attempt * 2)
                continue
            time.sleep(2)
        except Exception:
            time.sleep(2 ** attempt)
    return ""


def parse_wording(text):
    """Parse 'LABEL: text' lines into an 8-module wording list."""
    found = {}
    for ln in text.splitlines():
        m = re.match(r"\s*([A-Z]{4,8})\s*[:\-]\s*(.+)", ln)
        if m and m.group(1) in LABELS:
            lab = m.group(1)
            body = m.group(2).strip().strip('"').strip()
            if body:
                found[lab] = f"{lab}: {body}"
    if all(lab in found for lab in LABELS):
        return [found[lab] for lab in LABELS]
    return None


def parse_ordering(text):
    """Extract the 8 labels in order of appearance -> perm indices."""
    seq = []
    for tok in re.findall(r"[A-Z]{4,8}", text.upper()):
        if tok in LABELS and tok not in [LABELS[i] for i in seq]:
            seq.append(LABELS.index(tok))
    if len(seq) == 8:
        return seq
    return None


# =================================================================
# STAGE A1: OPRO wording optimization on the train set
# =================================================================
A1_ROUNDS = 24
TOPK = 6


def a1_meta_prompt(traj):
    top = sorted(traj, key=lambda e: e["score"], reverse=True)[:TOPK]
    lines = [
        "You are improving the WORDING of instructions given to a small",
        "math-solving model. The model performs these 8 labelled steps in",
        "this FIXED ORDER: " + ", ".join(LABELS) + ".",
        "Only wording may change; the labels, their order, and their",
        "intent are fixed. Here are wording sets tried so far and the",
        "accuracy each reached on hard math problems (best first):", ""]
    for e in top:
        lines.append(f"[accuracy {e['score']:.3f}]")
        for w in e["wordings"]:
            lines.append("  " + w)
        lines.append("")
    lines += [
        "Propose ONE NEW wording set you expect to score higher. Keep each",
        "label and its intent; improve only the phrasing (be concrete,",
        "unambiguous, and helpful to a weak model). Output EXACTLY 8 lines,",
        "one per step, in this format and order:",
        "RESTATE: <text>", "IDENTIFY: <text>", "ESTIMATE: <text>",
        "PLAN: <text>", "SIMPLIFY: <text>", "COMPUTE: <text>",
        "CHECK: <text>", "ANSWER: <text>"]
    return "\n".join(lines)


def stage_a1():
    traj = _load_json(TRAJ_JSON, [])
    state = _load_json(STATE_JSON, {})
    # seed with original wording
    if not traj:
        ensure("orig", ORIG_WORDINGS, CANON, TRAIN_Q)
        s = acc("orig", CANON, TRAIN_Q)
        if s is None:
            raise Pause()
        traj.append({"wid": "orig", "wordings": ORIG_WORDINGS,
                     "score": s, "round": 0})
        _save_json(TRAJ_JSON, traj)
    while len([e for e in traj if e["round"] > 0]) < A1_ROUNDS:
        pend = state.get("a1_pending")
        if pend is None:
            # propose (retry parsing a few times)
            wordings = None
            for _ in range(4):
                txt = opt_call(a1_meta_prompt(traj))
                wordings = parse_wording(txt)
                if wordings is not None:
                    break
            if wordings is None:
                # optimizer failed to produce a parseable set; skip round
                # by re-using best so far mutated trivially is not valid,
                # so just count a failed round to guarantee progress.
                nround = max(e["round"] for e in traj) + 1
                traj.append({"wid": "orig", "wordings": ORIG_WORDINGS,
                             "score": traj[0]["score"], "round": nround,
                             "failed_parse": True})
                _save_json(TRAJ_JSON, traj)
                continue
            wid = wording_hash(wordings)
            register_wording(wid, wordings)
            pend = {"wid": wid, "wordings": wordings}
            state["a1_pending"] = pend
            _save_json(STATE_JSON, state)
        ensure(pend["wid"], pend["wordings"], CANON, TRAIN_Q)
        s = acc(pend["wid"], CANON, TRAIN_Q)
        if s is None:
            raise Pause()
        nround = max(e["round"] for e in traj) + 1
        traj.append({"wid": pend["wid"], "wordings": pend["wordings"],
                     "score": s, "round": nround})
        state["a1_pending"] = None
        _save_json(TRAJ_JSON, traj)
        _save_json(STATE_JSON, state)
    best = max(traj, key=lambda e: e["score"])
    _save_json(BESTWORD_JSON, best)
    register_wording("opt", best["wordings"])
    # ensure the "opt" alias points at the best wording set in cache terms
    _registry["opt"] = best["wordings"]
    _save_json(WORDINGS_JSON, _registry)
    return True


# =================================================================
# STAGE A2/A3: ordering sweeps (orig vs opt wording)
# =================================================================
N_SWEEP = 50


def sweep_orderings():
    d = _load_json(SWEEP_JSON, None)
    if d:
        return [tuple(p) for p in d]
    rng = np.random.default_rng(2401)
    seen, out = set(), []
    while len(out) < N_SWEEP:
        p = tuple(int(x) for x in rng.permutation(N))
        if p not in seen:
            seen.add(p)
            out.append(p)
    _save_json(SWEEP_JSON, [list(p) for p in out])
    return out


def stage_sweep(wid):
    wordings = _registry[wid]
    for p in sweep_orderings():
        ensure(wid, wordings, p, HELDOUT_Q)
    # completeness check
    for p in sweep_orderings():
        if acc(wid, p, HELDOUT_Q) is None:
            raise Pause()
    return True


# =================================================================
# STAGE B: PRISM vs OPRO ordering search, 5 seeds, 30-Q fitness
# =================================================================
B_SEEDS = 5
B_BUDGET = 25       # total evals per method per seed (incl. 3 seed orderings)
B_SEED0 = 3


def b_meta_prompt(evaluated):
    top = sorted(evaluated, key=lambda e: e[1], reverse=True)[:10]
    lines = [
        "You are choosing the ORDER in which a small math model performs 8",
        "fixed reasoning steps: " + ", ".join(LABELS) + ".",
        "Wording is fixed; only the order may change. Orderings tried so",
        "far and their accuracy on hard math problems (best first):", ""]
    for perm, sc in top:
        lines.append(f"[accuracy {sc:.3f}] " +
                     ", ".join(LABELS[i] for i in perm))
    lines += ["",
              "Propose ONE NEW ordering (a permutation of all 8 steps, each",
              "exactly once) you expect to score higher. Output the 8 step",
              "names in order, comma-separated, nothing else."]
    return "\n".join(lines)


def novel(perm, evaluated_perms, rng, propose):
    for _ in range(12):
        cand = propose(rng)
        if cand is not None and tuple(cand) not in evaluated_perms:
            return tuple(cand)
    # fallback: random novel
    for _ in range(200):
        cand = tuple(int(x) for x in rng.permutation(N))
        if cand not in evaluated_perms:
            return cand
    return None


def prism_propose_fn(evaluated):
    def propose(rng):
        if len(evaluated) < 2:
            return list(rng.permutation(N))
        # tournament on fitness, then portfolio mutation
        idx = rng.integers(0, len(evaluated), min(3, len(evaluated)))
        parent = max((evaluated[i] for i in idx), key=lambda e: e[1])[0]
        child = list(parent)
        MUTATIONS[OPS4[rng.integers(len(OPS4))]](child, rng)
        return child
    return propose


def opro_propose_fn(evaluated):
    def propose(rng):
        txt = opt_call(b_meta_prompt(evaluated))
        return parse_ordering(txt)
    return propose


def run_method(seed, method):
    """Returns list of (perm_tuple, acc) in evaluation order, len B_BUDGET."""
    bstate = _load_json(BSTATE_JSON, {})
    ckey = f"{seed}:{method}"
    rec = bstate.get(ckey, {"evals": []})
    evaluated = [(tuple(p), a) for p, a in rec["evals"]]
    eval_perms = {p for p, _ in evaluated}
    rng = np.random.default_rng(24000 + seed * 7 +
                                (0 if method == "prism" else 1))
    # seed orderings: same 3 for both methods (seed-derived, method-agnostic)
    srng = np.random.default_rng(999 + seed)
    seeds3 = []
    while len(seeds3) < B_SEED0:
        p = tuple(int(x) for x in srng.permutation(N))
        if p not in seeds3:
            seeds3.append(p)
    plan = list(seeds3)
    while len(evaluated) < B_BUDGET:
        if len(evaluated) < B_SEED0:
            cand = plan[len(evaluated)]
            if cand in eval_perms:  # already done (resume)
                # shouldn't happen but guard
                cand = novel(None, eval_perms, rng,
                             lambda r: list(r.permutation(N)))
        else:
            propose = (prism_propose_fn(evaluated) if method == "prism"
                       else opro_propose_fn(evaluated))
            cand = novel(None, eval_perms, rng, propose)
        if cand is None:
            break
        ensure("orig", ORIG_WORDINGS, cand, TRACKB_Q)
        a = acc("orig", cand, TRACKB_Q)
        if a is None:
            raise Pause()
        evaluated.append((cand, a))
        eval_perms.add(cand)
        rec["evals"] = [[list(p), a2] for p, a2 in evaluated]
        bstate[ckey] = rec
        _save_json(BSTATE_JSON, bstate)
    return evaluated


def stage_b():
    for seed in range(B_SEEDS):
        for method in ("prism", "opro"):
            ev = run_method(seed, method)
            if len(ev) < B_BUDGET:
                raise Pause()
    return True


# =================================================================
# STAGE C: analysis
# =================================================================
def bootstrap_ci(xs, n=10000):
    xs = np.asarray(xs, float)
    if len(xs) < 2:
        return (float(xs.mean()) if len(xs) else float("nan"),
                float("nan"), float("nan"))
    rng = np.random.default_rng(7)
    m = [xs[rng.integers(0, len(xs), len(xs))].mean() for _ in range(n)]
    return float(xs.mean()), float(np.percentile(m, 2.5)), \
        float(np.percentile(m, 97.5))


def stage_c():
    L = []
    L.append("Experiment T: prompt-optimizer baselines (Iteration 24)")
    L.append(f"target {TARGET_MODEL} | optimizer {OPT_MODEL}")

    traj = _load_json(TRAJ_JSON, [])
    best = _load_json(BESTWORD_JSON, {})
    orig_train = traj[0]["score"] if traj else float("nan")
    L.append(f"\n[A1] OPRO wording optimization ({A1_ROUNDS} rounds, "
             f"60 train Q):")
    L.append(f"  original wording train acc {orig_train:.3f} -> best "
             f"optimized train acc {best.get('score', float('nan')):.3f} "
             f"(round {best.get('round')})")

    sw = sweep_orderings()
    orig_accs = np.array([acc("orig", p, HELDOUT_Q) for p in sw])
    opt_accs = np.array([acc("opt", p, HELDOUT_Q) for p in sw])
    std_o = float(orig_accs.std())
    std_p = float(opt_accs.std())
    ratio = std_p / std_o if std_o > 0 else float("nan")
    L.append(f"\n[A2/A3] ordering sweep, {N_SWEEP} orderings x "
             f"{len(HELDOUT_Q)} held-out Q:")
    L.append(f"  ORIGINAL wording: mean {orig_accs.mean():.3f} std "
             f"{std_o:.3f} range [{orig_accs.min():.3f},"
             f"{orig_accs.max():.3f}]")
    L.append(f"  OPTIMIZED wording: mean {opt_accs.mean():.3f} std "
             f"{std_p:.3f} range [{opt_accs.min():.3f},"
             f"{opt_accs.max():.3f}]")
    dmean, dlo, dhi = bootstrap_ci(opt_accs - orig_accs)
    L.append(f"  paired level lift (opt-orig) mean {dmean:+.3f} "
             f"CI [{dlo:+.3f},{dhi:+.3f}]  (did OPRO raise accuracy at all?)")
    h25 = "HOLDS" if (std_p >= 0.4 * std_o and std_p >= 0.03) else (
        "FALSIFIED" if std_p < 0.02 else "WEAK (between thresholds)")
    L.append(f"  H25 (ordering still matters after content optimization): "
             f"opt std {std_p:.3f} vs orig {std_o:.3f} (ratio {ratio:.2f}) "
             f"-> {h25}")

    # Track B
    bstate = _load_json(BSTATE_JSON, {})
    L.append(f"\n[B] ordering search, {B_SEEDS} seeds x {B_BUDGET} evals "
             f"x {len(TRACKB_Q)}-Q fitness (best-found at budget):")
    budgets = [3, 5, 10, 15, 20, 25]
    curves = {"prism": {b: [] for b in budgets},
              "opro": {b: [] for b in budgets}}
    finals = {"prism": [], "opro": []}
    for seed in range(B_SEEDS):
        for method in ("prism", "opro"):
            ev = [(tuple(p), a) for p, a in
                  bstate[f"{seed}:{method}"]["evals"]]
            best_so = -1
            best_at = {}
            for i, (_, a) in enumerate(ev, 1):
                best_so = max(best_so, a)
                best_at[i] = best_so
            for b in budgets:
                curves[method][b].append(best_at.get(min(b, len(ev)),
                                                     best_so))
            finals[method].append(best_at.get(B_BUDGET, best_so))
    for method in ("prism", "opro"):
        row = "  ".join(f"b{b}:{np.mean(curves[method][b]):.3f}"
                        for b in budgets)
        L.append(f"  {method.upper():5} {row}")
    pf, pflo, pfhi = bootstrap_ci(finals["prism"])
    of, oflo, ofhi = bootstrap_ci(finals["opro"])
    diff = np.array(finals["prism"]) - np.array(finals["opro"])
    dm, dl, dh = bootstrap_ci(diff)
    L.append(f"  best-found at budget {B_BUDGET}: PRISM {pf:.3f} "
             f"[{pflo:.3f},{pfhi:.3f}] vs OPRO {of:.3f} "
             f"[{oflo:.3f},{ofhi:.3f}]")
    L.append(f"  PRISM-minus-OPRO {dm:+.3f} CI [{dl:+.3f},{dh:+.3f}]")
    if dl > 0:
        h26 = "HOLDS (PRISM decisively better)"
    elif dh < 0:
        h26 = "FALSIFIED (OPRO decisively better)"
    else:
        h26 = ("directional: PRISM higher point estimate, CI overlaps"
               if dm >= 0 else
               "directional: OPRO higher point estimate, CI overlaps")
    L.append(f"  H26 (PRISM search >= generic LLM optimizer): {h26}")

    g = _guard_load()
    L.append(f"\nspend: {API.calls} target calls, "
             f"${g.get('reported_usd', 0):.2f} of ${CAP_USD} cap")
    txt = "\n".join(L)
    open(REPORT_TXT, "w").write(txt + "\n")
    print(txt)
    print("STUDY COMPLETE.")
    return True


# =================================================================
# driver
# =================================================================
STAGES = [("A1", stage_a1),
          ("A2", lambda: stage_sweep("orig")),
          ("A3", lambda: stage_sweep("opt")),
          ("B", stage_b),
          ("C", stage_c)]


def main():
    guard_update(0.0, poll=True)
    state = _load_json(STATE_JSON, {})
    done = set(state.get("stages_done", []))
    try:
        for name, fn in STAGES:
            if name in done:
                continue
            print(f"[stage {name}] starting", flush=True)
            fn()
            done.add(name)
            state = _load_json(STATE_JSON, {})
            state["stages_done"] = sorted(done)
            _save_json(STATE_JSON, state)
            print(f"[stage {name}] complete", flush=True)
    except Pause:
        API.save(poll=True)
        print("PAUSED (wall clock); rerun to resume", flush=True)
        return
    except Budget as e:
        API.save(poll=True)
        print(f"PAUSED ({e}); rerun to resume", flush=True)
        return
    API.save(poll=True)


def selftest():
    print("OpenRouter key:", "ok" if OR_KEY else "MISSING")
    print("Google key:", "ok" if GOOGLE_KEY else "MISSING")
    r = API.ask(ORIG_WORDINGS, CANON, 0)
    print(f"target graded: {r} (gold {POOL[0]['answer']!r})")
    txt = opt_call("Reply with the single word OK.")
    print(f"optimizer replied: {txt[:60]!r}")
    API.save(poll=True)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        selftest()
    else:
        if len(sys.argv) > 1:
            BUDGET_SECONDS = float(sys.argv[1])
        main()
