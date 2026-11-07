# Validation artifacts

These scripts call the same prompt/sample builders and numeric grader as the
registered Inspect tasks, using direct provider APIs because Inspect's provider
adapter stalled during these local runs. They are diagnostic reproductions, not
Inspect `.eval` logs and not complete full-size validations.

## Checked-in run coverage

| File | Recorded samples | Coverage | Notes |
| --- | ---: | --- | --- |
| `cells_gsm8k_exhaustive_gpt-4o-mini.csv` | 107 | 4 of 720 orderings, at most 32 questions per ordering | Partial OpenAI direct-API run. |
| `gemini_replication_cells.csv` | 385 | 4 of 720 orderings, at most 32 questions per ordering | Partial Gemini 2.5 Flash-Lite run; 379 responses ended with `STOP`, 6 with `MAX_TOKENS`. |

The exhaustive GSM8K task has 23,040 samples (720 orderings x 32 questions).
Neither CSV is a full-size validation run. The scripts are resumable and can be
used to continue a run; provide the relevant API key through the environment as
shown in each script's module docstring. Do not commit credentials.

`openai_direct.py` can also produce GSM8K exhaustive and MATH-500 cell files,
but those output files are not part of this snapshot.

## Corrected question-31 analysis

The registered GSM8K task intentionally keeps the frozen source label `2280`
for question 31, documented under Known issues in the parent README. The
separate `experiments/iteration-09` analysis reruns the landscape with the
arithmetic-correct answer `2180` to measure the label's effect. Its complete
720-ordering analysis is retained there; it does not change the registered
Inspect task or the historical PR pins.
