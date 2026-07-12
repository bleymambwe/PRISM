# PRISM: Ordering as a Search Space — Operator and Encoding Matching, a Pre-Flight Diagnostic, and Ground-Truth Benchmarks for Permutation Search

Blessings Mambwe
Submission draft v1 — 2026-07-08 (Iteration 13). Repository: github.com/bleymambwe/PRISM (tags iteration-02 … iteration-12)

## Abstract

Many systems consist of fixed components whose performance depends on the
order in which they are applied: neural modules, compiler passes,
curricula, options, and reasoning steps in language-model prompts. We
study this ordering problem in isolation with PRISM, a minimal elitist
evolutionary search over permutations, and make three contributions.
(1) Method selection from pre-search statistics: we show empirically that
the mutation operator must match the landscape type — on plateau-rich
landscapes a mismatched operator fails 100% of runs rather than slowing
down — and that a uniform operator portfolio automates the choice at
1.1-4.1x cost. Two classical statistics computable from a few hundred
evaluations (one-move fitness autocorrelation rho1 and fitness-distance
correlation FDC) recover the matched operator on 3/3 typed landscapes and
predict PRISM-versus-random outcomes on 8/8 fully enumerated landscapes;
the same statistics select the replacement policy and, when precedence
structure is present, an encoding-matched surrogate that outperforms
every population method tested (13.5 versus 55.7 evaluations to a single
optimum among 5,040 orderings, where random sampling finds none).
(2) Ground-truth benchmarking: deterministic, permutation-seeded neural
benchmarks whose landscapes we enumerate exhaustively (120 to 5,040
orderings), so search quality is reported as exact hit rates and regret —
a protocol that exposed, rather than hid, the regime in which evolutionary
search has no advantage over uniform random sampling. (3) A validated
application: reordering six reasoning instructions in a Gemini 2.5
Flash-Lite prompt swings GSM8K accuracy from 6.3% to 96.9%; the pre-flight
predicted both the correct operator (insert, the precedence-type
prediction) and the search outcome before any search ran, at both n = 6
(enumerable) and n = 8 (40,320 orderings, sampled statistics only). Two
falsified hypotheses are retained in the record and shaped the method.
Total experimental cost: under eleven dollars.

## 1. Introduction

Architecture and pipeline design usually tune which components to use.
We isolate the narrower question: given fixed components, in what order?
Formally, a candidate is a permutation pi in the symmetric group S_n and
the goal is to maximize a task evaluator F(pi). The question is narrow
enough to admit theory and exhaustive ground truth, yet broad enough to
cover neural module ordering, compiler phase ordering, curricula, option
sequencing, and prompt-instruction ordering.

Our contributions, in the order the research produced them:

- A minimal, fully reproducible permutation searcher (elitist
  evolutionary loop; every algorithm version is a git tag whose default
  parameters reproduce the previous version bit-for-bit under equal
  seeds).
- Empirical confirmation that mutation-operator choice is a requirement,
  not a tuning knob (Section 6.3), and its automation by an operator
  portfolio (Section 6.4).
- A ground-truth benchmark methodology — deterministic permutation-seeded
  fitness plus exhaustive enumeration — that grades search like an exam
  with an answer key (Section 6.5), and that surfaced an honest negative:
  on landscapes whose top end lacks local structure, evolutionary search
  is statistically indistinguishable from random sampling
  (Section 6.6).
- A two-statistic pre-flight (rho1, FDC) that predicted every observed
  outcome across eight enumerated landscapes and two live applications,
  and that now selects the operator, the replacement policy, and the
  surrogate encoding (Sections 6.6-6.8, 7).
- An encoding-matched surrogate (binary precedence features + ridge
  regression, BANANAS-style) that is the first method in the program to
  substantially beat the elitist searcher on structured landscapes
  (Section 6.8).
- A validated application with the largest effect we know of for prompt
  structure alone: 6.3% to 96.9% GSM8K accuracy by reordering six
  instructions (Section 6.7), with interpretable position effects.

## 2. Related Work

**Neural architecture search.** RL-based NAS [Zoph & Le, 1611.01578] and
its successors established the field's scale; regularized (aging)
evolution [Real et al., 1802.01548] is the closest algorithmic relative
of our replacement-policy study, and we adopt its aging mechanism in
Section 6.8. DARTS [Liu et al., 1806.09055] represents the
gradient-relaxation family whose failure modes (collapse) motivate
discrete search. NAS-Bench-101/201 [1902.09635, 2001.00326] pioneered
tabular ground truth for search research; our enumerated permutation
landscapes apply the same philosophy at a scale where *exhaustive* ground
truth is possible. Zero-cost proxies [Abdelfattah et al., 2101.08134;
Mellor et al., 2006.04647] motivate our multi-fidelity gating for
expensive evaluations. BANANAS [White et al., 1910.11858] supplies the
predictor-plus-acquisition pattern behind our surrogates; our
contribution there is the finding that the encoding must match the
landscape's structure class, mirroring operator matching.

ANASOD [Wan et al., 2111.04670] provides the closest complementary
abstraction. It replaces a fully specified cell by the normalized counts of
its operations and reports that, in the spaces studied, these distributions
retain enough discriminating power while being easier to optimize. PRISM does
not treat this as a competing universal claim. Instead, it asks a prior
method-selection question: for a fixed operation distribution, does exact edge
placement retain measurable and locally exploitable residual structure? If
not, the ANASOD quotient space is the appropriate representation; if so,
placement-aware search may add value within that distribution.

**Permutation evolutionary algorithms.** Operator-landscape
correspondence (swap for absolute-position, insert for precedence,
inversion for adjacency) follows Cicirello's classification [2022]; we
contribute controlled failure measurements (100% censoring under
mismatch) and automation via portfolios. Elitist convergence follows
Rudolph [1994]; fitness-distance correlation follows Jones & Forrest
[1995]. Pointer networks and neural combinatorial optimization
[1506.03134, 1611.09940] are the learned-constructive alternative we do
not pursue here.

**LLM prompt optimization.** Chain-of-thought [2201.11903],
self-consistency [2203.11171], APE [2211.01910], OPRO [2309.03409], and
DSPy [2310.03714] optimize prompt content or programs; our application
isolates instruction *order* with everything else fixed, and measures it
against exhaustive enumeration — to our knowledge the first complete
ordering landscape published for a prompting problem.

## 3. Framework

A candidate solution is a permutation pi = (pi_1 … pi_n) in S_n. Given a
task evaluator F, PRISM maximizes F over S_n. F may be classification
accuracy, negative loss, episodic return, or LLM task accuracy; the
searcher is domain-agnostic. All experiments use a distinct-evaluation
cost model (repeat queries of the same ordering are cached and free),
matching practice for expensive evaluators.

## 4. Algorithm

PRISM maintains a population (default 20) of permutations. Each
generation: evaluate all; copy the best unchanged (elitism 1); refill by
tournament selection (k = 3) and mutation (p_m = 0.05 per child).

Mutation operators: swap (two positions), insert (remove and re-insert),
inversion (reverse a segment), scramble (shuffle a segment). Meta-modes:
portfolio (uniform random operator per mutation event) and adaptive
(probability-matching weights with a floor that preserves
irreducibility). Replacement variants studied: aging (kill the oldest;
Real et al.) and an elitist-with-stagnation-restart hybrid. Surrogate
variants (Section 6.8) fit a ridge model over positional or precedence
encodings and evaluate only the top-predicted candidate per step.
Scale-aware defaults: population >= 40 and p_m >= 0.5 for n >= 7
(Section 6.6).

## 5. Theoretical Framing

The process is a finite Markov chain over populations. With p_m > 0 the
chain is irreducible; with elitism, populations containing an optimum
form an absorbing set, giving convergence with probability one. The
project's runtime claim — expected hitting time O(n^3 log n) under stated
assumptions — is empirically consistent to n = 16 for landscape-matched
operators (log-log exponents 2.79-3.44; E[T]/(n^3 ln n) flat across a 3x
range of n). Two boundaries are established empirically and must
accompany any statement of the theory: polynomial-time behavior requires
operator-landscape match and top-end locality; and the aging replacement
policy sacrifices strict elitism. Appendix B restates the guarantees
precisely for each replacement variant: the hybrid retains almost-sure
population convergence verbatim; aging retains almost-sure *discovery*
(convergence of the best-ever record) with an explicit
landscape-independent geometric bound, while population-level absorption
provably fails; and elitist portfolio search additionally carries a
crude unconditional worst-case bound that complements the
landscape-conditional polynomial claim.

## 6. Experiments

All experiments are seeded, budgeted, resumable, and reproducible from
the repository; every figure regenerates from committed CSVs. Two
hypotheses were falsified and are reported alongside the confirmations.

### 6.1 Reproduction with corrections

All five historical toy-benchmark headlines reproduce from a clean
environment (XOR/OR/AND/parity 100%, polynomial MSE 0.0070). Corrections
logged: order matters on 4/5 problems (AND has zero order-variance);
best-ever fitness under stochastic evaluation is inflated by selection
bias; only 3 of 5 permutation positions were functional in the original
benchmarks.

### 6.2 Synthetic runtime scaling

On deterministic Hamming and Kendall objectives (n = 4-12, 15 seeds),
log-log exponents are 3.1/2.9 excluding sizes contaminated by lucky
initial populations, extended to n = 16 by the operator study below.

### 6.3 Operator-landscape matching (requirement, not preference)

Four operators x three typed landscapes x n = 6-16, 15 seeds, censoring
at 10,000 generations. The literature-matched operator wins every type.
At n = 16: swap solves absolute-position in 405 generations while all
other operators censor on 100% of runs; insert leads precedence (396)
where all succeed; inversion solves adjacency (1,199) while all others
censor. Mismatch on plateau-rich landscapes is a hard failure. A
deceptive landscape defeats every operator by n = 8-10: the runtime
theory is landscape-conditional.

### 6.4 The operator portfolio

Uniform random operator per mutation event: zero censoring on every
landscape at every size, at 1.1-4.1x the matched operator's generations.
The adaptive variant identifies the matched operator on 3/3 landscapes
(a diagnostic) but does not beat uniform — its reward signal (~1
mutation event per generation) is too sparse.

### 6.5 Ground truth by construction

The v4 benchmarks stack permuted residual blocks (a plain deep stack was
falsified — every ordering collapsed to chance) with weight
initialization seeded from the permutation: fitness is deterministic and
landscapes are exhaustively enumerable. Enumerated: 120 orderings (n=5;
XOR optimum held by 8, parity by 2), 720 (n=6; 33), 5,040 (n=7 parity;
14 = 0.28%). Exact results: XOR n=5 hit rate 100%; parity n=5 40% with
mean regret 0.033; XOR n=6 90% with regret 0.008. An accidental
re-evaluation of 103 orderings across process restarts matched exactly.

### 6.6 The honest boundary and the pre-flight diagnostic

On the n=7 parity landscape, PRISM is statistically indistinguishable
from random sampling under the distinct-evaluation model: default
settings prematurely converge (4/15 hits at ~103 orderings explored —
random's odds at that budget); scale-aware settings hit 15/15 but at 384
mean evaluations versus random's 318; random matches or beats best-found
quality at every budget >= 50.

The explanation is measurable before searching. rho1 (one-move fitness
autocorrelation per operator) and FDC (fitness-distance correlation to
the nearest optimum) computed on all eight enumerated landscapes
reproduce every observed outcome: synthetic landscapes show rho1 up to
0.78 under their matched operators and FDC to -0.83 (search pays);
the neural landscapes are locally near-random under precise operators
(rho1 0.00-0.06) with FDC -0.06 at n=7 (needle in a haystack; PRISM ~
random); the deceptive landscape is smooth (rho1 0.65) but FDC +0.78 —
smoothness and guidance are different things, which is why both
statistics are required. rho1 recovers the matched operator on 3/3 typed
landscapes with no search run.

### 6.7 Application: LLM reasoning-chain ordering

Six reasoning instructions (restate, identify, plan, compute, check,
answer-format) permuted as numbered steps in a Gemini 2.5 Flash-Lite
prompt; fitness is accuracy on a fixed 32-question GSM8K subset
(temperature 0; per-ordering-per-question answer cache). All 720
orderings enumerated (~23,000 calls, ~$3-5).

Ordering alone swings accuracy from 6.3% to 96.9% (mean 0.72, std 0.23).
Position effects are directly interpretable: the answer-format
instruction first drops mean accuracy to 0.435 (the model answers before
reasoning) versus 0.870 last; the compute instruction first yields 0.908
versus 0.585 in fifth position. The pre-flight predicted the experiment:
rho1 selected insert (0.547) — the precedence-type prediction — and
FDC = -0.346 predicted searchable structure. At 40 seeds with bootstrap
CIs, all methods reach an exact optimum quickly and comparably (PRISM
9.9 [7,13] mean distinct evaluations versus random 10.8 [8,14]; an
earlier 15-seed reading suggesting a 3x gap did not survive the larger
seed count and is corrected here). With optima at 60/720 density, the
scientific payload of this experiment is the 90-point ordering effect,
the interpretable position-effect table, and the pre-flight's validated
forecasts — not search superiority on a landscape this friendly.

A harder instance (n = 8 modules; 40,320 orderings; first application
beyond enumerability; hard-capped spend $5.56) widened the ordering
effect to 0.10-1.00 and validated the *sampled* pre-flight end-to-end:
from 222 sampled orderings it selected insert (rho1 0.75) and forecast
"random likely competitive"; the search stage confirmed exactly that
(all methods saturate at 1.0). The saturation is a measurement-resolution
effect — with 20-question granularity, perfect ties are dense — yielding
a protocol rule: establish that the fitness statistic can discriminate
before spending search budget.

### 6.8 Method selection beyond operators: replacement and surrogates

Aging evolution (kill-oldest, no permanent elite) fixes the premature
convergence of 6.6 without hyperparameter surgery — parity n=7 hit rate
48% to 78% at equal budget — but lands at random's level (75%), exactly
as the locality theory predicts for FDC ~ 0; elitist search remains
fastest on structured landscapes. An elitist + stagnation-restart hybrid
is never the worst method on any landscape (a no-pre-flight default) but
wastes restarts where patience suffices.

The strongest result of the program's improvement studies: a
precedence-encoded surrogate (binary "i before j" features, ridge
regression, mutation-proposed candidates, evaluate-top-predicted). On
the pure-precedence Kendall landscape with a single optimum among 5,040
orderings it reaches the optimum in 14.8 mean evaluations, 95% CI
[14, 15], versus matched-operator elitist search at 54.2 [50, 59] —
non-overlapping intervals at 40 seeds — while random sampling finds the
optimum in only 2/40 runs within the 500-evaluation cap. It is
tied-best on XOR n=6 and parity n=7 (where, per Section 6.6, no method
separates from random: all 40-seed hit-rate CIs overlap random's
[0.60, 0.86]). A positional encoding, by contrast, is inert on parity
and indistinguishable elsewhere: surrogate power is an
encoding-landscape match, exactly parallel to operator matching — and
detectable by the same pre-flight.

## 7. The PRISM Protocol

The program's practical output is a decision procedure, each step backed
by the experiments cited:

1. **Gate** (6.7): evaluate ~30 random orderings. If fitness variance is
   negligible, ordering does not matter — stop. Verify the fitness
   statistic can discriminate at the chosen measurement resolution.
2. **Pre-flight** (6.6): from a few hundred evaluations compute rho1 per
   operator and (approximate) FDC.
3. **Select the method** (6.3, 6.4, 6.8): argmax rho1 (excluding
   scramble) names the operator; precedence signals select the
   precedence surrogate; FDC materially negative selects elitist search
   (fastest, keeps the guarantee); FDC near zero selects random sampling
   or aging (report random as the method of record); FDC positive:
   do not use evolutionary search.
4. **Report** (6.5, 6.6): distinct-evaluation budgets, a
   random-without-replacement baseline always, exact hit rates and
   regret where ground truth exists.

## 8. Discussion

PRISM is strongest when components are fixed, ordering matters, and the
landscape has exploitable structure — and the protocol now measures all
three before any budget is committed. The application results suggest
prompt-instruction ordering is a seriously underexplored, high-effect
surface: the position-effect tables are immediately reusable guidance,
and at the measured optimum densities, even "sample 30 orderings and
keep the best" is a defensible production recipe — a conclusion we can
state only because the baselines are honest.

## 9. Limitations

Polynomial-time behavior is landscape-conditional in two independent
ways (operator match; top-end locality), and deceptive landscapes defeat
every variant. Enumerable ground truth tops out at n = 7 here; larger
instances rely on sampled statistics whose error bounds we have not
characterized. Aging trades away strict elitism. The surrogate uses a
pure-exploitation acquisition; calibrated uncertainty may improve it.
Single LLM, single task family, fixed question subsets; the theoretical
claims await primary-source verification and formal restatement for the
aging/hybrid modes.

## 10. Reproducibility Statement

Every algorithm version is a git tag; defaults reproduce the prior
version bit-for-bit under equal seeds. Every experiment is a seeded,
budgeted, resumable script; every landscape enumeration and answer cache
is committed; every figure regenerates from committed CSVs. Total
experimental cost: under eleven dollars (LLM API fees; all other compute
on a 4-core laptop CPU).

## 11. Conclusion

Ordering alone is a meaningful, measurable search surface. Its search
methods succeed or fail for reasons that two cheap statistics predict in
advance; its benchmarks can carry exact answer keys; and its most
striking application to date — a 90-point accuracy swing from reordering
six prompt instructions — was predicted, not just found. The
contribution is not that evolution beats everything; it is a small,
analyzable optimizer whose failure modes are mapped as carefully as its
successes, and a protocol that tells you, before you spend, which tool
to use and whether to search at all.

## Appendix A. Experimental Details and Threats to Validity

Structured for reproduction; one block per experiment family. All runs:
seeded numpy RNGs, distinct-evaluation cost model with caching,
budgeted-resumable scripts in `experiments/iteration-XX/`.

### A.1 Synthetic operator studies (C, D, F)

Motivation: isolate operator-neighborhood effects on landscapes of
known type. Setup: hamming (absolute position), kendall (precedence),
adjacency (routing), deceptive objectives, closed-form, deterministic;
n in {6,8,10,12,14,16}; 15 seeds per cell; cap 10,000 generations
(censored runs recorded, never discarded). Variables: operator
(swap/insert/inversion/scramble/portfolio/adaptive) x landscape x n.
Hyperparameters: population 20, tournament 3, p_m 0.05, elitism 1.
Metrics: generations to optimum; censoring rate. Threats: single
hyperparameter set (mitigated by the D12 sweep at n=7); landscape
types are pure — real problems mix types (open problem, Section 9).

### A.2 Ground-truth neural benchmarks (G, H, I)

Motivation: eliminate best-observed bias; grade search exactly. Setup:
v4 = n permuted residual bottleneck blocks (widths/activations listed
in `toy_problems_v4.py`), weight init seeded from (permutation, trial),
fitness = mean accuracy of k=3 trials, 50-100 Adam steps, lr 0.1.
Enumerations: 120 (n=5), 720 (n=6), 5,040 (n=7) orderings; determinism
verified by 103 accidental re-evaluations matching exactly. Baselines:
six methods (elitist, aging, hybrid, two surrogates, random) at 40
seeds, Wilson 95% CIs (Iteration-14 statistics pass; full table in
`experiments/iteration-14/results/headline_cis.csv`). Key CI-backed
results: parity n=7 elitist 19/40 [0.33,0.63] < random 30/40
[0.60,0.86]; no method's hit-rate CI separates from random's on that
landscape; kendall n=7 surr-prec 14.8 [14,15] < elitist 54.2 [50,59],
random 2/40. Threats: the landscape family depends on the seeding
convention; k=3 is one noise-control choice; toy scale.

### A.3 Locality diagnostic (J) and its sampling error

Motivation: predict search outcomes pre-search. Metrics: rho1 =
Pearson correlation of f(pi) vs f(op(pi)) over sampled moves; FDC =
correlation of fitness with Cayley distance to nearest optimum.
Iteration-14 reliability study (200 resamples at realistic pre-flight
sizes — 100 move-pairs per operator, 200 FDC points): correct-operator
pick rate 0.99 (hamming), 0.94 (kendall), 0.96 (adjacency);
deceptive-regime call stability 1.00; FDC regime call stability 0.83
(xor n=6), 0.78 (parity n=7), 1.00 (LLM). When rho1 carries no signal
(neural landscapes, rho1 0.00-0.06) the operator pick is arbitrary
(agreement 0.39-0.41) — precisely the regime in which the operator
choice is immaterial. Threats: live pre-flights approximate FDC with
distance-to-best-known (validated once, Experiment M); scramble's rho1
is inflated by identity moves and is excluded from argmax.

### A.4 LLM instruction-ordering (K, M)

Motivation: a real, API-priced ordering surface with enumerable ground
truth at n=6. Setup: modules as numbered prompt steps; Gemini 2.5
Flash-Lite, temperature 0, max 600-650 output tokens; fixed GSM8K test
subsets (seed 42; 32 questions at n=6, first 20 at n=8); answer = last
'Answer: <number>' match, fallback last number; per-(ordering,question)
cache so each API call is paid once; staged variance gate before any
budget. Cost: ~$3-5 (n=6, 23k calls), $5.56 (n=8, 23.8k calls,
hard-capped in code). Metrics: accuracy per ordering; position
effects; distinct evaluations to first exact optimum vs
random-without-replacement. Threats: single model snapshot;
deterministic decoding is not bit-guaranteed across API versions (the
cache freezes one snapshot); extraction regex; GSM8K pretraining
contamination affects absolute accuracy but not ordering comparisons
(shared across orderings); fitness granularity (1/20) made n=8 optima
dense — the D16 resolution rule now precedes any search spend.

### A.5 What additional experiments would strengthen the work

Mixed-type landscapes; a second LLM and harder question set;
uncertainty-aware surrogate acquisition; n>=9 sampled-statistics
protocol; formal restatement of absorption under aging; primary-source
verification of the runtime bound's assumptions.

### A.6 ANASOD boundary experiment (NAS-Bench-201)

Motivation: test whether the pre-flight can decide when an
operation-distribution encoding is sufficient, rather than presuming that
placement always deserves optimization. NAS-Bench-201 has a fixed six-edge
cell and five operations, giving 15,625 architectures partitioned into 210
operation-count distributions. The implementation in
`experiments/iteration-19/anasod_boundary.py` exhaustively groups the table by
distribution and, for each dataset and group, reports within-group standard
deviation and range, swap-neighborhood rho1, and exact FDC to the nearest tied
best placement. Across the full table it reports eta-squared, the fraction of
architecture-level variance attributable to differences between operation
distributions. The ANASOD Figure-1 example (four 3x3 and two 1x1 convolutions)
has only 15 unique placements, so it is a transparent case study rather than
the sole basis for inference.

Interpretation was fixed before observing results. High
eta-squared, small within-distribution effects, and near-zero locality support
using ANASOD's quotient representation and a PRISM recommendation not to
optimize placement. Material within-distribution effects together with swap
locality and negative FDC identify slices for a subsequent budget-matched
PRISM-versus-random confirmation. Mixed results support the boundary thesis:
operation distribution is a useful coarse representation, while the
pre-flight identifies exceptions where placement remains exploitable.

The exhaustive run used `simple-hpo-bench==0.2.0`, a compact NATS-Bench backend
containing three repeated last-epoch validation accuracies for every cell.
Distribution membership explains 46.1% (CIFAR-10), 55.6% (CIFAR-100), and
61.2% (ImageNet16-120) of architecture-level variance (eta-squared); the
corresponding within-distribution fractions are 53.9%, 44.4%, and 38.8%.
Therefore operation counts are strongly informative but are not sufficient
statistics for these tables. Median within-slice standard deviations are
2.10, 3.32, and 3.28 accuracy points, respectively.

| Dataset | eta-squared (distribution) | Figure-1 slice range (points) | swap rho1 | exact FDC |
| --- | ---: | ---: | ---: | ---: |
| CIFAR-10 | 0.461 | 0.848 | 0.137 | -0.412 |
| CIFAR-100 | 0.556 | 2.530 | -0.143 | -0.273 |
| ImageNet16-120 | 0.612 | 4.956 | 0.223 | -0.721 |

The Figure-1 slice gives the intended mixed diagnosis: exact placement has a
small effect on CIFAR-10, a larger effect on the harder datasets, and clearly
usable swap-local structure only on ImageNet16-120. Across the 205 non-singleton
distributions, 98, 97, and 112 slices respectively satisfy the previously used
pre-flight conjunction rho1 > 0.2 and FDC < -0.15. This refines rather than
contradicts ANASOD: distribution is a valuable coarse encoding, while the value
of placement optimization is slice- and dataset-dependent. Results are exact
for the compact tables; replication against the official 4.7 GB archive and a
budget-matched search confirmation remain limitations. Synthetic fixture
output is software validation only.

## Appendix B. Convergence Statements for Replacement Variants

This appendix closes the theory gap opened by Section 6.8: aging
replacement breaks strict elitism, so the original absorption argument
does not apply as stated. We restate what survives, for the exact
implementations in the repository. Throughout, S_n is the symmetric
group, F : S_n -> R the fitness, Omega_opt = argmax F (|Omega_opt| =
m >= 1), and "portfolio mutation" draws one of {swap, insert,
inversion, scramble} uniformly and applies it once.

**Proposition B.1 (one-step universal reachability).** Under portfolio
mutation as implemented, for every parent pi and every target sigma in
S_n,

  Pr(mutate(pi) = sigma) >= delta_0 := 1 / (4 C(n,2) n!) = 1 / (2 n (n-1) n!).

*Proof.* With probability 1/4 the scramble operator is drawn; its
segment endpoints i < j are uniform over the C(n,2) unordered pairs,
so with probability 1/C(n,2) the segment is the entire permutation;
the segment is then shuffled uniformly (Fisher-Yates), so every
arrangement of S_n — in particular sigma — results with probability
1/n!. Multiplying the three factors gives the bound; other operators
and partial segments can only add probability. (Numerically verified:
2,000,000 Monte-Carlo draws at n=5 give 2.21e-4 against the bound
2.08e-4, and the full-segment shuffle is uniform to within Monte-Carlo
noise across all 24 targets at n=4;
`experiments/iteration-15/theory_check.py`.) ∎

**Proposition B.2 (aging mode: almost-sure discovery, geometric
bound; no population absorption).** Consider aging-PRISM (population
mu; each step: tournament over a random sample, one portfolio
mutation of the winner, append child, remove oldest). Let T be the
first step at which an optimal ordering is evaluated, and let b_t be
the best-ever-evaluated fitness (the record).

(i) Each step's child lies in Omega_opt with probability >= m delta_0,
regardless of the population's contents (Proposition B.1 applies to
whatever parent the tournament selects). Hence T is stochastically
dominated by a Geometric(m delta_0) variable:

  Pr(T > t) <= (1 - m delta_0)^t,  E[T] <= 2 n (n-1) n! / m.

The record process b_t is non-decreasing by construction and equals
max F for all t >= T; therefore the record converges to the optimum
almost surely, with the explicit landscape-independent bound above.
(For parity n=7 with m = 14 the bound is 30,240 steps; the observed
40-seed mean is 222.5 [170, 277] — the bound is a crude worst case,
as intended.)

(ii) Population-level absorption fails: an optimal individual entering
the population at step t is deterministically removed at step t + mu
(first-in-first-out), and the event that it is not re-created in the
intervening mu steps has positive probability (e.g., every one of the
mu mutation draws produces a non-optimal child, each of which has
probability bounded away from zero). Hence states whose populations
contain an optimum are not absorbing, and no almost-sure statement
about the *population* holds without the record. This is the precise
sense in which "aging trades the letter of the guarantee for
robustness" (Section 6.8). ∎

**Proposition B.3 (hybrid mode: Theorem 2.2 verbatim).** The
elitist-with-restart hybrid preserves the best-ever individual by
construction: in normal generations the elite slot copies the current
population maximum, and every restart re-injects the best-ever
ordering explicitly before re-randomizing the remainder. By induction
the population always contains an individual of best-ever fitness, so
populations containing an optimum form an absorbing set; irreducibility
is unchanged (mutation is untouched). The almost-sure convergence
argument for elitist PRISM therefore applies to the hybrid without
modification. ∎

**Remark B.4 (unconditional worst-case bound for elitist portfolio
search).** In elitist PRISM with portfolio mutation, each generation
produces mu - 1 children, each mutated with probability p_m, so an
optimum is discovered per generation with probability >=
1 - (1 - p_m m delta_0)^(mu-1). With elitism, discovery implies
permanent retention, giving

  E[generations to optimum] <= 1 / (1 - (1 - p_m m delta_0)^(mu-1))
                             ~ 2 n (n-1) n! / ((mu-1) p_m m).

This factorial-order bound is vacuous in practice but exact and
assumption-free; it brackets the claim of Section 5 from above, while
the O(n^3 log n) statement — which requires landscape structure — is
the claim of practical interest. The pair makes the division of labor
explicit: guarantees are cheap; *rates* are landscape-conditional.

## References

- Zoph, Le. Neural Architecture Search with Reinforcement Learning. arXiv:1611.01578.
- Real, Aggarwal, Huang, Le. Regularized Evolution for Image Classifier Architecture Search. arXiv:1802.01548.
- Liu, Simonyan, Yang. DARTS: Differentiable Architecture Search. arXiv:1806.09055.
- Ying et al. NAS-Bench-101. arXiv:1902.09635. Dong, Yang. NAS-Bench-201. arXiv:2001.00326.
- Wan et al. Approximate Neural Architecture Search via Operation Distribution Learning. WACV 2022; arXiv:2111.04670.
- Abdelfattah, Mehrotra, Dudziak, Lane. Zero-Cost Proxies for Lightweight NAS. arXiv:2101.08134.
- Mellor, Turner, Storkey, Crowley. Neural Architecture Search without Training. arXiv:2006.04647.
- White, Neiswanger, Savani. BANANAS: Bayesian Optimization with Neural Architectures for NAS. arXiv:1910.11858.
- Cicirello. Classification of permutation problems and mutation operators (2022).
- Rudolph. Convergence Analysis of Canonical Genetic Algorithms. IEEE TNN, 1994.
- Jones, Forrest. Fitness Distance Correlation as a Measure of Problem Difficulty. ICGA 1995.
- Vinyals, Fortunato, Jaitly. Pointer Networks. arXiv:1506.03134. Bello et al. Neural Combinatorial Optimization. arXiv:1611.09940.
- Wei et al. Chain-of-Thought Prompting. arXiv:2201.11903. Wang et al. Self-Consistency. arXiv:2203.11171.
- Zhou et al. Large Language Models are Human-Level Prompt Engineers. arXiv:2211.01910.
- Yang et al. Large Language Models as Optimizers. arXiv:2309.03409.
- Khattab et al. DSPy. arXiv:2310.03714.
- Stanley, Miikkulainen. Evolving Neural Networks through Augmenting Topologies. EC 10(2), 2002.
