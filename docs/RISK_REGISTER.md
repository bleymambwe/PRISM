# PRISM Risk Register

Last updated: 2026-07-06

| ID | Risk / Assumption | Impact | Status | Mitigation / Next Action |
| --- | --- | --- | --- | --- |
| R1 | Historical validation claims have not been independently rerun during continuity setup. | Publication or scale-up could rely on stale or non-reproducible results. | Open | Rerun `GNGN_Toy_Problems.ipynb` in a clean environment and log versions, seeds, commands, outputs, and runtime. |
| R2 | PRISM and GNGN terminology are both present, but their relationship is not explicitly resolved. | New contributors may confuse framework boundaries or cite the wrong concept. | Open | Add a terminology note after reviewing project history. |
| R3 | `other.md` reports that branch evolution / innovation-number handling is incomplete or underspecified. | Topology-evolution extensions may lack a defensible algorithmic basis. | Open | Formalize branch-level and within-branch innovation tracking before implementing topology crossover. |
| R4 | Existing Markdown files show mojibake / encoding artifacts in some symbols. | Mathematical notation and presentation quality may suffer. | Open | Perform a controlled encoding cleanup in a separate iteration with before/after checks. |
| R5 | The workspace previously lacked Git metadata. | Change history and rollback were weak. | Closed 2026-07-06 | Git was initialized at the project root on branch `main`. |
| R6 | Several PDFs have unclear source relationships. | Generated artifacts may be hard to reproduce or update. | Open | Map each PDF to its source `.tex`, notebook, or external origin. |
| R7 | Scale-up targets such as CIFAR-10, LLM applications, and compiler optimization are listed but not yet implemented in visible files. | Claims of readiness may exceed demonstrated evidence. | Open | Define one concrete next benchmark with success criteria, compute budget, and baseline comparisons. |
| R8 | No remote repository was configured at the time of local Git initialization. | Local commits may not be backed up or shareable until a remote push succeeds. | Closed 2026-07-06 | Created private GitHub remote `https://github.com/bleymambwe/PRISM` and pushed `main`. |

## Maintenance Rule

Update this register whenever an assumption becomes evidence, an open issue is
closed, or a new risk emerges.
