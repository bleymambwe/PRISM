# Iteration 28: corrected scoring as primary, leave-family-out probe, null calibration

Pre-registered in `hypotheses.json` (commit 368f78a) before any run. CPU only, no paid calls.
Re-run from the repository root: `corrected.py`, then `heldout.py` (resumable). Outputs in `results/`.
This is leave-one-family-out validation on the same 15 landscapes. It is not an independent test set.

## A. Corrected GSM8K scoring (now primary; `common.load(corrected=True)`)

| Check | Result |
|---|---|
| A3 arithmetic | 55 optima, min 0.0625, max 1.0 (original: 60 optima, max 0.96875). **Holds.** |
| A1 true operator and regime | Insert and search_pays before and after. rho1 insert 0.552 (was 0.546), FDC -0.379 (was -0.364). **Holds.** |
| A2 order uniform < protocol < ls_swap at B=100 | **Not supported.** All four policies reach 100% at B=100 on both tables, so the landscape cannot rank them. 55 of 720 orderings are optimal (7.6%). |

The correction changes the GSM8K landscape slightly and changes no conclusion about it. Use the
corrected table as primary and report the original as a sensitivity analysis.

## B. Held-out and null calibration (deployed probe at about 174 charged evaluations)

Ground truth "search pays" = best of {ls_swap, ea_portfolio} beats uniform by at least 0.15 at B=100
(margin fixed in advance). 10 of 15 landscapes are positives.

| Test | Result |
|---|---|
| B1 held-out balanced accuracy, threshold fitted on other families | **0.25** (bootstrap of BA minus 0.5: -0.45 to +0.01). Worse than a constant call. Hypothesis (no better than a constant call) **holds**. |
| B1 same, published threshold -0.15 | 0.50 (-0.20 to +0.25). Chance level. |
| B2 null: shuffled fitness, false "search pays" rate | **49.5%** (95% CI 34.9 to 64.6). Prediction (lower bound above 10%) **supported**. |
| B3 FDC exactly -1 at 20 charged evaluations | 0.3%. Does not test audit M06, which concerns the 2-sample probes at B=15 and B=25. Not reproduced here. |

Fitted thresholds per held-out family were -0.35 (llm), -0.05 (neural), -0.40 (sciml), -0.35
(synthetic). They differ by 0.35, so the threshold is not stable across families.

On each shuffled landscape the probe still returns "search pays" about half the time, because the
reference point is the best of the probe's own sample. That is the self-inclusion bias of M06,
measured. The rate ranges from 12.5% (sciml damped oscillator) to 99.5% (deceptive).

## Consequences for the manuscript

1. The deployed probe has no demonstrated skill at the binary decision it was built for: held-out
   balanced accuracy is at or below chance, and on structureless landscapes it says "search pays" half the time.
2. Do not report the probe's FDC rule as a validated decision rule. Report the null false-positive
   rate beside any regime call.
3. A cross-fitted reference (iteration 27) removes the self-reference but was less accurate at equal
   cost. The honest status is: no deployable probe in this repository has been shown to work.
4. These tests use 15 landscapes in 4 families, with a single landscape in the llm family and
   six sciml systems that share one generator. Treat the intervals as sensitivity, not generalization.
