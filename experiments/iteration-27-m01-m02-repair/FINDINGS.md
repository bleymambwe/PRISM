# Iteration 27: repair of audit findings M01 and M02

Pre-registered in `hypotheses.json` (commit 6a98cbb) before any run. CPU only, no paid calls.
Numbers: `results/REPORT.md`, `results/hypothesis_outcomes.json`. Re-run with
`fresh_budget.py`, `deployable_probe.py`, then `analyze.py`, from the repository root.

## What changed in method

- **M02.** The protocol is now run at its true total budget B for every B (6,000 runs), not read
  off a B=200 trace. The B=200 run reproduces the archive exactly on all 15 landscapes, which
  confirms the budget semantics are the only difference.
- **M01.** The deployed `preflight` (best-observed proxy reference) is measured with every
  evaluation charged, plus a cross-fit variant. The oracle-assisted 91% is no longer the headline.

## Outcomes (landscape-bootstrap 95% CI, 15 landscapes)

| Hypothesis | Result |
|---|---|
| H27-1 protocol not above fixed swap local search @100 | **Holds.** Fresh protocol 53.0% vs ls_swap 70.5%; difference -17.5 pts [-27.8, -7.5]. The protocol is credibly worse than a fixed optimizer. |
| H27-2 protocol above uniform @100 | **Supported.** +15.3 pts [+8.3, +22.0]. Fresh run is also better than the old prefix (53.0% vs 46.8%). |
| H27-3 probe takes >=80% of budget at B=15 and 25 | **Partly.** 93% at B=15, but 56% at B=25, 34% at B=50, 22% at B=100. Not met as stated. |
| H27-4 deployed regime agreement at m=200 below 91% | **Supported.** 70.7% [55.3, 82.7] using 174 charged calls, against the 91% oracle figure. |
| H27-5 proxy over-calls search_pays vs cross-fit | **Weak.** Point estimates positive at every m, CI excludes 0 only at m=20 (+36 pts). Cross-fit itself is worse overall (53.1% at m=200) because it halves the sample. |
| H27-6 charged cost | Deployed probe charges 174 distinct calls at target 200; the old estimator could use up to 7m raw accesses. |

## What this means for the paper

1. The old 91% reliability figure must not appear as a deployable result. The deployable probe is
   about 70% at the same cost, and at m=20 it equals the old estimator, so the sample size is not
   what separates them. The oracle reference is.
2. Operator selection by the deployed probe is right only 56% of the time at m=200.
3. The protocol beats uniform sampling but loses to a fixed swap local search by 17.5 points at
   B=100. The "protocol improves optimizer selection" claim has no support on these landscapes.
   A defensible framing is a diagnostic that beats random sampling at a cost, not a selector that beats good defaults.
4. The small-budget explanation in the old text (probe eats the budget) holds at B=15 only.
5. The floor variant is exploratory: it equals ls_swap wherever it skips the probe and equals the
   protocol elsewhere. It adds no evidence beyond "ls_swap is a strong default".

## Not fixed here

- FDC thresholds (-0.15, 0.30) were set on these same landscapes. No out-of-sample validation exists.
- Truth rho1 is a 20,000-pair estimate, and 15 landscapes are not a sample of a defined population.
- `prism-research/benchmarks/*.py` no longer exists on disk (git-ignored, bytecode only). `_compat.py`
  loads the artifact's identical `synthetic.py` instead (0 mismatches over all permutations, n=5..7).
