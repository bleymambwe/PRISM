# Iteration 27 — E1: the flagship landscape at 200 questions

**Status:** runner written and offline-tested; **not yet run, not yet pre-registered.**
**Budget:** US$16.81 projected · cap US$25 (approved ask: $20 + a $10 minimum prepay to reach the paid tier)
**Model:** `gemini-2.5-flash-lite`, temperature 0, `maxOutputTokens` 600 — identical to Experiment K

Re-enumerates all 720 orderings of the six Experiment-K modules on **200** GSM8K questions instead of 32.
Fitness granularity 3.1% → **0.5%**.

## Why this experiment, stated correctly

The registered justification in `publication/iclr-2027/02_EXPERIMENT_PROGRAM.md` was that the regime call
destabilises below 16 questions. **Tier 0 falsified that** (H33: 93.3% agreement at q=8, 88.3% at q=4). The
surviving reason is narrower and better evidenced: at 32 questions **60 of the 720 orderings are exactly
optimal**, uniform sampling finds one in ~11 draws, and "found the optimum" saturates at 100% by budget 50 —
so the metric cannot discriminate between methods. More questions break the ties.

E1 therefore buys **discriminating power**, not call stability. Do not restate the old justification in the
paper.

*Kill criterion, and it is real:* if the high-resolution landscape shows the 6.3% → 96.9% span was a
low-resolution artifact, **that is the paper** — report it. Do not tune around it.

## Files

| File | What it is |
|---|---|
| `e1_batch.py` | The runner. Six idempotent stages driven by repeated invocation |
| `test_e1_batch.py` | Offline checks — grading parity with Experiment K, JSONL schema, key round-trip, chunking, cost projection, result parsing. No API calls |
| `hypotheses.example.json` | Template. Copy to `hypotheses.json`, fill in, **commit**, then run |
| `data/gsm8k_test.jsonl` | Not committed. The GSM8K test split, one JSON object per line |
| `results/` | Answer cache, batch job ledger, spend guard, reports, landscape |

## Before the first submit

1. **Prepay US$10** on the Gemini API to reach the paid tier — the Batch API is a paid-tier feature.
2. `pip install google-genai`
3. Put the GSM8K test split at `data/gsm8k_test.jsonl` (e.g. `data/test.jsonl` from
   `github.com/openai/grade-school-math`). Stage 0 tells you this if it is missing.
4. **Write and commit `hypotheses.json`** — direction, decision threshold, reversal condition per hypothesis.
   The runner refuses to submit without it, and refuses if it is untracked by git: an uncommitted file has no
   precedence and cannot serve as pre-registration (D18/D25/D27).

## Running it

```bash
python test_e1_batch.py        # offline checks, no spend
python e1_batch.py --dry-run   # writes the JSONL chunks, submits nothing
python e1_batch.py             # advance every stage that can advance, exit
python e1_batch.py 600         # same, but keep polling for 600s
python e1_batch.py --status    # cells, jobs, spend
```

Batch jobs keep running while you are not. Nothing is lost by exiting — which is the point: this is the first
runner in the project that does not have to survive the machine's 3–8 minute background kill.

## The two gates, and why they exist

**SMOKE (20 cells).** Runs the same cells through batch *and* through the synchronous endpoint and requires
the grades to agree exactly. It validates the JSONL request schema and the result-parsing before 144,000
requests are committed, and writes the first raw result line to `results/smoke_raw_line.json` so the actual
response shape can be compared against the parser. If Google's batch response schema differs from what
`read_results()` expects, this is where you find out — for about half a cent.

**DRIFT (200 cells).** Re-asks a sample of Experiment K's published answers and reports cell-level agreement.
This is not bookkeeping: E1's whole claim is a comparison between the 32-question and 200-question
landscapes, and if the served model has moved since Experiment K, that comparison measures model drift rather
than resolution. The gate reports the number either way; `--reuse-32` (which reuses the 23,040 already-paid
cells and saves ~$2.70) is honoured **only** if agreement ≥ 98%.

The 200-question pool preserves Experiment K's 32 questions at indices 0–31, so the published landscape is a
strict subset of the new one whether or not the cache is reused.

## Cost guard

Batch bills after the fact, so the guard **projects** spend before submitting — measured profile
(205.6 in / 532.3 out tokens per call, `experiments/iteration-11/results/token_usage.csv`) × batch rates
($0.05 / $0.20 per M) — refuses to submit past the cap, then reconciles against the `usageMetadata` returned
with each response. State lives in `results/spend_guard.json`; token totals in the house
`token_usage.csv` format.

Chunks are 12,000 requests (~8.9M enqueued tokens), which keeps each job under the tier-1 enqueued-token
limit and gives partial ingest if one job fails. A failed or expired job leaves its cells missing, and the
next invocation resubmits exactly those.

## After it completes

1. Re-run the Tier 0 gauntlet and `density_gate.py` **against the new landscape** — free, and the actual
   point of E1 (`experiments/iteration-26-tier0-gauntlet/`).
2. Recompute every flagship statistic at the new resolution: ρ₁, FDC, regime call, optimum density,
   distinct fitness values, the position table.
3. Fold into the paper per `publication/iclr-2027/03_ENGINEER_GUIDE.md` §5.6.
