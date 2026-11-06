#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""build_cdc_vintage.py -- TASK 4, v8/cdc_vintage scope ONLY.

Rebuilds cdc_vintage.csv EXCLUSIVELY from the raw HTTP response bodies saved by
the curl commands recorded in T4_VERDICT.md (http_evidence/*.body). No value is
typed in by hand; every row must come from a body that was actually fetched
with HTTP 200. Duplicate (epiweek, issue) pairs returned by different queries
are asserted identical before being collapsed.
"""
from __future__ import annotations

import csv
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(BASE, "http_evidence")

Q1 = "https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501-201510"
Q2 = "https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201449-201501&issues=201501,201502"
Q3 = "https://api.delphi.cmu.edu/epidata/fluview/?regions=nat&epiweeks=201501&issues=201501"

SOURCES = [
    ("delphi_vintage_201501.body", Q1),
    ("delphi_multiweek.body", Q2),
]
CROSS_CHECK = ("delphi_issue_201501.body", Q3)

CORE = ("epiweek", "issue", "release_date", "region", "wili", "lag")
FIELDS = [
    "epiweek", "issue", "release_date", "region", "wili", "lag",
    "affected_weeks", "source_url", "source_type", "cdc_official_revision_id",
]


def load(name):
    with open(os.path.join(EV, name), "r", encoding="utf-8") as fh:
        return json.load(fh)


def key(r):
    return (int(r["epiweek"]), int(r["issue"]))


def core(r):
    return tuple(r[k] for k in CORE)


rows = {}
duplicate_checks = []
for fname, url in SOURCES:
    payload = load(fname)
    assert payload.get("result") == 1, (fname, payload.get("result"))
    assert payload.get("message") == "success", (fname, payload.get("message"))
    for r in payload["epidata"]:
        k = key(r)
        rec = {c: r[c] for c in CORE}
        rec["source_url"] = url
        rec["source_type"] = "delphi_epidata_fluview_v4_issue_proxy"
        rec["cdc_official_revision_id"] = "NOT_AVAILABLE"
        if k in rows:
            assert core(rows[k]) == core(rec), (
                "conflicting values for %s between queries: %s vs %s"
                % (k, core(rows[k]), core(rec)))
            duplicate_checks.append(k)
        else:
            rows[k] = rec

# Q3 (single issue) must agree field-for-field with the Q1 row it repeats.
q3 = load(CROSS_CHECK[0])
assert q3.get("result") == 1, q3.get("result")
for r in q3["epidata"]:
    k = key(r)
    assert k in rows, "Q3 row not present in fetched set: %s" % (k,)
    assert core(rows[k]) == core(r), "Q3 disagrees with Q1 for %s" % (k,)

# "affected weeks" = epiweeks in this fetched sample that were actually revised
# (at least two distinct issues AND at least two distinct wili values).
by_week = {}
for (wk, _iss), rec in rows.items():
    by_week.setdefault(wk, []).append(rec)
affected = sorted(wk for wk, rs in by_week.items()
                  if len({x["wili"] for x in rs}) >= 2)
affected_str = ";".join(str(w) for w in affected)
for rec in rows.values():
    rec["affected_weeks"] = affected_str

out = os.path.join(BASE, "cdc_vintage.csv")
with open(out, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
    w.writeheader()
    for k in sorted(rows):
        w.writerow(rows[k])

print("rows=%d" % len(rows))
print("distinct_epiweeks=%d" % len(by_week))
print("distinct_issues=%d" % len({k[1] for k in rows}))
print("affected_weeks=%s" % affected_str)
print("duplicate_cross_checks=%d %s" % (len(duplicate_checks), duplicate_checks))
print("q3_single_issue_cross_check=PASS")
print("wrote %s" % out)
