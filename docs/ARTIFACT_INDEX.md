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
| `prism-research/benchmarks/rl_ordering.py` | Lightweight RL option-ordering and curriculum-ordering benchmarks. | Added 2026-07-06 as a PRISM-RL proof of concept. |
| `prism-research/experiments/validate_toy_problems.py` | Script for reproducing the five toy validation benchmarks. | Reproduction run completed 2026-07-06 (Iteration 2); outputs at `prism-research/outputs/validation_*`, committed at tag `iteration-02`. |
| `prism-research/experiments/scaling_experiment.py` | Script for empirical hitting-time scaling experiments. | Generated outputs are indexed below. |
| `prism-research/experiments/rl_ordering_experiment.py` | Runner for lightweight PRISM-RL option and curriculum benchmarks. | Writes `rl_ordering_*` outputs. |
| `prism-research/docs/iteration-02.md` | Lab log for the reproduction and runtime-scaling validation iteration. | Existing project-level iteration note added to Git on 2026-07-06. |
| `prism-research/docs/handover-iteration-02.md` | Internal handover for the rebuilt PRISM codebase and runtime-scaling iteration. | Completed 2026-07-06: Experiment A results filled in (all headline results reproduced); superseded as current handover by `docs/HANDOVER.md`. |
| `prism-research/outputs/scaling_results.csv` | Per-run hitting-time results for synthetic scaling experiments. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/scaling_summary.csv` | Per-objective/per-size summary of scaling results. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/scaling_fit.txt` | Log-log fitted empirical exponents for scaling experiment. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/scaling_fit_refined.txt` | Refined scaling-fit diagnostics, including ratios against n^3 and n^3 log n. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/scaling_loglog.png` | Scaling log-log plot generated from the synthetic runtime experiment. | Existing generated artifact added to Git on 2026-07-06. |
| `prism-research/outputs/rl_ordering_results.csv` | Per-run PRISM-RL benchmark results. | Generated 2026-07-06. |
| `prism-research/outputs/rl_ordering_summary.csv` | Aggregated PRISM-RL benchmark summary. | Generated 2026-07-06. |
| `prism-research/outputs/rl_ordering_summary.md` | Human-readable PRISM-RL benchmark summary. | Generated 2026-07-06. |
| `prism-research/outputs/rl_ordering_gaps.png` | Plot comparing PRISM and random-search gaps to exact best fitness. | Generated 2026-07-06. |

## Iteration 3 (2026-07-06): Operator-Landscape Study

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `iterations/2026-07-06-iteration-03-operator-study.md` | Iteration-3 lab log: hypotheses, protocol (incl. v2 protocol change), results, interpretation. | Complete. |
| `prism-research/outputs/validation_results.csv`, `validation_variance.csv`, `validation_histories.npz`, `validation_convergence.png` | Iteration-2 Experiment A reproduction outputs. | Committed at tag `iteration-02`. |
| `experiments/iteration-03/operator_study.py` | Kill-safe, budgeted, resumable runner for Experiments C (operator x landscape) and D (deceptive). | Run with `python operator_study.py <budget-seconds>`, rerun until "STUDY COMPLETE". |
| `experiments/iteration-03/analyze_operator_study.py` | Analysis: rankings, H1 verdicts, scaling exponents, plot. | Complete. |
| `experiments/iteration-03/validate_toy_v3.py` | Experiment E: all-positions toy benchmark redesign. | H3 falsified (negative result, documented). |
| `experiments/iteration-03/results/operator_study_results.csv` | Per-run hitting times (status: ok/censored/skipped). | 810 rows; cap 10000 generations. |
| `experiments/iteration-03/results/operator_summary.csv`, `operator_ranking.txt`, `operator_scaling.txt`, `operator_study.png` | Aggregates, per-landscape operator rankings, exponents, figure. | Complete. |
| `experiments/iteration-03/results/toy_v3_results.csv` | Experiment E outputs. | Negative result. |
| `prism-research/core/prism.py` (updated) | Now supports `mutation=` swap/insert/inversion/scramble; swap default is bit-for-bit v2-compatible. | Compare versions via `git diff iteration-02..iteration-03`. |
| `prism-research/benchmarks/synthetic.py` (updated) | Added adjacency (R-type) and deceptive objectives. | Landscape typing documented in module docstring. |

## Current Paper and Presentation Deliverables

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `deliverables/PRISM_Framework_Research_Paper.md` | Editable research-paper draft covering PRISM framework, theory, experiments, limitations, and PRISM-RL. | Created 2026-07-06. |
| `deliverables/PRISM_Framework_Research_Paper.pdf` | Generated PDF version of the current research-paper draft. | Built with `scripts/build_research_paper_and_ppt.py` because no LaTeX engine was installed. |
| `deliverables/PRISM_Framework_Presentation_Outline.md` | Editable slide outline following the guidance in `presentation.md`. | Created 2026-07-06. |
| `deliverables/PRISM_Framework_Presentation.pptx` | Current PowerPoint deck for the PRISM framework. | 15 slides; built with `scripts/build_research_paper_and_ppt.py`. |
| `scripts/build_research_paper_and_ppt.py` | Build script for the current paper PDF and PPTX deck. | Uses `reportlab` and `python-pptx`; avoids LaTeX dependency on this machine. |

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
| `iterations/2026-07-06-prism-rl-lightweight-benchmarks.md` | Record of the PRISM-RL lightweight benchmark iteration. |
| `iterations/2026-07-06-paper-and-presentation-deliverables.md` | Record of the current paper and PowerPoint deliverable build. |
| `artifacts/README.md` | Organization rules for future generated artifacts. |
| `experiments/README.md` | Organization rules for future experiment packages. |
| `references/README.md` | Organization rules for future literature artifacts. |
| `scripts/README.md` | Organization rules for future automation scripts. |
| `iterations/2026-07-06-git-repository-setup.md` | Record of Git repository initialization and artifact staging. |

## Maintenance Rule

When adding, removing, moving, or superseding a meaningful artifact, update this
index in the same iteration.
