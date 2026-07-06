# PRISM Risk Register

Last updated: 2026-07-06

| ID | Risk / Assumption | Impact | Status | Mitigation / Next Action |
| --- | --- | --- | --- | --- |
| R1 | Historical validation claims have not been independently rerun during continuity setup. | Publication or scale-up could rely on stale or non-reproducible results. | Closed 2026-07-06 | Reproduced via `prism-research/experiments/validate_toy_problems.py` (clean environment, seed 42, versions logged in EXPERIMENT_LOG): all headline results reproduce, with three documented corrections (see HANDOVER). |
| R2 | PRISM and GNGN terminology are both present, but their relationship is not explicitly resolved. | New contributors may confuse framework boundaries or cite the wrong concept. | Open | Add a terminology note after reviewing project history. |
| R3 | `other.md` reports that branch evolution / innovation-number handling is incomplete or underspecified. | Topology-evolution extensions may lack a defensible algorithmic basis. | Open | Formalize branch-level and within-branch innovation tracking before implementing topology crossover. |
| R4 | Existing Markdown files show mojibake / encoding artifacts in some symbols. | Mathematical notation and presentation quality may suffer. | Open | Perform a controlled encoding cleanup in a separate iteration with before/after checks. |
| R5 | The workspace previously lacked Git metadata. | Change history and rollback were weak. | Closed 2026-07-06 | Git was initialized at the project root on branch `main`. |
| R6 | Several PDFs have unclear source relationships. | Generated artifacts may be hard to reproduce or update. | Open | Map each PDF to its source `.tex`, notebook, or external origin. |
| R7 | Scale-up targets such as CIFAR-10, LLM applications, and compiler optimization are listed but not yet implemented in visible files. | Claims of readiness may exceed demonstrated evidence. | Open | Define one concrete next benchmark with success criteria, compute budget, and baseline comparisons. |
| R8 | No remote repository was configured at the time of local Git initialization. | Local commits may not be backed up or shareable until a remote push succeeds. | Closed 2026-07-06 | Created private GitHub remote `https://github.com/bleymambwe/PRISM` and pushed `main`. |
| R9 | PRISM-RL evidence is currently limited to lightweight toy RL surfaces. | Results show feasibility, not competitive RL performance. | Open | Add a stronger RL benchmark with controlled stochasticity, repeated seeds, and nontrivial baselines. |
| R10 | Toy neural benchmark fitness is stochastic and only positions 0-2 are functional; the Iteration-3 depth-based redesign was falsified (all orderings untrainable). | Toy-benchmark claims (100% accuracy) reflect best-observed noise, not expected performance; not publication-grade. | Open (worsened 2026-07-06) | Redesign varying width/skip patterns instead of depth; control noise via k-run averaging or fixed per-eval init seeds. |
| R11 | Background processes on this machine are killed after a few minutes, and long unbudgeted runs lose work. | Experiments silently truncated; wasted compute. | Mitigated 2026-07-06 | Use the budgeted resumable runner pattern (`operator_study.py <budget-seconds>`, incremental CSV, resume-on-rerun) for all long experiments. |
| R12 | PRISM's polynomial-time behavior is landscape-conditional: mismatched operators hard-fail on plateau-rich landscapes and deceptive landscapes defeat all tested operators. | Overclaiming "O(n³ log n) runtime" without conditions would be scientifically wrong. | Partially mitigated 2026-07-06 (Iteration 4) | Operator-choice risk resolved: uniform portfolio (`mutation="portfolio"`) succeeds on all typed landscapes at ≤4x matched cost (Experiment F, D8). Deceptive-landscape limitation remains and must be stated in papers. Portfolio-on-deceptive untested. |

## Maintenance Rule

Update this register whenever an assumption becomes evidence, an open issue is
closed, or a new risk emerges.
