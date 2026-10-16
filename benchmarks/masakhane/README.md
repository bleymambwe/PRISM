# Masakhane handoff benchmark

This directory is a contribution template, not a fabricated benchmark. A
Masakhane-ready PRISM study must be completed with an African-language
collaborator and an openly licensed task or an explicit data-use agreement.

## Required contents

- language pair/task and community or native-speaker collaborators;
- dataset provenance, licence, consent and train/dev/test split;
- frozen preprocessing and evaluator version;
- baseline model and PRISM ordering/search configuration;
- deterministic seeds, budgets and raw per-example results;
- human evaluation where automatic scoring is not sufficient;
- README describing limitations, language coverage and harms/risks.

For a translation benchmark, add the test source/target files, preprocessing
files, vocabulary/configuration, model/checkpoint location and train/dev/test
metrics. Do not commit restricted data or credentials.

Suggested layout:

```text
benchmarks/masakhane/<language-or-task>/
  README.md
  metadata.yaml
  data_card.md
  run.py
  results/
```

The next step is community review through Masakhane before submitting a PR;
PRISM should not represent an English GSM8K result as a Masakhane contribution.
