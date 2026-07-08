# PRISM Artifact Index

Last updated: 2026-07-08

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

## Iteration 4 (2026-07-06): Operator-Portfolio PRISM

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `iterations/2026-07-06-iteration-04-operator-portfolio.md` | Iteration-4 lab log: portfolio/adaptive design, results, D8. | Complete. |
| `experiments/iteration-04/portfolio_study.py` | Budgeted resumable runner for Experiment F. | Protocol identical to Experiment C for baseline merging. |
| `experiments/iteration-04/analyze_portfolio.py` | Merges Experiment F with Iteration-3 baselines; overhead ratios, adaptive weights, figure. | Complete. |
| `experiments/iteration-04/results/portfolio_results.csv` | Per-run results incl. evaluations and final operator weights. | 540 rows. |
| `experiments/iteration-04/results/portfolio_summary.csv`, `portfolio_vs_fixed.txt`, `adaptive_weights.txt`, `portfolio_study.png` | Aggregates, comparison table, learned weights, figure. | Complete. |
| `prism-research/core/prism.py` (updated) | Adds `mutation="portfolio"` and `mutation="adaptive"`; fixed-operator paths bit-for-bit unchanged. | Compare via `git diff iteration-03..iteration-04`. |

## Iteration 5 (2026-07-06): Paper Update, Benchmark v4, Visual Research Log

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `iterations/2026-07-06-iteration-05-paper-and-benchmark-v4.md` | Iteration-5 lab log. | Complete. |
| `prism-research/benchmarks/toy_problems_v4.py` | Canonical toy benchmarks (D9): residual blocks, permutation-seeded init, deterministic k=3-trial fitness. | Supersedes v2 benchmarks for forward work. |
| `experiments/iteration-05/benchmark_v4_study.py` | Experiment G runner: determinism check, 120-permutation enumeration, cached PRISM search. | Budgeted/resumable. |
| `experiments/iteration-05/results/v4_landscape.csv`, `v4_search.csv`, `v4_summary.txt` | Full enumerated landscapes, per-seed search results, summary. | Complete. |
| `deliverables/PRISM_Framework_Research_Paper.md` / `.pdf` | Paper updated with Iterations 3-5 (operator matching, portfolio, v4 benchmarks); PDF rebuilt. | Current through Iteration 5. |
| `deliverables/PRISM_Iteration_Journey.html` | Self-contained animated visual research log (iterations 2-5): charts, hypothesis ledger, light/dark, reduced-motion. | Browser-verified both themes; also published as a claude.ai artifact. |

## Iteration 6 (2026-07-06/07): Scale-Up, Decks, Audio, Notion

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `iterations/2026-07-06-iteration-06-scaleup-and-communication.md` | Iteration-6 lab log. | Complete. |
| `experiments/iteration-06/v4_scaleup.py` | Experiment H runner: n=6 enumeration + search, n=7 PRISM-vs-random regret. | Budgeted/resumable. |
| `experiments/iteration-06/results/` | n6_landscape.csv (720 orderings), n6_search.csv, n7_search.csv, scaleup_summary.txt. | See iteration note for results. |
| `prism-research/benchmarks/toy_problems_v4.py` (updated) | Block pool extended to 8 types (indices 0-4 unchanged); `make_xor_fitness(k_trials)` factory. | n=5 results unaffected. |
| `scripts/build_versions_deck.py` → `deliverables/PRISM_Versions_Deck.pptx` | Versions deck: one chapter per git tag iteration-02..06, timeline, hypothesis ledger. | New. |
| `deliverables/PRISM_Framework_Presentation.pptx` (rebuilt) | Main deck refreshed with iterations 3-5 results. | Slides updated in build script. |
| `deliverables/audio/scripts/lesson-{1..6}-*.txt` | Lesson scripts: simple, student, practitioner, research, critics, full paper narration. | Committed. |
| `deliverables/audio/lesson-{1..6}-*.mp3` | Generated audio (~33 MB, OpenAI TTS tts-1, voices nova/onyx). | Local artifacts; regenerate via `scripts/generate_audio_lessons.py` (key from GCP Secret Manager). |
| Notion: documentation page + PRISM Research Tracker | 2026-07 research-status section; tracker DB with formula Progress, 21 rows, 5 views. | https://app.notion.com/p/2ccc1245c0b3812396d7dadfb28e48fd |
| `research-opportunity-mapping-2026-07-06/data/cloud_cost_analysis.csv` + `.md` | Cloud cost analysis: measured cost of iterations 2-6 on GCP (~$1 on-demand; $0.45 actually spent on TTS) + planned-benchmark costs/durations/services with cheapest-alternative column. | Prices verified 2026-07-07 (us-central1 list). |

## Team Briefing (2026-07-08)

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `deliverables/PRISM_TEAM_BRIEFING.txt` | Single consolidated plain-text reference: documentation map, algorithm at submission (loop, operators, variants, protocol, theory incl. Appendix B), every experiment A-N with what/how/result/meaning/comparison/threats, decisions D8-D18, related-work positioning, costs, reproduction, open items. | Keep in sync at iteration close-out; numbers only from committed CSVs. |

## Iteration 18 (2026-07-08): Research Loop Selection

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `iterations/2026-07-08-iteration-18-research-loop-selection.md` | Literature refresh, 0-10 hypothesis scoring, hardware/budget gate, D20 research direction selection, and Experiment R write-up. | Complete. |
| `experiments/iteration-18/transfer_guided_selection.py` | Cached experiment testing whether n=6 LLM position effects guide low-budget n=8 evaluation. | Complete; no API calls. |
| `experiments/iteration-18/results/transfer_guided_selection.txt` | Experiment R output: source-score correlation and guided-vs-random budget table. | Complete. |

## The PRISM Book (2026-07-07)

| Path | Purpose | Status / Notes |
| --- | --- | --- |
| `deliverables/PRISM_Book.pdf` | Illustrated multi-level book (14 pp): undergrad "in plain terms" boxes + rigorous bodies + "for researchers" notes; 8 figures generated from committed experiment CSVs; covers iterations 2-9. | Rebuild: `python scripts/build_book_figures.py && python scripts/build_prism_book.py`. |
| `scripts/build_book_figures.py` | All book figures from real data (concept, loop, scaling, operators, portfolio, landscapes, locality heatmap, LLM position effects). | `deliverables/book_figures/*.png`. |
| `scripts/build_prism_book.py` | Book layout/content (reportlab; cover, TOC, 9 chapters, theorem boxes, experiment ledger appendix). | Complete. |

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
