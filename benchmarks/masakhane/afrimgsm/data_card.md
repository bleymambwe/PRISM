# Data card: AfriMGSM few-shot ordering

**Source:** `masakhane/afrimgsm` on Hugging Face
(<https://huggingface.co/datasets/masakhane/afrimgsm>), introduced in
IrokoBench (Adelani et al., arXiv:2406.03368). Translations of a subset of
GSM8K into African languages (plus English and French).

**Licence:** Apache-2.0 per the Hugging Face card (checked 2026-10-15). The
card lists no further restrictions. GSM8K upstream terms should also be checked
by the user before redistribution.

**Splits (per language config):** train = 8, test = 250. There is no
validation split. This benchmark therefore halves the test set
deterministically: one half drives the ordering search, the other half is
reported. Do not report accuracy on the search half.

**Fields:** `question`, `answer`, `answer_number`, `equation_solution`.

**Languages:** 19 configs on the viewer (see `metadata.yaml`); the card's
stated language count is inconsistent with the viewer.

**Not committed:** no data is stored here. `run.py` downloads at run time.

## Known limitations / risks
- Only 8 exemplars: the permutation space is small (40,320) and exhaustive
  search is feasible; PRISM's value is budget efficiency, to be demonstrated,
  not assumed.
- 125 report items per language gives wide confidence intervals.
- Machine-tested translation quality varies by language; native-speaker review
  of the exemplars and a sample of questions is TODO.
- Results from one model do not generalise to others.

## TODO (user)
- Identify a native-speaker collaborator per reported language and record
  consent/acknowledgement.
- Request Masakhane community review before any upstream PR.
