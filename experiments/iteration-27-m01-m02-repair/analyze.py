"""Apply the pre-registered rules in hypotheses.json to the M01/M02 repair data."""

from __future__ import annotations

import csv
import json
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
G26 = os.path.join(HERE, "..", "iteration-26-tier0-gauntlet", "results")
RES = os.path.join(HERE, "results")
rng = np.random.default_rng(20261016)


def rows(path):
    with open(path, newline="", encoding="utf-8") as h:
        return list(csv.DictReader(h))


def boot(per_landscape: np.ndarray, reps=2000):
    """Landscape-level bootstrap CI of the mean."""
    idx = rng.integers(len(per_landscape), size=(reps, len(per_landscape)))
    m = per_landscape[idx].mean(axis=1)
    return float(per_landscape.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def per_land(table):
    names = sorted(table)
    return names, np.array([np.mean(table[n]) for n in names])


# ---------------------------- M02 ----------------------------
archive = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))  # method->B->landscape->hits
for r in rows(os.path.join(G26, "gauntlet_runs.csv")):
    for B in (15, 25, 50, 100, 200):
        archive[r["method"]][B][r["landscape"]].append(int(r[f"hit_by_{B}"]))

fresh = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
probe = defaultdict(lambda: defaultdict(list))
for r in rows(os.path.join(RES, "fresh_budget_runs.csv")):
    B = int(r["B"])
    fresh[r["method"]][B][r["landscape"]].append(int(r["hit_by_B"]))
    probe[r["method"]][B].append(int(r["probe_spent"]) / int(r["budget"]))

series = {
    "uniform": archive["uniform"], "ls_swap": archive["ls_swap"], "ea_portfolio": archive["ea_portfolio"],
    "protocol_archived_prefix": archive["prism_protocol"],
    "protocol_fresh": fresh["prism_protocol"], "protocol_floor_fresh(exploratory)": fresh["prism_floor"],
}
Bs = (15, 25, 50, 100, 200)
macro = {k: {B: boot(per_land(v[B])[1]) for B in Bs} for k, v in series.items()}


def diff(a, b, B):
    na, xa = per_land(a[B]); nb, xb = per_land(b[B])
    assert na == nb
    return boot(xa - xb)


h1 = diff(fresh["prism_protocol"], archive["ls_swap"], 100)
h2 = diff(fresh["prism_protocol"], archive["uniform"], 100)
repro = {}
for n in sorted(fresh["prism_protocol"][200]):
    repro[n] = (sum(archive["prism_protocol"][200][n]), sum(fresh["prism_protocol"][200][n]))
h3 = {B: float(np.mean(probe["prism_protocol"][B])) for B in Bs}

# ---------------------------- M01 ----------------------------
dp = rows(os.path.join(RES, "deployable_probe.csv"))
old = rows(os.path.join(G26, "sample_complexity.csv"))
old_by_m = defaultdict(list)
for r in old:
    old_by_m[int(r["probe_m"])].append(float(r["regime_agreement"]))
agree = defaultdict(lambda: defaultdict(dict))
cost = defaultdict(lambda: defaultdict(list))
sp = defaultdict(lambda: defaultdict(dict))
for r in dp:
    m = int(r["m_target"])
    agree[r["variant"]][m][r["landscape"]] = (float(r["regime_agreement"]), float(r["operator_agreement"]))
    cost[r["variant"]][m].append(float(r["mean_distinct_evals"]))
    if r["true_regime"] != "search_pays":
        sp[r["variant"]][m][r["landscape"]] = float(r["frac_search_pays"])
Ms = (20, 50, 100, 200, 500)
reg = {v: {m: boot(np.array([x[0] for x in agree[v][m].values()])) for m in Ms} for v in agree}
opa = {v: {m: boot(np.array([x[1] for x in agree[v][m].values()])) for m in Ms} for v in agree}
h5 = {}
for m in Ms:
    names = sorted(sp["deployed_proxy"][m])
    h5[m] = boot(np.array([sp["deployed_proxy"][m][n] - sp["crossfit"][m][n] for n in names]))

out = {
    "M02": {"macro_success": macro, "H27-1_protocol_minus_ls_swap@100": h1, "H27-2_protocol_minus_uniform@100": h2,
            "H27-3_probe_fraction": h3, "B200_repro_archived_vs_fresh_hits_of_40": repro},
    "M01": {"regime_agreement": reg, "operator_agreement": opa, "old_oracle_regime_agreement_mean": {m: float(np.mean(old_by_m[m])) for m in Ms},
            "mean_distinct_evals": {v: {m: float(np.mean(cost[v][m])) for m in Ms} for v in cost},
            "H27-5_proxy_minus_crossfit_search_pays_rate_on_non_search_pays": h5},
}
json.dump(out, open(os.path.join(RES, "hypothesis_outcomes.json"), "w"), indent=2)


def fmt(t):
    return f"{100*t[0]:.1f}% [{100*t[1]:.1f}, {100*t[2]:.1f}]"


L = ["# M01 / M02 repair results", "", "Landscape-bootstrap 95% CIs (2000 resamples). All 15 landscapes, 40 seeds (M02) / 200 resamples (M01).", "",
     "## M02: success@B, macro over 15 landscapes", "", "| Policy | B=15 | B=25 | B=50 | B=100 | B=200 |", "|---|---|---|---|---|---|"]
for k in series:
    L.append(f"| {k} | " + " | ".join(fmt(macro[k][B]) for B in Bs) + " |")
L += ["", f"**H27-1** protocol(fresh) - ls_swap @100: {fmt(h1)} pts. Pre-registered falsifier (CI wholly above 0): {'YES' if h1[1] > 0 else 'no'}.",
      f"**H27-2** protocol(fresh) - uniform @100: {fmt(h2)} pts. Supported (CI wholly above 0): {'YES' if h2[1] > 0 else 'no'}.",
      "**H27-3** probe share of budget (fresh protocol): " + ", ".join(f"B={B}: {100*h3[B]:.0f}%" for B in Bs) +
      f". Pre-registered >=80% at B=15 and 25: {'holds' if h3[15] >= .8 and h3[25] >= .8 else 'does not hold'}.", "",
      "B=200 reproduction (hits of 40, archived vs fresh): " + "; ".join(f"{n} {a}/{b}" for n, (a, b) in repro.items()), "",
      "## M01: deployed probe, every evaluation charged", "",
      "| Charged calls m | Deployed regime agr. | Cross-fit regime agr. | Deployed operator agr. | Old oracle estimator (mean) | Deployed mean evals charged |", "|---|---|---|---|---|---|"]
for m in Ms:
    L.append(f"| {m} | {fmt(reg['deployed_proxy'][m])} | {fmt(reg['crossfit'][m])} | {fmt(opa['deployed_proxy'][m])} | {100*np.mean(old_by_m[m]):.1f}% | {np.mean(cost['deployed_proxy'][m]):.0f} |")
r200 = reg["deployed_proxy"][200]
L += ["", f"**H27-4** deployed regime agreement at m=200: {fmt(r200)} vs 91% claimed. Supported (upper CI < 91%): {'YES' if r200[2] < .91 else 'no'}.",
      "**H27-5** proxy minus cross-fit rate of calling search_pays, on landscapes whose truth is not search_pays: " +
      "; ".join(f"m={m}: {fmt(h5[m])} pts" for m in Ms),
      "", "**H27-6** the old estimator's 7m raw accesses vs measured charge above.",
      "", "Caveats: FDC thresholds (-0.15, 0.30) were chosen on these same landscapes earlier and are not validated out of sample. Truth rho1 is a 20,000-pair estimate. 15 landscapes are not a sample from a defined population, so the CIs describe sensitivity to the landscape set, not generalization."]
open(os.path.join(RES, "REPORT.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L))
