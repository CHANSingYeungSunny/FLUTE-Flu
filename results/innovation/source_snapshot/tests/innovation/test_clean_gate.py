"""test_clean_gate.py — model-free tests for the pre-execution Gate.

No model, dataset, network or Torch/CUDA: the Gate's key construction,
create-only directory rule and artifact verification are exercised against a
SYNTHETIC run directory built here.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import clean_gate as CG  # noqa: E402


def make_run_dir(base: Path, *, baseline=False, pte=1, pie=25.0,
                 omit=(), state="COMPLETED"):
    d = base / "run"
    (d / "metrics").mkdir(parents=True, exist_ok=True)
    (d / "logs").mkdir(parents=True, exist_ok=True)
    (d / "checkpoints").mkdir(parents=True, exist_ok=True)
    files = {
        "config_resolved.yaml": {},
        "environment.txt": "platform: test\n",
        "git_commit.txt": "",
        "source_manifest.json": {"aggregate_sha256": "x"},
        "split_manifest.json": {"split": {"train": 717, "validation": 102,
                                          "test": 206}, "T": 104, "horizon": 24,
                                "n_variables": 7, "ili_channel": 4},
        "scaler_metadata.json": {"train_only": True, "n_variables": 7},
        "prompt_statistics_metadata.json": {"fit_scope": "train rows only"},
        "logs/train_history.csv": "epoch,train,val\n1,0.5,0.4\n",
        "predictions/validation_predictions.csv": "model_key\nunit\n",
        "metrics/paper_aligned_full_output_metrics.json": {
            "complete_seven_variable_output": True,
            "mse_all_7vars_full_horizon_z": 1.0,
            "mae_all_7vars_full_horizon_z": 0.8},
        "metrics/ilitotal_fixed_step_metrics.json": {
            "steps_never_averaged": True,
            "steps": {str(s): {"lead_weeks": s + 1, "mse_z": 1.0}
                      for s in range(4)}},
        "metrics/ilitotal_full_horizon_metrics.json": {"mse_z": 1.0},
        "metrics/pte_pie_metrics.json": {
            "thresholds": {"PTE_weeks": pte, "PIE_percent": pie},
            "forbidden_and_absent": ["Peak Hit Rate (0.70/0.75)"]},
        "run_status.json": {"state": state},
        "resource_usage.json": {"stochastic_seed_applicable": not baseline,
                                "checkpoint_applicable": not baseline},
    }
    if baseline:
        # v3.12 (D12): deterministic baselines never train, so they never
        # produce a training history. They also carry no checkpoint.
        files.pop("logs/train_history.csv", None)
    for rel, content in files.items():
        if rel in omit:
            continue
        p = d / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(content) if not rel.endswith((".txt", ".csv"))
                     else str(content), encoding="utf-8")
    # v3.12 (D12): the checkpoint is DECLARED BY THE MANIFEST and its hash must
    # match the real file. `checkpoints/` itself STAYS PRESENT (the D11 uniform
    # tree) — for baselines it must simply be EMPTY.
    if baseline:
        for f in (d / "checkpoints").iterdir():
            f.unlink()
        (d / "logs" / "train_history.csv").unlink(missing_ok=True)
    elif "checkpoints/checkpoint_manifest.json" not in omit:
        import hashlib
        ck = d / "checkpoints" / "best_val_mse.pt"
        ck.write_bytes(b"pt")
        (d / "checkpoints" / "checkpoint_manifest.json").write_text(
            json.dumps({
                "checkpoint_file": "checkpoints/best_val_mse.pt",
                "sha256_file": hashlib.sha256(ck.read_bytes()).hexdigest(),
                "restore_test": {"ok": True}}), encoding="utf-8")
    return d


def test_run_key_construction():
    assert CG.run_key_for("primary", "nlinear", 24, 42) == \
        "primary__nlinear__L24__seed42__w1"
    # D10: the frozen registry encodes the deterministic baselines' seed as
    # `seedna`, NOT as an empty token.
    assert CG.run_key_for("baseline", "last_value_naive", 24, "n/a") == \
        "baseline__last_value_naive__L24__seedna__w1"


def test_gate_dir_is_create_only(tmp_path, monkeypatch):
    monkeypatch.setenv("SLURM_JOB_ID", "testjob")
    # direct behaviour: an existing directory must be refused
    p = CG.gate_dir.__wrapped__ if hasattr(CG.gate_dir, "__wrapped__") else None
    # emulate by creating the expected dir first
    (tmp_path / "results" / "v3_clean" / "implementation" / "gate_testjob") \
        .mkdir(parents=True, exist_ok=True)
    import os
    os.environ["SLURM_JOB_ID"] = "testjob"
    with pytest.raises(SystemExit) as e:
        CG.gate_dir(str(tmp_path))
    assert "create-only" in str(e.value)


def test_verify_complete_stochastic_run(tmp_path):
    d = make_run_dir(tmp_path)
    res = CG.verify_run(d, is_baseline=False)
    assert res["passed"], res["checks"]
    assert res["checks"]["seven_variable_full_horizon_output"] is True
    assert res["checks"]["fixed_steps_0_3_present"] is True
    assert res["checks"]["pte_1_week_pie_25_pct"] is True
    assert res["checks"]["checkpoint_restore_ok"] is True


def test_verify_detects_missing_artifacts(tmp_path):
    d = make_run_dir(tmp_path, omit=("metrics/pte_pie_metrics.json",))
    res = CG.verify_run(d, is_baseline=False)
    assert res["checks"]["artifact_completeness"] is False
    assert not res["passed"]


def test_verify_detects_wrong_peak_thresholds(tmp_path):
    d = make_run_dir(tmp_path, pte=2, pie=20.0)
    res = CG.verify_run(d, is_baseline=False)
    assert res["checks"]["pte_1_week_pie_25_pct"] is False


def test_verify_detects_unsupported_peak_logic(tmp_path):
    d = make_run_dir(tmp_path)
    pp = d / "metrics" / "pte_pie_metrics.json"
    obj = json.loads(pp.read_text(encoding="utf-8"))
    obj["peak_hit_rate"] = 0.75
    pp.write_text(json.dumps(obj), encoding="utf-8")
    res = CG.verify_run(d, is_baseline=False)
    assert res["checks"]["unsupported_peak_logic_absent"] is False


def test_verify_baseline_semantics(tmp_path):
    d = make_run_dir(tmp_path, baseline=True)
    res = CG.verify_run(d, is_baseline=True)
    assert res["checks"]["baseline_seed_not_applicable"] is True
    assert res["checks"]["baseline_no_checkpoint"] is True
    assert res["passed"]


def test_verify_detects_failed_state(tmp_path):
    d = make_run_dir(tmp_path, state="FAILED")
    res = CG.verify_run(d, is_baseline=False)
    assert res["checks"]["run_status_completed"] is False


def test_required_files_cover_the_frozen_contract():
    for f in ("config_resolved.yaml", "source_manifest.json",
              "split_manifest.json", "scaler_metadata.json",
              "prompt_statistics_metadata.json",
              "checkpoints/checkpoint_manifest.json", "run_status.json",
              "resource_usage.json",
              "metrics/paper_aligned_full_output_metrics.json",
              "metrics/ilitotal_fixed_step_metrics.json",
              "metrics/ilitotal_full_horizon_metrics.json",
              "metrics/pte_pie_metrics.json"):
        # v3.12 (D12): schemas are arm-aware; this list is the STOCHASTIC one.
        assert f in CG.ARM_REQUIRED["stochastic"]


def test_covered_paths_are_complete():
    assert len(CG.PRIMARY) == 8
    assert len(CG.BASELINES) == 2
    assert len(CG.ABLATIONS) == 6
    assert CG.GPT2_CONTROLS == ["zero_text", "shuffled_text"]
