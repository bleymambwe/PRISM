"""Re-query GSM8K subset question 31 for all 720 Experiment K orderings.

Question 31 (the carnival question) carries a wrong gold label: the true total
is 2,180 (750 + 430 + 700 + 300), but GSM8K's rationale adds Maryam's 400
increment in place of Sarah's 300 and records 2280. Experiment K's answer cache
stores only correct/incorrect against that label, not the model's answer, so the
corrected landscape cannot be recovered from it.

This script re-sends question 31 under Experiment K's exact prompt builder,
answer extractor, model and generation config (Gemini 2.5 Flash-Lite,
temperature 0, maxOutputTokens 600), and stores the raw extracted answer. It is a
re-query, not a recovery of the original responses: agreement with the original
cache (score against 2280) is reported so the reader can judge how faithfully
the re-query reproduces them.

Kill-safe and resumable: rows are appended to results/q31_requery.csv and
finished orderings are skipped on restart.

    python q31_requery.py
"""

import csv
import itertools
import json
import os
import re
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_CSV = os.path.join(HERE, "results", "q31_requery.csv")
QUESTIONS = json.load(open(os.path.join(HERE, "data", "gsm8k_subset32.json")))
QIDX = 31
MODEL = "gemini-2.5-flash-lite"
URL = (f"https://generativelanguage.googleapis.com/v1beta/models/"
       f"{MODEL}:generateContent")
FIELDS = ["perm", "pred", "finish", "in_tok", "out_tok"]

# Copied verbatim from llm_chain_experiment.py so the prompt is identical.
MODULES = [
    "RESTATE: Restate the problem briefly in your own words.",
    "IDENTIFY: List the known quantities and what is being asked.",
    "PLAN: Devise a short step-by-step strategy before calculating.",
    "COMPUTE: Carry out the calculations step by step.",
    "CHECK: Verify the result against the problem statement.",
    "ANSWER: State the final answer on its own line as "
    "'Answer: <number>'.",
]


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


def get_key():
    r = subprocess.run(["gcloud", "secrets", "versions", "access",
                        "latest", "--secret=GOOGLE_API_KEY"],
                       capture_output=True, text=True, shell=True)
    if r.returncode != 0:
        sys.exit("secret access failed: " + r.stderr[:200])
    return r.stdout.strip()


def ask(key, perm, retries=6):
    import time
    prompt = build_prompt(perm, QUESTIONS[QIDX]["question"])
    for attempt in range(retries):
        try:
            r = requests.post(
                URL, params={"key": key},
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"temperature": 0,
                                           "maxOutputTokens": 600}},
                timeout=60)
            if r.status_code == 200:
                body = r.json()
                cand = (body.get("candidates") or [{}])[0]
                usage = body.get("usageMetadata", {})
                try:
                    text = cand["content"]["parts"][0]["text"]
                except (KeyError, IndexError):
                    text = ""
                return {"pred": extract_answer(text) or "",
                        "finish": cand.get("finishReason", ""),
                        "in_tok": usage.get("promptTokenCount", 0),
                        "out_tok": usage.get("candidatesTokenCount", 0)}
            if r.status_code in (429, 500, 502, 503):
                time.sleep(min(2 ** attempt * 2, 30))
                continue
            print(f"  API {r.status_code}: {r.text[:120]}", flush=True)
            time.sleep(2)
        except requests.RequestException:
            time.sleep(2 ** attempt)
    return None


def main():
    done = set()
    if os.path.exists(OUT_CSV):
        done = {row["perm"] for row in csv.DictReader(open(OUT_CSV))}
    todo = [list(p) for p in itertools.permutations(range(6))
            if json.dumps(list(p)) not in done]
    print(f"{len(done)} done, {len(todo)} to query", flush=True)
    if not todo:
        return
    key = get_key()
    new = not os.path.exists(OUT_CSV)
    f = open(OUT_CSV, "a", newline="")
    wr = csv.DictWriter(f, fieldnames=FIELDS)
    if new:
        wr.writeheader()
    lock = threading.Lock()
    with ThreadPoolExecutor(max_workers=16) as ex:
        for perm, res in zip(todo, ex.map(lambda p: ask(key, p), todo)):
            if res is None:
                continue
            with lock:
                wr.writerow({"perm": json.dumps(perm), **res})
                f.flush()
    f.close()


def write_corrected_landscape():
    """Rescore question 31 against 2180 and write llm_landscape_q31corrected.csv.

    The other 31 questions keep their cached Experiment K scores. Analyse with
    `python analyze_llm_landscape.py _q31corrected`.
    """
    res = os.path.join(HERE, "results")
    pred = {r["perm"]: r["pred"] for r in csv.DictReader(open(OUT_CSV))}
    scores = {}
    for r in csv.DictReader(open(os.path.join(res, "answer_cache.csv"))):
        scores.setdefault(r["perm"], {})[int(r["qidx"])] = int(r["correct"])
    with open(os.path.join(res, "llm_landscape_q31corrected.csv"), "w",
              newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["perm", "fitness"])
        for r in csv.DictReader(open(os.path.join(res, "llm_landscape.csv"))):
            s = dict(scores[r["perm"]])
            assert abs(sum(s.values()) / 32 - float(r["fitness"])) < 1e-9
            s[QIDX] = int(pred[r["perm"]] == "2180")
            wr.writerow([r["perm"], sum(s.values()) / 32])


if __name__ == "__main__":
    main()
    write_corrected_landscape()
