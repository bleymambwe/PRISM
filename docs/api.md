# API guide

## Public surface

`prism_search.preflight`
: Measures one-move autocorrelation for candidate operators, aligns FDC to the
  chosen move geometry, records variance and top-tie density, and returns a
  conservative recommendation.

`prism_search.PRISM.search`
: Runs a cached, steady-state evolutionary executor under a maximum number of
  distinct fitness evaluations.

`prism_search.PRISM.evolve`
: Runs the original generation-based executor for backward-compatible research
  reproduction.

`prism_search.fitness_distance_correlation`
: Computes FDC to the nearest exact or proxy reference under a named or custom
  distance.

`cayley_distance`, `ulam_distance`, `kendall_tau_distance`
: Distances aligned respectively to swap, insert/precedence, and adjacent-order
  geometry.

## Reference

::: prism_search

::: prism_search.core.PRISM
    options:
      show_source: false

::: prism_search.results.PreflightResult

