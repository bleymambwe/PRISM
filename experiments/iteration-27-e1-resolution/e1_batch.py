"""Iteration 27, Experiment E1: the flagship landscape at 200 questions,
run through the Gemini Batch API.

Re-enumerates all 720 orderings of the six Experiment-K reasoning modules
on 200 GSM8K questions (from 32), same wording, same frozen grader,
temperature 0, same model. Fitness granularity 3.1% -> 0.5%.

Why batch. Two reasons, and the second is the one that matters:
  1. Batch is 50% of standard rates -- $16.81 instead of $33.62 for the
     144,000 calls (measured profile: 206 in / 532 out tokens per call,
     experiments/iteration-11/results/token_usage.csv).
  2. Background processes on this machine die after 3-8 minutes, which is
     why every previous runner is a resumable foreground chunk loop. A
     batch job inverts that: submit a JSONL, exit, poll a job id later.
     No invocation of this script needs to live longer than a few seconds.

Why E1 is worth running at all -- note this changed after Tier 0. The
registered justification was that the regime call destabilises at low
question counts; H33 tested that and FALSIFIED it (93.3% agreement at
q=8). The surviving reason is tie density: at 32 questions 60 of the 720
orderings are exactly optimal, uniform sampling finds one in ~11 draws,
and "found the optimum" saturates at 100% by budget 50, so the metric
cannot discriminate. More questions break the ties. See
experiments/iteration-26-tier0-gauntlet/FINDINGS.md sections 3-4.

Stages. Each is idempotent and exits quickly; drive the experiment by
invoking the script repeatedly until it prints STUDY COMPLETE.

  0 POOL      build data/gsm8k_subset200.json, preserving the original 32
              as indices 0-31 so the published landscape is a strict
              subset of the new one.
  1 SMOKE     20 cells through batch AND through the sync endpoint;
              grades must agree exactly. Gate -- validates the JSONL
              schema and the result-parsing before 144,000 requests are
              committed. Writes the first raw result line to disk so the
              response shape can be eyeballed.
  2 DRIFT     re-ask a 200-cell sample of iteration-09's answer cache and
              report agreement with what was published. This protects
              E1's headline comparison: if the served model has moved
              since Experiment K, a 32-vs-200-question difference is
              confounded whether or not the old cache is reused. Reuse of
              the old 32 is opt-in (--reuse-32) and requires this gate.
  3 SUBMIT    chunk the missing cells into batch jobs and submit them.
  4 POLL      ingest finished jobs into the answer cache.
  5 LANDSCAPE write e1_landscape.csv once all 720 orderings are complete.

Cost guard. Batch bills after the fact, so the guard projects spend
BEFORE submitting (measured token profile x batch rates) and refuses to
submit past the cap; it then reconciles against the usageMetadata that
comes back with every response. Cap is scoped to this experiment.

Pre-registration. Per house practice (D18/D25/D27) SUBMIT refuses to run
unless hypotheses.json exists and is tracked by git -- the commit
timestamp is the registration, and it must precede any result.

Usage:
  python e1_batch.py                 run every stage that can advance, exit
  python e1_batch.py 600             same, but keep polling for 600s
  python e1_batch.py --status        print state and exit
  python e1_batch.py --dry-run       build the JSONL chunks, submit nothing
  python e1_batch.py --reuse-32      reuse iteration-09 cells for q<32
                                     (requires the drift gate to pass)

API key: Google Cloud Secret Manager (GOOGLE_API_KEY), per D10.
Requires: pip install google-genai
"""

import csv
import itertools
import json
import os
import random
import re
import subprocess
import sys
import time

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..", "..")
OUT = os.path.join(HERE, "results")
DATA = os.path.join(HERE, "data")
SRC09 = os.path.join(ROOT, "experiments", "iteration-09")

POOL_JSON = os.path.join(DATA, "gsm8k_subset200.json")
GSM8K_TEST = os.path.join(DATA, "gsm8k_test.jsonl")
CACHE_CSV = os.path.join(OUT, "answer_cache.csv")        # perm,qidx,correct
JOBS_CSV = os.path.join(OUT, "batch_jobs.csv")
USAGE_CSV = os.path.join(OUT, "token_usage.csv")
GUARD_JSON = os.path.join(OUT, "spend_guard.json")
SMOKE_JSON = os.path.join(OUT, "smoke_report.json")
SMOKE_RAW = os.path.join(OUT, "smoke_raw_line.json")
DRIFT_JSON = os.path.join(OUT, "drift_report.json")
LANDSCAPE_CSV = os.path.join(OUT, "e1_landscape.csv")
HYPOTHESES = os.path.join(HERE, "hypotheses.json")
CHUNK_DIR = os.path.join(OUT, "chunks")

# ---- the experiment, fixed ------------------------------------------
# MODULES, build_prompt, extract_answer and the grading rule are VERBATIM
# from experiments/iteration-09/llm_chain_experiment.py. Fitness must mean
# exactly what it meant in the published landscape; stage 1 tests that
# empirically rather than trusting this comment.
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
N_Q = 200
MODEL = "gemini-2.5-flash-lite"
MAX_OUTPUT_TOKENS = 600
SYNC_URL = (f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODEL}:generateContent")

# ---- cost model ------------------------------------------------------
PRICE_IN, PRICE_OUT = 0.05, 0.20        # $/M tokens, batch = 50% of list
EST_TIN, EST_TOUT = 205.6, 532.3        # measured, iteration-11
CAP_USD = 25.0                          # approved $20 + headroom
CHUNK_REQUESTS = 12_000                 # ~8.9M enqueued tokens < ~10M tier-1
POLL_SECONDS = 60

TERMINAL = {"JOB_STATE_SUCCEEDED", "JOB_STATE_FAILED",
            "JOB_STATE_CANCELLED", "JOB_STATE_EXPIRED"}


class Gate(Exception):
    """A stage refused to advance; the message says why."""


# =====================================================================
# key, prompt, grading
# =====================================================================
def get_key():
    r = subprocess.run(["gcloud", "secrets", "versions", "access", "latest",
                        "--secret=GOOGLE_API_KEY"],
                       capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        sys.exit("secret access failed: " + r.stderr[:200])
    return r.stdout.strip()


def build_prompt(perm, question):
    steps = "\n".join(f"{i+1}. {MODULES[m]}" for i, m in enumerate(perm))
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


def grade(text, gold):
    pred = extract_answer(text or "")
    try:
        return int(abs(float(pred or "nan") - float(gold)) < 1e-6)
    except ValueError:
        return 0


def perm_key(perm):
    """Canonical cache key -- identical to iteration-09's json.dumps form."""
    return json.dumps(list(perm))


def code(perm):
    """Compact form used inside batch request keys."""
    return "".join(str(i) for i in perm)


# =====================================================================
# question pool
# =====================================================================
def stage_pool():
    if os.path.exists(POOL_JSON):
        return json.load(open(POOL_JSON, encoding="utf-8"))

    os.makedirs(DATA, exist_ok=True)
    orig = json.load(open(os.path.join(SRC09, "data", "gsm8k_subset32.json"),
                          encoding="utf-8"))
    if not os.path.exists(GSM8K_TEST):
        raise Gate(
            f"need the GSM8K test split at {GSM8K_TEST}\n"
            "  one JSON object per line with 'question' and 'answer'\n"
            "  (answer ends '#### <gold>'), e.g. the test.jsonl from\n"
            "  github.com/openai/grade-school-math (data/test.jsonl)")

    seen = {q["question"] for q in orig}
    extra = []
    for line in open(GSM8K_TEST, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        r = json.loads(line)
        if r["question"] in seen:
            continue
        m = re.search(r"####\s*(-?[\d,]+(?:\.\d+)?)", r["answer"])
        if not m:
            continue
        extra.append({"question": r["question"], "answer": r["answer"],
                      "gold": m.group(1).replace(",", "")})

    random.Random(7).shuffle(extra)
    pool = orig + extra[:N_Q - len(orig)]
    if len(pool) < N_Q:
        raise Gate(f"only {len(pool)} usable questions found, need {N_Q}")

    json.dump(pool, open(POOL_JSON, "w", encoding="utf-8"), indent=1)
    print(f"[pool] wrote {len(pool)} questions "
          f"({len(orig)} preserved from Experiment K at indices "
          f"0-{len(orig)-1})")
    return pool


# =====================================================================
# cache, jobs ledger, spend guard
# =====================================================================
def load_cache():
    cache = {}
    if os.path.exists(CACHE_CSV):
        for r in csv.reader(open(CACHE_CSV)):
            if r and r[0] != "perm":
                cache[(r[0], int(r[1]))] = int(r[2])
    return cache


def append_cache(rows):
    new = not os.path.exists(CACHE_CSV)
    with open(CACHE_CSV, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["perm", "qidx", "correct"])
        w.writerows(rows)


def load_jobs():
    if not os.path.exists(JOBS_CSV):
        return []
    return list(csv.DictReader(open(JOBS_CSV)))


def save_jobs(jobs):
    with open(JOBS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=[
            "chunk", "job_name", "n_requests", "state", "ingested",
            "submitted_at"])
        w.writeheader()
        w.writerows(jobs)


def guard_load():
    if os.path.exists(GUARD_JSON):
        return json.load(open(GUARD_JSON))
    return {"cap_usd": CAP_USD, "reported_usd": 0.0, "pending_usd": 0.0,
            "calls": 0, "tin": 0, "tout": 0, "updated": None}


def guard_save(g):
    g["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    os.makedirs(OUT, exist_ok=True)
    tmp = GUARD_JSON + ".tmp"
    json.dump(g, open(tmp, "w"), indent=1)
    os.replace(tmp, GUARD_JSON)
    with open(USAGE_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["calls", "tin", "tout",
                                          "usd_reported"])
        w.writeheader()
        w.writerow({"calls": g["calls"], "tin": g["tin"], "tout": g["tout"],
                    "usd_reported": round(g["reported_usd"], 4)})


def project_usd(n_requests):
    return n_requests * (EST_TIN * PRICE_IN + EST_TOUT * PRICE_OUT) / 1e6


def guard_admit(n_requests):
    """Refuse to submit work whose projected cost breaches the cap."""
    g = guard_load()
    est = project_usd(n_requests)
    total = g["reported_usd"] + g["pending_usd"] + est
    if total > CAP_USD:
        raise Gate(f"COST CAP: ${g['reported_usd']:.2f} spent + "
                   f"${g['pending_usd']:.2f} in flight + ${est:.2f} "
                   f"projected = ${total:.2f} > ${CAP_USD:.2f}")
    g["pending_usd"] += est
    guard_save(g)
    return est


def guard_settle(est_released, tin, tout, calls):
    g = guard_load()
    g["pending_usd"] = max(0.0, g["pending_usd"] - est_released)
    g["reported_usd"] += (tin * PRICE_IN + tout * PRICE_OUT) / 1e6
    g["calls"] += calls
    g["tin"] += tin
    g["tout"] += tout
    guard_save(g)
    return g


# =====================================================================
# batch transport
# =====================================================================
def client():
    from google import genai
    return genai.Client(api_key=get_key())


def jsonl_line(perm, qidx, question):
    return json.dumps({
        "key": f"{code(perm)}#{qidx}",
        "request": {
            "contents": [{"parts": [{"text": build_prompt(perm, question)}]}],
            "generationConfig": {"temperature": 0,
                                 "maxOutputTokens": MAX_OUTPUT_TOKENS},
        },
    })


def write_chunk(path, cells, pool):
    with open(path, "w", encoding="utf-8") as f:
        for perm, qidx in cells:
            f.write(jsonl_line(perm, qidx, pool[qidx]["question"]) + "\n")


def submit_chunk(cl, path, display):
    from google.genai import types
    up = cl.files.upload(file=path,
                         config=types.UploadFileConfig(display_name=display,
                                                       mime_type="jsonl"))
    job = cl.batches.create(model=MODEL, src=up.name,
                            config={"display_name": display})
    return job.name


def read_results(cl, job):
    """Yield (key, text, tin, tout) for every response in a finished job.

    Defensive about response shape: the batch result is a GenerateContent
    response per line, but file-backed and inline-backed jobs differ, and
    error lines carry no candidates. Stage 1 writes a raw line to disk so
    the actual shape can be checked against this parser.
    """
    lines = []
    dest = getattr(job, "dest", None)
    if dest is not None and getattr(dest, "file_name", None):
        raw = cl.files.download(file=dest.file_name)
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        lines = [json.loads(ln) for ln in raw.splitlines() if ln.strip()]
    elif dest is not None and getattr(dest, "inlined_responses", None):
        for r in dest.inlined_responses:
            lines.append(json.loads(r.model_dump_json())
                         if hasattr(r, "model_dump_json") else dict(r))

    for ln in lines:
        key = ln.get("key")
        resp = ln.get("response") or {}
        if not key or ln.get("error") or not resp:
            continue
        try:
            text = resp["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            text = ""      # blocked or empty -- counts as wrong, as in K
        um = resp.get("usageMetadata") or {}
        yield (key, text,
               int(um.get("promptTokenCount", 0) or 0),
               int(um.get("candidatesTokenCount", 0) or 0))


def ask_sync(key, perm, qidx, pool, retries=5):
    """One synchronous call -- used only by the smoke and drift gates."""
    q = pool[qidx]
    body = {"contents": [{"parts": [{"text": build_prompt(
        perm, q["question"])}]}],
        "generationConfig": {"temperature": 0,
                             "maxOutputTokens": MAX_OUTPUT_TOKENS}}
    for attempt in range(retries):
        try:
            r = requests.post(SYNC_URL, params={"key": key}, json=body,
                              timeout=60)
            if r.status_code == 200:
                try:
                    text = (r.json()["candidates"][0]["content"]["parts"][0]
                            ["text"])
                except (KeyError, IndexError):
                    text = ""
                return grade(text, q["gold"])
            if r.status_code in (429, 500, 502, 503):
                time.sleep(min(2 ** attempt * 2, 30))
                continue
            print(f"  sync API {r.status_code}: {r.text[:120]}")
            time.sleep(2)
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return None


def run_small_batch(cl, cells, pool, tag, timeout_s=3600):
    """Submit a handful of cells and block until they come back."""
    os.makedirs(CHUNK_DIR, exist_ok=True)
    path = os.path.join(CHUNK_DIR, f"{tag}.jsonl")
    write_chunk(path, cells, pool)
    name = submit_chunk(cl, path, tag)
    print(f"[{tag}] submitted {len(cells)} requests as {name}")
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        job = cl.batches.get(name=name)
        if job.state.name in TERMINAL:
            break
        time.sleep(POLL_SECONDS)
    else:
        raise Gate(f"[{tag}] job did not finish within {timeout_s}s "
                   f"-- rerun to keep waiting ({name})")
    if job.state.name != "JOB_STATE_SUCCEEDED":
        raise Gate(f"[{tag}] job {job.state.name}: "
                   f"{getattr(job, 'error', None)}")
    return job


# =====================================================================
# stage 1 -- smoke: batch and sync must grade identically
# =====================================================================
def stage_smoke(cl, key, pool):
    if os.path.exists(SMOKE_JSON):
        rep = json.load(open(SMOKE_JSON))
        if rep.get("pass"):
            return
        raise Gate("smoke gate previously FAILED; delete "
                   f"{SMOKE_JSON} to retry after fixing the parser")

    rng = random.Random(11)
    cells = [([int(x) for x in rng.sample(range(N), N)],
              rng.randrange(min(32, len(pool)))) for _ in range(20)]

    guard_admit(len(cells) * 2)
    job = run_small_batch(cl, cells, pool, "smoke")

    got, tin, tout = {}, 0, 0
    first_raw = None
    for k, text, ti, to in read_results(cl, job):
        c, qi = k.split("#")
        got[(c, int(qi))] = grade(text, pool[int(qi)]["gold"])
        tin += ti
        tout += to
        if first_raw is None:
            first_raw = {"key": k, "text_head": text[:400],
                         "promptTokenCount": ti, "candidatesTokenCount": to}
    json.dump(first_raw or {}, open(SMOKE_RAW, "w"), indent=1)

    if len(got) != len(cells):
        raise Gate(f"smoke: parsed {len(got)}/{len(cells)} responses -- the "
                   f"result schema does not match read_results(); inspect "
                   f"{SMOKE_RAW}")

    agree, mismatches = 0, []
    for perm, qidx in cells:
        s = ask_sync(key, perm, qidx, pool)
        b = got[(code(perm), qidx)]
        if s == b:
            agree += 1
        else:
            mismatches.append({"perm": perm_key(perm), "qidx": qidx,
                               "sync": s, "batch": b})

    guard_settle(project_usd(len(cells) * 2), tin, tout, len(got))
    rep = {"n": len(cells), "agree": agree, "pass": agree == len(cells),
           "mismatches": mismatches, "tin": tin, "tout": tout}
    json.dump(rep, open(SMOKE_JSON, "w"), indent=1)
    print(f"[smoke] batch vs sync agreement {agree}/{len(cells)}")
    if not rep["pass"]:
        raise Gate("smoke gate FAILED -- batch and sync grade differently. "
                   "Do not submit the enumeration; investigate "
                   f"{SMOKE_JSON} first.")


# =====================================================================
# stage 2 -- drift: has the served model moved since Experiment K?
# =====================================================================
def stage_drift(cl, pool):
    if os.path.exists(DRIFT_JSON):
        return json.load(open(DRIFT_JSON))

    old = {}
    old_csv = os.path.join(SRC09, "results", "answer_cache.csv")
    if not os.path.exists(old_csv):
        raise Gate(f"iteration-09 answer cache not found at {old_csv}")
    for r in csv.reader(open(old_csv)):
        if r and r[0] != "perm":
            old[(r[0], int(r[1]))] = int(r[2])

    rng = random.Random(23)
    sample = rng.sample(sorted(old), min(200, len(old)))
    cells = [([int(x) for x in json.loads(pk)], qi) for pk, qi in sample]

    est = guard_admit(len(cells))
    job = run_small_batch(cl, cells, pool, "drift")

    agree, n, tin, tout = 0, 0, 0, 0
    for k, text, ti, to in read_results(cl, job):
        c, qi = k.split("#")
        qi = int(qi)
        now = grade(text, pool[qi]["gold"])
        was = old[(perm_key([int(x) for x in c]), qi)]
        agree += int(now == was)
        n += 1
        tin += ti
        tout += to
    guard_settle(est, tin, tout, n)

    rate = agree / n if n else 0.0
    rep = {"n": n, "agree": agree, "rate": round(rate, 4),
           "reuse_safe": rate >= 0.98,
           "note": ("cell-level agreement between the published Experiment K "
                    "answers and the same cells re-asked today")}
    json.dump(rep, open(DRIFT_JSON, "w"), indent=1)
    print(f"[drift] {agree}/{n} cells agree with Experiment K "
          f"({rate:.1%}) -- reuse of the original 32 is "
          f"{'permitted' if rep['reuse_safe'] else 'NOT permitted'}")
    if not rep["reuse_safe"]:
        print("[drift] the served model appears to have moved since "
              "Experiment K. Enumerate all 200 questions fresh, and say so "
              "in the paper: the 32-vs-200 comparison is otherwise "
              "confounded by model version, not resolution.")
    return rep


# =====================================================================
# stage 3 -- submit
# =====================================================================
def preregistered():
    if not os.path.exists(HYPOTHESES):
        raise Gate(f"pre-registration missing: write {HYPOTHESES} with a "
                   "direction, a decision threshold and a reversal "
                   "condition per hypothesis, and COMMIT it before "
                   "submitting. The commit timestamp is the registration "
                   "(D18/D25/D27).")
    r = subprocess.run(["git", "ls-files", "--error-unmatch", HYPOTHESES],
                       capture_output=True, text=True, cwd=HERE)
    if r.returncode != 0:
        raise Gate("hypotheses.json exists but is not committed. Commit it "
                   "before any evaluation runs -- an uncommitted file has "
                   "no precedence and cannot serve as pre-registration.")


def missing_cells(cache, reuse_32, drift_ok):
    perms = [list(p) for p in itertools.permutations(range(N))]
    q_lo = 32 if (reuse_32 and drift_ok) else 0
    cells = []
    for p in perms:
        pk = perm_key(p)
        for qi in range(N_Q):
            if qi < q_lo:
                continue
            if (pk, qi) not in cache:
                cells.append((p, qi))
    return cells


def stage_submit(cl, pool, cache, reuse_32, drift_ok, dry_run):
    if not dry_run:
        preregistered()
    jobs = load_jobs()
    in_flight = sum(int(j["n_requests"]) for j in jobs
                    if j["state"] not in TERMINAL or j["ingested"] != "1")
    cells = missing_cells(cache, reuse_32, drift_ok)
    todo = len(cells) - in_flight
    if todo <= 0:
        return jobs

    os.makedirs(CHUNK_DIR, exist_ok=True)
    start = len(jobs)
    queued = cells[in_flight:]
    for i in range(0, len(queued), CHUNK_REQUESTS):
        part = queued[i:i + CHUNK_REQUESTS]
        chunk = start + i // CHUNK_REQUESTS
        tag = f"e1_chunk_{chunk:02d}"
        path = os.path.join(CHUNK_DIR, f"{tag}.jsonl")
        write_chunk(path, part, pool)
        est = project_usd(len(part))
        if dry_run:
            print(f"[dry-run] {tag}: {len(part)} requests, ~${est:.2f}")
            continue
        guard_admit(len(part))
        name = submit_chunk(cl, path, tag)
        jobs.append({"chunk": chunk, "job_name": name,
                     "n_requests": len(part), "state": "JOB_STATE_PENDING",
                     "ingested": "0",
                     "submitted_at": time.strftime("%Y-%m-%d %H:%M:%S")})
        save_jobs(jobs)
        print(f"[submit] {tag}: {len(part)} requests -> {name} (~${est:.2f})")
    return jobs


# =====================================================================
# stage 4 -- poll and ingest
# =====================================================================
def stage_poll(cl, pool, cache):
    jobs = load_jobs()
    changed = False
    for j in jobs:
        if j["ingested"] == "1":
            continue
        job = cl.batches.get(name=j["job_name"])
        j["state"] = job.state.name
        if job.state.name not in TERMINAL:
            print(f"[poll] chunk {j['chunk']}: {job.state.name}")
            continue
        changed = True
        if job.state.name != "JOB_STATE_SUCCEEDED":
            print(f"[poll] chunk {j['chunk']} {job.state.name} -- its cells "
                  f"stay missing and will be resubmitted on the next run")
            j["ingested"] = "1"
            guard_settle(project_usd(int(j["n_requests"])), 0, 0, 0)
            save_jobs(jobs)
            continue

        rows, tin, tout = [], 0, 0
        for k, text, ti, to in read_results(cl, job):
            c, qi = k.split("#")
            qi = int(qi)
            pk = perm_key([int(x) for x in c])
            if (pk, qi) in cache:
                continue
            g = grade(text, pool[qi]["gold"])
            rows.append([pk, qi, g])
            cache[(pk, qi)] = g
            tin += ti
            tout += to
        append_cache(rows)
        guard_settle(project_usd(int(j["n_requests"])), tin, tout, len(rows))
        j["ingested"] = "1"
        save_jobs(jobs)
        print(f"[poll] chunk {j['chunk']}: ingested {len(rows)} cells "
              f"({tin/1e6:.2f}M in / {tout/1e6:.2f}M out)")
    return changed


# =====================================================================
# stage 5 -- landscape
# =====================================================================
def stage_landscape(cache, reuse_32, drift_ok):
    perms = [list(p) for p in itertools.permutations(range(N))]
    fits, complete = {}, 0
    for p in perms:
        pk = perm_key(p)
        vals = [cache.get((pk, qi)) for qi in range(N_Q)]
        if all(v is not None for v in vals):
            fits[pk] = sum(vals) / N_Q
            complete += 1
    if complete < len(perms):
        print(f"[landscape] {complete}/{len(perms)} orderings complete")
        return False

    with open(LANDSCAPE_CSV, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["perm", "fitness"])
        for k, v in sorted(fits.items(), key=lambda kv: -kv[1]):
            w.writerow([k, round(v, 6)])
    vals = sorted(fits.values())
    top = vals[-1]
    dens = sum(1 for v in vals if v == top) / len(vals)
    g = guard_load()
    with open(os.path.join(OUT, "e1_summary.txt"), "w") as f:
        f.write(
            f"E1 flagship landscape, {N_Q} questions, model {MODEL}\n"
            f"orderings            {len(fits)}\n"
            f"fitness granularity  {1/N_Q:.4f}\n"
            f"worst / best         {vals[0]:.4f} / {top:.4f}\n"
            f"span                 {top - vals[0]:.4f}\n"
            f"distinct values      {len(set(vals))}\n"
            f"optimum density      {dens:.4%}   (was 8.33% at 32 questions)\n"
            f"reused K cells       {'yes' if (reuse_32 and drift_ok) else 'no'}\n"
            f"spend                ${g['reported_usd']:.2f} of ${CAP_USD}\n")
    print(f"[landscape] written: span {vals[0]:.3f}-{top:.3f}, "
          f"optimum density {dens:.2%}, {len(set(vals))} distinct values")
    return True


# =====================================================================
def status():
    cache = load_cache()
    g = guard_load()
    jobs = load_jobs()
    print(f"cache      {len(cache):,} / {720 * N_Q:,} cells")
    print(f"jobs       {sum(1 for j in jobs if j['ingested'] == '1')}"
          f"/{len(jobs)} ingested")
    print(f"spend      ${g['reported_usd']:.2f} reported + "
          f"${g['pending_usd']:.2f} in flight, cap ${CAP_USD}")
    print(f"tokens     {g['tin']/1e6:.1f}M in / {g['tout']/1e6:.1f}M out "
          f"over {g['calls']:,} calls")


def main(argv):
    os.makedirs(OUT, exist_ok=True)
    dry_run = "--dry-run" in argv
    reuse_32 = "--reuse-32" in argv
    if "--status" in argv:
        return status()
    budget = next((float(a) for a in argv if a.replace(".", "").isdigit()),
                  0.0)

    pool = stage_pool()
    cl = None if dry_run else client()
    key = None if dry_run else get_key()
    drift_ok = False

    if not dry_run:
        stage_smoke(cl, key, pool)
        drift_ok = bool(stage_drift(cl, pool).get("reuse_safe"))
        if reuse_32 and drift_ok:
            old_csv = os.path.join(SRC09, "results", "answer_cache.csv")
            cache = load_cache()
            rows = [r for r in csv.reader(open(old_csv))
                    if r and r[0] != "perm" and (r[0], int(r[1])) not in cache]
            if rows:
                append_cache(rows)
                print(f"[reuse] imported {len(rows)} Experiment K cells "
                      f"(q < 32); disclose this in the paper")

    cache = load_cache()
    stage_submit(cl, pool, cache, reuse_32, drift_ok, dry_run)
    if dry_run:
        return print("[dry-run] chunks written to results/chunks/, "
                     "nothing submitted")

    t0 = time.time()
    while True:
        stage_poll(cl, pool, cache)
        cache = load_cache()
        if stage_landscape(cache, reuse_32, drift_ok):
            status()
            print("STUDY COMPLETE.")
            return
        stage_submit(cl, pool, cache, reuse_32, drift_ok, dry_run)
        if time.time() - t0 >= budget:
            status()
            print("rerun to resume (batch jobs keep running while you are "
                  "not; nothing is lost by exiting)")
            return
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except Gate as e:
        print(f"\nSTOPPED: {e}")
        sys.exit(1)
