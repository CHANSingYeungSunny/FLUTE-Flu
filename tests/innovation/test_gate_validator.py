"""test_gate_validator.py — model-free tests for the v3.12 Gate validator (D12).

Builds synthetic run directories and calls the REAL `clean_gate.verify_run`.
No weights, no dataset, no network, no Torch/CUDA, no model execution.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import clean_gate as CG      # noqa: E402


def _w(p: Path, obj) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2), encoding="utf-8")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def make_run(root: Path, is_baseline: bool, **over: dict) -> Path:
    """A fully-valid representative run directory (D11 uniform tree)."""
    rd = root / ("baseline__last_value_naive__L24__seedna__w1" if is_baseline
                 else "primary__nlinear__L24__seed42__w1")
    for d in CG.COMMON_REQUIRED:
        (rd / Path(d).parent).mkdir(parents=True, exist_ok=True)
    for d in ("logs", "predictions", "metrics", "checkpoints"):
        (rd / d).mkdir(parents=True, exist_ok=True)

    (rd / "config_resolved.yaml").write_text("model: x\n", encoding="utf-8")
    (rd / "environment.txt").write_text("py39\n", encoding="utf-8")
    (rd / "git_commit.txt").write_text("", encoding="utf-8")
    _w(rd / "source_manifest.json", {"aggregate_sha256": "a" * 64})
    _w(rd / "split_manifest.json", {"split": {"train": 717, "validation": 102,
                                              "test": 206}, "T": 104,
                                    "ili_channel": 4})
    _w(rd / "scaler_metadata.json", {"train_only": True, "n_variables": 7})
    _w(rd / "prompt_statistics_metadata.json", {"fit_scope": "train rows only"})
    (rd / "predictions" / "validation_predictions.csv").write_text(
        "model_key,variable\nx,ILITOTAL\n", encoding="utf-8")
    _w(rd / "metrics" / "paper_aligned_full_output_metrics.json",
       {"complete_seven_variable_output": True,
        "mse_all_7vars_full_horizon_z": 0.91,
        "mae_all_7vars_full_horizon_z": 0.55})
    _w(rd / "metrics" / "ilitotal_fixed_step_metrics.json",
       {"steps": {str(s): {"lead_weeks": s + 1} for s in range(4)},
        "steps_never_averaged": True})
    _w(rd / "metrics" / "ilitotal_full_horizon_metrics.json", {"mse": 0.9})
    _w(rd / "metrics" / "pte_pie_metrics.json",
       {"thresholds": {"PTE_weeks": 1, "PIE_percent": 25.0}})
    _w(rd / "run_status.json", {"state": "COMPLETED"})

    if is_baseline:
        _w(rd / "resource_usage.json", {"stochastic_seed_applicable": False,
                                        "checkpoint_applicable": False,
                                        "train_seconds": 0.0})
    else:
        _w(rd / "resource_usage.json", {"stochastic_seed_applicable": True,
                                        "checkpoint_applicable": True,
                                        "train_seconds": 9.2})
        (rd / "logs" / "train_history.csv").write_text(
            "epoch,train_mse\n1,1.0\n", encoding="utf-8")
        ck = rd / "checkpoints" / "best_val_mse.pt"
        ck.write_bytes(b"FAKE-TORCH-CHECKPOINT-BYTES")
        _w(rd / "checkpoints" / "checkpoint_manifest.json",
           {"checkpoint_file": "checkpoints/best_val_mse.pt",
            "sha256_file": _sha(ck), "best_epoch": 12,
            "restore_test": {"ok": True, "missing_keys": [],
                             "unexpected_keys": []}})

    # per-test overrides
    for key, val in over.items():
        kind, _, rest = key.partition("__")
        target = rd / rest if rest else rd
        if kind == "delete":
            if target.is_dir():
                for p in sorted(target.rglob("*"), reverse=True):
                    p.unlink() if p.is_file() else p.rmdir()
                target.rmdir()
            elif target.exists():
                target.unlink()
        elif kind == "text":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(val, encoding="utf-8")
        elif kind == "bytes":
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(val)
        elif kind == "json":
            _w(target, val)
    return rd


# ── A. manifest-driven checkpoint ─────────────────────────────────────────
def test_valid_manifest_declared_best_val_mse_passes(tmp_path):
    rd = make_run(tmp_path, False)
    res = CG.verify_run(rd, False)
    assert res["checks"]["checkpoint_file_present"] is True
    assert res["checks"]["checkpoint_sha256_matches"] is True
    assert res["checks"]["checkpoint_path_contained"] is True
    assert res["passed"] is True, [k for k, v in res["checks"].items() if not v]


def test_missing_checkpoint_file_fails(tmp_path):
    rd = make_run(tmp_path, False,
                  **{"delete__checkpoints/best_val_mse.pt": None})
    res = CG.verify_run(rd, False)
    assert res["checks"]["checkpoint_file_present"] is False
    assert res["passed"] is False


def test_checkpoint_hash_mismatch_fails(tmp_path):
    rd = make_run(tmp_path, False)
    man = json.loads((rd / "checkpoints" / "checkpoint_manifest.json")
                     .read_text(encoding="utf-8"))
    man["sha256_file"] = "0" * 64
    _w(rd / "checkpoints" / "checkpoint_manifest.json", man)
    res = CG.verify_run(rd, False)
    assert res["checks"]["checkpoint_sha256_matches"] is False
    assert res["passed"] is False


def test_path_traversal_in_declared_checkpoint_fails(tmp_path):
    rd = make_run(tmp_path, False)
    outside = tmp_path / "escaped.pt"
    outside.write_bytes(b"x")
    man = json.loads((rd / "checkpoints" / "checkpoint_manifest.json")
                     .read_text(encoding="utf-8"))
    man["checkpoint_file"] = "../../escaped.pt"
    man["sha256_file"] = _sha(outside)
    _w(rd / "checkpoints" / "checkpoint_manifest.json", man)
    res = CG.verify_run(rd, False)
    assert res["checks"]["checkpoint_path_contained"] is False
    assert res["checks"]["checkpoint_file_present"] is False
    assert res["passed"] is False


def test_absolute_declared_checkpoint_fails(tmp_path):
    rd = make_run(tmp_path, False)
    absf = tmp_path / "abs.pt"
    absf.write_bytes(b"x")
    man = json.loads((rd / "checkpoints" / "checkpoint_manifest.json")
                     .read_text(encoding="utf-8"))
    man["checkpoint_file"] = str(absf)
    man["sha256_file"] = _sha(absf)
    _w(rd / "checkpoints" / "checkpoint_manifest.json", man)
    res = CG.verify_run(rd, False)
    assert res["passed"] is False


@pytest.mark.skipif(os.name == "nt" and not os.environ.get("CI"),
                    reason="symlink needs privileges on Windows")
def test_symlink_escape_in_declared_checkpoint_fails(tmp_path):
    rd = make_run(tmp_path, False)
    outside = tmp_path / "outside.pt"
    outside.write_bytes(b"secret")
    link = rd / "checkpoints" / "linked.pt"
    try:
        os.symlink(str(outside), str(link))
    except (OSError, NotImplementedError):
        pytest.skip("symlink not supported here")
    man = json.loads((rd / "checkpoints" / "checkpoint_manifest.json")
                     .read_text(encoding="utf-8"))
    man["checkpoint_file"] = "checkpoints/linked.pt"
    man["sha256_file"] = _sha(outside)
    _w(rd / "checkpoints" / "checkpoint_manifest.json", man)
    res = CG.verify_run(rd, False)
    assert res["passed"] is False
    assert res["checks"]["checkpoint_path_contained"] is False


def test_restore_not_ok_fails(tmp_path):
    rd = make_run(tmp_path, False)
    man = json.loads((rd / "checkpoints" / "checkpoint_manifest.json")
                     .read_text(encoding="utf-8"))
    man["restore_test"] = {"ok": False}
    _w(rd / "checkpoints" / "checkpoint_manifest.json", man)
    res = CG.verify_run(rd, False)
    assert res["checks"]["checkpoint_restore_ok"] is False
    assert res["passed"] is False


def test_manifest_without_declared_path_fails(tmp_path):
    rd = make_run(tmp_path, False)
    man = json.loads((rd / "checkpoints" / "checkpoint_manifest.json")
                     .read_text(encoding="utf-8"))
    man.pop("checkpoint_file")
    _w(rd / "checkpoints" / "checkpoint_manifest.json", man)
    res = CG.verify_run(rd, False)
    assert res["checks"]["checkpoint_file_present"] is False
    assert res["passed"] is False


# ── B. baseline semantic no-checkpoint ────────────────────────────────────
def test_baseline_with_empty_checkpoint_dir_passes(tmp_path):
    rd = make_run(tmp_path, True)
    assert (rd / "checkpoints").is_dir() and not any(
        (rd / "checkpoints").iterdir())
    res = CG.verify_run(rd, True)
    assert res["checks"]["baseline_no_checkpoint"] is True
    assert res["passed"] is True, [k for k, v in res["checks"].items() if not v]


def test_baseline_with_checkpoint_file_fails(tmp_path):
    rd = make_run(tmp_path, True)
    (rd / "checkpoints" / "best_val_mse.pt").write_bytes(b"nope")
    res = CG.verify_run(rd, True)
    assert res["checks"]["baseline_no_checkpoint_file"] is False
    assert res["checks"]["baseline_no_checkpoint"] is False
    assert res["passed"] is False


def test_baseline_with_checkpoint_manifest_fails(tmp_path):
    rd = make_run(tmp_path, True)
    _w(rd / "checkpoints" / "checkpoint_manifest.json", {"x": 1})
    res = CG.verify_run(rd, True)
    assert res["checks"]["baseline_no_checkpoint_manifest"] is False
    assert res["passed"] is False


def test_baseline_with_checkpoint_applicable_true_fails(tmp_path):
    rd = make_run(tmp_path, True)
    _w(rd / "resource_usage.json", {"stochastic_seed_applicable": False,
                                    "checkpoint_applicable": True})
    res = CG.verify_run(rd, True)
    assert res["checks"]["baseline_no_checkpoint"] is False
    assert res["passed"] is False


def test_baseline_with_stochastic_seed_applicable_true_fails(tmp_path):
    rd = make_run(tmp_path, True)
    _w(rd / "resource_usage.json", {"stochastic_seed_applicable": True,
                                    "checkpoint_applicable": False})
    res = CG.verify_run(rd, True)
    assert res["checks"]["baseline_seed_not_applicable"] is False
    assert res["passed"] is False


# ── C. arm-aware completeness (do NOT weaken stochastic) ──────────────────
def test_baseline_without_train_history_passes_when_rest_complete(tmp_path):
    rd = make_run(tmp_path, True)
    assert not (rd / "logs" / "train_history.csv").exists()
    res = CG.verify_run(rd, True)
    assert res["checks"]["artifact_completeness"] is True
    assert res["checks"]["baseline_no_training_history"] is True
    assert res["passed"] is True


def test_stochastic_without_train_history_fails(tmp_path):
    rd = make_run(tmp_path, False,
                  **{"delete__logs/train_history.csv": None})
    res = CG.verify_run(rd, False)
    assert res["checks"]["artifact_completeness"] is False
    assert "logs/train_history.csv" in res["missing"]
    assert res["passed"] is False


def test_stochastic_without_checkpoint_manifest_fails(tmp_path):
    rd = make_run(tmp_path, False,
                  **{"delete__checkpoints/checkpoint_manifest.json": None})
    res = CG.verify_run(rd, False)
    assert res["checks"]["artifact_completeness"] is False
    assert res["passed"] is False


def test_schemas_are_explicitly_arm_specific():
    assert set(CG.ARM_REQUIRED) == {"stochastic", "baseline"}
    assert ("logs/train_history.csv"
            in CG.ARM_REQUIRED["stochastic"])
    assert ("checkpoints/checkpoint_manifest.json"
            in CG.ARM_REQUIRED["stochastic"])
    assert ("logs/train_history.csv" not in CG.ARM_REQUIRED["baseline"])
    assert ("checkpoints/checkpoint_manifest.json"
            not in CG.ARM_REQUIRED["baseline"])
    for f in ("predictions/validation_predictions.csv",
              "metrics/paper_aligned_full_output_metrics.json",
              "metrics/ilitotal_fixed_step_metrics.json",
              "metrics/ilitotal_full_horizon_metrics.json",
              "metrics/pte_pie_metrics.json", "run_status.json",
              "resource_usage.json", "split_manifest.json",
              "scaler_metadata.json"):
        assert f in CG.ARM_REQUIRED["baseline"], f
        assert f in CG.ARM_REQUIRED["stochastic"], f


# ── fail-closed + no legacy hard-coded filename ───────────────────────────
@pytest.mark.parametrize("bad", [
    {"delete__metrics/pte_pie_metrics.json": None},
    {"delete__predictions/validation_predictions.csv": None},
    {"delete__split_manifest.json": None},
    {"json__run_status.json": {"state": "FAILED"}},
    {"json__split_manifest.json": {"split": {"train": 1, "validation": 2,
                                             "test": 3}, "T": 104,
                                   "ili_channel": 4}},
])
def test_any_false_check_makes_the_gate_fail_closed(tmp_path, bad):
    is_base = "metrics/pte_pie_metrics.json" in next(iter(bad))
    rd = make_run(tmp_path, is_base, **bad)
    res = CG.verify_run(rd, is_base)
    assert res["passed"] is False


def test_validator_no_longer_hardcodes_best_validation_pt():
    src = (REPO / "scripts" / "innovation" / "clean_gate.py").read_text(
        encoding="utf-8")
    assert "best_validation.pt" not in src
    assert "declared_checkpoint" in src


def test_scientific_runtime_was_not_modified():
    """D12 is a Gate-validator-only fix."""
    import hashlib as h
    runner = REPO / "scripts" / "innovation" / "clean_runner.py"
    assert h.sha256(runner.read_bytes()).hexdigest() == \
        "2d5e96e177abe5f8ec44cc5e574782cb626943f943049a89f87031cb9046f0ef"


def test_d12_evidence_recorded():
    sc = REPO / "results" / "v3_clean" / "preregistration"
    pre = json.loads((sc / "d12_pre_repair_manifest.json").read_text(
        encoding="utf-8"))
    rec = json.loads((sc / "d12_repair_record.json").read_text(
        encoding="utf-8"))
    assert pre["defect"] == "D12"
    assert pre["scientific_runtime_modified"] is False
    assert rec["classification"] == \
        "BEHAVIOR_NEUTRAL_GATE_VALIDATOR_SCHEMA_ALIGNMENT_FIX"
    assert rec["clean_runner_sha256_unchanged"] is True
    assert rec["pre_repair_sha256"] != rec["post_repair_sha256"]
    assert (sc / "d12_repair.diff").exists()
