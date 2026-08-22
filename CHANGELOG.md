# Changelog

All notable changes to PRISM will be documented here. The project follows
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.0] - 2026-08-22

### Added

- Installable `prism-search` Python package.
- Tested pre-flight diagnostics, aligned permutation distances, and a
  distinct-evaluation-budget executor.
- JOSS paper, contribution guidance, governance, support, security, and
  reproducibility documentation.
- Continuous integration for supported Python versions and paper validation.

### Changed

- Retained `prism-research/core/prism.py` as a compatibility import for the
  original experiment scripts.

### Fixed

- `.zenodo.json` incorrectly declared BSD-3-Clause. The software has always
  been MIT (see `LICENSE`, `CITATION.cff`, `pyproject.toml`); corrected the
  metadata to match.

