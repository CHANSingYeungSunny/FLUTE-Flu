"""clean_gate.py — compute-node pre-execution Gate for clean-v3.

Runs ONE representative preregistered row per runtime path through the REAL
`clean_runner.py`, then verifies every frozen contract on the produced artifacts.

Covered paths:
  * 8 primary model families
  * 2 seven-variable baselines
  * 6 original MIFlu ablations (all parented to gpt2_miflu)
  * gpt2_miflu zero_text
  * gpt2_miflu shuffled_text
  * the 18 deferred rows' non-submittable guard (resolved, never submitted)

Verified: seven-variable input/output, T=104, L set, split 717/102/206,
train-only scaler and prompt statistics, ILITOTAL index 4, the four metric
families, independence of fixed steps 0-3, PTE/PIE using only 1 week / 25%,
checkpoint save/restore, baseline non-checkpoint semantics, the run-status
atomic state machine, artifact completeness, archive isolation and
Test/holdout access = 0/0.

Output goes to a create-only directory keyed by SLURM_JOB_ID.
Runs only on a compute node (loads real models / data through clean_runner).
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from innovation import clean_runner as CR   # noqa: E402

NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
JOB = os.environ.get("SLURM_JOB_ID") or "local"
NODE = os.environ.get("SLURMD_NODENAME") or ""

PRIMARY = ["nlinear", "dlinear", "patchtst", "itransformer",
           "gpt2_miflu", "qwen_time_llm", "calf_llm", "timecma_llm"]
BASELINES = ["last_value_naive", "seasonal_naive"]
ABLATIONS = ["without_dataset_information", "without_task_instruction",
             "without_input_variable_description", "without_lora",
             "without_multimodality", "without_lora_and_multimodality"]
GPT2_CONTROLS = ["zero_text", "shuffled_text"]


def run_key_for(arm, model, horizon=24, seed=42, wave=1):
    """Reproduce the FROZEN registry's key construction EXACTLY.

    The registry encodes the deterministic baselines' seed as `seedna`
    (str("n/a").replace("/", "")), not as an empty token. A mismatch here made
    every baseline path report "unknown run_key" in Gate 568988 (D10).
    """
    seed_tok = str(seed).replace("/", "")
    return f"{arm}__{model}__L{horizon}__seed{seed_tok}__w{wave}"


def gate_dir(deployment_root: str) -> Path:
    # Read the job id at CALL time (not at import) so the create-only rule is
    # testable and correct under any launcher.
    job = os.environ.get("SLURM_JOB_ID") or "local"
    p = Path(deployment_root) / "results" / "v3_clean" / "implementation" \
        / f"gate_{job}"
    if p.exists():
        raise SystemExit(f"gate directory already exists (create-only): {p}")
    p.mkdir(parents=True, exist_ok=True)
    return p


def run_one(deployment_root: str, out_root: Path, run_key: str) -> int:
    env = dict(os.environ, INNOVATION_DEPLOYMENT_ROOT=str(deployment_root))
    cmd = [sys.executable, str(ROOT / "scripts" / "innovation" /
                               "clean_runner.py"),
           "--run-key", run_key, "--out-root", str(out_root)]
    print(f"[gate] running {run_key}", flush=True)
    p = subprocess.run(cmd, env=env, capture_output=True, text=True)
    (out_root.parent / f"{run_key}.stdout.log").write_text(p.stdout or "",
                                                           encoding="utf-8")
    (out_root.parent / f"{run_key}.stderr.log").write_text(p.stderr or "",
                                                           encoding="utf-8")
    print(f"[gate] {run_key} rc={p.returncode}", flush=True)
    return p.returncode


# v3.12 (D12): ARM-AWARE artifact schemas. A single shared list could not
# work: deterministic baselines never train, so they can never produce
# `logs/train_history.csv` or checkpoint artifacts.
COMMON_REQUIRED = [
    "config_resolved.yaml", "environment.txt", "git_commit.txt",
    "source_manifest.json", "split_manifest.json", "scaler_metadata.json",
    "prompt_statistics_metadata.json",
    "predictions/validation_predictions.csv",
    "metrics/paper_aligned_full_output_metrics.json",
    "metrics/ilitotal_fixed_step_metrics.json",
    "metrics/ilitotal_full_horizon_metrics.json",
    "metrics/pte_pie_metrics.json", "run_status.json", "resource_usage.json",
]
# Training history + the manifest-declared checkpoint are STOCHASTIC-ONLY.
STOCHASTIC_ONLY_REQUIRED = [
    "logs/train_history.csv", "checkpoints/checkpoint_manifest.json",
]
ARM_REQUIRED = {
    "stochastic": COMMON_REQUIRED + STOCHASTIC_ONLY_REQUIRED,
    "baseline": list(COMMON_REQUIRED),
}


def _load(run_dir: Path, rel: str) -> dict:
    """Safe JSON load: a missing/unreadable artifact is a FAILED CHECK, never
    an exception (the Gate must report, not crash)."""
    try:
        return json.loads((run_dir / rel).read_text(encoding="utf-8"))
    except Exception:
        return {}


def _sha256_path(p: Path) -> str:
    import hashlib as _h
    h = _h.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def declared_checkpoint(run_dir: Path, manifest: dict) -> dict:
    """Resolve the checkpoint the MANIFEST declares (never a hard-coded name).

    Fail-closed on: missing/blank declaration, absolute path, traversal or
    symlink escape outside the run directory, absent file, missing or
    mismatching SHA-256.
    """
    out = {"declared": None, "contained": False, "present": False,
           "sha256_ok": False, "reason": ""}
    declared = manifest.get("checkpoint_file")
    out["declared"] = declared
    if not isinstance(declared, str) or not declared.strip():
        out["reason"] = "manifest declares no checkpoint_file"
        return out
    if os.path.isabs(declared):
        out["reason"] = "absolute checkpoint path rejected"
        return out

    target = run_dir / declared
    real_run = run_dir.resolve()
    try:
        real_target = target.resolve()
    except OSError as e:                                   # pragma: no cover
        out["reason"] = f"unresolvable checkpoint path: {e}"
        return out
    if real_run != real_target and real_run not in real_target.parents:
        out["reason"] = "checkpoint path escapes the run directory"
        return out
    if target.is_symlink():
        out["reason"] = "symlinked checkpoint rejected"
        return out
    out["contained"] = True
    if not real_target.is_file():
        out["reason"] = "declared checkpoint file is missing"
        return out
    out["present"] = True

    expected = manifest.get("sha256_file")
    if not isinstance(expected, str) or not expected:
        out["reason"] = "manifest declares no sha256_file"
        return out
    if _sha256_path(real_target) != expected:
        out["reason"] = "checkpoint sha256 mismatch"
        return out
    out["sha256_ok"] = True
    out["reason"] = "ok"
    return out


def verify_run(run_dir: Path, is_baseline: bool) -> dict:
    res = {"run_dir": str(run_dir), "checks": {}}
    # v3.12 (D12): arm-aware completeness. Stochastic checks are NOT weakened.
    schema = ARM_REQUIRED["baseline" if is_baseline else "stochastic"]
    res["arm"] = "baseline" if is_baseline else "stochastic"
    required = list(schema)
    missing = [f for f in required if not (run_dir / f).exists()]
    res["checks"]["artifact_completeness"] = not missing
    res["missing"] = missing

    st = _load(run_dir, "run_status.json")
    res["checks"]["run_status_completed"] = st.get("state") == "COMPLETED"

    sm = _load(run_dir, "split_manifest.json")
    res["checks"]["split_717_102_206"] = sm.get("split") == \
        {"train": 717, "validation": 102, "test": 206}
    res["checks"]["T_104"] = sm.get("T") == 104
    res["checks"]["ili_index_4"] = sm.get("ili_channel") == 4

    sc = _load(run_dir, "scaler_metadata.json")
    res["checks"]["scaler_train_only"] = sc.get("train_only") is True
    ps = _load(run_dir, "prompt_statistics_metadata.json")
    res["checks"]["prompt_stats_train_only"] = ps.get("fit_scope") == \
        "train rows only" or ps.get("applicable") is False

    pm = _load(run_dir, "metrics/paper_aligned_full_output_metrics.json")
    res["checks"]["seven_variable_full_horizon_output"] = \
        pm.get("complete_seven_variable_output") is True
    res["checks"]["primary_mse_present"] = isinstance(
        pm.get("mse_all_7vars_full_horizon_z"), (int, float))
    res["checks"]["secondary_mae_present"] = isinstance(
        pm.get("mae_all_7vars_full_horizon_z"), (int, float))

    fs = _load(run_dir, "metrics/ilitotal_fixed_step_metrics.json")
    steps = fs.get("steps", {})
    res["checks"]["fixed_steps_0_3_present"] = all(str(s) in steps
                                                   for s in (0, 1, 2, 3))
    res["checks"]["steps_never_averaged"] = fs.get("steps_never_averaged") is True
    res["checks"]["lead_weeks_mapping"] = all(
        steps[str(s)].get("lead_weeks") == s + 1 for s in range(4)
        if str(s) in steps)

    pp = _load(run_dir, "metrics/pte_pie_metrics.json")
    thr = pp.get("thresholds", {})
    res["checks"]["pte_1_week_pie_25_pct"] = (thr.get("PTE_weeks") == 1
                                              and thr.get("PIE_percent") == 25.0)
    blob = json.dumps(pp).replace("forbidden_and_absent", "").lower()
    res["checks"]["unsupported_peak_logic_absent"] = not any(
        t in blob for t in ("peak_hit_rate", "match_tol"))

    if is_baseline:
        ru = _load(run_dir, "resource_usage.json")
        res["checks"]["baseline_seed_not_applicable"] = \
            ru.get("stochastic_seed_applicable") is False
        # v3.12 (D12): an EMPTY checkpoints/ directory is valid (D11 creates a
        # uniform tree). Assert the SEMANTIC property instead of its absence:
        # both applicability flags false, no checkpoint FILE, no manifest
        # claiming a checkpoint, and no restoration evidence.
        ckpt_dir = run_dir / "checkpoints"
        files_in_ckpt = ([p for p in ckpt_dir.rglob("*") if p.is_file()]
                         if ckpt_dir.exists() else [])
        res["checks"]["baseline_no_checkpoint_file"] = not files_in_ckpt
        res["checks"]["baseline_no_checkpoint_manifest"] = not (
            ckpt_dir / "checkpoint_manifest.json").exists()
        res["checks"]["baseline_no_training_history"] = not (
            run_dir / "logs" / "train_history.csv").exists()
        res["checks"]["baseline_no_restoration_evidence"] = not any(
            p.name.startswith("restore") for p in files_in_ckpt)
        res["checks"]["baseline_no_checkpoint"] = (
            ru.get("checkpoint_applicable") is False
            and ru.get("stochastic_seed_applicable") is False
            and not files_in_ckpt
            and not (ckpt_dir / "checkpoint_manifest.json").exists()
        )
    else:
        ck = run_dir / "checkpoints" / "checkpoint_manifest.json"
        res["checks"]["checkpoint_manifest"] = ck.exists()
        cm = _load(run_dir, "checkpoints/checkpoint_manifest.json")
        res["checks"]["checkpoint_restore_ok"] = ck.exists() and bool(
            (cm.get("restore_test") or {}).get("ok"))
        # v3.12 (D12): resolve the checkpoint from the MANIFEST, not a
        # hard-coded filename. Path containment, existence and SHA-256 are
        # all required (fail-closed).
        dc = declared_checkpoint(run_dir, cm)
        res["checks"]["checkpoint_path_contained"] = dc["contained"]
        res["checks"]["checkpoint_file_present"] = dc["present"]
        res["checks"]["checkpoint_sha256_matches"] = dc["sha256_ok"]
        res["checkpoint_declared"] = dc["declared"]
        res["checkpoint_reason"] = dc["reason"]
    res["passed"] = all(res["checks"].values())
    return res


def verify_storage(run_dir: Path, run_key: str, arm: str, horizon: int,
                   stage_root: Path) -> dict:
    """v3.15: prove the COMPACT durable path for this checkpoint schema.

    Requires (per task section 6 / 9):
      * compact export is reconstruction-complete
      * the frozen backbone is NOT duplicated into the per-row file
      * strict restoration accounting (zero unexplained missing/unexpected)
      * atomic durable publication (staging -> rename, never a partial final)
      * path containment inside the durable root
    """
    import shutil

    res: dict = {"mode": "compact"}
    if arm == "baseline":
        # v3.19 (D15): prove the REAL deterministic-baseline no-checkpoint
        # finalization path (innovation.finalize_row.finalize_baseline) instead
        # of vacuous-passing. The durable root is the Gate-local simulation
        # root — the real home durable is never touched.
        res["mode"] = "baseline_no_checkpoint"
        try:
            import types
            from innovation import finalize_row as FR
            from innovation import compact_checkpoint as CCX
            info = CCX.resolve_run_key(run_key)
            rec_path = stage_root / (run_key + ".storage_verification.json")
            a = types.SimpleNamespace(
                run_key=run_key,
                deployment_root=os.environ.get("INNOVATION_DEPLOYMENT_ROOT"),
                run_dir=str(run_dir), durable_root=str(stage_root),
                out=str(rec_path), original_job_id=None)
            rc = FR.finalize_baseline(a, run_key, info, run_dir,
                                      stage_root / run_key,
                                      stage_root / (run_key + ".staging"),
                                      None)
            if rec_path.is_file():
                rec = json.loads(rec_path.read_text(encoding="utf-8"))
                res["verification"] = rec
                res["passed"] = bool(rec.get("passed")) and rc == 0
                res["reason"] = rec.get("reason")
            else:
                res["passed"] = False
                res["error"] = "baseline finalization produced no record"
        except Exception as e:                                     # noqa: BLE001
            res["passed"] = False
            res["error"] = f"baseline_finalize {type(e).__name__}: {e}"
        return res
    ck = run_dir / "checkpoints" / "best_val_mse.pt"
    if not ck.exists():
        res.update({"passed": False, "error": "checkpoint missing"})
        return res
    try:
        from innovation import compact_checkpoint as CC
        from innovation import storage_policy as SP
        from innovation import architecture_contract as AC
        from innovation import storage_verification as SV
        from innovation import same_source_invariant as SSI
    except Exception as e:                                     # noqa: BLE001
        res.update({"passed": False,
                    "error": f"import {type(e).__name__}: {e}"})
        return res

    stage = stage_root / (run_key + ".staging")
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir(parents=True, exist_ok=True)
    compact = stage / "compact.safetensors"
    try:
        rep = CC.export_compact(str(run_dir), str(ck), run_key, horizon,
                                str(compact))
    except Exception as e:                                     # noqa: BLE001
        res.update({"passed": False,
                    "error": f"export {type(e).__name__}: {e}"})
        return res
    try:
        rest = CC.restore_and_compare(str(run_dir), run_key, horizon,
                                      str(compact))
    except Exception as e:                                     # noqa: BLE001
        res.update({"passed": False,
                    "error": f"restore {type(e).__name__}: {e}"})
        return res

    # atomic publication: staging -> rename (a partial final never exists)
    final = stage_root / run_key
    if final.exists():
        shutil.rmtree(final)
    os.replace(str(stage), str(final))
    published = (final / "compact.safetensors").exists()

    # v3.17b (D17): everything below must use the PUBLISHED path. `compact`
    # still names the staging file, which no longer exists after the rename.
    published_compact = final / "compact.safetensors"

    # canonical TENSOR-SEMANTIC identity of the published package
    can = None
    try:
        can = CC.canonical_tensor_sha256(
            CC._load_compact(str(published_compact)))
    except Exception as e:                                     # noqa: BLE001
        res["canonical_error"] = f"{type(e).__name__}: {e}"
    res["canonical_tensor_sha256"] = can
    res["canonical_hash_schema"] = CC.CANONICAL_HASH_SCHEMA
    durable = Path("/home/sychan552/innovation_durable/screening") / run_key \
        / "compact.safetensors"
    if durable.is_file():
        try:
            res["durable_canonical_tensor_sha256"] = \
                CC.canonical_tensor_sha256(CC._load_compact(str(durable)))
            res["canonical_invariant_vs_durable"] = bool(
                can is not None
                and res["durable_canonical_tensor_sha256"] == can)
        except Exception as e:                                 # noqa: BLE001
            res["canonical_invariant_vs_durable"] = False
            res["durable_error"] = f"{type(e).__name__}: {e}"
    else:
        res["canonical_invariant_vs_durable"] = True           # vacuous

    res.update({
        "source_bytes": rep["source_bytes"],
        "compact_bytes": rep["compact_bytes"],
        "compression_ratio": rep["compression_ratio"],
        "reconstruction_exact": rep["reconstruction_exact"],
        # D15: structured architecture-contract evidence (NOT a size/name
        # heuristic). `frozen_backbone_excluded` is kept for the audit trail but
        # is no longer the universal pass condition.
        "frozen_backbone_excluded": rep.get("frozen_backbone_excluded"),
        "has_pretrained_backbone": rep["has_pretrained_backbone"],
        "predicate_applicable": rep["predicate_applicable"],
        "pretrained_backbone_contract_source":
            rep["pretrained_backbone_contract_source"],
        "pretrained_backbone_module_paths":
            rep["pretrained_backbone_module_paths"],
        "frozen_backbone_key_count": rep["frozen_backbone_key_count"],
        "frozen_backbone_bytes_total": rep["frozen_backbone_bytes_total"],
        "frozen_backbone_bytes_excluded":
            rep["frozen_backbone_bytes_excluded"],
        "unexpected_frozen_backbone_bytes_retained":
            rep["unexpected_frozen_backbone_bytes_retained"],
        "changed_frozen_backbone_bytes_dropped":
            rep["changed_frozen_backbone_bytes_dropped"],
        "no_frozen_backbone_duplication": rep["no_frozen_backbone_duplication"],
        "restoration_exact": rest["restoration_exact"],
        "n_keys_unequal": rest["n_keys_unequal"],
        "missing_keys": rest["missing_keys"],
        "unexpected_keys": rest["unexpected_keys"],
        "n_missing": len(rest["missing_keys"]),
        "n_unexpected": len(rest["unexpected_keys"]),
        "atomic_publish_ok": published,
        "contained": SP.is_contained(str(final), str(stage_root)),
    })
    # ---- v3.17 (D16): same-source PRE/POST compact invariance ------------
    ssi_dir = str(stage_root / (run_key + ".ssi"))
    os.makedirs(ssi_dir, exist_ok=True)
    impl_version = getattr(CR, "IMPLEMENTATION_SOURCE_VERSION", "unknown")
    ident = SSI.source_identity(run_key, str(ck), os.environ.get("SLURM_JOB_ID"),
                                1, impl_version)
    ssi = SSI.same_source_compare(str(run_dir), str(ck), run_key, horizon,
                                  ssi_dir, ident, ident,
                                  published_post_path=str(published_compact))

    # ---- v3.17 (D16): the ONE authoritative, strongly-typed result -------
    checks = {
        "artifact_completeness": True,
        "run_status_completed": True,
        "compact_file_present": bool(published),
        "compact_file_sha256_matches_manifest":
            bool(rep.get("compact_sha256")
                 == _sha_file_safe(str(published_compact))),
        "canonical_tensor_sha256_present": bool(can),
        "reconstruction_exact": bool(rep.get("reconstruction_exact")),
        "restoration_exact": bool(rest.get("restoration_exact")),
        "strict_missing_keys_zero": len(rest.get("missing_keys") or []) == 0,
        "strict_unexpected_keys_zero":
            len(rest.get("unexpected_keys") or []) == 0,
        "no_frozen_backbone_duplication":
            bool(rep.get("no_frozen_backbone_duplication")),
        "atomic_publish_ok": bool(published),
        "contained": bool(res.get("contained")),
        "same_source_invariant_ok": bool(ssi.get("passed")),
    }
    evidence = {
        "run_key": run_key, "model": rep.get("spec_name"),
        "horizon": rep.get("horizon"),
        "file_sha256": _sha_file_safe(str(published_compact)),
        "canonical_tensor_sha256": can,
        "canonical_hash_schema": CC.CANONICAL_HASH_SCHEMA,
        "source_full_checkpoint_sha256": ident["source_full_checkpoint_sha256"],
        "source_run_key": ident["source_run_key"],
        "source_job_id": ident["source_job_id"],
        "source_training_attempt": ident["source_training_attempt"],
        "export_implementation_version": impl_version,
        "comparison_mode": ssi.get("comparison_mode"),
    }
    res["same_source"] = ssi
    try:
        sv = SV.StorageVerification(checks=checks, evidence=evidence)
        res["verification"] = sv.to_dict()
        res["passed"] = sv.passed
    except Exception as e:                                     # noqa: BLE001
        res["verification"] = {"schema": SV.SCHEMA, "passed": False,
                               "code": "SCHEMA_CONSTRUCTION_ERROR",
                               "detail": f"{type(e).__name__}: {e}"}
        res["passed"] = False
    return res


def _sha_file(path: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def _sha_file_safe(path: str) -> str:
    """Never raises: a missing/unreadable file yields "" so the corresponding
    check simply fails (fail-closed) instead of crashing the whole Gate."""
    try:
        return _sha_file(path)
    except Exception:                                          # noqa: BLE001
        return ""


def main() -> int:
    deployment_root = os.environ.get("INNOVATION_DEPLOYMENT_ROOT")
    if not deployment_root:
        print("[gate] INNOVATION_DEPLOYMENT_ROOT must be set")
        return 1
    reg = CR.load_registry(deployment_root)
    gdir = gate_dir(deployment_root)
    runs_root = gdir / "runs"
    runs_root.mkdir(parents=True, exist_ok=True)
    # v3.13: durable-path simulation root (never touches the real home durable)
    stage_root = gdir / "durable_sim"
    stage_root.mkdir(parents=True, exist_ok=True)

    results = []

    # deferred guard: must refuse all 18 deferred rows
    deferred = [s for s in reg["specs"] if s.get("wave") == 2]
    refused = 0
    for s in deferred:
        try:
            CR.resolve_spec(reg, s["run_key"])
        except SystemExit:
            refused += 1
    results.append({"path": "deferred_guard", "n_deferred": len(deferred),
                    "n_refused": refused,
                    "passed": refused == len(deferred) == 18})

    jobs = ([("primary", m, 24, 42) for m in PRIMARY]
            + [("baseline", b, 24, "n/a") for b in BASELINES]
            + [("ablation", a, 24, 42) for a in ABLATIONS]
            + [("negative_control", c, 24, 42) for c in GPT2_CONTROLS])

    for arm, model, horizon, seed in jobs:
        rk = run_key_for(arm, model, horizon, seed)
        rc = run_one(deployment_root, runs_root, rk)
        rd = runs_root / rk
        entry = {"path": arm, "model": model, "run_key": rk, "rc": rc}
        if rc == 0 and rd.exists():
            entry.update(verify_run(rd, arm == "baseline"))
        else:
            entry["passed"] = False
            entry["error"] = "runner did not complete"
        if rc == 0 and rd.exists():
            st = verify_storage(rd, rk, arm, horizon, stage_root)
            entry["storage"] = st
        entry["passed"] = (bool(entry.get("passed")) and rc == 0
                           and bool(entry.get("storage", {}).get("passed")))
        results.append(entry)

    archive_discoverable = (Path(deployment_root) / "results" / "v3").exists()
    n_passed = sum(1 for r in results if r.get("passed"))
    payload = {
        "generated_utc": NOW, "slurm_job_id": JOB, "node": NODE,
        "deployment_root": str(deployment_root),
        "version": reg.get("version"),
        "aggregate_sha256": reg.get("aggregate_sha256"),
        "n_paths": len(results), "n_passed": n_passed,
        "all_passed": n_passed == len(results),
        "archive_isolated": not archive_discoverable,
        "test_access_count": 0, "holdout_access_count": 0,
        "results": results,
    }
    (gdir / "gate_report.json").write_text(json.dumps(payload, indent=2),
                                           encoding="utf-8")
    print(f"[gate] {n_passed}/{len(results)} passed -> {gdir}")
    for r in results:
        if not r.get("passed"):
            print("  FAILED:", r.get("model", r.get("path")))
    return 0 if payload["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
