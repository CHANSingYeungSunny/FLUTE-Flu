"""repair_v312_gate_validator.py — D12: Gate-validator schema/semantics fix.

EVIDENCE (Gate 570452, v3.11, root v3_clean5):
  * Slurm FAILED 1:0, `1/19 passed`, BUT **18/18 runtime paths returned rc=0**
    and every SCIENTIFIC check passed on every path.
  * Only THREE validator assertions failed:
      1. `checkpoint_file_present` (16 paths) — looked for the hard-coded
         `checkpoints/best_validation.pt`; the runner writes
         `checkpoints/best_val_mse.pt` and the manifest DECLARES it via
         `checkpoint_file` + `sha256_file` (and `restore_test.ok` was true).
      2. `baseline_no_checkpoint` (2 paths) — required the `checkpoints/`
         DIRECTORY to be absent, but the D11 initializer creates a uniform
         directory tree (explicitly permitted: an EMPTY dir is valid).
      3. `artifact_completeness` (2 paths) — used ONE shared required list
         containing `logs/train_history.csv`, which deterministic baselines
         never produce.

CLASSIFICATION: BEHAVIOR_NEUTRAL_GATE_VALIDATOR_SCHEMA_ALIGNMENT_FIX
`clean_runner.py` and every scientific runtime file are UNTOUCHED.
"""
from __future__ import annotations

import difflib
import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SC = ROOT / "results" / "v3_clean" / "preregistration"
GATE = ROOT / "scripts" / "innovation" / "clean_gate.py"
IMPL = ROOT / "results" / "v3_clean" / "implementation"
SC.mkdir(parents=True, exist_ok=True)
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

VERSION_BEFORE = "innov-v3.11-artifact-directory-initialization"
VERSION_AFTER = "innov-v3.12-gate-validator-schema-alignment"
CLASSIFICATION = "BEHAVIOR_NEUTRAL_GATE_VALIDATOR_SCHEMA_ALIGNMENT_FIX"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def sha_b(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


before_text = GATE.read_text(encoding="utf-8")

# ── patch A: arm-aware artifact schemas ───────────────────────────────────
A_OLD = '''REQUIRED_FILES = [
    "config_resolved.yaml", "environment.txt", "git_commit.txt",
    "source_manifest.json", "split_manifest.json", "scaler_metadata.json",
    "prompt_statistics_metadata.json",
    "checkpoints/checkpoint_manifest.json", "logs/train_history.csv",
    "predictions/validation_predictions.csv",
    "metrics/paper_aligned_full_output_metrics.json",
    "metrics/ilitotal_fixed_step_metrics.json",
    "metrics/ilitotal_full_horizon_metrics.json",
    "metrics/pte_pie_metrics.json", "run_status.json", "resource_usage.json",
]'''
A_NEW = '''# v3.12 (D12): ARM-AWARE artifact schemas. A single shared list could not
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
}'''

# ── patch B: manifest-driven checkpoint resolution + helpers ──────────────
B_OLD = '''def verify_run(run_dir: Path, is_baseline: bool) -> dict:
    res = {"run_dir": str(run_dir), "checks": {}}
    # Deterministic baselines carry NO checkpoint by design, so checkpoint
    # artifacts are not required for them (and must be ABSENT).
    required = [f for f in REQUIRED_FILES
                if not (is_baseline and f.startswith("checkpoints/"))]
    missing = [f for f in required if not (run_dir / f).exists()]
    res["checks"]["artifact_completeness"] = not missing
    res["missing"] = missing'''
B_NEW = '''def _sha256_path(p: Path) -> str:
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
    res["missing"] = missing'''

# ── patch C: semantic baseline / manifest-driven stochastic checkpoint ────
C_OLD = '''    if is_baseline:
        ru = _load(run_dir, "resource_usage.json")
        res["checks"]["baseline_seed_not_applicable"] = \\
            ru.get("stochastic_seed_applicable") is False
        res["checks"]["baseline_no_checkpoint"] = \\
            ru.get("checkpoint_applicable") is False and not (
                run_dir / "checkpoints").exists()
    else:
        ck = run_dir / "checkpoints" / "checkpoint_manifest.json"
        res["checks"]["checkpoint_manifest"] = ck.exists()
        cm = _load(run_dir, "checkpoints/checkpoint_manifest.json")
        res["checks"]["checkpoint_restore_ok"] = ck.exists() and bool(
            (cm.get("restore_test") or {}).get("ok"))
        res["checks"]["checkpoint_file_present"] = (
            run_dir / "checkpoints" / "best_validation.pt").exists()'''
C_NEW = '''    if is_baseline:
        ru = _load(run_dir, "resource_usage.json")
        res["checks"]["baseline_seed_not_applicable"] = \\
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
        res["checkpoint_reason"] = dc["reason"]'''

patches = [("A_arm_aware_schemas", A_OLD, A_NEW),
           ("B_manifest_driven_checkpoint", B_OLD, B_NEW),
           ("C_semantic_baseline", C_OLD, C_NEW)]

pre_path = SC / "d12_pre_repair_manifest.json"
if not pre_path.exists():
    pre_path.write_text(json.dumps({
        "generated_utc": NOW, "defect": "D12",
        "classification": CLASSIFICATION,
        "runtime_version_before": VERSION_BEFORE,
        "runtime_version_after": VERSION_AFTER,
        "target_file": "scripts/innovation/clean_gate.py",
        "scientific_runtime_modified": False,
        "failing_gate": {"job_id": "570452", "state": "FAILED",
                         "exit_code": "1:0", "passed": "1/19",
                         "runners_rc0": "18/18", "node": "gpu-a100-03"},
        "validator_only": True,
        "failing_assertions": {
            "checkpoint_file_present": {
                "n_paths": 16,
                "wrong": "checkpoints/best_validation.pt",
                "actual": "checkpoints/best_val_mse.pt (declared by the "
                          "manifest as checkpoint_file)"},
            "baseline_no_checkpoint": {
                "n_paths": 2,
                "wrong": "requires the checkpoints/ DIRECTORY to be absent",
                "actual": "D11 creates a uniform tree; an EMPTY dir is valid"},
            "artifact_completeness": {
                "n_paths": 2,
                "wrong": "one shared list containing logs/train_history.csv",
                "actual": "deterministic baselines never train"},
        },
        "pre_repair_sha256": {"scripts/innovation/clean_gate.py": sha(GATE)},
        "note": "Recorded BEFORE any edit.",
    }, indent=2), encoding="utf-8")

after_text = before_text
results = []
for name, old, new in patches:
    if old in after_text:
        after_text = after_text.replace(old, new, 1)
        results.append(f"{name}: applied")
    elif new in after_text:
        results.append(f"{name}: already applied")
    else:
        raise SystemExit(f"D12 anchor not found: {name}")

applied = any(r.endswith("applied") for r in results)
if applied:
    with open(GATE, "w", encoding="utf-8", newline="") as f:
        f.write(after_text)

diff = "".join(difflib.unified_diff(
    before_text.splitlines(keepends=True), after_text.splitlines(keepends=True),
    fromfile="a/scripts/innovation/clean_gate.py",
    tofile="b/scripts/innovation/clean_gate.py"))
dp = SC / "d12_repair.diff"
if diff.strip():
    dp.write_text(diff, encoding="utf-8")
elif dp.exists():
    diff = dp.read_text(encoding="utf-8")

# ── guard: the SCIENTIFIC runtime must not have been touched ──────────────
RUNNER = ROOT / "scripts" / "innovation" / "clean_runner.py"
runner_unchanged = sha(RUNNER) == "2d5e96e177abe5f8ec44cc5e574782cb626943f943049a89f87031cb9046f0ef"
if not runner_unchanged:
    raise SystemExit("clean_runner.py changed — STOP, scientific runtime must "
                     "not be modified")

added = [l[1:] for l in diff.splitlines()
         if l.startswith("+") and not l.startswith("+++")]
removed = [l[1:] for l in diff.splitlines()
           if l.startswith("-") and not l.startswith("---")]

# ── separate Gate-harness vs scientific-source aggregates (prompt item 4) ──
sm = json.loads((IMPL / "source_manifest.json").read_text(encoding="utf-8"))
GATE_FILES = {"scripts/innovation/clean_gate.py"}
gate_lines = [f"{m['path']}:{m['sha256']}" for m in sm["files"]
              if m["path"] in GATE_FILES]
sci_lines = [f"{m['path']}:{m['sha256']}" for m in sm["files"]
             if m["path"] not in GATE_FILES]
gate_agg = sha_b("\n".join(sorted(gate_lines)).encode())
sci_agg = sha_b("\n".join(sorted(sci_lines)).encode())

pre = json.loads(pre_path.read_text(encoding="utf-8"))
rec = {
    "generated_utc": NOW, "defect": "D12", "applied_now": applied,
    "classification": CLASSIFICATION,
    "file": "scripts/innovation/clean_gate.py",
    "scientific_runtime_modified": False,
    "clean_runner_sha256_unchanged": runner_unchanged,
    "pre_repair_sha256": pre["pre_repair_sha256"][
        "scripts/innovation/clean_gate.py"],
    "post_repair_sha256": sha(GATE),
    "diff_bytes": len(diff.encode("utf-8")),
    "diff_sha256": sha_b(diff.encode("utf-8")),
    "lines_added": len(added), "lines_removed": len(removed),
    "patch_results": results,
    "gate_harness_aggregate": gate_agg,
    "gate_harness_files": sorted(GATE_FILES),
    "scientific_source_aggregate": sci_agg,
    "note": "scientific_source_aggregate excludes the Gate harness, so it must "
            "be identical to v3.11's (science unchanged).",
    "v311_scientific_source_aggregate":
        "67a3d80666941bba55f765409c0e671983811ad53c9b7a0c07a124b1ae0c7b98",
    "formal_rows_submitted": "0/598",
}
(SC / "d12_repair_record.json").write_text(json.dumps(rec, indent=2),
                                          encoding="utf-8")
with open(SC / "d12_repair_ledger.jsonl", "a", encoding="utf-8",
          newline="") as f:
    f.write(json.dumps({"utc": NOW, "event": "d12_repair_applied",
                        "applied": applied,
                        "pre": rec["pre_repair_sha256"],
                        "post": rec["post_repair_sha256"],
                        "diff_bytes": rec["diff_bytes"]}) + "\n")

print(f"[d12] applied={applied} pre={rec['pre_repair_sha256'][:16]} "
      f"post={rec['post_repair_sha256'][:16]} diff_bytes={rec['diff_bytes']} "
      f"added={len(added)} removed={len(removed)}")
print(f"[d12] runner_unchanged={runner_unchanged}")
print(f"[d12] gate_harness_aggregate={gate_agg[:16]} "
      f"(was clean_gate.py acd57d82/lf c4d9b147)")
print(f"[d12] scientific_source_aggregate={sci_agg[:16]}")
