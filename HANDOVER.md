# PRISM ecosystem handover

Date: 2026-10-15

## Completed in this handover

- Added an optional Nevergrad bridge at
  `src/prism_search/integrations/nevergrad.py`.
- Added SAELens-compatible evaluator and pre-flight hooks at
  `src/prism_search/integrations/saelens.py` without adding a hard SAELens
  dependency.
- Added integration documentation under `docs/integrations/`.
- Added a Masakhane contribution template at
  `benchmarks/masakhane/README.md`.
- Added unit coverage for the SAELens boundary in `tests/test_integrations.py`.
- Kept the required runtime dependency set unchanged: NumPy only.

## Validation

Run:

```bash
python -m pytest -q
python -m build
```

Validation completed in this workspace: `python -m pytest tests evals -q`
reported **125 passed**, and `python -m compileall -q src tests` completed
without errors. The wheel build could not be completed locally because the
environment does not currently have the `wheel` build dependency installed;
the isolated build created the source distribution before that environment
timed out. Install the dev/build extra in CI before publishing.

The Nevergrad path requires the optional extra:

```bash
python -m pip install -e ".[nevergrad]"
```

Nevergrad was not installed in this workspace because the package resolver was
offline and the dependency was not cached. The optional adapter is therefore
compile-checked but not runtime-executed here.

## External work still required

### Nevergrad

Run a matched benchmark against Nevergrad's existing permutation examples,
decide whether PRISM should be proposed as a native optimizer or a benchmark
adapter, then open an upstream issue/PR. The upstream maintainers will require
their test/lint/type checks, reproducibility expectations and CLA.

### SAELens

Supply a real SAELens experiment using `preflight_sae`: frozen model and data,
an explicitly defined orderable feature/intervention space, baseline
comparisons, results, and a maintainer-reviewed example. The current hook is
API-stable scaffolding, not evidence of a completed SAELens study.

### Masakhane

Choose one African-language task with a community/native-speaker collaborator,
complete the benchmark template, document licensing/consent and limitations,
release reproducible results, and request community review before submitting.

## Important interpretation

PRISM is currently a permutation-landscape diagnostic and search package. The
three integrations are intentionally staged differently: Nevergrad has a
software adapter, SAELens has a callback boundary, and Masakhane has a
research contribution template. No external project should be told that its
integration is merged until its maintainers accept the corresponding upstream
contribution.
