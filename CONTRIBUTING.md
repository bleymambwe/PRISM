# Contributing to PRISM

PRISM welcomes bug reports, documentation fixes, reproducibility reports, new
permutation distances, and carefully benchmarked search operators.

## Before opening a change

Use the public issue tracker for bugs and feature proposals. For behavior
changes, describe the research use case, the decision being changed, expected
failure modes, and how the change will be tested. Please do not include API
keys, model responses containing private data, or restricted benchmark data.

## Development setup

```bash
python -m venv .venv
# PowerShell: .venv\Scripts\Activate.ps1
# POSIX: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
pre-commit install
```

Before submitting a pull request, run:

```bash
ruff check .
ruff format --check .
mypy src/prism_search
pytest --cov=prism_search --cov-report=term-missing
python -m build
twine check dist/*
```

Tests must be deterministic and should finish without network access. New
numerical behavior needs a focused unit test plus, when scientifically
relevant, a small regression fixture. Large or paid experiments belong in a
separately documented workflow and must not run in CI.

## Review and attribution

Maintainers review correctness, API compatibility, documentation, tests,
licensing, and research claims. Contributions are recorded through Git history
and the changelog. Substantial scholarly contributions may also qualify for
paper authorship under the project governance policy.

By contributing, you agree that your contribution is licensed under the BSD
3-Clause License and that you will follow the Code of Conduct.

