# PRISM Experiment Log

Last updated: 2026-07-06

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
