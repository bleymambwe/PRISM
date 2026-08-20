# Iteration 26 — Tier 0: the zero-cost program

**Registered:** 13 August 2026, before any result was computed.
**Cost:** US$0. CPU only, no API calls, no new model evaluations.
**Purpose:** close the rigor objections standing between the PRISM preprint and an
ICLR 2027 submission (`publication/iclr-2027/01_ACCEPTANCE_ANALYSIS.md` §3).

## Why this is free

Every landscape used here is **exactly enumerated and already committed**: 720 orderings of the
GSM8K instruction chain, 5,040 for parity n=7, 6 × 720 for the scientific-pipeline suite, and the
closed-form typed synthetics. They are complete lookup tables, so any optimizer can be *replayed*
against them at zero marginal cost. The expensive evaluations were paid for in earlier iterations.

## Experiments

### E0.1 — Baseline gauntlet
13 methods × 15 landscapes × 40 seeds, charged by **distinct evaluated permutations**, compared
against uniform sampling without replacement at equal budget. Because the landscapes are
enumerated, success is measured against **true optima**, not a best-observed proxy, and regret is
exact.

Methods: `uniform` · `ls_swap` · `ls_insert` · `ls_inversion` · `simulated_annealing` ·
`iterated_local_search` · `ea_elitist` · `ea_aging` · `ea_portfolio` · `surrogate_positional` ·
`surrogate_precedence` · `eda_precedence` · `prism_protocol`.

`prism_protocol` spends ~20% of its budget on the pre-flight probe **and is charged for it**, so the
end-to-end comparison is at equal total budget. Best-of-k random is not a separate method: it is
uniform sampling read off its own budget curve at k.

Each run executes once at the maximum budget and every smaller budget is read from the best-so-far
curve, so the budget grid {15, 25, 50, 100, 200} costs no extra evaluations.

Metrics: success@budget with Wilson intervals · evaluations-to-first-optimum · area under the
best-so-far curve · regret to the true optimum.

### E0.2 — Estimator sample complexity
Probe-size sweep m ∈ {20, 50, 100, 200, 500} × 200 bootstrap resamples per landscape, measuring how
often the regime call and the operator choice made from a probe of size m match the call made from
the full enumeration. Paired with a concentration argument for the ρ₁ and FDC estimators.

### E0.3 — Evaluator-resolution curves
Subsample q ∈ {4, 8, 16, 32} questions from the committed answer caches, recompute the landscape and
its regime call at each q, and measure where the call destabilises.

### E0.4 — Derived tables
Convert answer caches (`perm, qidx, correct`) into per-ordering landscape CSVs so the transfer
studies are re-derivable without re-spending API budget.

### E0.5 — Pooled calibration record
Pool every forecast registered before its outcome into one table: confusion matrix, conservative vs
genuine miss split, and a calibration summary.

## Pre-registered hypotheses

See `hypotheses.json`, committed before execution. Summary:

| ID | Claim | Falsified if |
|---|---|---|
| H27 | On landscapes the pre-flight calls "search pays", some structured method beats uniform decisively at budget 100 | no method's Wilson lower bound exceeds uniform's upper bound on any such landscape |
| H28 | On the LLM ordering landscape no method beats uniform decisively (PRISM ≈ random replicates under a full gauntlet) | any method's success@50 Wilson lower bound exceeds uniform's upper bound |
| H29 | The precedence surrogate is the strongest non-uniform method on precedence-structured landscapes | it is not top-2 by evaluations-to-optimum on `kendall_n7` |
| H30 | Charging the pre-flight probe does not sink the protocol: `prism_protocol` stays within 10pp of uniform's success@100 on every landscape | it falls >10pp below uniform anywhere |
| H31 | Regime-call accuracy rises monotonically with probe size and reaches ≥90% at m=200 where the margin to threshold is ≥0.10 | accuracy at m=200 is <90% on such landscapes |
| H32 | Operator selection by argmax ρ₁ is ≥90% stable at m≥100 pairs on typed synthetic landscapes | agreement <90% |
| H33 | The LLM regime call is unstable below q=16 questions | agreement with the full-32 call stays ≥80% at q=8 |

**H28 is the one that matters most and it predicts a negative result.** It is registered because the
paper's argument is that the protocol forecasts its own failures. Confirming it strengthens the
paper; falsifying it would be a bigger result still. Either outcome is reported.

## Reversal conditions

- If H30 fails, the pre-flight is too expensive at small budgets and the paper must say so and give
  the budget below which the protocol should not be run.
- If H27 fails, the "search pays" band does not identify landscapes where search pays, and the
  decision rule needs re-derivation rather than re-description.

## Outputs

`results/` — `landscape_summary.csv` · `gauntlet_runs.csv` (one row per run, append-only, resumable)
· `gauntlet_summary.csv` · `sample_complexity.csv` · `resolution_curves.csv` · `calibration.csv` ·
`TIER0_REPORT.md`.

## Runner notes

Background processes on this machine are killed after roughly five minutes, so `gauntlet.py` takes a
wall-clock budget in seconds, appends every completed run to CSV immediately, and skips
already-recorded `(landscape, method, seed)` keys on restart. Run it in foreground chunks until it
prints `GAUNTLET COMPLETE`.
