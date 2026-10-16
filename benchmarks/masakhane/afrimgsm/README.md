# AfriMGSM few-shot ordering (draft, no results)

Does the order of the 8 AfriMGSM exemplars change a model's accuracy, and can
PRISM find a good order within a small budget?

**Status:** scaffold only. No model has been run; `results/` is empty. Do not
describe this as a Masakhane contribution until a collaborator and the
community have reviewed it (see `data_card.md`).

## Run

```bash
pip install datasets
# 1. offline plumbing check; the dry-run backend is a stub, NOT a model
python run.py --language swa --backend dry-run --budget 40 --seeds 0
# 2. real model: any importable callable  fn(prompt: str) -> str
python run.py --language swa --backend mypkg.mymodel:generate --budget 200 --seeds 0 1 2 3 4
```

Per (language, seed) it runs a PRISM pre-flight, then a budgeted search, and
finally scores the best order, the identity order, and a random-order mean on
the held-out half. Every evaluation is appended to
`results/<lang>_<backend>_cache.jsonl`, so an interrupted run resumes without
re-querying the model (the search is deterministic given the seed and cache).
Output: `results/<lang>_<backend>_summary.json`.

Model name, decoding settings and checkpoint must be recorded in `metadata.yaml`
before results are shared.
