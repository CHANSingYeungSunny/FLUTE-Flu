"""test_artifact_dirs.py — model-free regression tests for D11 (Gate 569016).

No weights, no dataset, no network, no Torch/CUDA, no model execution. The
tests reproduce the EXACT pandas failure seen in Gate 569016 and verify the
single shared initializer plus its safety guards.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
RUNNER_SRC = REPO / "scripts" / "innovation" / "clean_runner.py"

from innovation import clean_runner as CR          # noqa: E402


# ── helpers ────────────────────────────────────────────────────────────────
def _layout(tmp_path: Path, run_key="primary__nlinear__L24__seed42__w1"):
    out_root = tmp_path / "runs"
    out_root.mkdir(parents=True, exist_ok=True)
    return out_root, out_root / run_key


# ── the two authoritative D11 signatures ──────────────────────────────────
def test_without_initializer_pandas_to_csv_fails_this_is_the_569016_bug(
        tmp_path):
    """Reproduces the observed failure EXACTLY: pandas does not mkdir."""
    out_root, run = _layout(tmp_path)
    os.makedirs(run, exist_ok=True)                    # run_dir only
    with pytest.raises(OSError) as ei:
        pd.DataFrame({"epoch": [1]}).to_csv(
            os.path.join(str(run), "logs", "train_history.csv"))
    assert "non-existent directory" in str(ei.value)


def test_stochastic_path_can_write_logs_train_history_after_init(tmp_path):
    out_root, run = _layout(tmp_path)
    resolved = CR.ensure_run_dirs(str(run), str(out_root))
    pd.DataFrame({"epoch": [1, 2], "train_mse": [1.0, 0.5]}).to_csv(
        os.path.join(resolved, "logs", "train_history.csv"), index=False)
    assert (run / "logs" / "train_history.csv").exists()


def test_baseline_path_can_write_predictions_after_init(tmp_path):
    out_root, run = _layout(tmp_path, "baseline__last_value_naive__L24__seedna__w1")
    resolved = CR.ensure_run_dirs(str(run), str(out_root))
    pd.DataFrame({"variable": ["ILITOTAL"], "step": [0]}).to_csv(
        os.path.join(resolved, "predictions",
                     "validation_predictions.csv"), index=False)
    assert (run / "predictions" / "validation_predictions.csv").exists()


# ── directory completeness / idempotence ──────────────────────────────────
def test_all_required_subdirectories_exist_before_any_write(tmp_path):
    out_root, run = _layout(tmp_path)
    CR.ensure_run_dirs(str(run), str(out_root))
    for name in CR.RUN_SUBDIRS:
        assert (run / name).is_dir(), name
    assert set(CR.RUN_SUBDIRS) == {"logs", "predictions", "metrics",
                                   "checkpoints"}


def test_initializer_is_idempotent(tmp_path):
    out_root, run = _layout(tmp_path)
    first = CR.ensure_run_dirs(str(run), str(out_root))
    marker = run / "logs" / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    second = CR.ensure_run_dirs(str(run), str(out_root))
    assert first == second
    assert marker.read_text(encoding="utf-8") == "keep"   # nothing clobbered


def test_directory_creation_is_restricted_to_the_four_names(tmp_path):
    out_root, run = _layout(tmp_path)
    CR.ensure_run_dirs(str(run), str(out_root))
    assert sorted(p.name for p in run.iterdir()) == sorted(CR.RUN_SUBDIRS)


# ── safety: containment, traversal, symlink escape ────────────────────────
def test_path_traversal_is_rejected(tmp_path):
    out_root, _ = _layout(tmp_path)
    with pytest.raises(SystemExit):
        CR.ensure_run_dirs(str(out_root / ".." / "escaped"), str(out_root))


def test_nested_run_dir_is_rejected(tmp_path):
    out_root, run = _layout(tmp_path)
    with pytest.raises(SystemExit):
        CR.ensure_run_dirs(str(run / "nested"), str(out_root))


@pytest.mark.skipif(os.name == "nt" and not os.environ.get("CI"),
                    reason="symlink creation needs privileges on Windows")
def test_symlink_escape_is_rejected(tmp_path):
    out_root, run = _layout(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        os.symlink(str(outside), str(run), target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlink not supported here")
    with pytest.raises(SystemExit):
        CR.ensure_run_dirs(str(run), str(out_root))


def test_no_path_outside_out_root_is_created(tmp_path):
    out_root, run = _layout(tmp_path)
    CR.ensure_run_dirs(str(run), str(out_root))
    outside = [p for p in tmp_path.iterdir() if p.name not in
               ("runs", "outside")]
    assert outside == [], outside


# ── run-key gating: no directory for unknown / deferred / accepted ────────
def _reg(spec):
    return {"specs": [spec]}


BASE = {"run_key": "primary__nlinear__L24__seed42__w1", "model": "nlinear",
        "horizon": 24, "seed": 42, "arm": "primary", "parent_model": "nlinear",
        "wave": 1, "executable_binding": True, "submittable": True}


def test_unknown_run_key_rejected_before_any_directory_is_created():
    with pytest.raises(SystemExit) as ei:
        CR.resolve_spec(_reg(dict(BASE)), "primary__nope__L24__seed42__w1")
    assert "unknown run_key" in str(ei.value)


def test_deferred_run_key_rejected():
    spec = dict(BASE, executable_binding=False, submittable=False)
    with pytest.raises(SystemExit) as ei:
        CR.resolve_spec(_reg(spec), spec["run_key"])
    assert "deferred" in str(ei.value)


def test_already_accepted_run_key_rejected():
    spec = dict(BASE, accepted=True)
    with pytest.raises(SystemExit) as ei:
        CR.resolve_spec(_reg(spec), spec["run_key"])
    assert "already accepted" in str(ei.value)


def test_resolution_happens_before_directory_creation_in_the_source():
    """Order guarantee: spec resolution (and therefore rejection) precedes the
    first `os.makedirs` in main(), so rejected keys can never create a dir."""
    src = RUNNER_SRC.read_text(encoding="utf-8")
    body = src[src.index("def main("):]
    assert body.index("resolve_spec") < body.index("os.makedirs(out_root")


# ── lifecycle / semantics preservation ────────────────────────────────────
def test_failed_run_is_never_marked_accepted():
    src = RUNNER_SRC.read_text(encoding="utf-8")
    assert 'status("FAILED"' in src
    assert "never mark a failed run accepted" in src
    assert '"accepted": True' not in src


def _baseline_block(src: str) -> str:
    """The baseline branch runs from `if arm == "baseline":` to its `return 0`;
    the stochastic/ablated/control path starts after it."""
    i = src.index('if arm == "baseline":')
    j = src.index("\n            return 0", i)
    return src[i:j]


def test_baseline_keeps_checkpoint_applicable_false():
    """`checkpoint_applicable` / `stochastic_seed_applicable` are RUNTIME
    run_status fields (not spec fields). The baseline branch must set both
    False and must never train or save a checkpoint."""
    src = RUNNER_SRC.read_text(encoding="utf-8")
    block = _baseline_block(src)
    assert '"checkpoint_applicable": False' in block
    assert "checkpoint_applicable=False" in block
    assert '"stochastic_seed_applicable": False' in block
    assert "stochastic_seed_applicable=False" in block
    assert "train_model" not in block, "baseline must not train"
    assert '"checkpoints"' not in block, "baseline must not write a checkpoint"


def test_stochastic_rows_still_expect_checkpoints():
    """The stochastic branch keeps checkpoint semantics unchanged, and the
    frozen registry still carries numeric seeds for those arms."""
    src = RUNNER_SRC.read_text(encoding="utf-8")
    assert '"checkpoint_applicable": True' in src
    assert "write_checkpoint_manifest" in src
    reg = json.loads((REPO / "results" / "v3_clean" / "runs"
                      / "complete_specs_598.json").read_text(encoding="utf-8"))
    stoch = [s for s in reg["specs"] if s["arm"] in
             ("primary", "ablation", "negative_control")]
    assert stoch
    assert all(isinstance(s["seed"], int) for s in stoch)


def test_no_test_or_holdout_path_is_referenced_by_the_initializer():
    src = RUNNER_SRC.read_text(encoding="utf-8")
    body = src[src.index("def ensure_run_dirs"):src.index("def load_registry")]
    for banned in ("test_evaluations", "holdout", "/test/"):
        assert banned not in body


def test_repair_evidence_recorded():
    sc = REPO / "results" / "v3_clean" / "preregistration"
    pre = json.loads((sc / "d11_pre_repair_manifest.json").read_text(
        encoding="utf-8"))
    rec = json.loads((sc / "d11_repair_record.json").read_text(
        encoding="utf-8"))
    assert pre["defect"] == "D11"
    assert pre["failure_signature"]["single_root_cause"] is True
    assert pre["failure_signature"]["missing_directories"] == ["logs",
                                                               "predictions"]
    assert rec["classification"] == \
        "BEHAVIOR_NEUTRAL_ARTIFACT_DIRECTORY_INITIALIZATION_FIX"
    assert rec["scientific_lines_changed"] == 0
    assert rec["pre_repair_sha256"] != rec["post_repair_sha256"]
    assert (sc / "d11_repair.diff").exists()
