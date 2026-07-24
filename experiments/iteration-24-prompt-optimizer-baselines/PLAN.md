# Iteration 24 — Experiment T: Prompt-Optimizer Baselines

**Status:** planned / pre-registered. Approved by Bley 2026-07-24 (D27).
**Prerequisite satisfied:** this is the D21-required "prompt-optimizer baselines"
condition for Paper B.
**Dedicated cost cap:** $5.00 (own two-meter guard, independent of the It-19 $9 cap
and the It-23 $10 cap). Realistic expected spend ≈ $1.75.

---

## 1. Why this experiment exists (the reviewer objection it answers)

PRISM's headline is that **reordering fixed prompt modules moves accuracy a lot**
(6.3%→96.9% in Experiment K; a 43-point spread in Experiment S). The first question a
reviewer asks is:

> "So what? A prompt optimizer would just rewrite the *wording* of those modules and get
> the same or better gains. Why does *order* matter, as opposed to just writing better
> instructions?"

Decision D21 made answering this a **required** condition before Paper B can be submitted,
not an optional extra. The objection actually contains two distinct sub-questions, so this
experiment has two tracks and two hypotheses:

1. **Is ordering value *complementary* to content optimization?** (Track A / H25) — after a
   real optimizer has improved the *wording*, does *order* still matter, or does good
   wording absorb the ordering effect?
2. **Is PRISM's *specialized search* more efficient than a *generic* LLM optimizer at
   finding a good ordering?** (Track B / H26) — restricted to the identical ordering search
   space, does PRISM's pre-flight-guided/portfolio search reach a good ordering in fewer
   evaluations than an off-the-shelf LLM-as-optimizer?

These are complementary framings: content-vs-order (A) and search-efficiency (B). Together
they let Paper B say "ordering is orthogonal, additive value — and our search for it is
competitive" rather than leaving the objection open.

---

## 2. The two hypotheses (pre-registered — committed to git before any evaluation)

### H25 — Complementarity of ordering and content optimization

After an OPRO-style optimizer rewrites the wording of all 8 modules (holding their **order
fixed** throughout optimization), reordering those now-optimized modules **still produces a
materially non-zero accuracy spread**.

- **Quantitative prediction:** the order-driven standard deviation on the optimized wording
  stays at **≥ 40% of** the original-wording std, and in absolute terms **≥ 0.03**.
  (Experiment S measured original-wording random-ordering std = 0.078; predict optimized-wording
  std lands roughly 0.03–0.05.)
- **Reasoning:** Experiment S's ordering effects looked *structural* (e.g., orderings that
  place ANSWER before COMPUTE collapse). Better word-choice should partly compensate but
  cannot remove a structural dependency like "you can't state the answer before you've been
  told to compute it."
- **Falsified if:** optimized-wording std **< 0.02** (statistically indistinguishable from
  grading noise at n=40 questions). That would be a genuine finding that content optimization
  *absorbs* the ordering effect — reported honestly, and it would weaken (not kill) Paper B's
  emphasis on order.

### H26 — PRISM search efficiency vs a generic LLM optimizer

On the identical ordering search space (8! permutations of the 8 fixed original-wording
modules), scored on the identical fixed question subset, PRISM's search reaches a
higher-accuracy ordering **at equal or smaller evaluation budget** than an OPRO-style LLM
optimizer proposing orderings freely.

- **Quantitative prediction:** at a budget of 25 fresh evaluations, PRISM's best-found
  accuracy ≥ OPRO's best-found accuracy (point estimate), across 5 seeds.
- **Honest uncertainty flag:** this is the *genuinely uncertain* hypothesis. Published
  OPRO/APE results show LLM-as-optimizer is surprisingly strong. If it matches or beats
  PRISM here, that is a real and reportable result — it would shift Paper B's weight toward
  the *transfer* results (which are more clearly PRISM-specific) rather than search efficiency.
- **Falsified if:** OPRO's best-found accuracy exceeds PRISM's by a margin whose 5-seed CI
  excludes zero.

---

## 3. Models (who does what)

| Role | Model | Notes |
|---|---|---|
| **Target model** — the one being *scored*; whose accuracy we are trying to move | `meta-llama/llama-3.1-8b-instruct` (OpenRouter, `provider: {sort: throughput}`, temp 0, max_tokens 4000) | Reused verbatim from Experiment S — already validated in the 20–60% band (27% pilot), same pool, same grader. No repeat of the 5-attempt model search. |
| **Optimizer model** — *proposes* candidates; never itself scored | `gemini-2.5-flash-lite` (Google API, `GOOGLE_API_KEY` in GCP Secret Manager) | Cheap, already integrated. Deliberately a *different* model from the target, so the optimizer can't "cheat" by sharing the target's weights/quirks. |
| **PRISM searcher** — Track B competitor | algorithmic (the portfolio EA in `prism-research/core/prism.py`) | No LLM. Pop 20, tournament k=3, portfolio mutation, elitism 1. |

**Baselines explicitly out of scope, and why:**
- **GREATER** — needs white-box gradients into the target model's internals; impossible against
  an API-served model with no exposed weights. Cite its *published* GSM8K/BBH numbers as
  context, do not run.
- **MIPROv2 / GEPA** — legitimate stronger baselines (pip-installable, API-compatible) but
  heavier dependencies; after this session's `math-verify` failure (installed clean, returned
  wrong answers silently), a second unverified dependency under a real result is a risk.
  **Stretch goal** after OPRO works, not a blocker.
- **APE** — essentially OPRO's single-shot precursor (generate-then-select vs iterative
  refinement); OPRO covers its spirit. Optional literal add-on.
- **PromptBridge** — not a baseline for *this* experiment. It transfers prompt *wording*
  across models, which maps onto the Q/Q2 cross-family transfer results, not content-vs-order.
  Belongs in Paper B related-work as a citation ("they transfer wording; we transfer structure").

**Why OPRO is hand-implemented rather than pip-installed:** OPRO's mechanism (keep a
best-first trajectory of tried candidates, show it to an LLM, ask for a better one) is small
enough to write and audit directly. Given the `math-verify` experience this session, a
self-contained, inspectable implementation is safer than an opaque dependency sitting under a
published result. It is genuinely the same core loop DSPy-MIPROv2 and GEPA build on.

---

## 4. Reused, unchanged, from Experiment S (Iteration 23)

- The **8 modules** (indices 0–7): RESTATE, IDENTIFY, ESTIMATE, PLAN, SIMPLIFY, COMPUTE,
  CHECK, ANSWER — with their original wordings.
- The **question pool**: `experiments/iteration-23-experiment-s/results/math500_pool.json`
  (100 MATH-500 problems, levels 3–5, simple-canonical-answer filter, seed 23).
- The **frozen grader** (`extract_boxed` / `normalize` / `to_number` / `ANSWER_TOKEN`,
  18/18 unit tests) — copied verbatim into this experiment so it is self-contained and does
  not import Experiment S's module-level cache/model-lock side effects.
- The **prompt template** (`build_prompt`), extended to accept a *wording list* so Track A
  can substitute optimized wordings.
- The **two-meter cost-guard** pattern (per-call API-reported cost + OpenRouter key-usage
  endpoint), with its own `spend_guard.json` and $5 cap.

### Train / test split (new for this experiment)

To prevent the wording optimizer from overfitting to the exact questions the ordering-spread
is later measured on:

- **Train set** = pool questions **0–59** (60 questions) — used only to *score candidates
  during OPRO optimization*.
- **Held-out set** = pool questions **60–99** (40 questions) — used only for the *final
  ordering sweeps* (H25) and Track-B search fitness (H26 uses a 30-question subset of these,
  indices 60–89).

### Cache design (avoids corrupting Experiment S data)

Experiment S's cache is keyed `(perm, qidx)` and assumes **original wording**. Track A uses
**different wording**, so sharing that cache would silently mix two prompts under one key.
Iteration 24 therefore uses its **own fresh cache**, keyed
**`(wording_id, perm_json, qidx)`** with `wording_id ∈ {"orig", "opt"}`. This makes the
experiment self-contained and correctly distinguishes original from optimized wording.
Original-wording rows (`wording_id="orig"`) are internally consistent and may be shared
between the Track-A original-wording sweep and Track-B (both use original wording), but are
**never** shared with Experiment S's differently-scoped cache.

---

## 5. How the optimization works — OPRO, step by step

OPRO (Yang et al., 2023, "Large Language Models as Optimizers") keeps a running
**trajectory** of (candidate, score) pairs and repeatedly asks an LLM to propose a better
candidate given the best ones so far.

**The loop (identical control flow for both tracks; only the "candidate" differs):**

1. Initialise the trajectory with a few seed candidates and their measured scores.
2. Build a **meta-prompt**: task description + the top-K scoring candidates so far (best
   first) as in-context examples + an instruction to "propose one new candidate you expect
   to score higher."
3. Send the meta-prompt to the **optimizer model** (Flash-Lite) → one new candidate.
4. **Score** the new candidate on a batch of questions using the **target model**
   (Llama-3.1-8B). *This is the only place real task cost is incurred.*
5. Append `(candidate, score)` to the trajectory.
6. Repeat for a fixed budget of rounds. Return the best-scoring candidate.

### Track A candidate = the 8-module *wording block* (order frozen)

Order is frozen at the **canonical order 0–7** (RESTATE…ANSWER — itself a sensible sequence:
ANSWER last, COMPUTE before ANSWER) throughout optimization. Each round the optimizer sees
the best full wording blocks tried and proposes a new full 8-module wording block.

**Meta-prompt skeleton (Track A):**
```
You are improving the wording of instructions given to a small math-solving
model. The model always performs these 8 labelled steps IN THIS FIXED ORDER:
RESTATE, IDENTIFY, ESTIMATE, PLAN, SIMPLIFY, COMPUTE, CHECK, ANSWER.

Here are wording sets tried so far and the accuracy each achieved on a fixed
set of hard math problems (best first):

[rank 1, acc 0.42]
  RESTATE: <wording> | IDENTIFY: <wording> | ... | ANSWER: <wording>
[rank 2, acc 0.40]
  ...

Propose ONE new wording set (all 8 steps, same labels, same intent, changed
phrasing only) that you expect to score higher. Output strictly as:
RESTATE: ...
IDENTIFY: ...
...
ANSWER: ...
```
- **Budget:** 24 rounds. Each round scores the full 8-module prompt on the 60-question train
  set → 24 × 60 = **1,440 target calls** + 24 optimizer calls.
- **Output:** the best-scoring wording block (`wording_id="opt"`).

**Illustrative example (invented, not a real result):** the original ANSWER module is
`"ANSWER: State the final answer on its own line as 'Answer: <number>'."`; OPRO might evolve
it to `"ANSWER: Compare your COMPUTE result to your ESTIMATE; if they disagree, recheck; then
output only the final number on its own line, prefixed exactly 'Answer: '."`

### Track B candidate = an *ordering* (wording frozen at original)

Each round the optimizer sees the best orderings tried and proposes a new full permutation of
the 8 fixed original-wording modules.

**Meta-prompt skeleton (Track B):**
```
You are choosing the ORDER in which a small math model performs 8 fixed
reasoning steps. The steps are: RESTATE, IDENTIFY, ESTIMATE, PLAN, SIMPLIFY,
COMPUTE, CHECK, ANSWER. Their wording is fixed; only the order may change.

Orderings tried so far and their accuracy on hard math problems (best first):
[acc 0.41] COMPUTE, IDENTIFY, PLAN, RESTATE, ESTIMATE, SIMPLIFY, CHECK, ANSWER
[acc 0.33] ...

Propose ONE new ordering (a permutation of all 8 steps, each exactly once)
that you expect to score higher. Output the 8 step names in order, comma-sep.
```
- Runs **head-to-head against the PRISM portfolio searcher**, both proposing orderings
  freely in 8! space, both scored on the **same fixed 30-question subset** (held-out indices
  60–89), both starting from the **same k=3 random seed orderings**, both with a budget of
  **25 fresh evaluations**, over **5 seeds**.
- **Cost:** 2 methods × 5 seeds × 25 evals × 30 questions = **7,500 target calls** + ~125
  optimizer calls. (Cache dedupes any repeated proposals.)
- **Metric:** best-found 30-Q accuracy vs evaluation budget (curve), and mean evals-to-reach
  a fixed threshold.

---

## 6. Execution stages (resumable, chunked, dashboard-tracked)

Same budgeted-runner discipline as Experiment S (`python run.py [budget-seconds]`, append-per-cell
cache, resume by key, wall-clock budget, dashboard refresh on each save, hard cost cap).

| Stage | What | Cost |
|---|---|---|
| 0 | Copy grader + pool; commit PLAN.md + hypotheses.json (pre-registration) | $0 |
| A1 | OPRO wording optimization on train set (24 rounds) | ≈ $0.20 |
| A2 | Ordering sweep on **original** wording, 50 random orderings × 40 held-out Q | ≈ $0.30 |
| A3 | Ordering sweep on **optimized** wording, same 50 orderings × 40 held-out Q | ≈ $0.30 |
| B | PRISM vs OPRO ordering search, 5 seeds × 25 evals × 30 Q, both methods | ≈ $1.00 |
| C | Analysis (H25/H26 verdicts, 40-seed / 5-seed bootstrap CIs) — free | $0 |
| D | Archive (EXPERIMENT_LOG, iteration write-up, ledger, dashboard, memory, commit+push) | $0 |

**Total ≈ $1.8 target spend; $5 cap.** Pre-registration = the git commit of this PLAN.md and
`hypotheses.json` *before* stage A1 runs; its timestamp is the proof the forecasts preceded
the results.

---

## 7. Measurements & analysis

| Measurement | Serves |
|---|---|
| OPRO wording trajectory (train accuracy per round) + best wording block | audit of the optimizer; H25 setup |
| Original-wording ordering-spread std (50 orderings, 40 held-out Q) | H25 baseline |
| Optimized-wording ordering-spread std (same 50 orderings, 40 held-out Q) | H25 test — ratio and absolute value |
| Paired per-ordering accuracy delta (opt − orig) + mean, 10k bootstrap CI | did optimization raise the *level* (sanity: OPRO worked at all)? |
| Best-found accuracy vs budget, PRISM vs OPRO, 5 seeds, 30-Q | H26 (the search-efficiency curve) |
| Mean evals-to-threshold, PRISM vs OPRO, with CI | H26 headline number |
| Cost meters (per-call reported + key-usage delta) | budget accountability |

### Interpretation matrix (decided in advance)

- **H25 holds + H26 holds:** best case — "ordering is orthogonal, additive value that
  content optimization does not absorb, and our search for it beats a generic optimizer."
  Paper B closes the reviewer objection cleanly.
- **H25 holds + H26 fails:** ordering still matters after content optimization (the important
  claim), but a generic LLM optimizer finds good orderings as fast as PRISM — Paper B keeps
  the complementarity claim and leans on *transfer* for PRISM-specificity, dropping/softening
  the search-efficiency claim.
- **H25 fails:** content optimization absorbs the ordering effect — the most consequential
  branch. Honestly reported; Paper B would reframe order as "one lever among several, most
  valuable when content is fixed/constrained" and lean hard on the transfer + pre-flight
  results, which are unaffected.
- **OPRO underperforms even random on H26:** likely means Flash-Lite reasons poorly over
  permutations; report as a limitation of the baseline rather than a PRISM win, and note
  MIPROv2/GEPA as the fairer (stretch) comparison.

Every branch is publishable; per the project's standing rule, a cleanly falsified hypothesis
is reported with the same rigor as a confirmed one.
