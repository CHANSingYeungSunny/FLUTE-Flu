"""test_clean_runner.py — model-free tests for the clean-v3 runner.

Nothing here loads a real model, reads the dataset, uses the network or touches
Torch/CUDA. Only spec resolution, guard behaviour, frame construction and
status bookkeeping are exercised.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import clean_metrics as CM            # noqa: E402
from innovation import clean_runner as CR             # noqa: E402


def base_spec(**over):
    s = {"run_key": "primary__nlinear__L24__seed42__w1", "arm": "primary",
         "model": "nlinear", "group": "A_non_llm", "horizon": 24, "seed": 42,
         "control": "", "parent_model": "nlinear", "wave": 1,
         "submittable": True, "executable_binding": True, "order": 1}
    s.update(over)
    return s


def reg_with(*specs):
    return {"version": "test", "aggregate_sha256": "x", "n_specs": len(specs),
            "specs": list(specs)}


# ── spec resolution guards ──────────────────────────────────────────────────
def test_resolves_a_unique_known_key():
    s = base_spec()
    assert CR.resolve_spec(reg_with(s), s["run_key"])["model"] == "nlinear"


def test_rejects_unknown_key():
    with pytest.raises(SystemExit) as e:
        CR.resolve_spec(reg_with(base_spec()), "nope")
    assert "unknown run_key" in str(e.value)


def test_rejects_duplicate_key():
    s = base_spec()
    dup = base_spec(group="B_llm")          # same run_key, different content
    with pytest.raises(SystemExit) as e:
        CR.resolve_spec(reg_with(s, dup), s["run_key"])
    assert "duplicate run_key" in str(e.value)


def test_rejects_malformed_spec():
    s = base_spec()
    del s["horizon"]
    with pytest.raises(SystemExit) as e:
        CR.resolve_spec(reg_with(s), s["run_key"])
    assert "malformed spec" in str(e.value)


def test_rejects_already_accepted():
    s = base_spec(accepted=True)
    with pytest.raises(SystemExit) as e:
        CR.resolve_spec(reg_with(s), s["run_key"])
    assert "already accepted" in str(e.value)


def test_rejects_deferred_non_submittable_row():
    s = base_spec(run_key="negative_control__zero_text__L24__seed42__w2",
                  arm="negative_control", model="zero_text",
                  parent_model=CR.DEFERRED_PARENT, wave=2,
                  submittable=False, executable_binding=False)
    with pytest.raises(SystemExit) as e:
        CR.resolve_spec(reg_with(s), s["run_key"])
    assert "deferred" in str(e.value).lower()


def test_rejects_unbound_deferred_parent_even_if_submittable():
    s = base_spec(arm="negative_control", model="llm_removed_or_alignment_only",
                  parent_model=CR.DEFERRED_PARENT)
    with pytest.raises(SystemExit) as e:
        CR.resolve_spec(reg_with(s), s["run_key"])
    assert "unbound" in str(e.value)


def test_all_eighteen_deferred_rows_are_refused():
    reg = json.loads((REPO / "results" / "v3_clean" / "runs"
                      / "complete_specs_598.json").read_text(encoding="utf-8"))
    deferred = [s for s in reg["specs"] if s.get("wave") == 2]
    assert len(deferred) == 18
    for s in deferred:
        with pytest.raises(SystemExit):
            CR.resolve_spec(reg, s["run_key"])


# ── seven-variable prediction frame ─────────────────────────────────────────
def test_frame_covers_all_seven_variables():
    n, N, L = 2, 7, 4
    yt = np.zeros((n, N, L))
    yp = np.ones((n, N, L))
    df = CR.build_full_prediction_frame(
        yp, yt, [100, 101], L, [f"v{i}" for i in range(N)],
        np.zeros(N), np.ones(N), "unit", 42)
    assert len(df) == n * N * L
    assert sorted(df["variable_index"].unique().tolist()) == list(range(7))
    # ILITOTAL is index 4 and present
    assert 4 in set(df["variable_index"])
    for c in CM.PREDICTION_COLUMNS:
        assert c in df.columns
    assert df["split"].unique().tolist() == ["val"]


def test_frame_physical_conversion_is_linear():
    n, N, L = 1, 7, 2
    yt = np.full((n, N, L), 2.0)
    yp = np.zeros((n, N, L))
    mean_v = np.full(N, 10.0)
    std_v = np.full(N, 3.0)
    df = CR.build_full_prediction_frame(
        yp, yt, [100], L, [f"v{i}" for i in range(N)], mean_v, std_v,
        "unit", 42)
    # z=2 -> physical 2*3+10 = 16 ; z=0 -> 10
    assert np.allclose(df["y_true_physical"].to_numpy(), 16.0)
    assert np.allclose(df["y_pred_physical"].to_numpy(), 10.0)


def test_primary_metric_from_full_frame_is_seven_variable():
    n, N, L = 1, 7, 3
    yt = np.zeros((n, N, L))
    yp = np.ones((n, N, L))
    df = CR.build_full_prediction_frame(
        yp, yt, [100], L, [f"v{i}" for i in range(N)], np.zeros(N),
        np.ones(N), "unit", 42)
    m = CM.paper_aligned_full_output_metrics(df)
    assert m["complete_seven_variable_output"] is True
    assert m["mse_all_7vars_full_horizon_z"] == pytest.approx(1.0)
    assert m["n_elements"] == 21


# ── parentage of the six original ablations ─────────────────────────────────
def test_all_six_original_ablations_parent_to_gpt2_miflu():
    for v in ("without_dataset_information", "without_task_instruction",
              "without_input_variable_description", "without_lora",
              "without_multimodality", "without_lora_and_multimodality"):
        base = CR.VARIANTS[v][0]
        assert base == "gpt2_miflu", v


def test_gpt2_miflu_controls_use_the_gpt2_encoder():
    assert CR.VARIANTS["zero_text"][1] == "gpt2"
    assert CR.VARIANTS["shuffled_text"][1] == "gpt2"
    assert CR.VARIANTS["zero_text"][3]["text_mode"] == "zero"
    assert CR.VARIANTS["shuffled_text"][3]["text_mode"] == "shuffle"


def test_multimodality_removal_flag_present():
    assert CR.VARIANTS["without_multimodality"][2]["multimodal"] is False


# ── protocol constants ──────────────────────────────────────────────────────
def test_frozen_geometry_and_channel():
    assert CR.N_VARIABLES == 7
    assert CR.T_WINDOW == 104
    assert CR.ILITOTAL_INDEX == 4
    assert CR.SPLIT == {"train": 717, "validation": 102, "test": 206}


def test_baselines_are_deterministic_and_checkpoint_free():
    for b in CR.BASELINES:
        assert b in ("last_value_naive", "seasonal_naive")


# ── status bookkeeping ──────────────────────────────────────────────────────
def test_atomic_status_write_and_states(tmp_path):
    p = tmp_path / "run_status.json"
    CR._atomic_write_json(str(p), {"state": "CREATED"})
    assert json.loads(p.read_text(encoding="utf-8"))["state"] == "CREATED"
    for st in ("RUNNING", "COMPLETED", "FAILED", "ACCEPTED"):
        CR._atomic_write_json(str(p), {"state": st})
        assert json.loads(p.read_text(encoding="utf-8"))["state"] == st
    # atomic write leaves no temporary file behind
    assert not os.path.exists(str(p) + ".tmp")
