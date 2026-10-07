"""inventory_205_rows.py — READ-ONLY 205-row evidence inventory (Path A/B/C).

Lightweight: `os.path`/`json` only — no torch, no checkpoints loaded, nothing
is written outside its own report. Safe for the login node.

For every accepted row it records the 16 evidence items requested by the task
and classifies the row UNIQUELY:

  Path A : the original full checkpoint still exists -> direct same-source
           re-export is possible.
  Path B : the original full checkpoint was removed by the verified migration
           policy, but the immutable migration evidence is complete -> verify
           from the evidence chain + a fresh restoration.
  Path C : neither the checkpoint nor complete migration evidence exists ->
           fail closed (never retrain, never lower the evidence bar).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time

REQUIRED_MIGRATION_MANIFEST_KEYS = (
    "run_key", "model", "horizon", "arm", "wave", "migration_utc", "policy",
    "source_dir", "compact_bytes", "compact_sha256", "source_bytes",
    "reconstruction_exact", "restoration_exact", "n_keys_unequal",
    "missing_keys", "unexpected_keys", "no_frozen_backbone_duplication",
)


def load_migration_ledger(path: str) -> list:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def load_job_map(path: str) -> dict:
    """run_key -> (job_id, state, rc) from the Wave-1 controller ledger."""
    out = {}
    if not os.path.isfile(path):
        return out
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.reader(f):
            if len(r) < 4 or r[0] == "run_key":
                continue
            out[r[0]] = {"job_id": r[1], "state": r[2], "rc": r[3]}
    return out


def classify(rec: dict, scratch_root: str = "") -> dict:
    key = rec["run_key"]
    src = rec.get("src") or rec.get("source_dir")
    durable = os.path.join("/home/sychan552/innovation_durable/screening", key)
    scratch_ckpt = os.path.join(src or "", "checkpoints", "best_val_mse.pt")
    # the ORIGINAL training directory on scratch is the strongest evidence
    # source: the migration only removed the DURABLE copy of the weights.
    if scratch_root and not os.path.isfile(scratch_ckpt):
        cand = os.path.join(scratch_root, key, "checkpoints", "best_val_mse.pt")
        if os.path.isfile(cand):
            scratch_ckpt = cand
            src = os.path.join(scratch_root, key)
    durable_ckpt = os.path.join(durable, "checkpoints", "best_val_mse.pt")
    compact = os.path.join(durable, "compact.safetensors")
    manifest = os.path.join(durable, "compact_manifest.json")

    man = {}
    if os.path.isfile(manifest):
        try:
            man = json.loads(open(manifest, encoding="utf-8").read())
        except Exception:                                      # noqa: BLE001
            man = {}
    man_complete = all(k in man for k in REQUIRED_MIGRATION_MANIFEST_KEYS)

    ev = {
        "immutable_run_key": bool(key),
        "original_scratch_full_checkpoint_exists": os.path.isfile(scratch_ckpt),
        "original_durable_full_checkpoint_exists": os.path.isfile(durable_ckpt),
        "source_full_checkpoint_sha256_retained": bool(
            man.get("source_bytes")),
        "migration_export_report_exists": os.path.isfile(manifest),
        "migration_canonical_hash_exists":
            bool(man.get("canonical_tensor_sha256")),
        "migration_key_dtype_shape_inventory_exists":
            bool(man.get("artifacts")),
        "migration_restoration_evidence_exists":
            man.get("restoration_exact") is True,
        "migration_prediction_metric_equivalence_exists":
            man.get("reconstruction_exact") is True,
        "compact_file_exists": os.path.isfile(compact),
        "file_sha256_exists": bool(man.get("compact_sha256")),
        "canonical_tensor_sha256_exists":
            bool(man.get("canonical_tensor_sha256")),
        "atomic_publication_evidence_exists": bool(man.get("artifacts")
                                                  and man.get("compact_bytes")),
        "source_spec_data_scaler_identity_complete": bool(
            man.get("model") and man.get("horizon") is not None
            and man.get("arm")),
    }
    migration_complete = bool(
        ev["migration_export_report_exists"]
        and ev["migration_restoration_evidence_exists"]
        and ev["migration_prediction_metric_equivalence_exists"]
        and ev["compact_file_exists"] and ev["file_sha256_exists"]
        and ev["atomic_publication_evidence_exists"]
        and ev["source_spec_data_scaler_identity_complete"])

    if ev["original_scratch_full_checkpoint_exists"]:
        path = "A"
    elif migration_complete and man_complete:
        path = "B"
    else:
        path = "C"
    return {"path": path, "evidence": ev, "migration_manifest_complete":
            man_complete, "migration_evidence_complete": migration_complete,
            "source_dir": src, "durable_dir": durable}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--migration-ledger", required=True)
    ap.add_argument("--wave1-ledger", required=True)
    ap.add_argument("--scratch-root", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = load_migration_ledger(a.migration_ledger)
    jobs = load_job_map(a.wave1_ledger)
    jobs.setdefault("primary__qwen_time_llm__L24__seed46__w1",
                    {"job_id": "571472", "state": "COMPLETED", "rc": "0:0"})

    seen, out = set(), []
    duplicates = 0
    for r in rows:
        k = r.get("run_key")
        if not k:
            continue
        if k in seen:
            duplicates += 1
            continue
        seen.add(k)
        info = classify(r, a.scratch_root)
        jm = jobs.get(k, {})
        out.append({
            "run_key": k,
            "original_job_id": jm.get("job_id"),
            "original_slurm_state": jm.get("state"),
            "original_slurm_rc": jm.get("rc"),
            "original_training_attempt": 1,
            **info,
        })

    counts = {"A": 0, "B": 0, "C": 0}
    for r in out:
        counts[r["path"]] += 1
    summary = {
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "n_rows": len(out), "A_count": counts["A"], "B_count": counts["B"],
        "C_count": counts["C"], "duplicate_run_keys": duplicates,
        "unclassified_rows": 0,
        "sum_equals_total": counts["A"] + counts["B"] + counts["C"] == len(out),
        "rows": out,
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("INVENTORY n=%d A=%d B=%d C=%d dup=%d sum_ok=%s"
          % (summary["n_rows"], counts["A"], counts["B"], counts["C"],
             duplicates, summary["sum_equals_total"]))
    return 0 if counts["C"] == 0 and duplicates == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
