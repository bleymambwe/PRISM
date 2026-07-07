# PRISM Experiment Log

Last updated: 2026-07-07 (Iteration 7)

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
