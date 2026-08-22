# Instruction-Order Sensitivity

An [Inspect AI](https://inspect.aisi.org.uk/) eval that measures how much a
model's mathematical accuracy depends on the **order** of a fixed set of
reasoning instructions whose wording never changes.

Implements the language-model instruction-ordering landscape of
[arXiv:2608.08344](https://doi.org/10.48550/arXiv.2608.08344), where 720
orderings of six fixed reasoning modules spanned **6.3% to 96.9%** accuracy on a
32-question GSM8K subset — a 90.6-point swing from presentation order alone.

## What it measures

Every sample is one *(ordering, question)* pair. A single mean accuracy would
hide the effect entirely, so the scorer reports statistics computed **across
orderings**:

| Metric | Reads as |
| --- | --- |
| `worst_ordering_accuracy` | What you get when you write a reasonable prompt and pick a bad order. **Read this one first.** |
| `ordering_std` | Population SD of per-ordering accuracy — the headline sensitivity number. |
| `ordering_range` | Best minus worst. |
| `best_ordering_accuracy` | The ceiling that ordering search could reach. |
| `ordering_mean` | Mean accuracy, weighting each ordering equally. |
| `ordering_count` | How many orderings contributed (audit for partial runs). |
| `accuracy` / `stderr` | Flat sample-grid statistics, for reference only. |

## Tasks

| Task | Modules | Questions | Default calls |
| --- | --- | --- | --- |
| `instruction_order_gsm8k` | 6 | 32 (frozen subset) | 50 × 32 = **1,600** |
| `instruction_order_gsm8k_exhaustive` | 6 | 32 | 720 × 32 = **23,040** |
| `instruction_order_math500` | 8 | 100 (levels 3–5) | 50 × 100 = **5,000** |

## Usage

```bash
uv sync --extra eval

# Required: task.py imports evals.instruction_order.* as an absolute package.
# pytest gets the repo root on sys.path from pyproject's `pythonpath` setting;
# `inspect eval`'s module loader doesn't add it, so set this explicitly or the
# run fails with `ModuleNotFoundError: No module named 'evals'`.
export PYTHONPATH=.

# Cheap default: 50 random orderings.
uv run inspect eval evals/instruction_order/task.py@instruction_order_gsm8k \
    --model openai/gpt-4o-mini

# Fewer orderings, spread out by PRISM's operator-aligned distance so a small
# budget still covers the space instead of clustering.
uv run inspect eval evals/instruction_order/task.py@instruction_order_gsm8k \
    --model openai/gpt-4o-mini -T orderings=12 -T design=diverse -T operator=swap

# The paper's full replication. ~23,000 calls — opt in knowingly.
uv run inspect eval evals/instruction_order/task.py@instruction_order_gsm8k_exhaustive \
    --model openai/gpt-4o-mini
```

MATH-500 additionally needs `uv sync --extra eval-math500` for `datasets`.

## Design decisions

**Temperature 0, always.** Sampling noise and ordering effects are the same
magnitude in these landscapes; anything above 0 makes them inseparable.

**A frozen, dependency-free grader.** `grading.py` does exact matching on
canonical numeric forms. A model-graded scorer would put a second order-sensitive
system in the measurement path, and a symbolic-equivalence library would make
scores drift across its own versions. Question pools are pre-filtered to the
answer forms this grader handles exactly (`SIMPLE_ANSWER`).

**Two prompt wrappers.** GSM8K relies on the `ANSWER` module alone (Experiment
K); MATH-500 adds a `\boxed{}` request (Experiment S). They differ because the
published landscapes differ. The grader accepts both conventions regardless.

**Frozen module wording.** `modules.py` is the experimental control — the only
thing that varies between conditions is order. Editing the strings breaks
comparability with the published landscapes and requires a task-version bump.

**Distinct orderings by construction.** Duplicate orderings would silently
reduce the number of conditions and inflate apparent agreement between them.

## Relationship to `prism_search`

`orderings.py` uses PRISM's operator-aligned permutation distances (Cayley for
swaps, Ulam for insert/precedence, Kendall for pair order) to build the
`diverse` design. That is the same distance alignment the paper's diagnostics
were computed under; using a mismatched pair is the documented way to get a
meaningless fitness-distance correlation.

The eval does **not** run PRISM's search. This measures a model's sensitivity;
it does not optimise against it.

## Register requirements

| Requirement | Status |
| --- | --- |
| `pyproject.toml` with a `[project]` table | Repo root. `task_path` may point anywhere inside the repo. |
| `inspect_ai` declared as a dependency | `[project.optional-dependencies] eval`. Kept optional so `prism_search` keeps its single required dependency (numpy), which the JOSS paper states. Install with `uv sync --extra eval`; that is also the `evaluation_report` command. |
| Tasks use the `@task` decorator | `task.py` — three tasks. |
| External assets pinned | GSM8K subset is committed to `data/`, so the repo commit SHA pins it. MATH-500 pins HF revision `6e4ed1a2…`. |
| arXiv paper the eval implements | [arXiv:2608.08344](https://doi.org/10.48550/arXiv.2608.08344) — §"The Instruction-Ordering Landscape". |
| Public repo, submitter is a contributor | Yes. |

Status:

- [x] `instruction_order_gsm8k` submitted: [Register Eval Submission #2242](https://github.com/UKGovernmentBEIS/inspect_evals/issues/2242)
      (opened 2026-08-22), pinned to `103444da69839ed5be8d1fa2d388571ae2897bc2`.
- [x] `instruction_order_gsm8k_exhaustive` submitted: [#2245](https://github.com/UKGovernmentBEIS/inspect_evals/issues/2245)
      (opened 2026-08-22), pinned to `2d578d761f70e2fef3a381a6243265247b297759`.
- [x] `instruction_order_math500` submitted: [#2246](https://github.com/UKGovernmentBEIS/inspect_evals/issues/2246)
      (opened 2026-08-22), pinned to `2d578d761f70e2fef3a381a6243265247b297759`.
      No separate git tag was needed for any of the three — the register accepts a raw 40-char
      commit SHA directly.
- [ ] Validation sweep / `evaluation_report` — deliberately skipped. The live register process
      only recommends this, it isn't a submission field, and this machine hit a reproducible
      hang in Python's async HTTP stack against every model provider tried (OpenRouter and
      OpenAI directly) that wasn't worth chasing further here. Worth doing from a different
      environment if it's cheap to try.
- [ ] From here it's out of this repo's hands: each issue triggers a bot that validates the
      submission, derives register metadata, and opens a PR against `inspect_evals` for a
      maintainer to review and merge. Watch the three issues above for that PR link and for any
      requested changes.

## Tests

```bash
uv run pytest evals/
```

`tests/test_grading.py` carries the grader case list over unchanged from
`experiments/iteration-23-experiment-s/_grader_test.py`. If one of those flips,
the eval is no longer measuring what the paper measured.
