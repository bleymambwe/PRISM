# PRISM Experiment Log

## 2026-07-12 (Iteration 17, Experiment Q): Cross-Model SLM Transfer — EXTREMES TRANSFER, STRUCTURE DOES NOT

- Question: do instruction-ordering effects measured on Gemini 2.5
  Flash-Lite transfer to a much smaller model (Gemma 26B MoE, 4B active —
  SLM class)? Doubles as the audit's second-model replication and the
  live D20 confirmation/reversal test.
- Design: same 6 modules, same 32 GSM8K questions as Experiment K;
  120 orderings (100 random seed-17 + source top-15 + bottom-5) x 32
  questions = 3,840 cells, cached and resumable; temperature 0.
- Spend: 4,101 calls; worst-case-if-billed $1.37 (Gemma tier
  free-of-charge; token-metered). Run in 16 foreground chunks 2026-07-11/12.
- Results (bootstrap CIs, 10k resamples):
  - Q1 fitness correlation (100 random orderings): Spearman 0.158
    [-0.018, 0.338] — WEAK; CI spans zero. Fine-grained landscape rank
    does not transfer across models.
  - Q2 position-effect table correlation: r = 0.064 — near zero. The
    flash-lite ANSWER-late gradient (0.44 -> 0.87) is absent on Gemma
    (flat/noisy row). Contrasts sharply with same-model cross-size
    transfer (Exp. O: 0.665).
  - Q3 extremes: source TOP-15 -> Gemma 0.565 [0.460, 0.665] vs
    random-100 0.442 [0.395, 0.490] vs source BOTTOM-5 0.150
    [0.088, 0.200]. Top-minus-random diff CI [+0.008, +0.234] (excludes
    zero, marginal); random-minus-bottom [+0.221, +0.372] (decisive).
    Top-15 individually heterogeneous on Gemma: 0.19-0.88.
  - Q4 order sensitivity: Gemma std 0.247, range [0.06, 0.91] vs
    flash-lite std 0.226 — the SLM is at least as order-sensitive.
  - Q5 warm-start (top-10% of the random pool by source score): 0.459
    [0.334, 0.603] vs random 0.442 — NO usable lift.
- Interpretation: cross-model transfer is asymmetric — ordering
  PATHOLOGY transfers robustly (avoid source-bottom orderings: ~29-pt
  penalty), ordering OPTIMALITY transfers weakly (+12 pts, marginal),
  and positional STRUCTURE does not transfer at all at this scale.
  Not a decisive D20 failure (reversal clause NOT triggered), but the
  transfer claim must be narrowed from "landscapes transfer" to
  "extreme orderings transfer; structure is model-specific." The
  causal-masking mechanism story is weakened for cross-model claims
  and needs the cross-family legs (Qwen/Llama) to arbitrate.
- Caveat: Gemma mean accuracy 0.442 on this set — near the middle of
  the scale, so noise per (ordering, question) cell is maximal; and the
  low mean may compress position effects. A harder-question re-test on
  a stronger SLM (benchmark #2 design) is the follow-up.
- Outputs: experiments/iteration-17/results/{gemma_answer_cache.csv,
  token_usage.csv, slm_transfer_report.txt}. Code:
  experiments/iteration-17/slm_transfer.py.

## 2026-07-08 (Iteration 18, Experiment R): Transfer-Guided Evaluation - MODEST SUPPORT

- Question: can n=6 LLM instruction-order position effects guide a
  low-budget n=8 evaluation policy, not just correlate with n=8 fitness?
- Free/cached: used Iteration 9 full n=6 LLM landscape and Iteration 11 n=8
  answer cache; no new API calls.
- Result: source-score vs n=8 fitness Spearman rho = 0.656, Pearson r =
  0.685 over 222 complete unbiased n=8 orderings. Guided evaluation reaches a
  perfect n=8 ordering by budget 5; random-without-replacement has 0.248
  probability of a perfect hit at budget 5. Top 10 percent by transferred score
  has mean target accuracy 0.900 vs random-pool mean 0.725.
- Interpretation: strengthens Iteration 16 from "transfer correlation" to a
  usable warm-start/evaluation policy, but not a standalone top-tier result
  because perfect n=8 orderings are not sparse.
- Outputs: experiments/iteration-18/results/transfer_guided_selection.txt.
  Write-up: iterations/2026-07-08-iteration-18-research-loop-selection.md.

## 2026-07-08 (Iteration 16, Experiments O+P): Transfer + SciML — CROSS-SIZE TRANSFER DISCOVERED

- O1 cross-task (XOR-v4 vs Parity-v4, 120 shared orderings): ZERO
  transfer (r = -0.004; top-10% overlap = chance). Good orderings are
  task-specific on the neural benchmarks.
- O2/O3 cross-size (LLM n=6 -> n=8, 222 unbiased random orderings):
  STRONG transfer — n=6 position effects predict n=8 fitness at
  Spearman 0.665 [0.582, 0.725]; selecting top-10% by the n=6-derived
  score gives mean accuracy 0.900 [0.873, 0.925] vs random 0.725 —
  a free +17.5-point warm start with zero n=8 evaluations.
- P (SciML, first of its kind): SINDy preprocessing-pipeline ordering,
  720 orderings enumerated (numpy-only, deterministic) — recovery
  error swings 0.1% <-> 23.2%; DIFF-position effect non-monotone and
  high-variance last; best = CLIP->SUBSAMPLE->SMOOTH->TRIM->MEDIAN->DIFF.
  Pre-flight FDC +0.109 -> borderline; 40 seeds: random 40/40 more
  reliable than PRISM 38/40 (directionally correct call). D19: FDC
  borderline band (+0.05..+0.3) handled as near-zero.
- Outputs: experiments/iteration-16/. Write-up:
  iterations/2026-07-08-iteration-16-transfer-and-sciml.md.

## 2026-07-08 (Iteration 15): Aging-Mode Theory Restatement — GAP 2 CLOSED

- Key fact: implemented scramble reaches ANY ordering from ANY parent in
  one move with prob >= 1/(2n(n-1)n!) (full-segment + uniform shuffle);
  portfolio inherits it. Numerically verified (2M draws: 2.21e-4 vs
  bound 2.08e-4; full-segment shuffle uniform over all 24 targets, n=4).
- Paper Appendix B (new): B.1 one-step reachability; B.2 aging = a.s.
  RECORD convergence with explicit geometric bound (E[T] <= 2n(n-1)n!/m;
  parity n=7 bound 30,240 vs observed 222.5) + proof that population
  absorption FAILS; B.3 hybrid preserves best-ever by construction =>
  original theorem verbatim (the theory-preserving robustness option);
  B.4 unconditional worst-case bound for elitist portfolio.
- Outputs: experiments/iteration-15/results/theory_check.txt. Write-up:
  iterations/2026-07-08-iteration-15-theory-restatement.md.

## 2026-07-08 (Iteration 14): Statistics Pass + Claims Audit — ONE HEADLINE CORRECTED

- 40-seed Wilson/bootstrap CIs for all headline comparisons (4
  landscapes x 6 methods) + pre-flight sampling-error study (200
  resampled pre-flights): operator pick 0.94-0.99 correct on typed
  landscapes, deceptive call 1.00 stable, parity regime call 0.78.
- CORRECTION: the It-9 "PRISM 3x faster than random" LLM claim did not
  survive 40 seeds (9.9 [7,13] vs 10.8 [8,14]); downgraded everywhere.
  Kendall surrogate result strengthened (disjoint CIs). Full audit:
  docs/ICML_READINESS_AUDIT.md.
- Outputs: experiments/iteration-14/results/. Write-up:
  iterations/2026-07-08-iteration-14-rigor-and-communication.md.

Last updated: 2026-07-08 (Iteration 18)

## 2026-07-08 (Iteration 12, Experiment N): Hybrid + Precedence Surrogate — FIRST METHOD TO BEAT ELITIST PRISM

- Free (cached/closed-form). Six methods x four landscapes incl.
  kendall n=7 (a SINGLE optimum in 5040).
- H18 STRONGLY CONFIRMED: the precedence-pair surrogate (binary
  "i before j" ridge) finds kendall's single needle in 13.5 mean evals
  vs elitist 55.7 and random 0/15 — 4x the matched operator; also
  best/tied-best on XOR n=6 (13.5) and parity n=7 (33/40). Surrogate
  power = encoding-landscape match, parallel to operator matching.
- H17 partially confirmed: elitist+restart hybrid matches elitist on
  structured (17.4 vs 18.5) and reaches aging-level robustness on
  parity (29/40), but restarts waste budget on kendall (89.5) —
  a no-pre-flight default, not a replacement for guided choice.
- D17: precedence surrogate is the method of record when the
  pre-flight shows precedence structure.
- Outputs: experiments/iteration-12/. Write-up:
  iterations/2026-07-08-iteration-12-hybrid-surrogate.md.

## 2026-07-08 (Iteration 11, Experiment M): Harder LLM Instance — PRE-FLIGHT VALIDATED AT SCALE

- n=8 modules (40,320 orderings, first beyond-enumeration application),
  20 GSM8K questions, Gemini Flash-Lite; hard budget cap in code;
  actual spend $5.56 (23,805 calls, token-metered).
- Gate: ordering swings accuracy 0.10-1.00 (std 0.240) — larger than n=6.
- Sampled pre-flight (222 orderings): rho1 -> insert 0.75 (precedence
  prediction holds at n=8); approx-FDC -0.095 -> "random likely
  competitive". Search stage (4 seeds each): PRISM = random = 1.0000 at
  every budget — the pre-flight forecast exactly right.
- Lesson (D16): optimum density is partly measurement resolution
  (20-question granularity makes perfect ties dense); choose fitness
  resolution before spending search budget.
- Outputs: experiments/iteration-11/. Write-up:
  iterations/2026-07-08-iteration-11-harder-llm.md.

## 2026-07-07 (Iteration 10, Experiment L): Literature-Driven Improvements — GUIDELINE, NOT SILVER BULLET

- Candidates from the downloaded papers: aging evolution (Real et al.
  2019), BANANAS-style surrogate (White et al.; positional one-hot +
  ridge), zero-cost proxies (Abdelfattah et al.; noted for GPU scale).
- Protocol: 4 methods × 3 cached landscapes × 15 seeds (free), 40-seed
  verification on parity n=7, cap 500 distinct evals.
- Results: aging lifts parity-n=7 hit rate 48% → 78% at equal budget
  (fixes premature convergence without hyperparameter surgery) but
  lands exactly at random's 75% — as the locality theory predicts for
  FDC ≈ 0. Elitist PRISM remains fastest on structured landscapes
  (18.5 vs 28.7 evals, XOR n=6). Surrogate wins mildly only where its
  encoding matches structure (LLM 5.8 evals); inert on parity.
- Decision D15: replacement policy added to the pre-flight guideline
  (FDC negative → elitist+matched/portfolio; FDC ≈ 0 → random or
  aging; aging = safe default). Theory note: aging sacrifices strict
  elitism, so Theorem 2.2's absorption argument needs restating.
- Code/outputs: `experiments/iteration-10/`. Write-up:
  `iterations/2026-07-07-iteration-10-literature-improvements.md`.

## 2026-07-07 (Iteration 9, Experiment K): LLM Reasoning-Chain Ordering — FLAGSHIP RESULT

- Setup: 6 reasoning-module instructions permuted in the prompt;
  fitness = Gemini 2.5 Flash-Lite (temp 0) accuracy on a fixed
  32-question GSM8K subset; key from GCP Secret Manager. All 720
  orderings enumerated (~23k cached API calls, ≈$3-5).
- Ordering effect: accuracy 0.063-0.969 by ordering alone (std 0.230).
  Position effects: ANSWER-format first 0.435 vs last 0.870; COMPUTE
  first 0.908 vs fifth 0.585.
- D14 pre-flight validated end-to-end on a real application: rho1 →
  insert (0.547; the precedence-type theoretical prediction),
  FDC −0.346 → search beats random. Both correct.
- Search (15 seeds, exact): PRISM mean 6 distinct evals to first
  optimum vs random 18 (3×); optima moderately dense (60/720 = 8.3%),
  so the honest framing is a modest absolute edge on a friendly
  landscape with the methodology fully transferred.
- Code: `experiments/iteration-09/llm_chain_experiment.py` (staged:
  variance gate → enumeration; per-call resumable cache) +
  `analyze_llm_landscape.py`.
- Outputs: `experiments/iteration-09/results/`. Write-up:
  `iterations/2026-07-07-iteration-09-llm-reasoning-chain.md`.

## 2026-07-07 (Iteration 8, Experiment J): Landscape Locality Diagnostic — H11 CONFIRMED

- Objective: predict PRISM-vs-random outcomes and operator matching
  from pre-search statistics.
- Code: `experiments/iteration-08/locality_study.py` (~2 min; zero new
  training — cached/closed-form landscapes).
- Metrics: one-step move autocorrelation rho1 per operator (4000
  sampled moves) + fitness-distance correlation (FDC, Cayley distance
  to nearest optimum) on 8 enumerated landscapes.
- Results: rho1 recovers the matched operator 3/3 (hamming→swap 0.655,
  kendall→insert 0.777, adjacency→inversion 0.675) with no search run;
  FDC separates outcomes 8/8: −0.83 (fast convergence) … −0.20/−0.25
  (usable at small n) … −0.06 (n=7 parity: PRISM ≈ random) … +0.78
  (deceptive: anti-guidance despite high smoothness). Neural
  landscapes have rho1 ≈ 0.00–0.06 under precise operators — locally
  near-random, explaining Experiment I.
- Caveat: scramble's rho1 inflated by identity moves; compare it only
  across landscapes.
- Decision D14: rho1+FDC pre-flight is mandatory for new applications.
- Outputs: `experiments/iteration-08/results/locality.{csv,txt}`.
  Write-up: `iterations/2026-07-07-iteration-08-landscape-locality.md`.

## 2026-07-07 (Iteration 7, Experiment I): n=7 Parity Discriminating Protocol — H10 FALSIFIED

- Objective: PRISM vs random under evaluations-to-first-optimum on a
  sparse-optimum ground-truth landscape (fixes It-6 Stage B).
- Code: `experiments/iteration-07/n7_parity_protocol.py`
  (multiprocessing enumeration, 3 workers, budgeted/resumable) +
  `extended_analysis.py` (free, cached).
- Landscape: all 5040 orderings enumerated — optimum 1.0000 held by
  14/5040 (0.28%); std 0.113. H9 (sparsity) confirmed.
- Headline: default PRISM (pop 20, p_m 0.05) hit 4/15 seeds (premature
  convergence: only ~103 distinct orderings explored); random hits
  100% at mean 318 evals. At PRISM's actual budget random would hit
  ~31% ≈ PRISM's 27%. Tuned (pop 40, p_m 0.6): 15/15 hits but at mean
  384 evals — still not better than random's 318/336. Best-found
  quality at equal budgets: random matches or beats PRISM at every
  budget ≥50.
- Conclusion: **on this neural landscape PRISM has no advantage over
  uniform random sampling under a distinct-evaluation cost model** —
  landscape locality, not the algorithm, governs when evolutionary
  search pays (contrast: synthetic landscapes where matched-operator
  PRISM beats random by orders of magnitude).
- Decisions D12 (n≥7 hyperparameters + mandatory random baseline) and
  D13 (locality measurement before attributing wins) adopted.
- Outputs: `experiments/iteration-07/results/`. Write-up:
  `iterations/2026-07-07-iteration-07-n7-parity-protocol.md`.

## 2026-07-07 (Iteration 6, Experiment H): v4 Scale-Up — STAGE A SUCCESS, STAGE B SATURATED

- Objective: scale the exact-ground-truth methodology beyond n=5.
- Code: `experiments/iteration-06/v4_scaleup.py` (budgeted, resumable);
  block pool extended to 8 types (`toy_problems_v4.py`, indices 0-4
  unchanged).
- Stage A (n=6 XOR, k=3): all 720 orderings enumerated — optimum
  1.0000 held by 33/720, landscape std 0.1103. PRISM (portfolio, 80
  gens, 10 seeds): hit rate 0.90, mean regret 0.0083. Methodology
  scales.
- Stage B (n=7 XOR, k=1, 800-eval budget, 4 seeds): PRISM and random
  both saturate at 1.0000 — the k=1 objective's optimum set is too
  dense to discriminate. PRISM converged after touching only 127-164
  distinct permutations vs random's 800, but time-to-first-hit was not
  recorded for random, so no speed claim. Protocol lesson: use parity
  (sparse optima) + evaluations-to-first-optimum at n=7.
- Incident: brief chunk overlap wrote 103 duplicate enumeration rows;
  all values identical (unplanned determinism check passed); deduped.
- Outputs: `experiments/iteration-06/results/`. Write-up:
  `iterations/2026-07-06-iteration-06-scaleup-and-communication.md`.

## 2026-07-06 (Iteration 5, Experiment G): Benchmark v4 with Exact Ground Truth — COMPLETE

- Objective/hypotheses: H6 — residual blocks fix the v3 trainability
  collapse; H7 — permutation-seeded init makes fitness deterministic;
  H8 — ordering still matters with residual blocks.
- Code: `prism-research/benchmarks/toy_problems_v4.py` +
  `experiments/iteration-05/benchmark_v4_study.py` (budgeted,
  resumable). All 120 orderings enumerated per task (k=3 seeded trials
  each), then PRISM (portfolio mutation, 60 generations, 10 seeds)
  against the enumerated cache.
- Results: all three hypotheses confirmed. XOR-v4: optimum 1.0000
  (8/120 orderings), landscape std 0.120, PRISM hit rate 100%.
  Parity-v4: optimum 0.9583 (2/120), std 0.098, hit rate 40%, mean
  regret 0.0333. Determinism verified by repeat evaluation.
- Decision D9: v4 is the canonical toy benchmark design; substantially
  closes R10.
- Outputs: `experiments/iteration-05/results/` (landscape CSV, search
  CSV, summary). Write-up:
  `iterations/2026-07-06-iteration-05-paper-and-benchmark-v4.md`.

## 2026-07-06 (Iteration 4, Experiment F): Operator-Portfolio PRISM — COMPLETE

- Objective/hypotheses: H4 — a uniform operator portfolio (random
  operator per mutation event) succeeds on all landscape types without
  configuration at ≤4x matched-operator cost; H5 — adaptive credit
  assignment closes part of the gap.
- Code: `experiments/iteration-04/portfolio_study.py` (budgeted,
  resumable) + `analyze_portfolio.py`. Modes {portfolio, adaptive} x
  {hamming, kendall, adjacency} x n ∈ {6..16}, 15 seeds, cap 10000 —
  protocol identical to Iteration-3 Experiment C for direct merging.
- Results: **H4 confirmed** — portfolio: zero censoring everywhere,
  overhead 1.1-4.1x vs matched fixed operator (vs unbounded failure for
  mismatched fixed operators). **H5 partially confirmed** — adaptive
  weights rank the literature-matched operator top on 3/3 landscapes
  (automated landscape typing), but hitting times do not consistently
  beat the uniform portfolio and each mutation event costs one extra
  evaluation.
- Decision D8: uniform portfolio is the recommended default for unknown
  landscapes; fixed matched operator when the type is known; adaptive
  as a landscape-diagnosis tool.
- Outputs: `experiments/iteration-04/results/` (CSV, summary,
  comparison table, weights, figure). Full write-up:
  `iterations/2026-07-06-iteration-04-operator-portfolio.md`.

## 2026-07-06 (Iteration 2, Experiment A): Toy Validation Reproduction — COMPLETE

This closes the "Historical Experiment: Toy Convergence Validation"
follow-up below: the reproduction has now been run from a clean
environment.

- Code: `prism-research/experiments/validate_toy_problems.py` (port of
  notebook cell 17), seed 42, 150 generations, pop 20, k=3, p_m 0.05,
  elitism 1.
- Environment: Windows 10, Python 3.12.6, numpy 1.26.4, torch 2.12.1+cpu
  (no GPU). Total wall time ≈ 34 min.
- Results: XOR/OR/AND/parity accuracy 1.0000; polynomial MSE 0.0070
  (reference 0.0068). All headline numbers reproduce.
- Corrections to the historical record: order matters for 4/5 problems
  (AND has zero variance across orderings); "convergence generation" is
  unstable because fitness is stochastic (all classification problems
  hit best fitness at generation 0 via lucky noisy evaluations); only
  positions 0-2 of the permutation are functional in these benchmarks.
- Outputs: `prism-research/outputs/validation_*` (committed, tag
  `iteration-02`). Full write-up:
  `prism-research/docs/iteration-02.md`.

## 2026-07-06 (Iteration 3, Experiment E): All-Positions Toy Benchmark — NEGATIVE RESULT

- Objective/hypothesis: H3 — deepening XOR/parity networks to 5
  permuted layers (all positions functional) increases fitness variance
  across orderings.
- Code: `experiments/iteration-03/validate_toy_v3.py`, seed 42,
  60 generations.
- Result: H3 falsified. Stage-1 variance dropped to exactly 0 (all
  orderings at chance 0.500 on both problems) — the deeper stacks are
  untrainable within the 50-100-step budget. The search still reported
  best fitness 1.0, which stage-1 shows must be evaluation-noise luck;
  independently confirms the best-ever-fitness inflation problem.
- Outputs: `experiments/iteration-03/results/toy_v3_results.csv`.
- Follow-up: benchmark redesign must vary something other than depth;
  add noise control (k-run averaging or fixed per-eval init seeds).

## 2026-07-06 (Iteration 3, Experiments C & D): Operator x Landscape Study

- Objective/hypothesis: H1 — literature-matched mutation operators
  (swap on absolute-position, insert on precedence, inversion on
  adjacency landscapes; per `other.md`/Cicirello) minimize hitting
  time. H2 — deceptive landscape blows up hitting times without
  violating the worst-case bound.
- Code: `experiments/iteration-03/operator_study.py` +
  `analyze_operator_study.py`. Operators {swap, insert, inversion,
  scramble} x landscapes {hamming, kendall, adjacency} x
  n ∈ {6,8,10,12,14,16}, 15 seeds, cap 20000 generations; deceptive:
  {swap, inversion} x n ∈ {6,8,10}.
- Baseline: Iteration-2 swap results (verified to reproduce exactly).
- Protocol v2: cap 10000 generations (lowered from 20000 after the
  first run was killed mid-way; rankings unaffected), kill-safe
  incremental CSV with resume, early-abort after >=14/15 censoring at
  a size (larger sizes recorded as status=skipped).
- Status: COMPLETE (2026-07-06).
- Results: **H1 confirmed on all three landscape types** — matched
  operators best everywhere (swap on hamming 405 gens at n=16 vs total
  censoring for all others; insert on kendall best at 5/6 sizes;
  inversion on adjacency 1199 at n=16 vs total censoring for all
  others). Key insight: smooth landscapes (kendall) are
  operator-forgiving (~10-40% spread, zero censoring); plateau-rich
  landscapes (hamming, adjacency) turn operator mismatch into hard
  failure. Matched-operator scaling exponents 2.79 (hamming/swap),
  2.98 (kendall/insert), 3.44 (adjacency/inversion) — consistent with
  O(n³ log n) out to n=16. **H2 confirmed**: deceptive landscape
  censors almost everything by n=8-10 for both operators tested;
  polynomial-time behavior is landscape-conditional.
- Outputs: `experiments/iteration-03/results/operator_study_results.csv`
  plus `operator_summary.csv`, `operator_ranking.txt`,
  `operator_scaling.txt`, `operator_study.png`. Full write-up:
  `iterations/2026-07-06-iteration-03-operator-study.md`.

## 2026-07-06: PRISM-RL Lightweight Benchmarks

- Objective: test whether PRISM can be applied as a framework to lightweight
  reinforcement-learning ordering problems.
- Code: `prism-research/benchmarks/rl_ordering.py` and
  `prism-research/experiments/rl_ordering_experiment.py`.
- Benchmarks:
  - `option_route_grid`: deterministic semi-MDP where each permutation item is
    a navigation option and fitness is episodic return after executing the
    option order.
  - `chain_curriculum`: tabular Q-learning chain where each permutation item is
    a curriculum task and fitness is final target performance plus a small
    training-efficiency term.
- Protocol: exact enumeration for the small search spaces; PRISM over eight
  seeds; random-search baseline with the same number of fitness evaluations.
- Results: `option_route_grid` exact best 80.0 at permutation
  `2 5 3 0 7 6 1 4`; swap hit rate 0.25, inversion hit rate 0.625.
  `chain_curriculum` exact best 1.00425 at permutation `5 3 0 1 2 4`;
  swap hit rate 0.75, insert hit rate 1.00.
- Interpretation: PRISM transfers to RL when the RL problem exposes a finite
  ordering surface such as options or curriculum tasks. The core algorithm did
  not require RL-specific changes; customization is primarily the fitness
  evaluator and, for route-like objectives, mutation choice.
- Outputs: `prism-research/outputs/rl_ordering_*`.

## Historical Experiment: Synthetic Runtime Scaling

Source artifacts:

- `prism-research/experiments/scaling_experiment.py`
- `prism-research/benchmarks/synthetic.py`
- `prism-research/outputs/scaling_results.csv`
- `prism-research/outputs/scaling_summary.csv`
- `prism-research/outputs/scaling_fit.txt`
- `prism-research/outputs/scaling_fit_refined.txt`
- `prism-research/outputs/scaling_loglog.png`

Objective: Estimate empirical hitting-time scaling for PRISM on deterministic
synthetic permutation objectives.

Reported protocol in script:

- Objectives: hamming and kendall.
- `n` values: 4, 5, 6, 7, 8, 10, 12.
- Seeds: 0 through 14.
- Maximum generations: 30000.
- Target fitness: 1.0.
- Parameters: population 20, tournament k=3, swap mutation probability 0.05,
  elitism 1.

Existing output summary:

- Hamming empirical exponent: 3.73 over n = 4, 5, 6, 7, 8, 10, 12.
- Kendall empirical exponent: 3.68 over n = 4, 5, 6, 7, 8, 10, 12.
- Refined fits excluding n <= 5: hamming 3.14, kendall 2.89.
- The scaling log-log plot is stored at
  `prism-research/outputs/scaling_loglog.png`.

Reproducibility status: Outputs existed before the 2026-07-06 git setup and
were added to Git. The experiment was not rerun during repository setup.
The internal notes `prism-research/docs/iteration-02.md` and
`prism-research/docs/handover-iteration-02.md` provide additional context, but
the latter contains placeholder text for the toy-benchmark reproduction.

Open follow-up:

- Rerun `python prism-research/experiments/scaling_experiment.py` in a captured
  environment and compare outputs with the committed CSVs.
- Record runtime, Python version, NumPy version, and machine details.

## Historical Experiment: Toy Convergence Validation

Source artifacts:

- `GNGN_Toy_Problems.ipynb`
- `research.md`, sections "Validation Results" and "Appendix: Quick Reference"

Objective: Validate theoretical convergence properties on small benchmark
problems.

Reported tasks:

- XOR classification.
- OR classification.
- AND classification.
- 3-bit parity classification.
- Polynomial regression.

Reported method: Population-based permutation search with tournament selection,
swap mutation, and elitism over permutations of five branch types. The notebook
contains 19 cells: 9 Markdown cells and 10 code cells.

Reported results in existing documentation:

- 100 percent accuracy on XOR, OR, AND, and 3-bit parity.
- MSE 0.0068 on polynomial regression.
- Convergence in roughly 100 to 150 generations.
- Empirical convergence rate reported near lambda = 0.96.

Reproducibility status: Not rerun during the 2026-07-05 continuity setup.
Before publication or scale-up, rerun the notebook from a clean environment,
record package versions, random seeds, hardware, runtime, and output artifacts.

Open follow-up:

- Confirm whether the notebook result is deterministic under fixed seeds.
- Export final plots and result tables into `artifacts/`.
- Move or copy a maintained experiment package under `experiments/` once the
  intended code layout is clarified.

## 2026-07-05: Continuity Setup

Type: Documentation/process implementation.

Objective: Implement the documentation requirements from `instructions.md`.

Experiment run: None.

Result: Added project-level documentation and logs. See
`iterations/2026-07-05-continuity-setup.md`.
# Iteration 19: ANASOD--PRISM boundary diagnostic (complete)

- Objective: determine when NAS-Bench-201 operation distributions are a
  sufficient abstraction and when edge placement retains exploitable residual
  structure.
- Method: exhaustive partition of 15,625 architectures into 210 distributions;
  eta-squared across distributions; within-slice SD/range, exact swap rho1, and
  exact FDC to nearest tied optimum on each dataset.
- Implementation: `experiments/iteration-19/anasod_boundary.py`; accepts a
  compact CSV or the official `.pth` API archive.
- Verification: the 15-placement synthetic fixture completes and recovers its
  deliberately injected locality. This verifies code paths only.
- Data: `simple-hpo-bench==0.2.0` compact NATS-Bench tables, three repeated
  last-epoch validation accuracies per architecture; means analyzed.
- Results: eta-squared = 0.461/0.556/0.612 on CIFAR-10/CIFAR-100/ImageNet16;
  residual within-distribution fractions = 0.539/0.444/0.388. Figure-1 slice
  placement ranges = 0.848/2.530/4.956 points; rho1 = 0.137/-0.143/0.223;
  FDC = -0.412/-0.273/-0.721.
- Interpretation: ANASOD is supported as a strong coarse abstraction but not a
  sufficient statistic; placement structure is conditional on slice/dataset.
- Limitation: compact last-epoch backend rather than official 4.7 GB archive;
  budget-matched search confirmation remains. Do not cite fixture metrics.
