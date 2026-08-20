# Reproducibility guide

PRISM separates software verification from scientific-result reproduction.
This prevents a paid or obsolete external service from becoming a prerequisite
for checking the package.

## Tier 1: package verification

CPU-only, deterministic, no network after installation:

```bash
python -m pip install -e ".[dev]"
ruff check src tests tools prism-research/core
ruff format --check src tests tools prism-research/core
mypy src/prism_search
pytest --cov=prism_search --cov-report=term-missing
python -m build
twine check dist/*
```

## Tier 2: free baseline experiments

From the repository root:

```bash
python prism-research/experiments/scaling_experiment.py
python prism-research/experiments/rl_ordering_experiment.py
python prism-research/experiments/validate_toy_problems.py  # optional torch
```

Each archived `experiments/iteration-*` directory contains its runner and
committed results. Run only the study being checked, record Python and
dependency versions, and compare regenerated files outside the tracked result
directory before accepting differences.

## Tier 3: frozen external-model studies

Iterations 9, 11, 17, 19-crossfamily, 23, and 24 used external model APIs.
Their committed answer caches are the primary reproducibility artifacts. API
reruns can change because models, pricing, and service behavior are external.
Never commit credentials; apply a strict spend cap; record provider, model,
date, seed, decoding settings, question-pool hash, and cache provenance.

## Minimum result record

Every new study should preserve:

- immutable input/configuration and seed;
- canonical permutation key and evaluator version;
- one row per distinct evaluation or an append-only response cache;
- pre-flight forecast written before the main executor outcome;
- baseline under the same distinct-evaluation budget;
- uncertainty, ties, censored runs, null results, and failures;
- runtime, hardware, dependency lock or environment export, and cost where
  external services are used.

