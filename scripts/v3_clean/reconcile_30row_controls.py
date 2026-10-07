"""reconcile_30row_controls.py — items 1-7: reconcile the frozen 30-row
negative-control matrix against the CURRENT wiring.

Reads ONLY the frozen matrix (never modifies it) and reports, per row, the
parent model / control / horizon / seed / intervention, then checks whether any
frozen row is silently dropped, renamed or re-interpreted by the current
implementation.
"""
from __future__ import annotations

import csv
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = (ROOT / "results" / "v3_superseded_archive" / "preregistration"
          / "proposed_negative_control_matrix.csv")
WIRING = (ROOT / "results" / "v3_clean" / "implementation"
          / "ablation_control_wiring_v2.json")
OUT = ROOT / "results" / "v3_clean" / "preregistration"
OUT.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

rows = list(csv.DictReader(open(MATRIX, encoding="utf-8")))
wiring = json.loads(WIRING.read_text(encoding="utf-8"))["variant_registry"]


def intervention_for(control: str, parent: str) -> str:
    spec = wiring.get(control, {})
    applies = spec.get("applies_to")
    if applies and parent not in applies:
        return "UNSUPPORTED_BY_CURRENT_WIRING"
    return json.dumps(spec.get("kwargs", {}), sort_keys=True)


detailed = []
for r in rows:
    ctrl = r["control"]
    parent = r["parent_model"]
    det = {"control": ctrl, "parent_model": parent, "horizon": r["horizon"],
           "seed": r["seed"], "role": r.get("role", ""),
           "counts_toward_primary_architecture":
               r.get("counts_toward_primary_architecture", ""),
           "intervention": intervention_for(ctrl, parent)}
    detailed.append(det)

by_control = defaultdict(list)
for d in detailed:
    by_control[d["control"]].append(d)

summary = {}
for ctrl, ds in by_control.items():
    parents = sorted({d["parent_model"] for d in ds})
    unsupported = sorted({d["parent_model"] for d in ds
                          if d["intervention"] == "UNSUPPORTED_BY_CURRENT_WIRING"})
    summary[ctrl] = {
        "n_rows": len(ds),
        "parents_in_frozen_matrix": parents,
        "horizons": sorted({d["horizon"] for d in ds}),
        "seeds": sorted({d["seed"] for d in ds}),
        "parents_unsupported_by_current_wiring": unsupported,
    }

stop_required = []
for ctrl, s in summary.items():
    if s["parents_unsupported_by_current_wiring"]:
        stop_required.append(ctrl)

report = {
    "generated_utc": NOW,
    "matrix_file": "results/v3_superseded_archive/preregistration/"
                   "proposed_negative_control_matrix.csv",
    "matrix_rows": len(rows),
    "matrix_modified": False,
    "summary_by_control": summary,
    "controls_with_unsupported_parents": stop_required,
    "rows": detailed,
}

if stop_required:
    report["decision"] = "V3_V2_PROTOCOL_REVIEW_REQUIRED"
    report["reason"] = ("the frozen matrix contains control rows whose parent "
                        "model is not supported by the current wiring; the "
                        "original scientific meaning of those rows must be "
                        "recovered, and the matrix must NOT be edited to fit "
                        "the implementation")
else:
    report["decision"] = "RECONCILED"

json.dump(report, open(OUT / "negative_control_matrix_reconciliation.json",
                       "w", encoding="utf-8"), indent=2)

print("=== 30-row negative control matrix ===")
print("rows:", len(rows))
for ctrl, s in summary.items():
    print(f"\n{ctrl}")
    print(f"  n_rows      : {s['n_rows']}")
    print(f"  parents     : {s['parents_in_frozen_matrix']}")
    print(f"  horizons    : {s['horizons']}")
    print(f"  seeds       : {s['seeds']}")
    print(f"  unsupported : {s['parents_unsupported_by_current_wiring'] or 'none'}")
print("\ndecision:", report["decision"])
if stop_required:
    print("STOP REQUIRED for:", stop_required)
