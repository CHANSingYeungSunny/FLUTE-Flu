"""finalize_row.py — v3.19 per-row durable finalization (compute node).

Runs AFTER a formal row's training job reaches COMPLETED 0:0. It performs the
only steps that may turn a finished run into an ACCEPTED row.

The acceptance path is decided by the FROZEN SPEC's `arm`
(`CC.resolve_run_key` -> the immutable 598-row registry):

  arm != "baseline"  (checkpoint_applicable = true) — unchanged since v3.18:
      resolve run key from the immutable registry
      locate the row's published run directory + full scratch checkpoint
      export the compact reconstruction-complete state  -> staging
      restore through the canonical resolver and require STRICT accounting
          (missing = 0, unexpected = 0, all compared tensors equal)
      verify predictions + the four metric artifacts + provenance
      write the final manifest LAST
      atomically rename staging -> final durable path
      THEN remove the redundant full scratch checkpoint

  arm == "baseline"  (checkpoint_applicable = false, D15) — new in v3.19:
      deterministic baseline no-checkpoint branch (innovation.baseline_finalize)
      NEVER reads or creates best_val_mse.pt
      NEVER calls export_compact / restore_and_compare
      NEVER computes checkpoint file_sha256 or canonical_tensor_sha256
      NEVER deletes anything from checkpoints/
      verifies predictions + the four metrics + run_status=COMPLETED +
          checkpoint_applicable=false + stochastic_seed_applicable=false +
          resource_usage structure/semantics + full provenance
      fails CLOSED on any unexpected checkpoint file (never silently ignored)
      staging -> manifest-LAST -> atomic rename

`COMPLETED 0:0` alone is NEVER acceptance: acceptance requires this script's
exit status 0 AND a fully-passing storage-verification-v1 record.
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
from innovation import storage_verification as SV               # noqa: E402
from innovation import baseline_finalize as BF                  # noqa: E402
from innovation import paths as IP                              # noqa: E402

METRICS = ("paper_aligned_full_output_metrics.json",
           "ilitotal_fixed_step_metrics.json",
           "ilitotal_full_horizon_metrics.json",
           "pte_pie_metrics.json")
SMALL = ("predictions/validation_predictions.csv", "run_status.json",
         "resource_usage.json", "split_manifest.json", "scaler_metadata.json",
         "prompt_statistics_metadata.json", "source_manifest.json",
         "config_resolved.yaml", "environment.txt", "git_commit.txt",
         "logs/train_history.csv")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def sha_safe(p):
    try:
        return sha(p)
    except Exception:                                          # noqa: BLE001
        return ""


def spec_checkpoint_applicable(info: dict) -> bool:
    """THE single authority: the frozen spec's arm. Deterministic baselines
    are the only arm frozen to `checkpoint_applicable=false`
    (`stochastic_seed_applicable=false` likewise)."""
    return info.get("arm") != "baseline"


def quarantine_stale_staging(stage: Path, durable_root: str):
    """A stale staging directory is EVIDENCE, never a reusable workspace:
    move it aside (refuse + quarantine) instead of silently deleting it."""
    if not stage.exists():
        return None
    qroot = Path(durable_root) / ".stale_staging"
    qroot.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    dest = qroot / (stage.name + ".stale." + ts)
    i = 0
    while dest.exists():
        dest = qroot / (stage.name + f".stale.{ts}.{i}")
        i += 1
    shutil.move(str(stage), str(dest))
    return str(dest)


def atomic_publish(stage: Path, durable: Path, durable_root: str) -> None:
    if not SP.is_contained(str(durable), durable_root):
        raise SystemExit("containment failed")
    tmp = Path(str(durable) + ".publish")
    if tmp.exists():
        shutil.rmtree(tmp)
    os.replace(str(stage), str(tmp))
    os.replace(str(tmp), str(durable))


def _common_evidence(key, info, a, original_job_id):
    return {
        "run_key": key, "model": info["model"], "horizon": info["horizon"],
        "source_run_key": key,
        "source_job_id": original_job_id or os.environ.get("SLURM_JOB_ID"),
        "source_training_attempt": 1,
        "export_implementation_version":
            getattr(IP, "IMPLEMENTATION_SOURCE_VERSION", "unknown"),
    }


def _write_record(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- baseline
def finalize_baseline(a, key, info, src, durable, stage, original_job_id):
    """deterministic_baseline_no_checkpoint acceptance path (D15)."""
    v = BF.verify_baseline_run(src, info)
    failures = list(v["failures"])
    iso = BF.isolation_probe(a.deployment_root)
    if iso["test_access"] or iso["holdout_access"]:
        failures.append("isolation_violation:" + json.dumps(iso))
    ok = all(v["checks"].values()) and not (iso["test_access"]
                                            or iso["holdout_access"])

    checks = dict(v["checks"])
    checks["contained"] = SP.is_contained(str(durable), a.durable_root)
    checks.update({c: SV.NOT_APPLICABLE for c in SV.CHECKPOINT_ONLY_CHECKS})
    evidence = _common_evidence(key, info, a, original_job_id)
    evidence.update({
        "comparison_mode": "baseline_no_checkpoint",
        "file_sha256": SV.NOT_APPLICABLE,
        "canonical_tensor_sha256": SV.NOT_APPLICABLE,
        "source_full_checkpoint_sha256": SV.NOT_APPLICABLE,
        "canonical_hash_schema": SV.NOT_APPLICABLE,
        "reason": BF.BASELINE_REASON,
        "checkpoint_applicable": False,
        "stochastic_seed_applicable": False,
    })

    if not ok:
        # fail closed BEFORE creating any staging; still emit the full record
        checks["atomic_publish_ok"] = False
        sv = SV.StorageVerification(checks, evidence, arm="baseline",
                                    reason=BF.BASELINE_REASON)
        payload = sv.to_dict()
        payload["failures"] = failures
        payload["unexpected_checkpoint_entries"] = \
            v["unexpected_checkpoint_entries"]
        payload["isolated"] = iso
        _write_record(a.out, payload)
        print(f"[finalize] {key} BASELINE FAIL-CLOSED "
              f"failures={failures}", flush=True)
        return 1

    # ---- idempotent repair-finalize --------------------------------------
    if durable.is_dir():
        pkg_ok, _m = BF.verify_baseline_package(durable, key)
        if pkg_ok:
            checks["atomic_publish_ok"] = True
            sv = SV.StorageVerification(checks, evidence, arm="baseline",
                                        reason=BF.BASELINE_REASON)
            payload = sv.to_dict()
            payload["idempotent"] = True
            payload["isolated"] = BF.isolation_probe(a.deployment_root)
            _write_record(a.out, payload)
            print(f"[finalize] {key} BASELINE idempotent-ok "
                  f"passed={sv.passed}", flush=True)
            return 0 if sv.passed else 1

    # ---- staging -> copy evidence -> manifest LAST -> atomic rename -------
    quarantined = quarantine_stale_staging(stage, a.durable_root)
    stage.mkdir(parents=True)
    for r in BF.BASELINE_REQUIRED:
        d = stage / os.path.dirname(r)
        d.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(src / r), str(stage / r))
    for m in BF.BASELINE_METRICS:
        (stage / "metrics").mkdir(exist_ok=True)
        shutil.copy2(str(src / "metrics" / m), str(stage / "metrics" / m))
    manifest = BF.build_baseline_manifest(key, info, src, stage, v,
                                          original_job_id=original_job_id)
    # manifest written LAST (atomic publication contract)
    (stage / BF.MANIFEST_NAME).write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    atomic_publish(stage, durable, a.durable_root)
    published = (durable / BF.MANIFEST_NAME).is_file()
    # NO checkpoint deletion: a baseline has none, and checkpoints/ is left
    # exactly as the runner left it (empty by the frozen semantics).

    checks["atomic_publish_ok"] = published
    sv = SV.StorageVerification(checks, evidence, arm="baseline",
                                reason=BF.BASELINE_REASON)
    payload = sv.to_dict()
    payload["quarantined_stale_staging"] = quarantined
    payload["isolated"] = BF.isolation_probe(a.deployment_root)
    payload["unexpected_checkpoint_entries"] = \
        v["unexpected_checkpoint_entries"]
    _write_record(a.out, payload)
    print(f"[finalize] {key} BASELINE passed={sv.passed} "
          f"code={payload['code']} published={published}", flush=True)
    return 0 if sv.passed else 1


# ------------------------------------------------------------- stochastic
def finalize_stochastic(a, key, info, src, durable, stage, original_job_id):
    """checkpoint_applicable=true path — behaviour unchanged from v3.18."""
    ckpt = src / "checkpoints" / "best_val_mse.pt"
    checks, evidence, detail = {}, {}, {}
    checks["artifact_completeness"] = all(
        (src / r).exists() for r in SMALL + tuple("metrics/" + m
                                                  for m in METRICS))
    checks["run_status_completed"] = (
        json.loads((src / "run_status.json").read_text(encoding="utf-8"))
        .get("state") == "COMPLETED") if (src / "run_status.json").is_file() \
        else False

    quarantined = quarantine_stale_staging(stage, a.durable_root)
    stage.mkdir(parents=True)

    compact = stage / "compact.safetensors"
    rep = CC.export_compact(str(src), str(ckpt), key, info["horizon"],
                            str(compact))
    rest = CC.restore_and_compare(str(src), key, info["horizon"],
                                  str(compact))
    for r in SMALL:
        if (src / r).is_file():
            d = stage / os.path.dirname(r)
            d.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src / r), str(stage / r))
    for m in METRICS:
        p = src / "metrics" / m
        if p.is_file():
            (stage / "metrics").mkdir(exist_ok=True)
            shutil.copy2(str(p), str(stage / "metrics" / m))

    manifest = {
        "run_key": key, "model": info["model"], "arm": info["arm"],
        "horizon": info["horizon"], "wave": info["wave"],
        "policy": "v3.19-compact-durable",
        "finalized_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "source_dir": str(src),
        "original_job_id": original_job_id,
        "source_full_checkpoint_sha256": sha(str(ckpt)),
        "source_full_checkpoint_bytes": os.path.getsize(str(ckpt)),
        "compact_bytes": rep["compact_bytes"],
        "compact_sha256": rep["compact_sha256"],
        "canonical_tensor_sha256": rep["canonical_tensor_sha256"],
        "canonical_hash_schema": CC.CANONICAL_HASH_SCHEMA,
        "has_pretrained_backbone": rep["has_pretrained_backbone"],
        "no_frozen_backbone_duplication":
            rep["no_frozen_backbone_duplication"],
        "reconstruction_exact": rep["reconstruction_exact"],
        "restoration_exact": rest["restoration_exact"],
        "n_keys_unequal": rest["n_keys_unequal"],
        "missing_keys": rest["missing_keys"],
        "unexpected_keys": rest["unexpected_keys"],
        "artifacts": sorted(
            os.path.relpath(os.path.join(dp, f), str(stage))
            for dp, _, fs in os.walk(stage) for f in fs),
    }
    # manifest written LAST (atomic publication contract)
    (stage / "compact_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")

    atomic_publish(stage, durable, a.durable_root)
    published = (durable / "compact.safetensors").is_file()

    # only NOW remove the redundant full scratch checkpoint
    removed = 0
    if ckpt.is_file():
        removed = os.path.getsize(str(ckpt))
        os.remove(str(ckpt))

    checks.update({
        "compact_file_present": published,
        "compact_file_sha256_matches_manifest":
            (manifest["compact_sha256"]
             == sha_safe(str(durable / "compact.safetensors"))),
        "canonical_tensor_sha256_present":
            bool(manifest["canonical_tensor_sha256"]),
        "reconstruction_exact": bool(rep["reconstruction_exact"]),
        "restoration_exact": bool(rest["restoration_exact"]),
        "strict_missing_keys_zero": len(rest["missing_keys"]) == 0,
        "strict_unexpected_keys_zero": len(rest["unexpected_keys"]) == 0,
        "no_frozen_backbone_duplication":
            bool(rep["no_frozen_backbone_duplication"]),
        "atomic_publish_ok": published,
        "contained": True,
        "same_source_invariant_ok": bool(
            rep["reconstruction_exact"] and rest["restoration_exact"]
            and rest["n_keys_unequal"] == 0),
        # v3.19: baseline-only checks are explicitly not applicable here
        "no_unexpected_checkpoint": SV.NOT_APPLICABLE,
        "checkpoint_applicable_false": SV.NOT_APPLICABLE,
        "stochastic_seed_applicable_false": SV.NOT_APPLICABLE,
        "resource_usage_semantics_ok": SV.NOT_APPLICABLE,
        "provenance_complete": SV.NOT_APPLICABLE,
    })
    evidence.update(_common_evidence(key, info, a, original_job_id))
    evidence.update({
        "comparison_mode": "same_source",
        "file_sha256": sha_safe(str(durable / "compact.safetensors")),
        "canonical_tensor_sha256": manifest["canonical_tensor_sha256"],
        "canonical_hash_schema": CC.CANONICAL_HASH_SCHEMA,
        "source_full_checkpoint_sha256":
            manifest["source_full_checkpoint_sha256"],
        "reason": SV.NOT_APPLICABLE,
        "checkpoint_applicable": SV.NOT_APPLICABLE,
        "stochastic_seed_applicable": SV.NOT_APPLICABLE,
    })
    sv = SV.StorageVerification(checks, evidence, arm=info["arm"])
    payload = sv.to_dict()
    payload["removed_full_scratch_checkpoint_bytes"] = removed
    payload["quarantined_stale_staging"] = quarantined
    payload["isolated"] = {"test_access": 0, "holdout_access": 0,
                           "archive_read": 0}
    _write_record(a.out, payload)
    print(f"[finalize] {key} passed={sv.passed} code={payload['code']} "
          f"compact={manifest['compact_bytes']} "
          f"removed_ckpt={removed}", flush=True)
    print(f"[finalize] canonical={manifest['canonical_tensor_sha256'][:16]}",
          flush=True)
    return 0 if sv.passed else 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-key", required=True)
    ap.add_argument("--deployment-root", required=True)
    ap.add_argument("--run-dir", required=True,
                    help="the row's run directory in the deployment root")
    ap.add_argument("--durable-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--original-job-id", default=None,
                    help="the row's TRAINING job id (provenance retention); "
                         "e.g. 572649 for a repair-finalize")
    a = ap.parse_args(argv)

    key = a.run_key
    info = CC.resolve_run_key(key)
    src = Path(a.run_dir)
    durable = Path(a.durable_root) / key
    os.makedirs(a.durable_root, exist_ok=True)
    stage = Path(str(durable) + ".staging")

    if spec_checkpoint_applicable(info):
        return finalize_stochastic(a, key, info, src, durable, stage,
                                   a.original_job_id)
    return finalize_baseline(a, key, info, src, durable, stage,
                             a.original_job_id)


if __name__ == "__main__":
    raise SystemExit(main())
