# Experiments Directory

Use this directory for reproducible experiment packages.

Recommended layout:

```text
experiments/
  YYYY-MM-DD-short-slug/
    README.md
    config.*
    run.*
    results/
    artifacts/
    logs/
```

Each experiment `README.md` should include:

- Objective and hypothesis.
- Task or dataset definition.
- Algorithm/code version.
- Parameters and random seeds.
- Environment details.
- Exact run command or notebook procedure.
- Output locations.
- Result summary and interpretation.
- Known limitations.

Record each experiment in `docs/EXPERIMENT_LOG.md`.
