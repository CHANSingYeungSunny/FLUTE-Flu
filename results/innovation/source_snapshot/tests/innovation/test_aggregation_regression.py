"""
(a) AGGREGATION regression (pre-HPC clarification 2a)
=====================================================

Re-aggregate the SAME exported prediction CSV with the EXISTING pipeline and
with the innovation metrics layer, and report EVERY compared quantity (not just
aggregate metric equality):

  date-index equality, y_true max abs diff, y_pred max & mean abs diff,
  MSE diff, MAE diff, PTE equality, PIE diff, row count, date start, date end.

This does NOT claim full pipeline equivalence — that is the job of the
end-to-end regression in test_pipeline_regression_endtoend.py.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from innovation import metrics as M  # noqa: E402
from innovation import run_artifacts as ART  # noqa: E402
from innovation.paths import AUDIT_DIR, DATA_DIR  # noqa: E402

PRED_CSV = os.path.join(DATA_DIR, "predictions_miflu_L24_paper_protocol.csv")
RTOL, ATOL = 1e-9, 1e-12
REPORT = os.path.join(AUDIT_DIR, "aggregation_regression_report.json")


def run() -> dict:
    import compute_miflu_indicators as CMI

    ref = pd.read_csv(PRED_CSV)
    test = ref[ref["split"] == "test"].copy()

    ex = CMI.aggregate_lead_time(test, mode="fixed_step", step=0)
    inn = M.aggregate_fixed_step(test, step=0)

    ex_dates = pd.to_datetime(ex["week_start_date"]).values
    inn_dates = pd.to_datetime(inn["week_start_date"]).values
    gt_a, gt_b = ex["gt"].to_numpy(float), inn["gt"].to_numpy(float)
    pr_a, pr_b = ex["pred"].to_numpy(float), inn["pred"].to_numpy(float)

    _, agg_ex = CMI.compute_peak_indicators(gt_a, pr_a)
    agg_in = M.series_peak_metrics(gt_a, pr_a)

    def _eq(x, y):
        if x is None or y is None:
            return x is None and y is None
        return bool(abs(float(x) - float(y)) <= 1e-9)

    rep = {
        "reference_csv": PRED_CSV,
        "tolerances": {"rtol": RTOL, "atol": ATOL, "pte_pie_abs": 1e-9},
        "row_count_existing": int(len(ex)),
        "row_count_innovation": int(len(inn)),
        "row_count_equal": bool(len(ex) == len(inn)),
        "abs_week_equal": bool(np.array_equal(ex["abs_week"].to_numpy(),
                                              inn["abs_week"].to_numpy())),
        "date_index_equal": bool(np.array_equal(ex_dates, inn_dates)),
        "date_start": str(pd.Timestamp(inn_dates.min()).date()),
        "date_end": str(pd.Timestamp(inn_dates.max()).date()),
        "y_true_max_abs_diff": float(np.max(np.abs(gt_a - gt_b))) if len(gt_a) else 0.0,
        "y_pred_max_abs_diff": float(np.max(np.abs(pr_a - pr_b))) if len(pr_a) else 0.0,
        "y_pred_mean_abs_diff": float(np.mean(np.abs(pr_a - pr_b))) if len(pr_a) else 0.0,
        "mse_existing": float(M.mse(gt_a, pr_a)),
        "mse_innovation": float(M.mse(gt_b, pr_b)),
        "mse_diff": float(abs(M.mse(gt_a, pr_a) - M.mse(gt_b, pr_b))),
        "mae_existing": float(M.mae(gt_a, pr_a)),
        "mae_innovation": float(M.mae(gt_b, pr_b)),
        "mae_diff": float(abs(M.mae(gt_a, pr_a) - M.mae(gt_b, pr_b))),
        "pte_existing": agg_ex.get("peak_timing_error_weeks"),
        "pte_innovation": agg_in.get("peak_timing_error_weeks"),
        "pte_equal": _eq(agg_ex.get("peak_timing_error_weeks"),
                         agg_in.get("peak_timing_error_weeks")),
        "pie_existing": agg_ex.get("mean_peak_magnitude_rel_err_pct"),
        "pie_innovation": agg_in.get("mean_peak_magnitude_rel_err_pct"),
        "pie_diff": (None if (agg_ex.get("mean_peak_magnitude_rel_err_pct") is None
                              or agg_in.get("mean_peak_magnitude_rel_err_pct") is None)
                     else float(abs(agg_ex["mean_peak_magnitude_rel_err_pct"]
                                    - agg_in["mean_peak_magnitude_rel_err_pct"]))),
        "n_true_peaks_equal": bool(agg_ex["n_true_peaks"] == agg_in["n_true_peaks"]),
        "n_hit_equal": bool(agg_ex["n_hit"] == agg_in["n_hit"]),
    }
    rep["all_agree"] = bool(
        rep["row_count_equal"] and rep["abs_week_equal"] and rep["date_index_equal"]
        and rep["y_true_max_abs_diff"] <= ATOL
        and rep["y_pred_max_abs_diff"] <= ATOL
        and rep["mse_diff"] <= 1e-9 and rep["mae_diff"] <= 1e-9
        and rep["pte_equal"] and rep["n_true_peaks_equal"] and rep["n_hit_equal"]
        and (rep["pie_diff"] is None or rep["pie_diff"] <= 1e-9))
    ART.write_json(REPORT, rep)
    return rep


def test_aggregation_regression():
    if not os.path.exists(PRED_CSV):
        print(f"[SKIP] reference predictions not found: {PRED_CSV}")
        return
    rep = run()
    print(json.dumps({k: v for k, v in rep.items()
                      if k not in ("reference_csv",)}, indent=2)[:1200])
    assert rep["row_count_equal"], rep
    assert rep["date_index_equal"] and rep["abs_week_equal"], rep
    assert rep["y_true_max_abs_diff"] <= ATOL, rep
    assert rep["y_pred_max_abs_diff"] <= ATOL, rep
    assert rep["mse_diff"] <= 1e-9 and rep["mae_diff"] <= 1e-9, rep
    assert rep["pte_equal"] and rep["n_true_peaks_equal"], rep
    assert rep["all_agree"], rep


if __name__ == "__main__":
    test_aggregation_regression()
    print("[test_aggregation_regression] OK")
