---
title: 'PRISM: Auditable landscape diagnostics for permutation-valued research decisions'
tags:
  - Python
  - evolutionary computation
  - fitness landscapes
  - permutation optimization
  - reproducible research
authors:
  - name: Blessings Mambwe
    affiliation: 1
    corresponding: true
affiliations:
  - name: ML Collective
    index: 1
date: 13 August 2026
bibliography: paper.bib
---

# Summary

Many research workflows contain a fixed set of components whose order is not
fixed: compiler passes, data transformations, scientific-pipeline stages,
neural modules, or reasoning instructions. Trying a few plausible orderings can
miss large performance differences, but running an optimizer is not always
better than sampling. `PRISM` is a Python package that measures the landscape
before committing the main evaluation budget. Its seeded *pre-flight* estimates
whether one-step changes preserve fitness, whether better candidates tend to be
closer to the best known ordering, whether the evaluator distinguishes
candidates, and whether many candidates tie at the top. It then records a
conservative recommendation to use structured evolution, uniform sampling,
avoid local search, or improve the evaluator.

PRISM also provides permutation distances aligned to different neighborhood
operators and an evolutionary executor whose budget counts distinct candidates
rather than repeated proposals. The runtime package has one required dependency
(Numpy), supports Python 3.10--3.13, and is accompanied by deterministic tests,
examples, API documentation, and archived experiment records.

# Statement of need

Permutation optimization appears in several research communities, but the
choice of optimizer and neighborhood is often made before researchers measure
whether the objective contains exploitable structure. This is risky when one
fitness call involves a simulation or external model, and it can make negative
results hard to interpret: search may fail because the landscape is locally
uninformative, globally deceptive, tied at evaluator resolution, or paired with
the wrong move geometry.

PRISM makes that decision explicit and falsifiable. For each proposed move it
estimates the correlation between the fitness of sampled parents and one-move
children. It then computes fitness--distance correlation (FDC) using a distance
matched to the selected move: Cayley distance for arbitrary swaps, Ulam distance
for insert/precedence moves, and Kendall distance for pair-order structure.
Exact optima may be supplied; otherwise the best frozen pilot candidates are
clearly labelled as proxies. Repeated candidates are cached, so diagnostic and
search reports expose both distinct evaluations and cache hits.

The target users are researchers who have a deterministic scalar evaluator and
a fixed set of uniquely identified components. PRISM is not intended for
continuous optimization, component discovery, or uncritical use of its
empirical decision bands in a new domain. The pre-flight should be registered
before the main run, compared with an equal-budget baseline, and retained when
its forecast is wrong [@mambwe2026prism].

# State of the field

General scientific optimization is available through SciPy [@virtanen2020],
while DEAP [@fortin2012], pymoo [@blank2020], and Nevergrad [@rapin2018] provide
extensible evolutionary or derivative-free algorithms. Optuna focuses on
efficient hyperparameter optimization [@akiba2019]. Chips-n-Salsa supplies a
rich Java toolkit for stochastic local search, including permutation operators
and reproducibility controls [@cicirello2022]. These projects are appropriate
when the optimization method is already chosen or when their broader algorithm
catalogue is required.

PRISM was built as a separate, small package because its scholarly unit is the
*pre-optimization decision protocol*, not another general optimizer catalogue.
It couples local autocorrelation, aligned FDC, evaluator-resolution signals,
explicit proxy provenance, and a forecast record in one result object. Existing
general libraries can still be used as downstream executors; PRISM's diagnosis
does not require replacing them. The included executor exists to make the
published distinct-evaluation protocol reproducible and to provide a controlled
reference implementation.

# Software design

The package separates four concerns: mutation operators, permutation distances,
landscape diagnostics, and execution. Operators mutate plain integer lists so a
fitness function remains independent of a framework-specific individual type.
Distance functions validate that inputs contain the same unique elements.
Diagnostics accept an arbitrary callable, use a local immutable-key cache, and
return a frozen structured record rather than writing hidden global state.
Execution offers two intentionally distinct interfaces: `search` is a
steady-state, cached algorithm for real distinct-evaluation budgets, while
`evolve` preserves the generational behavior needed to reproduce the original
studies.

This boundary avoids coupling scientific measurement to one evolutionary
library, keeps the core dependency surface small, and makes each numerical
choice unit-testable. Input validation rejects invalid populations, mutation
modes, sample sizes, and non-finite fitness values. Seeds are passed to Numpy's
local generator rather than global random state. Empirical thresholds are
parameters with documented defaults, so domain-specific calibration does not
require a fork.

# Research impact statement

PRISM has been used by its developer across synthetic landscapes, neural toy
problems, scientific pipelines, reinforcement-learning ordering surfaces,
instruction-order studies, and tabular neural-architecture slices. The
associated preprint reports both successful and failed forecasts and publishes
the runners, response caches, and result tables used in those analyses
[@mambwe2026prism]. The software therefore has demonstrated use in an active
research program, but external adoption has not yet been demonstrated. Public
issues, releases, independent reproductions, and downstream studies will be
tracked before JOSS submission rather than presented as anticipated impact.

# AI usage disclosure

OpenAI Codex, a GPT-5-family coding agent whose exact serving revision was not
exposed, assisted on 13 August 2026 with repository auditing, refactoring, test
scaffolding, documentation, and drafting this manuscript. BrowsePilot was used
to extract public JOSS guidance and paper pages. The submitting author must
review, edit, and validate every assisted output, confirm that the core problem
framing and design decisions are human-owned, and replace this final sentence
with that confirmation before submission. The authors remain responsible for
accuracy, originality, licensing, and ethical and legal compliance.

# Acknowledgements

The author thanks Jake Beck for manuscript feedback and the ML Collective
research community. No external funding supported this software work.

# References

