"""Peak criterion: PTE<=1wk AND PIE<=25%; tie/incomplete/zero-denominator rules."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bootstrap  # noqa: F401,E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from innovation import metrics as M  # noqa: E402


def _season_series(gt_peak_idx, pred_shift, gt_peak_val=100.0, pie_mult=1.0):
    """One complete season (weeks 40..next 20) with a controllable peak."""
    weeks = [202040 + i for i in range(0, 21)] + [202101 + i for i in range(0, 21)]
    n = len(weeks)
    gt = np.zeros(n)
    pred = np.zeros(n)
    gt[gt_peak_idx] = gt_peak_val
    pidx = min(max(gt_peak_idx + pred_shift, 0), n - 1)
    pred[pidx] = gt_peak_val * pie_mult
    return pd.DataFrame({"abs_week": list(range(n)), "epiweek": weeks,
                         "gt": gt, "pred": pred})


def test_hit_requires_both_criteria():
    # PTE=0, PIE=0 -> hit
    _, a = M.seasonal_peak_metrics(_season_series(10, 0))
    assert a["peak_hit_ratio"] == 1.0, a
    # PTE=2 weeks -> miss (timing)
    _, a = M.seasonal_peak_metrics(_season_series(10, 2))
    assert a["peak_hit_ratio"] == 0.0, a
    # PTE=1 week, PIE=30% -> miss (intensity)
    _, a = M.seasonal_peak_metrics(_season_series(10, 1, pie_mult=1.30))
    assert a["peak_hit_ratio"] == 0.0, a
    # PTE=1 week, PIE=10% -> hit
    _, a = M.seasonal_peak_metrics(_season_series(10, 1, pie_mult=1.10))
    assert a["peak_hit_ratio"] == 1.0, a


def test_incomplete_season_not_scored():
    s = _season_series(10, 0).head(10)
    by, a = M.seasonal_peak_metrics(s)
    assert a["n_seasons_evaluable"] == 0, a
    assert (by["status"] == "incomplete_season").all(), by


def test_zero_denominator_reports_null_not_zero():
    s = _season_series(5, 0, gt_peak_val=0.0)
    by, a = M.seasonal_peak_metrics(s)
    row = by.iloc[0]
    assert row["status"] == "zero_denominator", row
    assert row["pie_pct"] is None, row
    assert a["n_hits"] == 0, a


def test_tie_takes_earliest_week():
    s = _season_series(10, 0)
    s.loc[12, "gt"] = s.loc[10, "gt"]          # tie at the max
    by, _ = M.seasonal_peak_metrics(s)
    # earliest index (abs_week 10) must be reported, not 12
    assert int(by.iloc[0]["gt_peak_week"]) == 10, by


if __name__ == "__main__":
    test_hit_requires_both_criteria()
    test_incomplete_season_not_scored()
    test_zero_denominator_reports_null_not_zero()
    test_tie_takes_earliest_week()
    print("[test_peak_criteria] OK")
