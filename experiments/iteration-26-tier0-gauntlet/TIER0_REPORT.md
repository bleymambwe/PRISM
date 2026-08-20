# Iteration 26 — Tier 0 results

**Cost: US$0.** Every number here was produced on CPU by replaying optimizers and estimators against landscapes that were already enumerated and committed. No model was called.

Hypotheses were registered in `hypotheses.json` and committed at `32f4d9d`, before any result in this file existed.


## The evidence base

| landscape | family | n | orderings | optima | density | distinct values |
|---|---|---|---|---|---|---|
| llm_gsm8k_n6 | llm | 6 | 720 | 60 | 0.0833 | 29 |
| parity_n5 | neural | 5 | 120 | 2 | 0.0167 | 13 |
| parity_n7 | neural | 7 | 5040 | 14 | 0.0028 | 16 |
| xor_n5 | neural | 5 | 120 | 8 | 0.0667 | 7 |
| xor_n6 | neural | 6 | 720 | 33 | 0.0458 | 8 |
| sciml_cubic_oscillator | sciml | 6 | 720 | 3 | 0.0042 | 315 |
| sciml_damped_oscillator | sciml | 6 | 720 | 1 | 0.0014 | 124 |
| sciml_lorenz63 | sciml | 6 | 720 | 3 | 0.0042 | 485 |
| sciml_lotka_volterra | sciml | 6 | 720 | 8 | 0.0111 | 188 |
| sciml_rossler | sciml | 6 | 720 | 1 | 0.0014 | 511 |
| sciml_vanderpol | sciml | 6 | 720 | 2 | 0.0028 | 565 |
| adjacency_n7 | synthetic | 7 | 5040 | 2 | 0.0004 | 7 |
| deceptive_n7 | synthetic | 7 | 5040 | 1 | 0.0002 | 7 |
| hamming_n7 | synthetic | 7 | 5040 | 1 | 0.0002 | 7 |
| kendall_n7 | synthetic | 7 | 5040 | 1 | 0.0002 | 22 |

`distinct values` is the number of different fitness values the landscape can express. The flagship language-model landscape resolves 720 orderings onto only 29 distinct accuracies, because 32 questions admit 33 possible scores. That is the resolution objection stated as a measurement, and it motivates the paid resolution upgrade.


## Pre-registered outcomes

| id | claim | outcome |
|---|---|---|
| H27 | On landscapes called 'search pays', some method decisively beats uniform at budget 100 | **HOLDS** |
| H28 | No method decisively beats uniform on the language-model landscape at budget 50 | **HOLDS** |
| H29 | The precedence surrogate is top-2 by evaluations-to-optimum on kendall n=7 | **HOLDS** |
| H30 | Charging the pre-flight probe keeps the protocol within 10pp of uniform at budget 100 | **HOLDS** |

### H27

- `landscapes_called_search_pays`: ['adjacency_n7', 'hamming_n7', 'kendall_n7', 'llm_gsm8k_n6', 'parity_n5', 'sciml_damped_oscillator', 'sciml_lorenz63', 'sciml_rossler', 'sciml_vanderpol', 'xor_n5', 'xor_n6']
- `decisive_winners_by_landscape`: {'adjacency_n7': ['ea_aging', 'ea_elitist', 'ea_portfolio', 'ls_inversion', 'ls_swap', 'simulated_annealing', 'surrogate_positional', 'surrogate_precedence'], 'hamming_n7': ['ea_aging', 'ea_elitist', 'ea_portfolio', 'ls_inversion', 'ls_swap', 'surrogate_positional', 'surrogate_precedence'], 'kendall_n7': ['ea_aging', 'ea_elitist', 'ea_portfolio', 'eda_precedence', 'iterated_local_search', 'ls_insert', 'ls_inversion', 'ls_swap', 'simulated_annealing', 'surrogate_positional', 'surrogate_precedence'], 'llm_gsm8k_n6': [], 'parity_n5': [], 'sciml_damped_oscillator': ['ea_elitist', 'ea_portfolio', 'iterated_local_search', 'ls_insert', 'ls_inversion', 'ls_swap', 'surrogate_positional', 'surrogate_precedence'], 'sciml_lorenz63': ['ea_aging', 'ea_elitist', 'ea_portfolio', 'eda_precedence', 'iterated_local_search', 'ls_insert', 'ls_swap', 'surrogate_precedence'], 'sciml_rossler': ['ea_aging', 'ea_elitist', 'ea_portfolio', 'eda_precedence', 'iterated_local_search', 'ls_insert', 'ls_inversion', 'ls_swap', 'surrogate_precedence'], 'sciml_vanderpol': ['ea_portfolio', 'iterated_local_search', 'ls_insert', 'ls_swap'], 'xor_n5': [], 'xor_n6': []}

### H28

- `uniform_success_at_50`: 1.0
- `decisive_winners`: []

### H29

- `ranking_by_mean_evals_to_optimum`: [['surrogate_precedence', 14.88], ['surrogate_positional', 59.23], ['eda_precedence', 82.12], ['ls_swap', 85.08], ['iterated_local_search', 94.67]]

### H30

- `protocol_minus_uniform_at_100`: {'adjacency_n7': 0.1, 'deceptive_n7': 0.0, 'hamming_n7': 0.075, 'kendall_n7': 0.075, 'llm_gsm8k_n6': 0.0, 'parity_n5': -0.025, 'parity_n7': 0.225, 'sciml_cubic_oscillator': 0.15, 'sciml_damped_oscillator': 0.1, 'sciml_lorenz63': 0.15, 'sciml_lotka_volterra': 0.225, 'sciml_rossler': 0.175, 'sciml_vanderpol': 0.075, 'xor_n5': 0.0, 'xor_n6': 0.05}
- `worst`: -0.025

## Success at budget 100, by landscape

| landscape | ea portfolio | eda precedence | ls insert | prism protocol | simulated annealing | surrogate precedence | uniform |
|---|---|---|---|---|---|---|---|
| adjacency_n7 | 0.35 | 0.15 | 0.125 | 0.1 | 0.25 | 0.725 | 0.0 |
| deceptive_n7 | 0.0 | 0.025 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| hamming_n7 | 0.375 | 0.125 | 0.025 | 0.075 | 0.1 | 0.475 | 0.0 |
| kendall_n7 | 0.35 | 0.475 | 0.525 | 0.075 | 0.3 | 1.0 | 0.0 |
| llm_gsm8k_n6 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| parity_n5 | 0.975 | 0.975 | 0.95 | 0.975 | 0.95 | 1.0 | 1.0 |
| parity_n7 | 0.275 | 0.25 | 0.3 | 0.325 | 0.275 | 0.175 | 0.1 |
| sciml_cubic_oscillator | 0.95 | 0.475 | 0.725 | 0.425 | 0.2 | 0.25 | 0.275 |
| sciml_damped_oscillator | 0.5 | 0.1 | 0.375 | 0.125 | 0.1 | 0.5 | 0.025 |
| sciml_lorenz63 | 0.925 | 0.75 | 1.0 | 0.5 | 0.55 | 0.925 | 0.35 |
| sciml_lotka_volterra | 0.95 | 0.775 | 0.775 | 0.75 | 0.55 | 0.475 | 0.525 |
| sciml_rossler | 0.675 | 0.425 | 1.0 | 0.225 | 0.15 | 0.425 | 0.05 |
| sciml_vanderpol | 0.8 | 0.175 | 0.75 | 0.45 | 0.325 | 0.225 | 0.375 |
| xor_n5 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| xor_n6 | 1.0 | 0.975 | 0.975 | 1.0 | 0.95 | 1.0 | 0.95 |

Success is the fraction of 40 seeds that evaluated a **true** global optimum within the budget. Because the landscapes are enumerated, this is exact rather than a best-observed proxy.


## Pooled calibration record

Every forecast this project registered before its outcome, in one table: **22/33 correct (66.7%)**, with 11 misses of which **5 were conservative** (the protocol said random would be competitive and search won anyway).

| source | forecasts | correct | rate | misses | conservative |
|---|---|---|---|---|---|
| gauntlet_landscape | 15 | 9 | 60.0% | 6 | 2 |
| nasbench_slice | 18 | 13 | 72.2% | 5 | 3 |

The protocol emits categorical regime calls, not probabilities, so a Brier score would require inventing confidences it never claimed. The honest calibration statement is the observed hit rate per call, reported above, together with the direction of the misses.


## E0.2 — how large must the probe be?

| probe m | landscapes | regime agreement | operator agreement | mean |FDC error| |
|---|---|---|---|---|
| 20 | 15 | 0.705 | 0.577 | 0.186 |
| 50 | 15 | 0.816 | 0.695 | 0.109 |
| 100 | 15 | 0.866 | 0.754 | 0.075 |
| 200 | 15 | 0.909 | 0.814 | 0.047 |
| 500 | 15 | 0.959 | 0.857 | 0.025 |

Agreement is measured against the call computed from the full enumeration, over 200 resampled probes per landscape.


## E0.3 — how many questions does the call need?

| landscape | questions | subset | regime agreement | operator agreement | distinct values | full call |
|---|---|---|---|---|---|---|
| llm_gsm8k_n6 | 32 | 4 | 0.8833 | 0.9667 | 5.0 | search_pays |
| llm_gsm8k_n6 | 32 | 8 | 0.9333 | 1.0 | 8.8 | search_pays |
| llm_gsm8k_n6 | 32 | 16 | 1.0 | 1.0 | 16.02 | search_pays |
| llm_gsm8k_n8 | 20 | 4 | 0.9667 | 0.5667 | 5.0 | search_pays |
| llm_gsm8k_n8 | 20 | 8 | 0.9667 | 0.4667 | 9.0 | search_pays |
| llm_gsm8k_n8 | 20 | 16 | 1.0 | 0.5667 | 16.62 | search_pays |
| llm_gemma_n6 | 32 | 4 | 1.0 | 0.5833 | 4.78 | search_pays |
| llm_gemma_n6 | 32 | 8 | 0.9667 | 0.5667 | 8.58 | search_pays |
| llm_gemma_n6 | 32 | 16 | 0.7167 | 0.55 | 15.78 | search_pays |
| llm_llama_n6 | 32 | 4 | 0.2333 | 0.4667 | 4.67 | random_competitive |
| llm_llama_n6 | 32 | 8 | 0.3167 | 0.4667 | 7.22 | random_competitive |
| llm_llama_n6 | 32 | 16 | 0.4667 | 0.5833 | 12.13 | random_competitive |
| llm_qwen_n6 | 32 | 4 | 0.6 | 0.4333 | 3.07 | search_pays |
| llm_qwen_n6 | 32 | 8 | 0.95 | 0.4 | 4.42 | search_pays |
| llm_qwen_n6 | 32 | 16 | 0.9667 | 0.1833 | 6.6 | search_pays |
| llm_math500_n8 | 100 | 4 | 0.2333 | 0.4333 | 4.5 | random_competitive |
| llm_math500_n8 | 100 | 8 | 0.35 | 0.4667 | 7.98 | random_competitive |
| llm_math500_n8 | 100 | 16 | 0.5167 | 0.3833 | 14.52 | random_competitive |
| llm_math500_n8 | 100 | 32 | 0.7667 | 0.5667 | 23.18 | random_competitive |
| llm_math500_n8 | 100 | 64 | 0.85 | 0.55 | 39.87 | random_competitive |

## E0.4 — derived landscape tables

Answer caches converted to per-ordering fitness tables, so every language-model landscape in the paper is now loadable without an API key.

| file | orderings | questions | distinct values | range |
|---|---|---|---|---|
| experiments/iteration-09/results/derived_landscape.csv | 720 | 32 | 29 | 0.0625–0.96875 |
| experiments/iteration-11/results/n8_landscape.csv | 1170 | 20 | 20 | 0.05–1.0 |
| experiments/iteration-17/results/gemma_landscape.csv | 120 | 32 | 29 | 0.03125–0.90625 |
| experiments/iteration-19-crossfamily/results/qwen_landscape.csv | 120 | 32 | 10 | 0.65625–0.96875 |
| experiments/iteration-19-crossfamily/results/llama_landscape.csv | 120 | 32 | 20 | 0.0–0.625 |
| experiments/iteration-23-experiment-s/results/math500_landscape.csv | 429 | 20-101 | 47 | 0.0–0.52 |
