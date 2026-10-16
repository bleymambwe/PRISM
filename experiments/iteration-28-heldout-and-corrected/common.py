"""Shared loader: iteration-26 landscapes with the corrected GSM8K table as primary."""

import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(HERE, "..", "iteration-27-m01-m02-repair"))
sys.path.insert(0, os.path.join(HERE, "..", "iteration-26-tier0-gauntlet"))
sys.path.insert(0, os.path.join(ROOT, "src"))

import _compat  # noqa: F401,E402
import landscapes as L  # noqa: E402

CORRECTED = os.path.join(ROOT, "experiments", "iteration-09", "results", "llm_landscape_q31corrected.csv")
GSM = "llm_gsm8k_n6"


def corrected_table():
    table = {}
    with open(CORRECTED, newline="", encoding="utf-8") as h:
        for r in csv.DictReader(h):
            table[tuple(json.loads(r["perm"]))] = float(r["fitness"])
    return table


def load(corrected=True):
    records = L.load_all()
    if corrected:
        old = records[GSM]
        records[GSM] = L.LandscapeRecord(GSM, old.family, old.n, corrected_table(), "q31 corrected")
    return records
