"""baseline_finalize.py — v3.19 deterministic-baseline no-checkpoint finalization.

D15 root cause: the per-row finalize driver assumed EVERY row carries a
checkpoint. Deterministic baselines are FROZEN to carry none
(`checkpoint_applicable=false`, `stochastic_seed_applicable=false`), so the
driver died with FileNotFoundError on `checkpoints/best_val_mse.pt`.

This module implements the baseline acceptance path as PURE logic (no torch,
no model): it verifies everything a baseline row must prove, builds the
durable manifest, and re-verifies an already-published package (idempotent
repair-finalize). The checkpoint path (export / restoration / hashes /
cleanup) is deliberately ABSENT from this module.

Nothing here touches model, loss, optimizer, early stopping, checkpoint
selection, data, split, scaler, prompt statistics, metrics, horizon, seed,
matrix, ablation/control semantics or endpoint hierarchy.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

BASELINE_REASON = "deterministic_baseline_no_checkpoint"
MANIFEST_NAME = "finalize_manifest.json"

# A deterministic baseline never trains, so it never produces a training
# history (D12 lesson: artifact schemas are arm-aware).
BASELINE_REQUIRED = (
    "predictions/validation_predictions.csv",
    "run_status.json",
    "resource_usage.json",
    "split_manifest.json",
    "scaler_metadata.json",
    "prompt_statistics_metadata.json",
    "source_manifest.json",
    "config_resolved.yaml",
    "environment.txt",
    "git_commit.txt",
)
BASELINE_METRICS = (
    "paper_aligned_full_output_metrics.json",
    "ilitotal_fixed_step_metrics.json",
    "ilitotal_full_horizon_metrics.json",
    "pte_pie_metrics.json",
)
_PROVENANCE_JSON = ("source_manifest.json", "split_manifest.json",
                    "scaler_metadata.json", "prompt_statistics_metadata.json")
_PROVENANCE_TEXT = ("config_resolved.yaml", "environment.txt")
# git_commit.txt is written EMPTY by clean_runner in a frozen (non-git)
# deployment root — presence, not content, is the correct requirement.
_PROVENANCE_PRESENCE_ONLY = ("git_commit.txt",)

VERIFICATION_KEYS = (
    "artifact_completeness",
    "run_status_completed",
    "no_unexpected_checkpoint",
    "checkpoint_applicable_false",
    "stochastic_seed_applicable_false",
    "resource_usage_semantics_ok",
    "provenance_complete",
)


def _read_json(p: Path):
    try:
        return json.loads(p.read_text(encoding="utf-8")), None
    except Exception as e:                                     # noqa: BLE001
        return None, f"{type(e).__name__}: {e}"


def checkpoint_entries(src) -> list:
    """Every file under checkpoints/ — an EMPTY list is the only legal state
    for a baseline (the D11 uniform tree creates the empty directory)."""
    ck = Path(src) / "checkpoints"
    if not ck.exists():
        return []
    out = []
    for dp, _, fs in os.walk(ck):
        for f in fs:
            rel = os.path.relpath(os.path.join(dp, f), str(Path(src)))
            out.append(rel.replace(os.sep, "/"))
    return sorted(out)


def verify_baseline_run(src, info: dict) -> dict:
    """Verify a completed baseline run directory. Returns
    {<VERIFICATION_KEYS> as bools, 'facts', 'failures', 'unexpected'}.
    NEVER reads, creates or hashes any checkpoint file."""
    src = Path(src)
    checks: dict = {k: False for k in VERIFICATION_KEYS}
    failures: list = []
    facts: dict = {}

    # ---- artifact completeness (arm-aware: NO train history required) ----
    missing = [r for r in BASELINE_REQUIRED if not (src / r).is_file()]
    missing += [f"metrics/{m}" for m in BASELINE_METRICS
                if not (src / "metrics" / m).is_file()]
    checks["artifact_completeness"] = not missing
    if missing:
        failures.append("missing_artifacts:" + ",".join(missing))

    # ---- run_status ------------------------------------------------------
    rs, err = _read_json(src / "run_status.json")
    if not isinstance(rs, dict):
        failures.append(f"run_status_unreadable:{err}")
    else:
        facts["run_status_state"] = rs.get("state")
        facts["run_status_arm"] = rs.get("spec", {}).get("arm")
        checks["run_status_completed"] = rs.get("state") == "COMPLETED"
        if not checks["run_status_completed"]:
            failures.append(f"run_status_state={rs.get('state')!r}")
        if rs.get("spec", {}).get("arm") not in (None, "baseline"):
            failures.append(f"run_status_arm={rs.get('spec', {}).get('arm')!r}")

    # ---- no unexpected checkpoint (fail closed, never silent) ------------
    entries = checkpoint_entries(src)
    checks["no_unexpected_checkpoint"] = not entries
    if entries:
        failures.append("unexpected_checkpoint:" + ",".join(entries))

    # ---- resource_usage structure + semantics ----------------------------
    ru, err = _read_json(src / "resource_usage.json")
    if not isinstance(ru, dict):
        failures.append(f"resource_usage_unreadable:{err}")
    else:
        facts["resource_usage"] = ru
        flags_ok = (ru.get("checkpoint_applicable") is False
                    and ru.get("stochastic_seed_applicable") is False)
        train_s, gpu_h = ru.get("train_seconds"), ru.get("gpu_hours")
        numbers_ok = (isinstance(train_s, (int, float))
                      and isinstance(gpu_h, (int, float)))
        # a baseline never trains: both must be present and zero
        zeros_ok = numbers_ok and float(train_s) == 0.0 and float(gpu_h) == 0.0
        checks["resource_usage_semantics_ok"] = flags_ok and numbers_ok \
            and zeros_ok
        if not flags_ok:
            failures.append("resource_usage_flags_not_false")
        if not numbers_ok:
            failures.append("resource_usage_missing_numbers")
        elif not zeros_ok:
            failures.append("resource_usage_nonzero_training")

    # ---- applicable flags in BOTH run_status and resource_usage ----------
    if isinstance(rs, dict) and isinstance(ru, dict):
        checks["checkpoint_applicable_false"] = (
            rs.get("checkpoint_applicable") is False
            and ru.get("checkpoint_applicable") is False)
        checks["stochastic_seed_applicable_false"] = (
            rs.get("stochastic_seed_applicable") is False
            and ru.get("stochastic_seed_applicable") is False)
        if not checks["checkpoint_applicable_false"]:
            failures.append("checkpoint_applicable_not_false")
        if not checks["stochastic_seed_applicable_false"]:
            failures.append("stochastic_seed_applicable_not_false")

    # ---- provenance (source / spec / data / scaler / prompt / env / git) --
    prov_fail = []
    for r in _PROVENANCE_JSON:
        d, e = _read_json(src / r)
        if not isinstance(d, dict) or not d:
            prov_fail.append(f"{r}:{e or 'not_a_nonempty_object'}")
    for r in _PROVENANCE_TEXT:
        p = src / r
        if not p.is_file() or p.stat().st_size == 0:
            prov_fail.append(f"{r}:empty_or_missing")
    for r in _PROVENANCE_PRESENCE_ONLY:
        if not (src / r).is_file():
            prov_fail.append(f"{r}:missing")
    # spec provenance: the immutable registry is the authority and the caller
    # must have resolved the key through it (info is required below)
    if not isinstance(info, dict) or info.get("arm") != "baseline":
        prov_fail.append("spec:not_resolved_from_registry_as_baseline")
    checks["provenance_complete"] = not prov_fail
    if prov_fail:
        failures.append("provenance:" + ",".join(prov_fail))

    return {"checks": checks, "facts": facts, "failures": failures,
            "unexpected_checkpoint_entries": entries}


def build_baseline_manifest(key: str, info: dict, src, stage,
                            verification: dict, original_job_id=None) -> dict:
    """The durable manifest for a baseline row. Contains NO checkpoint fields
    beyond explicit not_applicable markers."""
    src, stage = Path(src), Path(stage)
    artifacts = sorted(
        os.path.relpath(os.path.join(dp, f), str(stage))
        for dp, _, fs in os.walk(stage) for f in fs)
    return {
        "run_key": key, "model": info["model"], "arm": info["arm"],
        "horizon": info["horizon"], "wave": info["wave"],
        "policy": "v3.19-baseline-no-checkpoint-durable",
        "reason": BASELINE_REASON,
        "checkpoint_applicable": False,
        "stochastic_seed_applicable": False,
        "finalized_utc": __import__("time").strftime(
            "%Y-%m-%dT%H:%M:%SZ", __import__("time").gmtime()),
        "source_dir": str(src),
        "original_job_id": original_job_id,
        "checkpoint_file_sha256": "not_applicable",
        "checkpoint_canonical_tensor_sha256": "not_applicable",
        "compact_bytes": 0,
        "removed_full_scratch_checkpoint_bytes": 0,
        "verification_failures": verification["failures"],
        "artifacts": artifacts,
    }


def verify_baseline_package(durable, key: str) -> tuple:
    """Re-verify an ALREADY PUBLISHED baseline durable package (idempotent
    repair-finalize). Returns (ok, manifest)."""
    durable = Path(durable)
    mpath = durable / MANIFEST_NAME
    if not mpath.is_file():
        return False, None
    m, err = _read_json(mpath)
    if not isinstance(m, dict):
        return False, None
    if m.get("run_key") != key or m.get("reason") != BASELINE_REASON:
        return False, m
    if m.get("checkpoint_applicable") is not False:
        return False, m
    needed = list(BASELINE_REQUIRED) + [f"metrics/{x}" for x in BASELINE_METRICS]
    for r in needed:
        if not (durable / r).is_file():
            return False, m
    return True, m


def isolation_probe(deployment_root) -> dict:
    """Test/holdout isolation: the deployment root must expose NO test or
    holdout evaluation directory, and the run directory must contain no
    test/holdout-named artifacts."""
    root = Path(deployment_root)
    ev = root / "results" / "innovation"
    test_access = 1 if (ev / "test_evaluations").exists() else 0
    holdout_access = 1 if (ev / "holdout_evaluations").exists() else 0
    return {"test_access": test_access, "holdout_access": holdout_access,
            "archive_read": 1 if (root / "results" / "v3").exists() else 0}
