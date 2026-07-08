# PRISM Literature and Source Review Log

## Direct Reviews / Current Literature Refresh (Iteration 18)

### Ok and Lee 2026 - Lost in the Prompt Order
- Link: https://arxiv.org/html/2601.14152
- Reviewed: 2026-07-08 (direct abstract/excerpt).
- Research question: does prompt-order sensitivity already have a mechanistic
  explanation?
- Key claim: in MCQA, context-question-option ordering beats
  question-option-context because causal masking prevents earlier option tokens
  from attending to later context; interventions partly close the gap.
- Impact on PRISM: strengthens the LLM order-sensitivity framing but means a
  paper must distinguish PRISM's exhaustive instruction-order landscapes and
  transfer diagnostics from existing prompt-order mechanism work.

### Zhou et al. 2026 - The Curse of Verbalization
- Link: https://aclanthology.org/2026.findings-eacl.218.pdf
- Reviewed: 2026-07-08 (direct abstract/excerpt).
- Key claim: reasoning performance improves when information presentation
  order aligns with utilization order; verbalization flexibility correlates
  with reasoning ability across models.
- Impact on PRISM: aligns directly with the instruction-order transfer
  hypothesis; raises the bar for novelty by making order-alignment a known
  reasoning factor.

### Kimi Team 2025 - Kimi Linear
- Link: https://arxiv.org/pdf/2510.26692
- Reviewed: 2026-07-08 (direct abstract/excerpt).
- Key claim: a hybrid linear-attention architecture can outperform full
  attention while reducing KV cache usage and improving long-context
  throughput.
- Impact on PRISM: transformer-replacement framing is deprioritized; it would
  require large-scale training and hardware results beyond this workspace.

### Lahoti et al. 2026 - Mamba-3
- Link: https://www.arxiv.org/pdf/2603.15569
- Reviewed: 2026-07-08 (direct abstract/excerpt).
- Key claim: SSM-style sequence models continue to improve retrieval,
  state-tracking, and language modeling efficiency.
- Impact on PRISM: reinforces that architecture-replacement claims are crowded
  and not locally evidenced.

### Haverbeck et al. 2026 - The risk of KV cache compression
- Link: https://arxiv.org/html/2607.01520
- Reviewed: 2026-07-08 (direct abstract/excerpt).
- Key claim: KV compression can be characterized by minimax risk and intrinsic
  cache compressibility.
- Impact on PRISM: KV/memory optimization is plausible but already has strong
  theory competition.

### Pan 2026 - PolyKV; Yang et al. 2026 - CompilerKV
- Links: https://arxiv.org/html/2606.15157v1 and
  https://arxiv.org/html/2602.08686
- Reviewed: 2026-07-08 (direct abstracts/excerpts).
- Key claim: layer/head/risk-adaptive KV compression methods are improving
  LongBench performance under tight budgets.
- Impact on PRISM: PRISM as KV policy search is deferred unless GPU budget and
  strong baselines are available.

### Cicirello 2022 - Fitness Landscape Analysis of Permutation Problems
- Link: https://arxiv.org/abs/2208.11188
- Reviewed: 2026-07-08 (direct abstract/excerpt).
- Key claim: distance metrics classify permutation problem features and inform
  mutation-operator choice.
- Impact on PRISM: supports the operator/landscape diagnostic as a method
  component, but also limits novelty of the underlying operator-matching idea.

### Qiu and Miikkulainen 2023 - Shortest Edit Path Crossover
- Link: https://proceedings.mlr.press/v202/qiu23b.html
- Reviewed: 2026-07-08 (direct abstract/excerpt).
- Key claim: theory-driven crossover can address the permutation problem in
  black-box NAS and outperform mutation/RL baselines.
- Impact on PRISM: PRISM as generic NAS/operator search must be positioned
  carefully; instruction-order landscapes remain more distinctive locally.

Last updated: 2026-07-08 (Iteration 18 literature refresh)

## Direct Reviews (Iteration 10)

### Real et al. 2019 — Regularized Evolution for Image Classifier Architecture Search
- Local path: `research-opportunity-mapping-2026-07-06/papers/pdfs/05_*.pdf`
- Reviewed: 2026-07-07 (direct). Key mechanism: aging evolution —
  sample-tournament, mutate winner, append child, remove OLDEST.
- Impact on PRISM: tested in Experiment L; fixes premature convergence
  (48%→78% hit rate on parity n=7) but converges to random's level on
  weak-locality landscapes; elitist scheme stays faster on structured
  ones. Adopted into guideline D15. Theory caveat: breaks strict
  elitism, so the absorption theorem needs restating for aging mode.

### White et al. — BANANAS: Bayesian Optimization with Neural Architectures
- Local path: `papers/pdfs/14_*.pdf`. Reviewed: 2026-07-07 (direct).
- Key mechanism: predictor over encodings + acquisition over
  mutation-proposed candidates; encoding choice dominates.
- Impact: positional-one-hot ridge surrogate tested in Experiment L —
  mild win on the LLM landscape (matches its position-effect
  structure), inert on parity. Follow-up: precedence-pair encoding.

### Abdelfattah et al. 2021 — Zero-Cost Proxies for Lightweight NAS
- Local path: `papers/pdfs/15_*.pdf`. Reviewed: 2026-07-07 (direct).
- Key result: single-minibatch proxies preserve rank (τ≈0.82 on
  NAS-Bench-201), speeding all search families ~4×.
- Impact: mapped to PRISM as k=1 screen → k=3 confirm multi-fidelity
  gating for expensive neural fitness; relevant when GPU-scale
  benchmarks start; no-op on cached landscapes.

## Iteration-3 Entries

### Permutation Operator-Landscape Classification (via other.md synthesis)

- Citation: Cicirello (2022) permutation-type classification
  (A-permutations/absolute positions, R-permutations/adjacencies,
  P-permutations/precedences), as summarized in `other.md`
  "Permutation operators must match problem structure". Related primary
  sources named there: Rudolph (1994) elitist-GA convergence; Eiben et
  al. (1991) Markov-chain EA analysis.
- Link or local path: `other.md` (secondary summary; primary papers not
  yet independently retrieved).
- Reviewed by: Claude (Iteration 3).
- Date reviewed: 2026-07-06.
- Research question: should PRISM's mutation operator depend on the
  fitness landscape's permutation type?
- Key claims: swap/cycle mutation suits A-type, inversion (2-opt-like)
  suits R-type, insert suits P-type; crossover analogues PMX/CX, ERX,
  OX respectively.
- Methods relevant to PRISM: directly testable — PRISM v2 hard-coded
  swap mutation; Iteration-3 Experiment C tests the matched-operator
  prediction on typed synthetic landscapes.
- Evidence quality: secondary summary; classification is standard in
  the permutation-EA literature. Primary-source verification is a
  follow-up.
- Limitations: our synthetic landscapes are idealized instances of each
  type; real ordering problems mix types.
- How it changes project direction: PRISM gains a `mutation=` parameter
  (v2-compatible default) and, if H1 holds, an operator-selection
  guideline becomes part of the method and paper.

This file records literature, references, and source documents that have been
reviewed or cited by project materials. Entries should distinguish direct paper
review from inherited notes or secondary summaries.

## Inherited Source Notes

### NEAT, Innovation Numbers, and Speciation

Source: `other.md`

Status: Inherited analysis, not independently revalidated during the 2026-07-05
continuity setup.

Key finding recorded in existing notes: Innovation numbers are mentioned in the
GNGN material but are not fully specified. Branch IDs may act as implicit
branch-level innovation numbers, but within-branch gene innovation tracking and
NEAT-style crossover remain underspecified.

Research impact: This is a major design issue if PRISM/GNGN is extended from
fixed branch permutation search toward topology evolution.

Follow-up:

- Verify the source papers and exact NEAT compatibility-distance formulation.
- Decide whether innovation tracking belongs in the next PRISM algorithm
  version or only in a GNGN/topology-evolution extension.
- Formalize the relationship between permutation-level distance and
  topology-level distance.

### Presentation and Visualization Guidance

Source: `presentation.md`

Status: Inherited presentation guide.

Key content: Beamer/LaTeX setup, color palette, math presentation guidance,
TikZ/network diagrams, and slide structure for a GNGN/NEAT audience.

Research impact: Useful for dissemination, but not itself evidence for
algorithmic correctness.

## Future Literature Entry Format

Use this structure for each paper or source:

- Citation:
- Link or local path:
- Reviewed by:
- Date reviewed:
- Research question:
- Key claims:
- Methods relevant to PRISM:
- Evidence quality:
- Limitations:
- How it changes project direction:
