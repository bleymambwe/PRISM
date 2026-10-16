# M01 / M02 repair results

Landscape-bootstrap 95% CIs (2000 resamples). All 15 landscapes, 40 seeds (M02) / 200 resamples (M01).

## M02: success@B, macro over 15 landscapes

| Policy | B=15 | B=25 | B=50 | B=100 | B=200 |
|---|---|---|---|---|---|
| uniform | 16.2% [4.5, 30.7] | 21.5% [7.0, 37.8] | 29.5% [12.5, 48.8] | 37.7% [18.3, 58.5] | 52.5% [33.0, 72.5] |
| ls_swap | 17.5% [5.0, 32.2] | 23.5% [8.7, 40.0] | 41.2% [25.3, 58.0] | 70.5% [55.0, 83.7] | 86.2% [71.7, 98.2] |
| ea_portfolio | 17.2% [6.0, 30.3] | 26.5% [12.0, 44.0] | 39.3% [22.5, 58.5] | 67.5% [49.8, 83.0] | 87.3% [71.0, 99.0] |
| protocol_archived_prefix | 18.3% [7.3, 31.5] | 24.8% [10.2, 42.3] | 32.8% [14.8, 53.3] | 46.8% [28.8, 65.7] | 79.8% [65.3, 91.5] |
| protocol_fresh | 18.2% [6.0, 33.0] | 23.7% [9.2, 41.0] | 34.7% [16.8, 53.3] | 53.0% [37.2, 68.8] | 79.8% [65.5, 91.5] |
| protocol_floor_fresh(exploratory) | 17.5% [4.7, 32.2] | 23.5% [8.7, 41.0] | 41.2% [25.8, 58.8] | 53.0% [37.0, 69.8] | 79.8% [65.2, 91.3] |

**H27-1** protocol(fresh) - ls_swap @100: -17.5% [-27.8, -7.5] pts. Pre-registered falsifier (CI wholly above 0): no.
**H27-2** protocol(fresh) - uniform @100: 15.3% [8.3, 22.0] pts. Supported (CI wholly above 0): YES.
**H27-3** probe share of budget (fresh protocol): B=15: 93%, B=25: 56%, B=50: 34%, B=100: 22%, B=200: 24%. Pre-registered >=80% at B=15 and 25: does not hold.

B=200 reproduction (hits of 40, archived vs fresh): adjacency_n7 31/31; deceptive_n7 0/0; hamming_n7 38/38; kendall_n7 33/33; llm_gsm8k_n6 40/40; parity_n5 40/40; parity_n7 20/20; sciml_cubic_oscillator 31/31; sciml_damped_oscillator 21/21; sciml_lorenz63 34/34; sciml_lotka_volterra 38/38; sciml_rossler 34/34; sciml_vanderpol 39/39; xor_n5 40/40; xor_n6 40/40

## M01: deployed probe, every evaluation charged

| Charged calls m | Deployed regime agr. | Cross-fit regime agr. | Deployed operator agr. | Old oracle estimator (mean) | Deployed mean evals charged |
|---|---|---|---|---|---|
| 20 | 72.0% [53.6, 88.2] | 40.8% [35.5, 45.7] | 36.6% [30.3, 44.3] | 70.5% | 20 |
| 50 | 72.2% [56.5, 85.7] | 47.5% [38.4, 55.9] | 43.1% [40.0, 46.2] | 81.6% | 48 |
| 100 | 69.0% [53.5, 82.1] | 49.5% [38.6, 59.8] | 49.5% [44.1, 54.5] | 86.6% | 93 |
| 200 | 70.7% [55.3, 82.7] | 53.1% [38.6, 66.5] | 56.3% [48.7, 63.1] | 90.9% | 174 |
| 500 | 76.9% [62.7, 88.0] | 61.5% [44.4, 78.2] | 66.8% [56.9, 76.4] | 95.9% | 376 |

**H27-4** deployed regime agreement at m=200: 70.7% [55.3, 82.7] vs 91% claimed. Supported (upper CI < 91%): YES.
**H27-5** proxy minus cross-fit rate of calling search_pays, on landscapes whose truth is not search_pays: m=20: 36.4% [19.7, 53.0] pts; m=50: 22.4% [-3.5, 48.3] pts; m=100: 20.6% [-1.7, 43.0] pts; m=200: 10.4% [-7.2, 28.4] pts; m=500: 2.2% [-11.5, 19.0] pts

**H27-6** the old estimator's 7m raw accesses vs measured charge above.

Caveats: FDC thresholds (-0.15, 0.30) were chosen on these same landscapes earlier and are not validated out of sample. Truth rho1 is a 20,000-pair estimate. 15 landscapes are not a sample from a defined population, so the CIs describe sensitivity to the landscape set, not generalization.
