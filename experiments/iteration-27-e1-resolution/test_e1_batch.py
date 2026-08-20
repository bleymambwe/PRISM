"""Offline checks for e1_batch.py — no API calls, no real state touched."""
import importlib.util
import json
import os
import sys
import tempfile

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e1_batch.py")
spec = importlib.util.spec_from_file_location("e1", SRC)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)          # must have no import-time side effects
print("import: ok (no gcloud call, no network)")

tmp = tempfile.mkdtemp()
m.OUT = tmp
m.CACHE_CSV = os.path.join(tmp, "answer_cache.csv")
m.GUARD_JSON = os.path.join(tmp, "spend_guard.json")
m.USAGE_CSV = os.path.join(tmp, "token_usage.csv")
m.CHUNK_DIR = os.path.join(tmp, "chunks")
m.N_Q = 3
pool = [{"question": f"Q{i}?", "answer": "...", "gold": str(i)}
        for i in range(m.N_Q)]

# --- 1. grading parity with iteration-09 -----------------------------
cases = [("blah\nAnswer: 18", "18", 1), ("Answer: $1,234.0", "1234", 1),
         ("Answer: 7", "18", 0), ("no number here", "18", 0),
         ("...the total is 18.", "18", 1), ("", "18", 0)]
for text, gold, want in cases:
    got = m.grade(text, gold)
    assert got == want, (text, gold, got, want)
print(f"grading: {len(cases)}/{len(cases)} cases match Experiment K rules")

# --- 2. prompt is byte-identical to iteration-09 ----------------------
sys.path.insert(0, os.path.dirname(SRC))
K = open(os.path.join(os.path.dirname(SRC), "..", "iteration-09",
                      "llm_chain_experiment.py"), encoding="utf-8").read()
k_modules = K[K.index("MODULES = ["):K.index("]\nN = 6")+1]
assert eval(k_modules.split("=", 1)[1].strip()) == m.MODULES
ns = {"MODULES": m.MODULES}
exec(K[K.index("def build_prompt"):K.index("def extract_answer")], ns)
assert ns["build_prompt"]([2, 0, 1, 5, 4, 3], "Q?") == \
    m.build_prompt([2, 0, 1, 5, 4, 3], "Q?")
print("prompt+modules: byte-identical to iteration-09")

# --- 3. JSONL schema round-trip --------------------------------------
line = json.loads(m.jsonl_line([0, 1, 2, 3, 4, 5], 2, pool[2]["question"]))
assert line["key"] == "012345#2"
assert line["request"]["generationConfig"] == {
    "temperature": 0, "maxOutputTokens": m.MAX_OUTPUT_TOKENS}
assert "Problem: Q2?" in line["request"]["contents"][0]["parts"][0]["text"]
print("jsonl: key/contents/generationConfig shape ok")

# --- 4. key <-> cache-key round-trip ---------------------------------
c = m.code([3, 1, 0, 5, 2, 4])
assert m.perm_key([int(x) for x in c]) == "[3, 1, 0, 5, 2, 4]"
print("keys: batch key round-trips to the iteration-09 cache format")

# --- 5. missing_cells + chunking + projection ------------------------
cells = m.missing_cells({}, reuse_32=False, drift_ok=False)
assert len(cells) == 720 * m.N_Q, len(cells)
cache = {(m.perm_key(p), q): 1 for p, q in cells[:100]}
assert len(m.missing_cells(cache, False, False)) == 720 * m.N_Q - 100
full = 720 * 200
est = m.project_usd(full)
assert 16.5 < est < 17.2, est
print(f"cells: {len(cells)} at N_Q={m.N_Q}; full run projects ${est:.2f}")

# --- 6. reuse-32 skips the published questions -----------------------
m.N_Q = 200
assert len(m.missing_cells({}, reuse_32=True, drift_ok=True)) == 720 * 168
assert len(m.missing_cells({}, reuse_32=True, drift_ok=False)) == 720 * 200
print("reuse-32: honoured only when the drift gate passes")
m.N_Q = 3

# --- 7. guard admits then refuses ------------------------------------
m.CAP_USD = 1.0
m.guard_admit(1000)
try:
    m.guard_admit(100_000)
    raise AssertionError("cap did not fire")
except m.Gate as e:
    assert "COST CAP" in str(e)
g = m.guard_load()
assert g["pending_usd"] > 0
m.guard_settle(m.project_usd(1000), tin=1000, tout=2000, calls=10)
g = m.guard_load()
assert abs(g["pending_usd"]) < 1e-9 and g["calls"] == 10
print(f"guard: cap fires, pending settles, reported ${g['reported_usd']:.6f}")

# --- 8. result parsing against a synthetic batch response ------------
class FakeDest:
    file_name = "files/xyz"
    inlined_responses = None


class FakeJob:
    dest = FakeDest()


class FakeFiles:
    def download(self, file):
        rows = [
            {"key": "012345#1", "response": {
                "candidates": [{"content": {"parts": [{"text": "Answer: 1"}]}}],
                "usageMetadata": {"promptTokenCount": 200,
                                  "candidatesTokenCount": 500}}},
            {"key": "543210#2", "response": {
                "candidates": [{"content": {"parts": [{"text": "Answer: 9"}]}}],
                "usageMetadata": {"promptTokenCount": 210,
                                  "candidatesTokenCount": 480}}},
            {"key": "111111#0", "error": {"code": 400, "message": "bad"}},
            {"key": "222222#0", "response": {"candidates": []}},
        ]
        return "\n".join(json.dumps(r) for r in rows).encode()


class FakeClient:
    files = FakeFiles()


out = list(m.read_results(FakeClient(), FakeJob()))
assert len(out) == 3, out                      # error line dropped
assert out[0] == ("012345#1", "Answer: 1", 200, 500)
assert out[2] == ("222222#0", "", 0, 0)        # empty candidates -> wrong
assert m.grade(out[0][1], pool[1]["gold"]) == 1
assert m.grade(out[1][1], pool[2]["gold"]) == 0
print("parsing: 3/4 lines ingested, error line dropped, empty -> incorrect")

print("\nALL OFFLINE CHECKS PASS")
