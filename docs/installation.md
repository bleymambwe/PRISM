# Installation

## Supported Python

PRISM supports CPython 3.10 through 3.13. The runtime dependency is Numpy. Use
an isolated environment so optional research dependencies do not affect other
projects.

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Until a package index release exists, install a tagged GitHub checkout rather
than an unpinned branch when reproducibility matters.

## Optional groups

```bash
python -m pip install -e ".[plot]"  # plotting for legacy studies
python -m pip install -e ".[test]"  # tests and coverage
python -m pip install -e ".[dev]"   # full contributor toolchain
python -m pip install -e ".[docs]"  # local documentation site
```

Verify the installation:

```bash
python -c "import prism_search; print(prism_search.__version__)"
pytest
```

