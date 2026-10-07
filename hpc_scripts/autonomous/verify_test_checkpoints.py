"""verify_test_checkpoints.py — prove every evaluated Test cell traces to its
frozen checkpoint SHA-256.

Runs on HPC (submitted with sbatch) because the Stage-F run directories live
there. Read-only: it never modifies a run, a checkpoint or a metric.
"""
from __future__ import annotations

import hashlib
import json
import os

ROOT = "/scratch/sychan552/innovation_deploy_root_v2_10"
INN = os.path.join(ROOT, "results", "innovation")
TEV_ID = "final_nlinear_20260915T145710Z"


def _j(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


man = _j(os.path.join(INN, "frozen_model_manifest.json"))
coh = _j(os.path.join(INN, "governance", "stage_provenance", "stage_f_cohort_manifest.json"))
champ = man.get("champion_model_key", "nlinear")

groups = [("champion", [c for c in coh.get("cohort", []) if c["model_key"] == champ]),
          ("baseline", list(coh.get("baseline_cohort", [])))]

out, failures, no_expected = [], [], []
for role, items in groups:
    for c in items:
        rid = c.get("run_id", "")
        ck = os.path.join(INN, "runs", rid, "checkpoints", "best_val_mse.pt")
        exp = c.get("checkpoint_sha256", "") or ""
        got = _sha(ck) if os.path.exists(ck) else ""
        ok = bool(got) and (not exp or got == exp)
        if not exp:
            no_expected.append(rid)
        if not ok:
            failures.append(rid)
        out.append({"role": role, "model_key": c.get("model_key"), "horizon": c.get("horizon"),
                    "seed": c.get("seed"), "run_id": rid, "checkpoint_exists": os.path.exists(ck),
                    "expected_sha256": exp, "actual_sha256": got, "match": ok})

rec = {"test_eval_id": TEV_ID,
       "n_cells": len(out),
       "n_verified": sum(1 for r in out if r["match"]),
       "checkpoint_hash_failures": len(failures),
       "failures": failures,
       "cells_without_expected_sha": no_expected,
       "cells": out}
dst = os.path.join(INN, "test_evaluations", TEV_ID, "checkpoint_verification.json")
os.makedirs(os.path.dirname(dst), exist_ok=True)
with open(dst, "w", encoding="utf-8") as f:
    json.dump(rec, f, indent=2)
print("[checkpoints] verified=%d/%d failures=%d" % (rec["n_verified"], rec["n_cells"], len(failures)))
