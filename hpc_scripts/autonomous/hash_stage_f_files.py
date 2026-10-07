"""hash_stage_f_files.py — sha256 of each Stage F run's validation predictions and
resolved config (read-only; outside the frozen hash).

Usage: python hash_stage_f_files.py <deployment_root> <cohort_manifest.json> <out.json>
"""
from __future__ import annotations

import hashlib
import json
import os
import sys


def _sha(p):
    try:
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return ""


def main() -> int:
    root, man_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
    man = json.load(open(man_path, encoding="utf-8"))
    out = {}
    for c in man["cohort"]:
        rid = c["run_id"]
        d = os.path.join(root, "results", "innovation", "runs", rid)
        out[rid] = {
            "val_pred_sha": _sha(os.path.join(d, "predictions",
                                              "validation_predictions.csv")),
            "config_sha": _sha(os.path.join(d, "config_resolved.yaml")),
        }
    json.dump(out, open(out_path, "w", encoding="utf-8"), indent=1)
    print("[hash] hashed %d Stage F runs -> %s" % (len(out), out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
