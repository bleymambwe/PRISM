# PRISM documentation

PRISM is a Python package for permutation-valued research decisions. Its main
contribution is a pre-flight protocol: measure local fitness preservation,
global guidance, evaluator variance, and tie density before spending the main
optimization budget. The result is an auditable recommendation to use
evolution, uniform sampling, avoid local search, or improve the evaluator.

The package is appropriate when the components are fixed and only their order
changes. It does not discover new components, fit neural-network weights, or
guarantee that its empirical thresholds transfer to an unvalidated domain.

Start with [installation](installation.md), then follow the [quick
start](quickstart.md). Researchers reproducing the paper should use the
[reproducibility guide](reproducibility.md).

