# Iteration 25 — Experiment U: Agentic Tool-Ordering Landscape (BFCL)

**Status:** pre-registered / **UNAPPROVED — no spend authorized.** This document and
`hypotheses.json` are committed to git *before any evaluation* to establish the pre-registration
timestamp. The runner is **not** built or run until Bley explicitly approves the cost.
**Proposed dedicated cost cap (on approval):** $15.00 (own two-meter guard, independent of all
prior caps). Realistic expected spend ≈ $6–10. **Nothing runs until approved.**

**2026-08-22 addendum — reuse `inspect_evals.bfcl` instead of hand-rolling BFCL:** while
preparing the `evals/instruction_order` submission to the Inspect Evals register, found that
`UKGovernmentBEIS/inspect_evals` — the same registry — already ships a working BFCL
implementation at `src/inspect_evals/bfcl/`: dataset loading (`data.py`), prompt construction
(`prompts.py`), an AST-match scorer (`score/scorer.py`, `score/multi_turn_scorer.py`), and both
single- and multi-turn solvers (`solve/`). §3 and §6 below currently assume building menu
selection, prompt construction, and AST scoring from scratch. On approval, the runner should
instead depend on `inspect_evals` (or vendor just its `bfcl/score/` and `bfcl/utils/` modules)
and insert the ordering permutation as a thin layer in front of their existing dataset/prompt
loader — the same pattern `evals/instruction_order/orderings.py` already uses to reuse PRISM's
own distance code rather than reimplementing it. This should lower both the implementation risk
and the realistic-spend estimate above (fewer new failure points in the scoring path); the stage
cost table in §6 has not yet been re-costed against this — do that before re-opening the approval
decision.

---

## 1. Why this experiment exists

### 1a. The research gap it fills (breadth for Paper B → main track)

Every PRISM instruction-ordering landscape so far (K, M, S) permutes **reasoning modules** in a
**static, single-turn** prompt. The publication guide (`docs/PUBLICATION_GUIDE_2026-07-25.md`)
identified the one blocker for a top-tier *main-track* Paper B: **task-family breadth** — the
"you only showed this on one kind of task" objection. Experiment U extends the ordering thesis to
**agentic tool use**, which is (i) a genuinely different regime (multi-tool selection, function
calling, stateful potential) and (ii) the highest-visibility area in LLM research in 2026. It
converts PRISM's claim from "order matters in static reasoning prompts" to "order matters — and is
*predictable* — across static reasoning **and** agentic tool orchestration."

### 1b. The direct open question in the literature (a citable hook)

The 2026 pre-print **TOOL-SHADOW v1** ("Auditing Position-Induced Tool-Choice Bias in LLM Agent
Harnesses", clawRxiv 2604.01646) argues that the flat, ordered tool list in an agent's system
prompt is **not neutral** — position (primacy/recency, attention-sink, lost-in-the-middle) induces
an implicit prior over which tool is called — and states plainly that the community has **"no
public, pre-registered audit of whether the ordering itself alters call frequency"** and no pooled
effect size. It offers only a *pre-validation framework*, not a measurement. **Experiment U is
exactly that missing measurement:** an enumerated/sampled tool-ordering landscape with a fitness
signal and a pre-registered pre-flight forecast. We can cite TOOL-SHADOW as the framing and supply
the empirical result it says is absent. (Related supporting evidence found in the same search:
Liu et al. 2023 lost-in-the-middle, Xiao et al. 2024 attention sinks, Lu et al. 2022 ICL
label-ordering — all consistent with a positional tool-choice effect.)

---

## 2. The object being optimized (a pure permutation — deliberately)

The candidate is an **ordering of N tool/function descriptions** in the agent's tool-schema list /
system prompt, for a **fixed tool menu**, evaluated across a **fixed set of BFCL tasks**. Only the
order changes; the N descriptions, their wording, and the task set are held constant — the exact
K/M/S design, with *tool descriptions* substituted for *reasoning modules* and *tool-call
correctness* substituted for *answer accuracy*.

**Explicitly a permutation, not a DAG.** A second strand of the literature (tianpan.co, "Tool Call
Ordering Is a Partial Order, Not a Set"; the LLM-Compiler `DEPENDS_ON` pattern) shows that the
*execution* order of tool calls often has hidden dependency structure — a partial order / DAG, not
a free permutation. That is a **topology** optimization problem and is **out of scope** for
Experiment U (it needs graph-edit distance for FDC and a topology mutation operator — a genuine
extension of PRISM beyond permutations, flagged as future work in §8). Experiment U optimizes the
**presentation order of tool descriptions**, which is a clean permutation and the exact quantity
TOOL-SHADOW is about.

---

## 3. Fitness — why BFCL, and which parts of it

**Benchmark: Berkeley Function-Calling Leaderboard (BFCL)** — the de-facto standard for tool use
(Patil et al., PMLR 2025), deterministic **Abstract Syntax Tree (AST)** matching of the emitted
call (function name + argument structure) against ground truth. AST match is fast, deterministic,
and platform-independent — it preserves PRISM's frozen-grader discipline and gives a fitness signal
with real resolution.

**Use only the deterministic AST-checkable categories** — `simple`, `multiple`, `parallel`,
`parallel_multiple` (and their `live_*` variants) — for the **primary** landscape. **Do not** use
the stateful multi-turn or LLM-judge categories for the primary sweep. Reason (from the search):
the validity audit *"Benchmarking the Benchmarks"* (arXiv 2607.02577) found an **18.5%
evaluator–human misalignment** across BFCL v4 / τ²-bench / LiveMCPBench / MCP-Atlas, and up to a
**18.9-point run-to-run spread** on stateful/LLM-judge benchmarks — large enough to swamp an
ordering effect. Deterministic AST categories keep the noise floor low enough to measure ordering
(the D16 resolution lesson applies directly).

The `multiple` / `parallel_multiple` categories are the natural fit: the model is shown a **set** of
candidate functions and must pick and call the right one(s) — so the **order of the candidate
descriptions is the treatment**, and the correct-vs-distractor selection is the readout.

### Constructing the fixed N-tool menu (holds the toolset constant across tasks)

BFCL items each ship their own function list of varying length. To make ordering the *only*
variable, we build a **fixed menu of N tools** (target **N = 7** → 5,040 orderings, enumerable like
K; or **N = 8** → 40,320, sampled like M) by selecting N BFCL functions and collecting tasks whose
ground-truth call targets one of the menu functions. **Every task is shown all N tools**, in the
permuted order under test. Publish the menu + task-selection code so the mapping is auditable
(the same discipline as the NAS-Bench permutation-slice mapping).

---

## 4. Hypotheses (pre-registered — committed before any evaluation)

### H27 — Agentic ordering sensitivity
For a fixed N-tool menu on the AST-checkable BFCL subset, permuting the tool-description order
produces a **materially non-zero** tool-call-accuracy spread.
- **Quantitative prediction:** random-ordering accuracy **std ≥ 0.05** (predict 0.05–0.15, likely
  larger than reasoning-module landscapes because a mis-ranked distractor flips a discrete choice).
- **Falsified if:** std **< 0.02** (indistinguishable from AST-grading noise at the chosen task
  count) — a real, reportable finding that tool selection is order-robust.

### H28 — Pre-flight forecast (7th validated live application)
The ρ1 (swap / insert / inversion move-autocorrelation) + FDC pre-flight, computed on the
tool-ordering landscape and **registered to git before the main sweep**, correctly forecasts whether
guided/search beats random on this landscape.
- **Adds the 7th entry** to the prediction ledger (after J, K, M, Q2-directional, S).
- **Falsified if:** the registered forecast (search-helps vs random-competitive) is contradicted by
  the measured search-vs-random outcome.

### H29 — Position-effect transfer across models
The position effects (which slot the correct tool occupies — primacy vs recency vs middle-suppression,
i.e. the "tool-shadow" shape) **transfer across ≥ 2 target model families**.
- **Quantitative prediction:** cross-model position-rank correlation **r > 0.4** (mirrors Q2's
  cross-family transfer test, r = 0.582 on Llama).
- **Falsified if:** the 2-model position-rank CI spans 0 (structure is model-specific, as Gemma was
  in Experiment Q before Q2 corrected it — either outcome reportable).

### H30 — Multi-turn persistence (STRETCH, gated, may be dropped)
If a stateful/multi-turn BFCL subset is run, ordering effects persist (std ≥ 40% of the single-turn
std). **Gated** on Track-A resolution AND remaining budget; carries the grader-noise caveat above;
reported as exploratory, not confirmatory.

---

## 5. Models

| Role | Model (proposed) | Notes |
|---|---|---|
| Target #1 (scored) | `meta-llama/llama-3.1-8b-instruct` (OpenRouter, native tool-calling, temp 0) | Reused from S/T; **must pass a D16 pilot in [0.2, 0.8] on the chosen BFCL subset** — if at ceiling/floor, swap per the S model-selection protocol. |
| Target #2 (H29 transfer) | a second tool-calling family (e.g. a Qwen or Ministral FC model on OpenRouter) | Only the subset needed for the position-transfer test; keeps cost down. |
| PRISM searcher (H28) | portfolio EA (`prism-research/core/prism.py`) | No LLM; pop 20, tournament k=3, portfolio mutation, elitism 1. |
| OPRO ordering proposer (H28 baseline) | `gemini-2.5-flash-lite` | Reuse Experiment T's hand-implemented OPRO loop verbatim — proposes tool orderings. |

**Model-selection gate (D16):** a mandatory pilot precedes any spend; if Llama-3.1-8B is saturated
on the AST subset (frontier models score high on `simple`/`multiple`), pick a weaker/smaller
tool-calling model or a harder subset (`parallel_multiple`, more distractors) to land in band.

---

## 6. Execution stages (on approval; resumable, chunked, dashboard-tracked)

| Stage | What | Est. cost |
|---|---|---|
| 0 | Build fixed N-tool menu + task set from BFCL; commit PLAN.md + hypotheses.json (**done now, pre-registration**) | $0 |
| P | **Pilot / D16 resolution gate** — is the target in [0.2, 0.8] on the AST subset? | ≈ $0.30 |
| 1 | **Pre-flight** — ρ1 (3 operators) + FDC on the tool-ordering landscape; **register forecast to git** | ≈ $0.50 |
| 2 | **Main landscape** — sweep 120–150 orderings × 40–60 tasks (enumerate if N=7 and budget allows) | ≈ $3–5 |
| 3 | **Search phase** — PRISM vs OPRO vs random, 5 seeds × budget, on the same fitness (H28) | ≈ $1–2 |
| 4 | **Transfer leg** — second model on the position-effect subset (H29) | ≈ $1–2 |
| 5 | **Analysis** — H27/H28/H29 verdicts, bootstrap CIs; H30 only if gated-in | $0 |
| 6 | Archive (EXPERIMENT_LOG, iteration write-up, ledger, dashboard, memory, commit+push) | $0 |

Budgeted-runner discipline throughout (`python run.py [budget-seconds]`, append-per-cell cache,
resume by key, wall-clock budget, two-meter cost guard, hard cap, dashboard refresh on save) — the
pattern proven across S and T on this machine.

---

## 7. Interpretation matrix (decided in advance)

- **H27 holds + H28 holds:** best case — "tool ordering swings agent accuracy, and the pre-flight
  predicts when search over orderings helps." Supplies the empirical result TOOL-SHADOW says is
  missing; the strongest possible breadth result for Paper B.
- **H27 holds + H29 holds:** the position-effect *structure* transfers across model families →
  reusable "put the relevant tool at slot X" guidance, parallel to the ANSWER-late rule from K.
- **H27 holds + H28 fails:** ordering matters but the landscape is locally near-random (FDC≈0, as in
  the LLM reasoning landscapes) so search ≈ random — fully consistent with the pre-flight thesis;
  report as "avoid catastrophic orderings; search is not the differentiator here."
- **H27 fails (std < 0.02):** tool selection is order-robust on this subset — a clean, honest
  negative that *bounds* the tool-shadow effect (itself publishable, and directly answers
  TOOL-SHADOW's open question in the negative). Per the standing rule, reported with equal rigor.

---

## 8. Explicitly out of scope (with reasons)

- **DAG / dependency-order (execution-order) optimization** — a topology problem, not a permutation;
  needs graph-edit-distance FDC + a topology operator. A real PRISM *extension*, not this
  experiment. Flagged as the natural follow-on ("PRISM-DAG").
- **Stateful multi-turn / LLM-judge BFCL categories as the primary landscape** — grader noise
  (18.5% misalignment; up to 18.9-pt run-to-run spread per arXiv 2607.02577) would swamp the effect;
  admitted only as the gated H30 stretch.
- **τ-bench, τ²-bench, AppWorld, ToolACE, MCP-Atlas** — higher-fidelity agentic benchmarks but
  pricier and noisier (multi-turn, user simulators, LLM judges). Each is a *separate, higher-budget*
  decision, catalogued in `docs/BENCHMARK_DISCOVERY_2026-07-25.md`; not bundled into this cap.
- **Any spend at all** — until Bley approves. This file is the pre-registration only.
