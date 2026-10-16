"""Study A: corrected GSM8K scoring as primary. Recomputes truth and success rates."""

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: F401,E402
from fresh_budget import run as run_protocol  # noqa: E402
from optimizers import run_method  # noqa: E402
from prism_search.distances import DISTANCES, OPERATOR_DISTANCE  # noqa: E402
from sample_complexity import FULL_PAIRS, OPERATORS, _pearson, regime_of, rho1_estimate  # noqa: E402

OUT = os.path.join(common.HERE, "results", "corrected_scoring.json")
SEEDS = 40


def truth(rec):
    keys = list(rec.table)
    fits = np.array([rec.table[k] for k in keys])
    rhos = {op: rho1_estimate(keys, rec.table, op, np.random.default_rng(7), FULL_PAIRS) for op in OPERATORS}
    op = max(OPERATORS, key=rhos.__getitem__)
    opt = list(rec.optima)
    dist = np.array([min(DISTANCES[OPERATOR_DISTANCE[op]](list(k), list(o)) for o in opt) for k in keys])
    fdc = _pearson(fits, dist)
    return {"rho1": rhos, "true_operator": op, "true_fdc": fdc, "true_regime": regime_of(fdc),
            "n_optima": len(opt), "min": float(fits.min()), "max": float(fits.max()), "mean": float(fits.mean())}


def success(rec, method, B):
    hits = 0
    for s in range(SEEDS):
        if method == "protocol":
            o, _, _ = run_protocol(rec.table, rec.optima, rec.n, B, s, "protocol")
        else:
            o = run_method(method, rec.table, rec.optima, rec.n, B, s)
        hits += int(o.hit is not None and o.hit <= B)
    return hits / SEEDS


def main():
    t0 = time.time()
    res = {}
    for label, corrected in (("corrected", True), ("original", False)):
        rec = common.load(corrected)[common.GSM]
        res[label] = {"truth": truth(rec)}
        for B in (100, 200):
            res[label][f"B{B}"] = {m: success(rec, m, B) for m in ("uniform", "ls_swap", "ea_portfolio", "protocol")}
        print(label, json.dumps(res[label]["truth"]), res[label]["B100"], flush=True)
    c, o = res["corrected"], res["original"]
    res["A1"] = {"operator_unchanged": c["truth"]["true_operator"] == o["truth"]["true_operator"],
                 "regime_unchanged": c["truth"]["true_regime"] == o["truth"]["true_regime"]}
    b = c["B100"]
    res["A2_order_uniform_lt_protocol_lt_swap_at_100"] = b["uniform"] < b["protocol"] < b["ls_swap"]
    res["A3"] = {"n_optima": c["truth"]["n_optima"], "min": c["truth"]["min"], "max": c["truth"]["max"]}
    json.dump(res, open(OUT, "w"), indent=2)
    print("A1", res["A1"], "A2", res["A2_order_uniform_lt_protocol_lt_swap_at_100"], "A3", res["A3"], f"{time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
