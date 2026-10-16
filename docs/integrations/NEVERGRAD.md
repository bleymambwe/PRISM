# Nevergrad integration

PRISM now exposes an optional bridge at `prism_search.integrations.nevergrad`.
It keeps PRISM's maximization convention while adapting the objective to
Nevergrad's minimization API and constraining candidates to permutations.

Install and run:

```bash
python -m pip install -e ".[nevergrad]"
```

```python
from prism_search.integrations.nevergrad import minimize

result = minimize(
    8,
    lambda ordering: sum(i == value for i, value in enumerate(ordering)),
    budget=100,
    optimizer="NGOpt",
    seed=7,
)
print(result.best_perm, result.best_fitness)
```

Before upstreaming to Nevergrad, run a matched benchmark against native
permutation-capable optimizers, report seeds/budgets/evaluation counts, and
open an issue proposing whether PRISM belongs as a native optimizer or as an
external benchmark adapter. Nevergrad's own test, typing, lint, reproducibility
and CLA requirements remain maintainer-side work.
