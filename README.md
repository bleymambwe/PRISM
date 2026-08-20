# PRISM — code and reproducibility artifacts

Companion repository for **PRISM: A Predictive Protocol for Permutation Optimization via
Landscape Diagnostics** — [arXiv:2608.08344](https://arxiv.org/abs/2608.08344).

PRISM measures a fitness landscape *before* choosing a search strategy. It uses inexpensive
landscape diagnostics — one-step move autocorrelation and fitness–distance correlation — to
predict useful mutation operators, identify when structured search is likely to beat random
sampling, and detect regimes where search provides little advantage.

The paper positions PRISM **not as a universally superior optimizer**, but as a framework for
deciding *whether* permutation search is worth running, *which* representation and operator to
use, and *when* simpler alternatives are preferable.

## What is here

| Path | Contents |
| --- | --- |
| `src/prism_search/` | The installable package: mutation operators, operator-aligned permutation distances, landscape diagnostics and the search executor. One required dependency (NumPy). |
| `evals/instruction_order/` | An [Inspect AI](https://inspect.aisi.org.uk/) eval implementing the paper's instruction-ordering landscape, where 720 orderings of six fixed reasoning modules span 6.3%–96.9% accuracy on GSM8K. |
| `tests/` | Deterministic unit and regression tests for the package and the eval. |
| `experiments/` | 23 pre-registered experiment iterations. Each carries a `PLAN.md` stating the hypothesis before the run, `hypotheses.json`, the runner code, and `results/` including per-run token and cost accounting. |
| `docs/` | The research record: `EXPERIMENT_LOG.md`, `DECISION_LOG.md`, `LITERATURE_LOG.md`, `RISK_REGISTER.md`, `ITERATION_TEMPLATE.md`, `ARTIFACT_INDEX.md`, and the July 2026 experiments audit report. |
| `scripts/` | Figure generation, dashboard and report build scripts. |
| `deliverables/book_figures/` | Generated figures. |
| `deliverables/PRISM_Framework_Research_Paper.md` | Long-form framework write-up. |
| `GNGN_Toy_Problems.ipynb` | Early toy-problem convergence notebook (XOR, OR, AND, 3-bit parity, polynomial regression). |

Experiments cover synthetic permutation landscapes, neural architecture benchmarks, scientific
machine-learning pipelines, LLM instruction ordering, cross-model transfer, and prompt-optimizer
baselines.

## Installing the package

PRISM requires Python 3.10 or newer.

```bash
git clone https://github.com/bleymambwe/PRISM.git
cd PRISM
python -m pip install -e .
```

```python
from prism_search import PRISM, preflight

def fixed_points(ordering):
    return sum(index == value for index, value in enumerate(ordering))

diagnostics = preflight(n=8, fitness_fn=fixed_points, seed=7)
print(diagnostics.recommendation, diagnostics.selected_operator)
```

The pre-flight thresholds are empirical operating bands, not universal laws.
Report them with the seed, probe sizes, evaluator version, reference type and
uncertainty. See [`docs/quickstart.md`](docs/quickstart.md) and
[`docs/api.md`](docs/api.md).

## Running the instruction-ordering eval

```bash
python -m pip install -e ".[eval]"
inspect eval evals/instruction_order/task.py@instruction_order_gsm8k --model openai/gpt-4o-mini
```

It reports spread across orderings rather than a single accuracy — the headline
figure is `worst_ordering_accuracy`, what you get when a reasonable prompt
happens to use a bad order. See
[`evals/instruction_order/README.md`](evals/instruction_order/README.md).

## How the experiments are organised

Each iteration is pre-registered: the plan and hypotheses are written and committed **before**
the run, and the result is recorded afterwards whether or not it supported the hypothesis.
Iteration 23 is labelled a mixed, honest result in its own commit message — that is deliberate.
`docs/EXPERIMENT_LOG.md` is the index; `docs/DECISION_LOG.md` records why each direction was
taken or dropped.

Runs that call hosted models read their API key at runtime from Google Secret Manager by name
(`--secret=OPENROUTER_API_KEY`). No credentials are stored in this repository.

## Reproducing a run

```bash
git clone https://github.com/bleymambwe/PRISM.git
cd PRISM
# each iteration is self-contained; read its PLAN.md first
python experiments/iteration-24-prompt-optimizer-baselines/prompt_optimizer_baselines.py
```

Iterations that query hosted LLMs need an `OPENROUTER_API_KEY` available to the mechanism named
in that iteration's runner, and will incur cost. Each `PLAN.md` states the cost cap that was set
before the run, and `results/token_usage.csv` records what was actually spent.

## Scope

This repository holds the code and reproducibility artifacts. Working notes, drafts, slide decks,
narrated audio and third-party reading material live in a separate private workspace and are
deliberately not published here. See [`REPO_SCOPE.md`](REPO_SCOPE.md) for the rule and the reasoning.

## Citation

```bibtex
@misc{mambwe2026prism,
  title  = {PRISM: A Predictive Protocol for Permutation Optimization via Landscape Diagnostics},
  author = {Mambwe, Blessings},
  year   = {2026},
  eprint = {2608.08344},
  archivePrefix = {arXiv},
  primaryClass  = {cs.LG}
}
```

## License

Two licences, split by what the material is:

| Material | Licence |
| --- | --- |
| Software — `src/prism_search/`, `evals/`, `tests/`, `scripts/`, `.github/` | [MIT](LICENSE) |
| Research artifacts — `experiments/`, `docs/`, `deliverables/book_figures/`, `GNGN_Toy_Problems.ipynb` | [CC BY 4.0](LICENSE-ARTIFACTS) |

The artifact licence matches the release statement in
[arXiv:2608.08344](https://arxiv.org/abs/2608.08344), which places the seeded
scripts, evaluation caches, frozen question pools, result tables and forecast
record under CC BY 4.0. The code carries MIT instead because CC BY 4.0 is not an
OSI-approved software licence.

© 2026 Blessings Mambwe.
