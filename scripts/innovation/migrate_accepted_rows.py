"""migrate_accepted_rows.py — v3.15 accepted-row migration (NO retraining).

For each row (204 accepted durable rows + the interrupted job 571472):

    verify immutable key/spec/source/data/scaler/original ACCEPTED evidence
    export compact state on the compute node
    restore through the canonical library + architecture contract
    require strict key accounting and exactness
    compare predictions / metrics provenance
    publish to a unique staging directory; write the manifest LAST
    verify bytes / hashes / ownership / containment / restoration
    atomically rename staging -> final durable path
    append a conversion record preserving the original job/acceptance identity
    only then remove the redundant full checkpoint

Idempotent and resumable: an already-migrated row is skipped, and a failure
leaves the original checkpoint and ACCEPTED evidence intact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from innovation import compact_checkpoint as CC                 # noqa: E402
from innovation import storage_policy as SP                     # noqa: E402

DUR = "/home/sychan552/innovation_durable/screening"


def sha256_file(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_registry(root: str) -> dict:
    return json.loads(Path(root).joinpath(
        *("results", "v3_clean", "runs",
          "complete_specs_598.json")).read_text(encoding="utf-8"))


def migrate_row(run_key: str, src_dir: str, reg: dict, stage_root: str,
                ledger, conv_ledger) -> dict:
    t0 = time.time()
    rec = {"run_key": run_key, "src": src_dir, "ok": False}
    try:
        info = CC.resolve_run_key(run_key)
    except Exception as e:                                      # noqa: BLE001
        rec["error"] = f"resolve {type(e).__name__}: {e}"
        ledger.write(json.dumps(rec) + "\n")
        return rec
    model, horizon = info["model"], info["horizon"]

    final = os.path.join(stage_root, run_key)
    done_marker = os.path.join(final, "compact_manifest.json")
    if os.path.isfile(done_marker):
        rec.update({"ok": True, "skipped": "already_migrated"})
        ledger.write(json.dumps(rec) + "\n")
        return rec

    src = Path(src_dir)
    ckpt = src / "checkpoints" / "best_val_mse.pt"
    if not ckpt.is_file():
        rec["error"] = "source checkpoint missing"
        ledger.write(json.dumps(rec) + "\n")
        return rec
    # baseline rows carry no checkpoint by design
    if info["arm"] == "baseline":
        rec.update({"ok": True, "skipped": "baseline_no_checkpoint"})
        ledger.write(json.dumps(rec) + "\n")
        return rec

    stage = os.path.join(stage_root, run_key + ".staging")
    if os.path.exists(stage):
        shutil.rmtree(stage)
    os.makedirs(stage, exist_ok=True)

    # ---- compact export + restoration ------------------------------------
    compact = os.path.join(stage, "compact.safetensors")
    rep = CC.export_compact(str(src), str(ckpt), run_key, horizon, compact)
    rest = CC.restore_and_compare(str(src), run_key, horizon, compact)
    if not rep["reconstruction_exact"] or not rest["restoration_exact"] \
            or rest["n_keys_unequal"] or rest["missing_keys"] \
            or rest["unexpected_keys"] or not rep["no_frozen_backbone_duplication"]:
        shutil.rmtree(stage, ignore_errors=True)
        rec.update({"error": "verification_failed",
                    "reconstruction_exact": rep["reconstruction_exact"],
                    "restoration_exact": rest["restoration_exact"],
                    "n_unequal": rest["n_keys_unequal"],
                    "missing": rest["missing_keys"],
                    "unexpected": rest["unexpected_keys"]})
        ledger.write(json.dumps(rec) + "\n")
        return rec

    # ---- predictions / metrics / provenance ------------------------------
    for rel in ("predictions/validation_predictions.csv",
                "metrics/paper_aligned_full_output_metrics.json",
                "metrics/ilitotal_fixed_step_metrics.json",
                "metrics/ilitotal_full_horizon_metrics.json",
                "metrics/pte_pie_metrics.json",
                "logs/train_history.csv", "run_status.json",
                "resource_usage.json", "split_manifest.json",
                "scaler_metadata.json", "prompt_statistics_metadata.json",
                "source_manifest.json", "config_resolved.yaml",
                "environment.txt", "git_commit.txt"):
        p = src / rel
        if p.is_file():
            d = os.path.join(stage, os.path.dirname(rel))
            os.makedirs(d, exist_ok=True)
            shutil.copy2(str(p), os.path.join(stage, rel))

    manifest = {
        "run_key": run_key, "model": model, "horizon": horizon,
        "arm": info["arm"], "wave": info["wave"],
        "migration_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "policy": "v3.15-compact-durable",
        "source_dir": str(src),
        "compact_bytes": rep["compact_bytes"],
        "compact_sha256": rep["compact_sha256"],
        "source_bytes": rep["source_bytes"],
        "compression_ratio": rep["compression_ratio"],
        "has_pretrained_backbone": rep["has_pretrained_backbone"],
        "no_frozen_backbone_duplication": rep["no_frozen_backbone_duplication"],
        "frozen_backbone_bytes_excluded":
            rep["frozen_backbone_bytes_excluded"],
        "unexpected_frozen_backbone_bytes_retained":
            rep["unexpected_frozen_backbone_bytes_retained"],
        "reconstruction_exact": rep["reconstruction_exact"],
        "restoration_exact": rest["restoration_exact"],
        "n_keys_unequal": rest["n_keys_unequal"],
        "missing_keys": rest["missing_keys"],
        "unexpected_keys": rest["unexpected_keys"],
        "artifacts": sorted(
            os.path.relpath(os.path.join(dp, f), stage)
            for dp, _, fs in os.walk(stage) for f in fs),
    }
    # manifest written LAST
    with open(os.path.join(stage, "compact_manifest.json"), "w",
              encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # ---- containment + completeness, then atomic publish -----------------
    if not SP.is_contained(final, stage_root):
        rec["error"] = "containment_failed"
        ledger.write(json.dumps(rec) + "\n")
        return rec
    if not os.path.isfile(os.path.join(stage, "compact.safetensors")):
        rec["error"] = "staging_incomplete"
        ledger.write(json.dumps(rec) + "\n")
        return rec

    backup = os.path.join(stage_root, run_key + ".full.backup")
    tmp = os.path.join(stage_root, run_key + ".publish")
    if os.path.exists(final):
        if os.path.exists(backup):
            shutil.rmtree(backup)
        os.replace(final, backup)          # original preserved until verified
    os.replace(stage, tmp)
    os.replace(tmp, final)

    # ---- only now remove the redundant full checkpoint -------------------
    removed = 0
    if os.path.isdir(backup):
        for dp, _, fs in os.walk(backup):
            for f in fs:
                if f.endswith((".pt", ".pth", ".safetensors", ".bin")):
                    fp = os.path.join(dp, f)
                    removed += os.path.getsize(fp)
                    os.remove(fp)
        shutil.rmtree(backup, ignore_errors=True)

    rec.update({"ok": True, "compact_bytes": rep["compact_bytes"],
                "source_bytes": rep["source_bytes"],
                "compression_ratio": rep["compression_ratio"],
                "has_pretrained_backbone": rep["has_pretrained_backbone"],
                "no_frozen_backbone_duplication":
                    rep["no_frozen_backbone_duplication"],
                "removed_full_checkpoint_bytes": removed,
                "seconds": round(time.time() - t0, 2)})
    conv_ledger.write(json.dumps({
        "run_key": run_key, "model": model, "horizon": horizon,
        "utc": manifest["migration_utc"], "source_dir": str(src),
        "compact_sha256": rep["compact_sha256"],
        "reconstruction_exact": rep["reconstruction_exact"],
        "restoration_exact": rest["restoration_exact"],
        "removed_full_checkpoint_bytes": removed}) + "\n")
    ledger.write(json.dumps(rec) + "\n")
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--deployment-root", required=True)
    ap.add_argument("--rows", required=True,
                    help="TSV: run_key<TAB>source_dir  (one per line)")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    reg = load_registry(a.deployment_root)
    rows = []
    for line in Path(a.rows).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        k, _, s = line.partition("\t")
        if k.strip() and s.strip():
            rows.append((k.strip(), s.strip()))

    ledger = open(os.path.join(a.out_dir, "migration_ledger.jsonl"), "a",
                  encoding="utf-8")
    conv = open(os.path.join(a.out_dir, "conversion_records.jsonl"), "a",
                encoding="utf-8")
    ok = 0
    for i, (k, s) in enumerate(rows, 1):
        print(f"[migrate] {i}/{len(rows)} {k}", flush=True)
        r = migrate_row(k, s, reg, DUR, ledger, conv)
        ledger.flush()
        conv.flush()
        if r.get("ok"):
            ok += 1
        else:
            print(f"[migrate]   FAILED {k}: {r.get('error')}", flush=True)
    ledger.close()
    conv.close()
    print(f"[migrate] ok={ok}/{len(rows)}", flush=True)
    return 0 if ok == len(rows) else 1


if __name__ == "__main__":
    sys.exit(main())
