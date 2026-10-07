"""
(b) END-TO-END pipeline regression (pre-HPC clarification 2b)
============================================================

Compares outputs produced by the OLD MIFlu path and the INNOVATION runner under
the SAME model state (a checkpoint produced by the existing MIFlu) and the SAME
inputs. Reports date-index equality, y_true / y_pred differences, MSE / MAE
differences, PTE equality, PIE difference, row count and the date window.

This is what justifies the claim "the innovation runner reproduces the old
pipeline", NOT the CSV re-aggregation test.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402
import _repro  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from innovation import metrics as M  # noqa: E402
from innovation import run_artifacts as ART  # noqa: E402
from innovation.data_pipeline import (build_windows, load_raw_df,  # noqa: E402
                                      load_scaler, normalize, to_array)
from innovation.paths import AUDIT_DIR, PROJECT_ROOT  # noqa: E402
from innovation.trainer import predict_frame  # noqa: E402

REPORT = os.path.join(AUDIT_DIR, "pipeline_regression_report.json")
L, T = 24, 104
N_VAL = 8          # small val subset keeps the test fast


def run() -> dict:
    device = "cuda" if __import__("torch").cuda.is_available() else "cpu"
    scaler = load_scaler()
    raw = load_raw_df()
    data = normalize(to_array(raw), scaler)
    w = build_windows(data, L)
    X, Y, idx = w["X_val"][:N_VAL], w["Y_val"][:N_VAL], w["idx_val"][:N_VAL]

    old, adapter, ckpt, ckpt_sha, sd_match = _repro.build_old_and_adapter(
        L, T, X.shape[1], device)
    x_probe, htext, ctx_meta = _repro.make_inputs(L, T, X.shape[1], N_VAL,
                                                  device)

    old_frame = _repro.old_path_frame(old, X, Y, idx, T, L, scaler, htext,
                                      device, batch_size=N_VAL)
    ctx_fn = lambda b: htext[:b]  # noqa: E731  (identical context for both paths)
    new_frame = predict_frame(adapter, X, Y, idx, T, L, scaler, "val", device,
                              batch_size=N_VAL, ctx_fn=ctx_fn)

    key = ["abs_week", "step"]
    a = old_frame.sort_values(key).reset_index(drop=True)
    b = new_frame.sort_values(key).reset_index(drop=True)

    mt = M.evaluate_predictions(old_frame, "val")
    mn = M.evaluate_predictions(new_frame, "val")

    rep = {
        "model_state": {"checkpoint_sha256": ckpt_sha,
                        "state_dicts_match": sd_match},
        "context": ctx_meta,
        "device": device,
        "row_count_old": int(len(a)), "row_count_new": int(len(b)),
        "row_count_equal": bool(len(a) == len(b)),
        "date_index_equal": bool(np.array_equal(
            pd.to_datetime(a["week_start_date"]).values,
            pd.to_datetime(b["week_start_date"]).values)),
        "date_start": str(pd.to_datetime(b["week_start_date"]).min().date()),
        "date_end": str(pd.to_datetime(b["week_start_date"]).max().date()),
        "y_true_diff": _repro.diff_stats(a["ground_truth_ili"], b["ground_truth_ili"]),
        "y_pred_z_diff": _repro.diff_stats(a["prediction_ili"], b["prediction_ili"]),
        "y_pred_phys_diff": _repro.diff_stats(
            a["prediction_ili_phys"], b["prediction_ili_phys"]),
        "mse_z_old": mt["mse_all_z"], "mse_z_new": mn["mse_all_z"],
        "mse_z_diff": float(abs(mt["mse_all_z"] - mn["mse_all_z"])),
        "mae_z_old": mt["mae_all_z"], "mae_z_new": mn["mae_all_z"],
        "mae_z_diff": float(abs(mt["mae_all_z"] - mn["mae_all_z"])),
        "pte_old": (mt.get("peak") or {}).get("mean_pte_weeks"),
        "pte_new": (mn.get("peak") or {}).get("mean_pte_weeks"),
        "pte_equal": ((mt.get("peak") or {}).get("mean_pte_weeks")
                      == (mn.get("peak") or {}).get("mean_pte_weeks")),
        "pie_old": (mt.get("peak") or {}).get("mean_pie_pct"),
        "pie_new": (mn.get("peak") or {}).get("mean_pie_pct"),
    }
    p_o = (mt.get("peak") or {}).get("mean_pie_pct")
    p_n = (mn.get("peak") or {}).get("mean_pie_pct")
    rep["pie_diff"] = (None if (p_o is None or p_n is None) else float(abs(p_o - p_n)))
    rep["tolerance"] = {"z_max_abs_diff": 1e-5, "phys_max_abs_diff": 1e-2,
                        "mse_diff": 1e-6}
    rep["all_agree"] = bool(
        rep["row_count_equal"] and rep["date_index_equal"]
        and rep["y_true_diff"]["max_abs_diff"] <= 1e-9
        and rep["y_pred_z_diff"]["max_abs_diff"] <= 1e-5
        and rep["y_pred_phys_diff"]["max_abs_diff"] <= 1e-2
        and rep["mse_z_diff"] <= 1e-6 and rep["mae_z_diff"] <= 1e-6)
    ART.write_json(REPORT, rep)
    return rep


def test_pipeline_regression_endtoend():
    rep = run()
    print(json.dumps({k: rep[k] for k in
                      ("row_count_equal", "date_index_equal", "date_start",
                       "date_end", "y_pred_z_diff", "y_pred_phys_diff",
                       "mse_z_diff", "mae_z_diff", "pte_equal", "pie_diff",
                       "all_agree")}, indent=2))
    assert rep["row_count_equal"], rep
    assert rep["date_index_equal"], rep
    assert rep["y_true_diff"]["max_abs_diff"] <= 1e-9, rep
    assert rep["y_pred_z_diff"]["max_abs_diff"] <= 1e-5, rep
    assert rep["y_pred_phys_diff"]["max_abs_diff"] <= 1e-2, rep
    assert rep["mse_z_diff"] <= 1e-6 and rep["mae_z_diff"] <= 1e-6, rep
    assert rep["all_agree"], rep


if __name__ == "__main__":
    test_pipeline_regression_endtoend()
    print("[test_pipeline_regression_endtoend] OK")
