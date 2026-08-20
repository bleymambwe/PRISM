# Quick start

## Freeze the research decision

Define a permutation length and a deterministic fitness function. The function
must return a finite scalar and should not change its dataset, model, grader, or
randomness between candidates. If evaluation is stochastic, aggregate repeated
measurements outside PRISM and document the policy.

```python
from prism_search import preflight


def fitness(ordering):
    return sum(index == value for index, value in enumerate(ordering))


report = preflight(
    n=7,
    fitness_fn=fitness,
    pair_samples=100,
    landscape_samples=200,
    seed=2026,
)
print(report)
```

The pre-flight caches repeated orderings. `distinct_evaluations` is therefore a
fitness-call count, while `cache_hits` records reused candidates. If exact
optima are unknown, FDC uses the best frozen pilot candidates and labels them
`best_observed_proxy`.

## Interpret the recommendation

- `evolution`: FDC is materially negative under a distance aligned to the
  selected operator. Structured search may exploit global guidance.
- `uniform_sampling`: guidance is weak. Use a seeded random baseline as the
  method of record.
- `avoid_local_search`: FDC is strongly positive and improvement may point away
  from the target.
- `improve_evaluator`: the pilot has negligible variance; optimizer comparison
  is not meaningful yet.

These bands are empirical. Revalidate them in a new domain and preserve null or
incorrect forecasts in a forecast ledger.

## Run a distinct-budget search

```python
from prism_search import PRISM

optimizer = PRISM(
    n=7,
    fitness_fn=fitness,
    mutation=report.selected_operator,
    pop_size=20,
    seed=2026,
)
result = optimizer.search(max_evaluations=500)
```

Use `search` for expensive evaluations because no duplicate candidate consumes
the budget. `evolve` is retained to reproduce the original generational studies
and can reevaluate population members.

