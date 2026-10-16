# SAELens integration

PRISM does not import SAELens internals. Instead, it provides a stable callback
boundary so SAELens experiments can define the expensive evaluator while PRISM
owns permutation validation and landscape diagnostics.

```python
from prism_search.integrations.saelens import preflight_sae

def score_feature_order(ordering):
    # Run the SAELens hook/ablation/reconstruction experiment here.
    return evaluate_order_with_saelens(ordering)

result = preflight_sae(8, score_feature_order, seed=7)
```

## Runnable example

`examples/saelens_feature_ordering.py` runs the callback boundary end to end.
The default `--mode synthetic` uses an order-dependent toy evaluator and needs
only NumPy. `--mode saelens` (requires `sae-lens` and `transformer-lens`)
orders cumulative ablation of top SAE features on gpt2-small, but that path is
untested here: SAELens was not installed in the development environment, and
the release/hook names may need adjusting for your SAELens version. The
synthetic run shows only that the plumbing works, not a research result.

The remaining research requirement is a real case study: choose one SAE
objective, define what is being ordered, freeze model/checkpoint/data versions,
and compare PRISM's recommendation with random ordering and at least one
SAELens-native baseline. Do not claim SAELens integration is complete until
that case study and a maintainer-reviewed example exist.
