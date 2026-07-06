# PRISM Research Workspace

This workspace contains research material for PRISM, the Permutation-based
Reasoning and Intelligence Search Method, plus related GNGN/NEAT notes,
presentations, notebooks, and generated PDFs.

## Current State

As of 2026-07-05, the project appears to be in a documented validation stage:

- `research.md` reports complete theoretical framing, toy-problem validation,
  and readiness for scale-up experiments.
- `GNGN_Toy_Problems.ipynb` contains the toy convergence validation notebook.
- `other.md` records additional analysis on innovation numbers, speciation,
  NEAT-style topology evolution, and usage examples.
- `PRISM_Research_Blog.tex` and `PRISM_Presentation.tex` are publication and
  presentation sources.
- The workspace was not initially a Git repository; as of 2026-07-06 it is
  initialized on branch `main` and pushed to the private GitHub remote
  `https://github.com/bleymambwe/PRISM`.

The claims above are inherited from existing project documents and should be
reproduced before being treated as independently verified results.

## Start Here

1. Read `docs/HANDOVER.md` for the current handover.
2. Read `docs/ARTIFACT_INDEX.md` to understand each file and its role.
3. Use `docs/CONTINUITY_PROTOCOL.md` before starting any new research iteration.
4. Create a new file under `iterations/` using `docs/ITERATION_TEMPLATE.md`.
5. Record decisions, experiments, literature, and risks in the relevant files
   under `docs/`.

## Documentation System

The documentation layer implements the requirements in `instructions.md`.

| File | Purpose |
| --- | --- |
| `docs/CONTINUITY_PROTOCOL.md` | Operating protocol for each research iteration. |
| `docs/HANDOVER.md` | Current concise handover for the next researcher. |
| `docs/ARTIFACT_INDEX.md` | Inventory of files and their relationship to the project. |
| `docs/DECISION_LOG.md` | Significant decisions and evidence supporting them. |
| `docs/EXPERIMENT_LOG.md` | Experiment summaries, locations, and reproducibility status. |
| `docs/LITERATURE_LOG.md` | Reviewed or referenced literature and source notes. |
| `docs/RISK_REGISTER.md` | Risks, assumptions, limitations, and unresolved questions. |
| `iterations/` | Per-iteration working notes and handovers. |
| `experiments/` | Future experiment packages, configs, outputs, and summaries. |
| `artifacts/` | Future generated figures, tables, model outputs, and exports. |
| `references/` | Future papers, citation notes, and reference metadata. |
| `scripts/` | Future reproducibility and automation scripts. |

## Working Rule

Every meaningful research or implementation step should leave enough context for
another researcher to resume without private knowledge from prior contributors.
Record the objective, method, result, interpretation, decision, and next action
while the work is performed, not only at the end.
