"""test_clean_metrics.py — model-free hand-checked tests for clean-v3 metrics.

No model is loaded, no Torch/CUDA is used, no dataset is read and no network
access happens. Every expected value below is computed BY HAND in the test.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

# `innovation` lives under <repo>/scripts, which is not on sys.path by default.
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))

from innovation import clean_metrics as CM  # noqa: E402


def frame(true_z, pred_z, true_p, pred_p, var_index, horizon=4, n_steps=4,
          origin=100):
    """One origin, one variable: build rows with explicit values."""
    rows = []
    for k in range(n_steps):
        rows.append({
            "model_key": "unit", "horizon": horizon, "seed_or_rep": 42,
            "split": "val", "forecast_origin": origin,
            "target_date": f"2016-01-{4 + k:02d}",
            "step": k, "lead_weeks": k + 1,
            "variable": f"var{var_index}", "variable_index": var_index,
            "y_true_z": true_z[k], "y_pred_z": pred_z[k],
            "y_true_physical": true_p[k], "y_pred_physical": pred_p[k],
        })
    return pd.DataFrame(rows, columns=CM.PREDICTION_COLUMNS)


def seven_var_frame(pred_z_value=1.0, pred_p_value=2.0):
    """7 variables x 4 steps x 1 origin; truths are all ZERO."""
    frames = []
    for vi in range(7):
        frames.append(frame([0.0] * 4, [pred_z_value] * 4,
                            [0.0] * 4, [pred_p_value] * 4, vi))
    return pd.concat(frames, ignore_index=True)


# ── 1. paper-aligned full-output metrics ────────────────────────────────────
def test_full_output_mse_mae_hand_computed():
    d = seven_var_frame(pred_z_value=1.0)
    m = CM.paper_aligned_full_output_metrics(d)
    # every one of 7 variables x 4 steps = 28 elements: err = 1.0
    # MSE = mean(1^2) = 1.0        MAE = mean(|1|) = 1.0
    assert m["mse_all_7vars_full_horizon_z"] == pytest.approx(1.0)
    assert m["mae_all_7vars_full_horizon_z"] == pytest.approx(1.0)
    assert m["n_elements"] == 28
    assert m["complete_seven_variable_output"] is True
    assert m["variables_observed"] == [0, 1, 2, 3, 4, 5, 6]


def test_full_output_mse_scales_with_error():
    d = seven_var_frame(pred_z_value=2.0)
    m = CM.paper_aligned_full_output_metrics(d)
    # error = 2 -> MSE = 4, MAE = 2
    assert m["mse_all_7vars_full_horizon_z"] == pytest.approx(4.0)
    assert m["mae_all_7vars_full_horizon_z"] == pytest.approx(2.0)


def test_full_output_flags_incomplete_variable_set():
    d = seven_var_frame()
    d = d[d["variable_index"] != 6]          # drop one variable
    m = CM.paper_aligned_full_output_metrics(d)
    assert m["complete_seven_variable_output"] is False


# ── 2. ILITOTAL identity and fixed steps ────────────────────────────────────
def test_ilitotal_index_is_four():
    assert CM.ILITOTAL_INDEX == 4


def test_fixed_steps_are_independent_and_never_averaged():
    # ILITOTAL only, with a DIFFERENT error at each step
    steps_err = {0: 1.0, 1: 2.0, 2: 3.0, 3: 4.0}
    rows = []
    for k in range(4):
        rows.append({
            "model_key": "unit", "horizon": 4, "seed_or_rep": 42,
            "split": "val", "forecast_origin": 100,
            "target_date": f"2016-01-{4 + k:02d}",
            "step": k, "lead_weeks": k + 1,
            "variable": "ILITOTAL", "variable_index": 4,
            "y_true_z": 0.0, "y_pred_z": steps_err[k],
            "y_true_physical": 0.0, "y_pred_physical": steps_err[k],
        })
    d = pd.DataFrame(rows, columns=CM.PREDICTION_COLUMNS)
    m = CM.ilitotal_fixed_step_metrics(d)
    assert m["steps_never_averaged"] is True
    assert m["never_pooled_into_champion_score"] is True
    for k in range(4):
        st = m["steps"][str(k)]
        assert st["lead_weeks"] == k + 1
        assert st["mse_z"] == pytest.approx(steps_err[k] ** 2)
        assert st["mae_z"] == pytest.approx(steps_err[k])
    # the four step MSEs must NOT be collapsed into one number anywhere
    assert "mse_mean" not in m
    assert "average" not in m


def test_fixed_step_metrics_ignore_other_variables():
    d = seven_var_frame(pred_z_value=9.0)
    # force ILITOTAL rows to a known small error
    d.loc[d["variable_index"] == 4, ["y_pred_z", "y_pred_physical"]] = 1.0
    m = CM.ilitotal_fixed_step_metrics(d)
    for k in range(4):
        assert m["steps"][str(k)]["mse_z"] == pytest.approx(1.0)


# ── 3. ILITOTAL full-horizon ────────────────────────────────────────────────
def test_ilitotal_full_horizon():
    d = seven_var_frame(pred_z_value=1.0)
    d.loc[d["variable_index"] == 4, ["y_pred_z", "y_pred_physical"]] = 3.0
    m = CM.ilitotal_full_horizon_metrics(d)
    # 4 ILITOTAL rows, error = 3 -> MSE = 9, MAE = 3
    assert m["mse_z"] == pytest.approx(9.0)
    assert m["mae_z"] == pytest.approx(3.0)
    assert m["n"] == 4


# ── 4. PTE / PIE with literature thresholds only ───────────────────────────
def _peak_frame(true_p, pred_p):
    rows = []
    for k in range(4):
        rows.append({
            "model_key": "unit", "horizon": 4, "seed_or_rep": 42,
            "split": "val", "forecast_origin": 100,
            "target_date": f"2016-01-{4 + k:02d}",
            "step": 0, "lead_weeks": 1,
            "variable": "ILITOTAL", "variable_index": 4,
            "y_true_z": 0.0, "y_pred_z": 0.0,
            "y_true_physical": true_p[k], "y_pred_physical": pred_p[k],
        })
    return pd.DataFrame(rows, columns=CM.PREDICTION_COLUMNS)


def test_pte_pie_meet_literature_criterion():
    # observed peak at index 2 (value 30); predicted peak at index 1 (value 30)
    d = _peak_frame([10.0, 20.0, 30.0, 20.0], [10.0, 30.0, 20.0, 20.0])
    m = CM.pte_pie_metrics(d, steps=(0,))
    st = m["steps"]["0"]
    assert st["PTE_weeks"] == pytest.approx(1.0)      # |1 - 2| = 1 week
    assert st["PIE_percent"] == pytest.approx(0.0)    # |30-30|/30 = 0%
    assert st["accurate_peak_timing"] is True         # 1 <= 1
    assert st["accurate_peak_intensity"] is True      # 0 <= 25
    assert st["literature_criterion_met"] is True


def test_pte_pie_fail_timing_at_two_weeks():
    # observed peak index 2 ; predicted peak index 0 -> PTE = 2 weeks > 1
    d = _peak_frame([10.0, 20.0, 30.0, 20.0], [40.0, 20.0, 30.0, 10.0])
    m = CM.pte_pie_metrics(d, steps=(0,))
    st = m["steps"]["0"]
    assert st["PTE_weeks"] == pytest.approx(2.0)
    assert st["accurate_peak_timing"] is False
    assert st["literature_criterion_met"] is False


def test_pte_pie_fail_intensity_above_25_percent():
    # same peak week, but predicted intensity 50 vs observed 30 -> 66.7% > 25
    d = _peak_frame([10.0, 20.0, 30.0, 20.0], [10.0, 20.0, 50.0, 20.0])
    m = CM.pte_pie_metrics(d, steps=(0,))
    st = m["steps"]["0"]
    assert st["PTE_weeks"] == pytest.approx(0.0)
    assert st["PIE_percent"] == pytest.approx(66.66666666666667)
    assert st["accurate_peak_intensity"] is False


def test_forbidden_peak_constructs_absent():
    d = _peak_frame([10.0, 20.0, 30.0, 20.0], [10.0, 30.0, 20.0, 20.0])
    m = CM.pte_pie_metrics(d, steps=(0,))
    # scan the COMPUTED payload only; `forbidden_and_absent` is a documentation
    # list whose entries name the forbidden constructs on purpose.
    blob = str({k: v for k, v in m.items()
                if k != "forbidden_and_absent"}).lower()
    for forbidden in ("peak_hit_rate", "peak_hit_ratio", "match_tol",
                      "hit_ratio", "peak_gate", "weighted"):
        assert forbidden not in blob, forbidden
    assert CM.PTE_THRESHOLD_WEEKS == 1
    assert CM.PIE_THRESHOLD_PCT == 25.0
    assert "Peak Hit Rate (0.70/0.75)" in m["forbidden_and_absent"]


# ── 5. seven-variable baselines ────────────────────────────────────────────
def test_naive_baselines_emit_all_seven_variables():
    n, N, T, L = 2, 7, 104, 4
    rng = np.random.default_rng(0)
    X = rng.normal(size=(n, N, T)).astype(np.float32)
    Y = rng.normal(size=(n, N, L)).astype(np.float32)
    for name in ("last_value_naive", "seasonal_naive"):
        d = CM.naive_prediction_frame(
            name, X, Y, [100, 101], L, [f"var{i}" for i in range(7)],
            np.zeros(N, dtype=float), np.ones(N, dtype=float))
        assert len(d) == n * N * L
        assert sorted(d["variable_index"].unique().tolist()) == list(range(7))
        # every required prediction-schema column present
        for c in CM.PREDICTION_COLUMNS:
            assert c in d.columns
        # persistence: last value repeats the final input value
        if name == "last_value_naive":
            got = d[(d["forecast_origin"] == 100)
                    & (d["variable_index"] == 3)]["y_pred_z"].to_numpy()
            assert np.allclose(got, float(X[0, 3, -1]))


# ── 6. archive isolation ───────────────────────────────────────────────────
def test_superseded_archive_isolated_from_active_root():
    assert not (REPO / "results" / "v3").exists(), \
        "the old active v3 path must no longer exist"
    arch = REPO / "results" / "v3_superseded_archive"
    assert arch.exists(), "the superseded archive must be preserved"
    marker = arch / "SUPERSEDED_MARKER.txt"
    assert marker.exists()
    assert "SUPERSEDED_NOT_ACTIVE_NOT_SELECTION_ELIGIBLE" in marker.read_text(
        encoding="utf-8")
    assert (REPO / "results" / "v3_clean").exists()
