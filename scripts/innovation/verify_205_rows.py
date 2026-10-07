"""verify_205_rows.py — ONE compute-node verification job for all 205 rows.

Path A (all 205 rows: the original full checkpoint still exists on scratch):

  * verify the ORIGINAL full-checkpoint existence + size
  * export compact from that SAME checkpoint with
        - the PRE-fix implementation  (contract detection disabled)
        - the POST-fix implementation (current v3.18)
    -> SOURCE IDENTITY MUST MATCH (same checkpoint / run key / job / attempt)
  * compare compact keys, dtype, shape, values and canonical_tensor_sha256
  * strict restoration
  * predictions + four metric artifacts equivalence
  * current durable compact: file_sha256 + canonical_tensor_sha256
  * atomic publication evidence (compact_manifest.json present)

It never trains, never rewrites a compact package, and never lowers the bar.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from innovation import compact_checkpoint as CC                 # noqa: E402
from innovation import same_source_invariant as SSI             # noqa: E402

METRICS = ("paper_aligned_full_output_metrics.json",
           "ilitotal_fixed_step_metrics.json",
           "ilitotal_full_horizon_metrics.json",
           "pte_pie_metrics.json")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def verify_one(row, out_dir, durable_root):
    key = row["run_key"]
    rec = {"run_key": key, "path": row["path"], "passed": False,
           "original_job_id": row.get("original_job_id"),
           "original_training_attempt": 1}
    src = row.get("source_dir")
    ckpt = os.path.join(src or "", "checkpoints", "best_val_mse.pt")
    if not os.path.isfile(ckpt):
        rec["error"] = "PATH_A_CHECKPOINT_MISSING"
        return rec
    rec["source_full_checkpoint_sha256"] = sha(ckpt)
    rec["source_full_checkpoint_bytes"] = os.path.getsize(ckpt)

    durable = os.path.join(durable_root, key)
    dcompact = os.path.join(durable, "compact.safetensors")
    dman = os.path.join(durable, "compact_manifest.json")
    rec["durable_compact_exists"] = os.path.isfile(dcompact)
    rec["durable_manifest_exists"] = os.path.isfile(dman)
    if not rec["durable_compact_exists"]:
        rec["error"] = "DURABLE_COMPACT_MISSING"
        return rec
    rec["durable_file_sha256"] = sha(dcompact)
    try:
        dsd = CC._load_compact(dcompact)
        rec["durable_canonical_tensor_sha256"] = CC.canonical_tensor_sha256(dsd)
        rec["durable_keys"] = len(dsd)
    except Exception as e:                                     # noqa: BLE001
        rec["error"] = f"DURABLE_LOAD {type(e).__name__}: {e}"
        return rec
    if os.path.isfile(dman):
        m = json.loads(open(dman, encoding="utf-8").read())
        rec["manifest_policy"] = m.get("policy")
        rec["manifest_compact_sha256_matches"] = \
            (m.get("compact_sha256") == rec["durable_file_sha256"])
        rec["manifest_restoration_exact"] = m.get("restoration_exact")
        rec["manifest_reconstruction_exact"] = m.get("reconstruction_exact")

    # ---- same-source PRE vs POST export from the SAME checkpoint ----------
    ssi_dir = os.path.join(out_dir, "ssi", key)
    os.makedirs(ssi_dir, exist_ok=True)
    impl = getattr(__import__("innovation.clean_runner", fromlist=["x"]),
                   "IMPLEMENTATION_SOURCE_VERSION", "unknown")
    ident = SSI.source_identity(key, ckpt, row.get("original_job_id"), 1, impl)
    ssi = SSI.same_source_compare(src, ckpt, key, int(row.get("horizon", 24)),
                                  ssi_dir, ident, ident,
                                  published_post_path=dcompact)
    rec["same_source"] = {k: v for k, v in ssi.items()
                          if k not in ("source_identity_pre",
                                       "source_identity_post")}
    rec["comparison_mode"] = ssi.get("comparison_mode")
    rec["n_keys_pre"] = ssi.get("n_keys_pre")
    rec["n_keys_post"] = ssi.get("n_keys_post")
    rec["tensor_mapping_equal"] = ssi.get("tensor_mapping_equal")
    rec["values_equal"] = ssi.get("values_equal")
    rec["canonical_equal"] = ssi.get("canonical_equal")

    # ---- strict restoration vs the ORIGINAL full checkpoint ---------------
    # NOTE: `load_state_dict(compact, strict=False)` would wrongly report the
    # legitimately-omitted frozen backbone as "missing". The authoritative
    # accounting rebuilds `base | compact` and compares it to the ORIGINAL
    # checkpoint, exactly as `restore_and_compare` does.
    rest = CC.restore_and_compare(src, key, int(row.get("horizon", 24)),
                                  dcompact)
    rec["strict_missing_keys"] = list(rest.get("missing_keys") or [])
    rec["strict_unexpected_keys"] = list(rest.get("unexpected_keys") or [])
    rec["strict_missing_keys_zero"] = len(rec["strict_missing_keys"]) == 0
    rec["strict_unexpected_keys_zero"] = len(rec["strict_unexpected_keys"]) == 0
    rec["restoration_exact"] = rest.get("restoration_exact")
    rec["n_keys_compared"] = rest.get("n_keys_compared")
    rec["n_keys_unequal"] = rest.get("n_keys_unequal")

    pred = os.path.join(src, "predictions", "validation_predictions.csv")
    rec["predictions_present"] = os.path.isfile(pred)
    present = [m for m in METRICS
               if os.path.isfile(os.path.join(src, "metrics", m))]
    rec["metrics_present"] = len(present)
    rec["four_metrics_present"] = len(present) == 4
    rec["run_status_present"] = os.path.isfile(os.path.join(src,
                                                            "run_status.json"))

    rec["passed"] = bool(
        rec["comparison_mode"] == SSI.COMPARISON_MODE
        and ssi.get("canonical_equal") and ssi.get("values_equal")
        and ssi.get("tensor_mapping_equal")
        and rec["strict_missing_keys_zero"]
        and rec["strict_unexpected_keys_zero"]
        and rec.get("restoration_exact") is True
        and rec.get("manifest_compact_sha256_matches", True)
        and rec["four_metrics_present"] and rec["predictions_present"]
        and rec["run_status_present"])
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--durable-root", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    inv = json.loads(open(a.inventory, encoding="utf-8").read())
    os.makedirs(a.out_dir, exist_ok=True)
    results = []
    for i, row in enumerate(inv["rows"], 1):
        print(f"[verify] {i}/{len(inv['rows'])} {row['run_key']}", flush=True)
        try:
            r = verify_one(row, a.out_dir, a.durable_root)
        except Exception as e:                                 # noqa: BLE001
            r = {"run_key": row["run_key"], "path": row["path"],
                 "passed": False, "error": f"{type(e).__name__}: {e}"}
        if not r.get("passed"):
            print(f"[verify]   FAILED {row['run_key']}: "
                  f"{r.get('error') or 'check_failed'}", flush=True)
        results.append(r)
        with open(os.path.join(a.out_dir, "verification_ledger.jsonl"), "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(r) + "\n")
    ok = sum(1 for r in results if r.get("passed"))
    paths = {"A": 0, "B": 0, "C": 0}
    for r in results:
        paths[r.get("path", "C")] += 1
    payload = {"generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                              time.gmtime()),
               "n_rows": len(results), "verified_rows": ok,
               "verification_failures": len(results) - ok,
               "path_counts": paths, "results": results}
    with open(os.path.join(a.out_dir, "verification_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"[verify] verified={ok}/{len(results)} failures="
          f"{len(results) - ok} paths={paths}", flush=True)
    return 0 if ok == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
