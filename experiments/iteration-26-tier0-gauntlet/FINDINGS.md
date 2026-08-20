# Iteration 26 — what Tier 0 actually found

Companion to the auto-generated `TIER0_REPORT.md`, which reports the numbers.
This file states what they mean, including the places the numbers are weaker
than they look.

**Cost: US$0.** 7,800 optimizer runs, 75 estimator sweeps, 20 resolution
sweeps — all CPU, all replayed against landscapes enumerated in earlier
iterations. Hypotheses were committed at `32f4d9d` before any result existed.

---

## 1. Six of seven pre-registered hypotheses hold; one is falsified

| ID | Claim | Outcome |
|---|---|---|
| H27 | On "search pays" landscapes, some method decisively beats uniform | **HOLDS** — 8 of 11 |
| H28 | No method decisively beats uniform on the LLM landscape | **HOLDS** — but see §2 |
| H29 | Precedence surrogate is top-2 on `kendall_n7` | **HOLDS** — decisively |
| H30 | Charging the probe keeps the protocol within 10pp of uniform | **HOLDS** — worst −0.025 |
| H31 | Regime accuracy ≥0.90 at m=200 on clear-margin landscapes | **HOLDS** — 0.986 mean |
| H32 | Operator agreement ≥0.90 at m≥100 on typed synthetics | **HOLDS** — 0.953 |
| H33 | LLM regime call unstable below q=16 | **FALSIFIED** |

---

## 2. H28 holds, but partly for the wrong reason — state this plainly

`uniform` reaches a **true** optimum on the flagship GSM8K landscape in **100% of
40 seeds by budget 50**. No method can beat 1.0, so at that budget the
hypothesis is confirmed by saturation rather than by evidence.

The honest comparison is at budget 15, the only unsaturated point:

| method | success@15 | Wilson | mean evals to optimum |
|---|---|---|---|
| eda_precedence | 0.850 | [0.709, 0.929] | 8.57 |
| surrogate_precedence | 0.825 | [0.681, 0.913] | 8.47 |
| **uniform** | **0.800** | **[0.652, 0.895]** | **10.85** |
| simulated_annealing | 0.775 | [0.625, 0.877] | 11.35 |
| ea_portfolio | 0.725 | [0.572, 0.839] | 9.43 |
| prism_protocol | 0.650 | [0.495, 0.779] | 12.78 |
| ls_insert | 0.500 | [0.352, 0.648] | 17.27 |

**H28 survives on the merits**: no method's Wilson lower bound clears uniform's
upper bound. The best structured methods reach an optimum about 2.4 evaluations
sooner than random out of roughly 11 — real, but nowhere near decisive, and two
methods are *worse* than random.

This is the published "PRISM ≈ random on language-model landscapes" result,
now replicated against **twelve** alternative optimizers instead of one. That is
a materially stronger negative result than the paper currently claims, and it is
the honest headline of E0.1.

---

## 3. The protocol's three wrong calls all look alike

Pooling the pre-flight's regime call against what the gauntlet observed, over
15 landscapes at the largest budget where uniform had not saturated:

- **10 of 15 calls correct.**
- **3 wrong in the costly direction** — called "search pays", search did not win:
  `llm_gsm8k_n6`, `xor_n5`, `xor_n6`.
- **2 wrong in the safe direction** — called "random competitive", search won
  anyway: `sciml_cubic_oscillator`, `sciml_lotka_volterra`.

The three costly errors share a property the decision rule does not look at:

| landscape | FDC | optimum density | distinct fitness values |
|---|---|---|---|
| llm_gsm8k_n6 | −0.364 | **8.33%** | 29 |
| xor_n5 | −0.341 | **6.67%** | 7 |
| xor_n6 | −0.225 | **4.58%** | 8 |
| *(8 correct "search pays" calls)* | −0.043 … −0.824 | **≤1.67%** | 7 … 565 |

Within the "search pays" branch the separation is clean: every wrong call has
optimum density ≥4.58%, every correct one ≤1.67%. The reading is that
**fitness–distance correlation says the landscape is well-guided, but says
nothing about whether there is anything left to win.** When 8% of orderings are
already optimal, uniform sampling trips over one in about eleven draws and
guidance cannot pay for itself.

**Scope this honestly.** It is post-hoc, it rests on 11 landscapes, and the
separation is *not* clean over all 15 (`deceptive_n7` has the lowest density of
any landscape and search still loses there, correctly predicted by the deceptive
branch). It is a candidate second gate on one branch, not a law — `density_gate.py`
tests and reports exactly this, including the failure of the broader version.

---

## 4. H33 falsified: the regime call is more robust than assumed

Registered claim: the LLM regime call destabilises below 16 questions, dropping
under 80% agreement at q=8. Measured on the flagship: **93.3% agreement at q=8**,
and 88.3% even at q=4. Falsified.

But the picture across all six language-model landscapes is the interesting part:

| landscape | full-set call | agreement at q=8 |
|---|---|---|
| llm_gsm8k_n6 | search_pays | 0.933 |
| llm_gsm8k_n8 | search_pays | 0.967 |
| llm_gemma_n6 | search_pays | 0.967 |
| llm_qwen_n6 | search_pays | 0.950 |
| **llm_llama_n6** | random_competitive | **0.317** |
| **llm_math500_n8** | random_competitive | **0.350** |

The unstable ones are exactly the landscapes whose FDC sits **near a decision
boundary**. This is the same law E0.2 measures directly: call stability is
governed by the margin between the statistic and the threshold, not by the
number of questions. A landscape far from the boundary is callable on four
questions; one near it is not callable on a hundred.

**This changes a recommendation.** `publication/iclr-2027/02_EXPERIMENT_PROGRAM.md`
justified experiment E1 (200 questions, US$30) as buying regime-call stability.
It does not — the call was already stable. E1 is still worth running, but for a
different and narrower reason: more questions reduce the **tie density** that
§3 identifies as the actual cause of the protocol's costly errors, and finer
fitness granularity is what makes "found the optimum" a meaningful metric on
this landscape at all. The pre-registered reversal consequence has been applied.

---

## 5. Estimator sample complexity behaves like the theory

Regime and operator agreement against the full-enumeration truth, over 200
resampled probes per landscape:

| probe m | regime agreement | operator agreement | mean \|FDC error\| |
|---|---|---|---|
| 20 | 0.705 | 0.577 | 0.186 |
| 50 | 0.816 | 0.695 | 0.109 |
| 100 | 0.866 | 0.754 | 0.075 |
| 200 | 0.909 | 0.814 | 0.047 |
| 500 | 0.959 | 0.857 | 0.025 |

The error falls by a factor of 7.4 as m rises by a factor of 25; √25 = 5, so the
decay is close to the m^(−1/2) the Fisher-transform argument predicts, slightly
faster. `sample_complexity.py` records the predicted flip rate alongside the
observed one per landscape so the two can be compared directly.

The practical statement the paper can now make: **a 200-evaluation probe returns
the right regime call about 91% of the time overall, and ≥95.5% on every
landscape whose statistic sits at least 0.10 from a decision boundary.**

---

## 6. The precedence surrogate result replicates, hard

On `kendall_n7` — a pure precedence landscape with a single optimum in 5,040:

| method | mean evaluations to the optimum |
|---|---|
| **surrogate_precedence** | **14.88** |
| surrogate_positional | 59.23 |
| eda_precedence | 82.12 |
| ls_swap | 85.08 |
| iterated_local_search | 94.67 |

Iteration 12 reported 13.5 for the same method against 55.7 for elitist search.
Independently reimplemented here, it lands at 14.88 — a four-fold margin over the
next-best method, confirmed against a much wider field. Encoding-matched
surrogates are the strongest single finding in the gauntlet.

---

## 7. Charging the probe does not sink the protocol

`prism_protocol` spends ~20% of its budget on the pre-flight and is charged for
it. Against uniform at **equal total budget**, success@100 differs by:

worst case **−0.025** (`parity_n5`), best case **+0.225** (`parity_n7`,
`sciml_lotka_volterra`), positive on 11 of 15 landscapes.

This answers the "the diagnostic will cost more than it saves" objection with a
measurement rather than an argument.

---

## 8. What this does and does not buy the ICLR submission

**Closed.** The "baselines are too weak" objection: twelve optimizers, equal
distinct-evaluation budgets, probe cost charged, exact optima, 40 seeds, Wilson
intervals. The "where is the theory" objection now has a sample-complexity
statement with matching empirics.

**Strengthened.** The central negative result is no longer one method tying
another; it is twelve methods failing to decisively beat random sampling on the
flagship landscape.

**Newly exposed, and this is the uncomfortable one.** The protocol got **3 of 15**
regime calls wrong in the costly direction, and the paper's current decision rule
has no mechanism that would catch them. §3 proposes one. A reviewer who runs the
released artifact will find these three cases, so the paper is better off naming
them first.

**Not closed.** Breadth. Everything here is a replay of landscapes the project
already owned; no new task, model family, or wording set was added. That is what
Tier 1 is for.
