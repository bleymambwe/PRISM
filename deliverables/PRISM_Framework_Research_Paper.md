# PRISM: A Permutation-Based Search Framework for Ordering Problems

Blessings Mambwe  
Draft date: 2026-07-06 (updated end of Iteration 5)

## Abstract

Many machine-learning and decision-making systems contain a fixed set of
components whose performance depends strongly on the order in which those
components are applied. PRISM, the Permutation-based Reasoning and Intelligence
Search Method, treats such systems as finite ordering problems and searches the
permutation space using an evolutionary loop with tournament selection, mutation
over permutations, and elitism. This draft consolidates the current PRISM
framework, its theoretical finite-state convergence framing, validation and
scaling results, a completed operator-landscape study, an operator-portfolio
mechanism that automates operator selection, a noise-controlled benchmark
redesign with exact enumerated ground truth, and a lightweight reinforcement
learning proof of concept. Three empirical findings anchor the paper:
(1) hitting times scale consistently with the O(n^3 log n) theory out to n=16
for landscape-matched mutation operators; (2) matching the mutation operator to
the landscape type is not an optimization but a requirement — mismatched
operators fail outright on plateau-rich landscapes — and a uniform operator
portfolio automates the choice at a bounded 1.1-4.1x cost; (3) on deceptive
landscapes all tested operators fail, so the polynomial-runtime claim is
landscape-conditional. Limitations of the earlier evidence (partially-used
permutations, stochastic fitness inflation) are documented and fixed by the
redesigned benchmarks.

## 1. Introduction

Architecture and policy design often focus on selecting components, adding
connections, or tuning continuous parameters. PRISM asks a narrower but
scientifically useful question: given a fixed set of operations or modules, in
what order should they be executed?

This turns the search space into the symmetric group over `n` items. The
framework is relevant when the components are already known but their sequencing
is uncertain, including neural module ordering, operator pipelines, curriculum
learning, option sequencing in reinforcement learning, compiler pass ordering,
and reasoning-chain module ordering.

The current implementation represents each candidate as a permutation and
evolves a population using:

- ordering as the genome,
- tournament selection,
- mutation over permutations,
- elitism to preserve the best candidate,
- repeated evaluation through a task-specific fitness function.

## 2. Framework

Let `S_n` be the set of all permutations of `n` fixed components. A candidate
solution is

```text
pi = (pi_1, pi_2, ..., pi_n),    pi in S_n.
```

Given a task-specific evaluator `F`, PRISM maximizes

```text
max_{pi in S_n} F(pi).
```

The evaluator may represent classification accuracy, negative loss, hitting
time, episodic return, Q-learning curriculum performance, or another measurable
objective. PRISM itself is agnostic to the domain.

## 3. Algorithm

PRISM maintains a population of permutations. At each generation, it evaluates
fitness, carries forward elite individuals, and fills the remaining population
through tournament-selected parents and mutation.

```text
Input: n components, fitness function F, population size N, mutation rate p_m
Initialize N random permutations from S_n
For each generation:
  Evaluate F(pi) for every population member
  Copy the best elite individual(s)
  While the next population is not full:
    Select a parent by tournament selection
    Copy the parent
    With probability p_m, mutate the copied permutation
    Add the child to the next population
Return the best permutation observed
```

The baseline mutation is swap mutation. The current code also supports insert,
inversion, and scramble mutation, plus two portfolio modes: `portfolio` draws
one of the four operators uniformly at random per mutation event, and
`adaptive` draws operators with probability-matching weights updated by
whether each mutation improved on its parent (with a weight floor that
preserves chain irreducibility, and hence the convergence guarantee). This
does not change the core framework; it adds a controlled customization point
for different permutation landscapes.

## 4. Theoretical Framing

The inherited PRISM theory models the evolutionary process as a finite Markov
chain over populations of permutations. With a nonzero mutation probability and
elitism, populations containing an optimal permutation form an absorbing set:
once an optimum is found, elitism prevents its loss.

The project handover records three main theoretical claims:

- convergence to an optimal absorbing set with probability one,
- expected runtime bounded by `O(n^3 log n)` generations under the stated
  assumptions,
- geometric convergence behavior characterized by the transient-state spectral
  radius.

These claims are part of the project theory and should be rechecked against
primary literature and formal assumptions before external submission.

## 5. Experiments

### 5.1 Neural Toy Validation

The cleaned PRISM implementation reproduces the headline toy benchmark results
from the original notebook:

| Task | Best fitness |
| --- | ---: |
| XOR | 1.0000 |
| OR | 1.0000 |
| AND | 1.0000 |
| 3-bit parity | 1.0000 |
| Polynomial regression | MSE about 0.0070 |

The reproduction also corrected the historical interpretation: the AND task
showed zero order-variance, best-ever classification fitness can be inflated by
stochastic evaluation, and only the first two or three positions of the original
length-five permutation affect the neural toy networks.

### 5.2 Synthetic Runtime Scaling

Deterministic synthetic objectives provide cleaner hitting-time measurements.
The current scaling outputs report:

| Objective | All-size exponent | Exponent excluding n <= 5 |
| --- | ---: | ---: |
| Hamming | 3.73 | 3.14 |
| Kendall | 3.68 | 2.89 |

The ratios `E[T] / (n^3 log n)` stay within a narrow band over the tested size
range, which is consistent with the recorded `O(n^3 log n)` theory. This does
not prove the bound, but it is a useful empirical sanity check. The operator
study below extends the evidence to n = 16: log-log exponents for
landscape-matched operators are 2.79 (Hamming/swap), 2.98 (Kendall/insert),
and 3.44 (adjacency/inversion) — all consistent with the cubic-plus-log
theory.

### 5.3 Operator-Landscape Matching (Completed Study)

The operator study tested the hypothesis, drawn from the permutation-EA
literature (Cicirello's A/R/P classification), that mutation should match the
landscape type: swap for absolute-position structure, insert for precedence
structure, inversion for adjacency structure. Protocol: four mutation
operators x three typed synthetic landscapes x n in {6, 8, 10, 12, 14, 16},
15 seeds, 10000-generation cap.

The literature-matched operator was empirically best on all three landscape
types. Mean generations to optimum at n = 16 (asterisk marks censoring at the
cap):

| Landscape (type) | Matched operator | All mismatched operators |
| --- | --- | --- |
| Hamming (absolute position) | swap: 405 | 10000* (100 percent failure) |
| Kendall (precedence) | insert: 396 | 440-588 (all succeed) |
| Adjacency (edges) | inversion: 1199 | 10000* (100 percent failure) |

The effect's shape is the key finding: smooth landscapes (Kendall) are
operator-forgiving, while plateau-rich landscapes turn operator mismatch into
a hard failure rather than a slowdown. A deceptive landscape (fitness gradient
pointing away from the optimum) defeated every tested operator by n = 8-10,
demonstrating that the polynomial-runtime behavior is landscape-conditional
even though the probability-one convergence guarantee still holds.

### 5.4 Operator Portfolio: Automating the Choice

Requiring users to type their landscape a priori is error-prone, and Section
5.3 shows a wrong guess can cost everything. The portfolio mode removes the
choice: each mutation event draws one of the four operators uniformly at
random. Under the identical protocol, the portfolio solved every landscape at
every size with zero censoring, at 1.1-4.1x the matched operator's
generations:

| Landscape | Matched fixed (n=16) | Portfolio (n=16) | Overhead |
| --- | ---: | ---: | ---: |
| Hamming | 405 | 1140 | 2.8x |
| Kendall | 396 | 501 | 1.3x |
| Adjacency | 1199 | 1915 | 1.6x |

The adaptive variant (probability-matching credit assignment) correctly
identified the literature-matched operator on all three landscapes via its
final weight vector, making it a usable automated landscape-typing diagnostic,
but its hitting times did not consistently beat the uniform portfolio and it
costs one extra evaluation per mutation event. Recommendation: fixed matched
operator when the landscape type is known; uniform portfolio otherwise;
adaptive for landscape diagnosis.

### 5.5 Noise-Controlled Neural Benchmarks with Exact Ground Truth

The redesigned toy benchmarks (v4) fix the documented flaws of the originals.
Each network stacks five permuted residual bottleneck blocks (distinct widths
and activations), so every permutation position is functional; residual
connections keep all orderings trainable, avoiding the failure of a plain
five-layer redesign in which every ordering collapsed to chance accuracy.
Fitness is made deterministic by seeding weight initialization from the
permutation itself and averaging three trials, which eliminates best-ever
fitness inflation and makes the full landscape exactly enumerable.

Enumerating all 120 orderings gives ground truth:

| Task | Optimum | Orderings achieving it | Landscape mean (std) |
| --- | ---: | ---: | --- |
| XOR-v4 | 1.0000 | 8 of 120 | 0.804 (0.120) |
| Parity-v4 | 0.9583 | 2 of 120 | 0.720 (0.098) |

Ordering demonstrably matters (fitness spans 0.50-1.00 on XOR-v4), and the
optimum is a genuine needle (1.7 percent of the space for parity). Against
this ground truth, PRISM with portfolio mutation (60 generations, 10 seeds)
achieved a 100 percent hit rate on XOR-v4 and a 40 percent hit rate on
Parity-v4 with mean regret 0.033 — misses land on near-optimal orderings.
These are honest, reproducible search statistics rather than best-observed
noise.

### 5.6 Scale-Up, a Falsification, and the Locality Diagnostic

Scaling the ground-truth methodology to n = 6 succeeded (all 720
orderings enumerated; optimum held by 33; PRISM hit rate 0.90, mean
regret 0.0083). At n = 7 the program then produced its most important
negative result. On the fully enumerated parity landscape (5040
orderings, optimum held by 14 = 0.28 percent), PRISM with default
hyperparameters prematurely converges (4/15 seeds reach an optimum,
exploring only ~103 distinct orderings — statistically identical to
random sampling at that budget), and even tuned for full exploration
(population 40, mutation rate 0.6: 15/15 hits) it needs 384 mean
distinct evaluations against random-without-replacement's 318. Random
sampling also matches or beats PRISM's best-found quality at every
distinct-evaluation budget of 50 or more. **On this landscape, PRISM
has no advantage over uniform random sampling.**

The explanation is measurable before any search runs. Two classical
statistics — one-step move autocorrelation per operator (rho1) and
fitness-distance correlation to the nearest optimum (FDC) — computed on
all eight enumerated landscapes, reproduce every observed outcome:

| Landscape class | rho1 (matched op) | FDC | Search outcome |
| --- | ---: | ---: | --- |
| Synthetic typed (hamming/kendall/adjacency) | 0.66 / 0.78 / 0.68 | -0.83 / -0.32 / -0.25 | matched PRISM >> random |
| Neural v4, n=5-6 | 0.01-0.06 | -0.20 to -0.25 | high hit rates at small scale |
| Neural v4, n=7 parity | 0.02 | -0.06 | PRISM ~ random |
| Deceptive | 0.65 (smooth!) | +0.78 | everything fails |

rho1 recovers the matched operator on 3/3 typed landscapes without
running any search; FDC's sign and magnitude separate "search pays"
(strongly negative) from "needle in a haystack" (near zero) from
"deceptive" (positive — smooth but pointing away). The resulting
pre-flight diagnostic — sample a few hundred evaluations, read off the
matched operator and whether evolutionary search should beat random —
is now a mandatory step for every new PRISM application, and, we
suggest, for permutation-search applications generally.

### 5.7 Lightweight Reinforcement Learning

PRISM was also tested as an RL ordering framework through two small benchmarks.

The first benchmark, `option_route_grid`, is a deterministic semi-MDP. Each
permutation item is a navigation option to a landmark. The genome orders the
options. Fitness is episodic return after executing the option sequence.

The second benchmark, `chain_curriculum`, is a tabular Q-learning chain. Each
permutation item is a curriculum goal. Fitness combines final target
performance with a small training-efficiency term.

Results:

| Benchmark | Operator | Hit rate | Mean gap to exact best |
| --- | --- | ---: | ---: |
| option_route_grid | swap | 0.25 | 5.50 |
| option_route_grid | inversion | 0.625 | 1.75 |
| chain_curriculum | swap | 0.75 | about 0.00003 |
| chain_curriculum | insert | 1.00 | 0.00000 |

These results show that PRISM can transfer to reinforcement settings when the
RL problem exposes a finite ordering surface. The RL-specific work is in the
fitness wrapper, not in the PRISM loop itself.

## 6. Discussion

PRISM is strongest when:

- the candidate components are fixed,
- ordering matters,
- the permutation space is small or medium sized,
- evaluation is deterministic or can be stabilized through repeated trials,
- the landscape type suggests a suitable mutation operator.

The reinforcement-learning proof of concept is especially useful because it
clarifies the framework boundary. PRISM is not a new low-level RL control
algorithm. It is a meta-level ordering optimizer that can sit above RL tasks,
options, curricula, or modules.

## 7. Limitations

The current evidence is promising but preliminary:

- **PRISM's advantage over random sampling is landscape-conditional in two
  independent ways.** The mutation operator must match the landscape type
  (Section 5.3; mitigated by the portfolio), and the landscape's top end
  must have exploitable locality at all (Section 5.6: on the n=7 neural
  landscape, FDC ~ -0.06, PRISM is statistically indistinguishable from
  uniform random sampling under a distinct-evaluation cost model). Any
  application claim must ship with the locality diagnostic and a
  random-without-replacement baseline.
- Default hyperparameters (population 20, mutation rate 0.05) are n<=6
  settings; at n>=7 they cause premature convergence. Scale-aware settings
  (population >= 40, mutation rate >= 0.5) restore full exploration.
- The polynomial-runtime behavior is landscape-conditional: deceptive
  landscapes defeat all tested operators, and mismatched fixed operators fail
  on plateau-rich landscapes (mitigated but not eliminated by the portfolio).
- The original (v2) neural toy benchmarks did not use every permutation
  position and had stochastic fitness; those results should be read through
  the corrections in Section 5.1. The v4 benchmarks fix both flaws but remain
  small (n = 5).
- Synthetic landscapes are idealized single-type instances; real ordering
  problems mix landscape types.
- The PRISM-RL benchmarks are intentionally lightweight and not competitive RL
  benchmarks.
- The current theoretical writeup needs primary-source verification and careful
  assumption auditing before publication (including the operator
  classification, currently cited from a secondary synthesis).
- Larger tasks may require caching, parallel evaluation, noise-aware selection,
  or surrogate models.

## 8. Next Work

The most useful next steps are:

1. Scale the v4 benchmark design beyond n = 5 (enumeration becomes impossible;
   use the portfolio and report regret against best-known).
2. Apply PRISM to LLM reasoning-chain ordering (a precedence-type problem;
   insert or portfolio mutation predicted).
3. Test the portfolio on the deceptive landscape and explore smarter credit
   assignment (UCB, windowed rewards) for the adaptive mode.
4. Scale PRISM-RL to stochastic gridworld option ordering or curriculum
   ordering across multiple small tasks.
5. Map each theoretical claim to a formal proof and primary references.

## 9. Conclusion

PRISM provides a compact framework for optimizing the order of fixed components.
The current implementation, theory, synthetic scaling evidence, completed
operator-landscape study, portfolio mechanism, exactly-enumerated benchmark
ground truth, and lightweight RL extension support the central claim that
ordering alone is a meaningful search surface. The operator story is the
strongest experimental arc: operator-landscape matching is a requirement, not
a tuning choice, and it can be automated at a bounded constant-factor cost.
The strongest near-term scientific contribution is not that PRISM replaces
neural architecture search or reinforcement learning, but that it isolates and
studies a reusable class of ordering problems with a simple, analyzable
evolutionary algorithm whose failure modes are mapped as carefully as its
successes.
