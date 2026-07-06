# PRISM Artifact Index

Last updated: 2026-07-06

This index records the purpose and status of visible project artifacts. It
separates existing historical material from the new continuity structure.

## Historical Root Artifacts

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `instructions.md` | Continuity and documentation requirements. | Implemented by the documentation layer added on 2026-07-05. |
| `research.md` | Main PRISM handover document covering theory, implementation, validation, insights, assets, and next steps. | Primary inherited project narrative. Claims should be reproduced before independent publication. |
| `GNGN_Toy_Problems.ipynb` | Notebook validating convergence on toy problems including XOR, OR, AND, 3-bit parity, and polynomial regression. | Main executable validation artifact currently visible. |
| `other.md` | Additional analysis on GNGN innovation numbers, speciation, NEAT-style topology evolution, and usage patterns. | Contains important open design issues, including incomplete branch-evolution specification. |
| `presentation.md` | Guide for building a publication-ready GNGN/NEAT research presentation. | Presentation planning and tooling reference. |
| `PRISM_Research_Blog.tex` | LaTeX source for a comprehensive PRISM research summary. | Publication-style source artifact. |
| `PRISM_Presentation.tex` | LaTeX Beamer source for PRISM presentation. | Presentation source artifact. |
| `main.pdf` | Existing PDF artifact. | Exact source relationship not yet verified. |
| `PRISM Algorithm.pdf` | Existing PRISM algorithm PDF. | Historical generated or source-derived research artifact. |
| `Prism Comphersive Algorithm.pdf` | Existing comprehensive PRISM PDF. | Historical generated artifact; filename spelling preserved as found. |
| `screenshot.png` | Existing visual artifact. | Purpose not yet verified. |
| `skills.md` | Empty Markdown file. | Purpose not yet documented. |

## PRISM Research Codebase

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `prism-research/README.md` | Describes the runnable PRISM codebase layout, setup, and naming note. | Inherited code package found before repository initialization. |
| `prism-research/core/prism.py` | Seeded PRISM implementation with early stopping and per-generation history. | Runnable core implementation. |
| `prism-research/benchmarks/toy_problems.py` | PyTorch toy-problem fitness functions extracted from the notebook. | Requires PyTorch; contains known stochastic fitness behavior. |
| `prism-research/benchmarks/synthetic.py` | Deterministic synthetic permutation objectives for scaling tests. | NumPy-only benchmark support. |
| `prism-research/experiments/validate_toy_problems.py` | Script for reproducing the five toy validation benchmarks. | No generated validation outputs were present during the 2026-07-06 git setup. |
| `prism-research/experiments/scaling_experiment.py` | Script for empirical hitting-time scaling experiments. | Generated outputs are indexed below. |
| `prism-research/docs/iteration-02.md` | Lab log for the reproduction and runtime-scaling validation iteration. | Existing project-level iteration note added to Git on 2026-07-06. |
| `prism-research/docs/handover-iteration-02.md` | Internal handover for the rebuilt PRISM codebase and runtime-scaling iteration. | Contains placeholder text for Experiment A; do not treat the toy reproduction statement as verified without rerunning. |
| `prism-research/outputs/scaling_results.csv` | Per-run hitting-time results for synthetic scaling experiments. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/scaling_summary.csv` | Per-objective/per-size summary of scaling results. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/scaling_fit.txt` | Log-log fitted empirical exponents for scaling experiment. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/scaling_fit_refined.txt` | Refined scaling-fit diagnostics, including ratios against n^3 and n^3 log n. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/scaling_loglog.png` | Scaling log-log plot generated from the synthetic runtime experiment. | Existing generated artifact added to Git on 2026-07-06. |

## Continuity Structure Added 2026-07-05

| Path | Purpose |
| --- | --- |
| `README.md` | Workspace entry point and navigation guide. |
| `docs/CONTINUITY_PROTOCOL.md` | Operating protocol for ongoing research documentation. |
| `docs/HANDOVER.md` | Current concise handover for the next researcher. |
| `docs/DECISION_LOG.md` | Project decision log. |
| `docs/EXPERIMENT_LOG.md` | Experiment inventory and reproduction status. |
| `docs/LITERATURE_LOG.md` | Literature and source-review log. |
| `docs/RISK_REGISTER.md` | Risk, assumption, limitation, and open-question register. |
| `docs/ITERATION_TEMPLATE.md` | Template for future iteration notes. |
| `iterations/2026-07-05-continuity-setup.md` | Record of the continuity setup iteration. |
| `artifacts/README.md` | Organization rules for future generated artifacts. |
| `experiments/README.md` | Organization rules for future experiment packages. |
| `references/README.md` | Organization rules for future literature artifacts. |
| `scripts/README.md` | Organization rules for future automation scripts. |
| `iterations/2026-07-06-git-repository-setup.md` | Record of Git repository initialization and artifact staging. |

## Maintenance Rule

When adding, removing, moving, or superseding a meaningful artifact, update this
index in the same iteration.
