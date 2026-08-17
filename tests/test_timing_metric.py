"""
test_timing_metric.py — Regression test for the Timing (|Δt|) = 0.0 bug
========================================================================

Fix Brief #3: Timing and Peak Intensity must be computed ONLY over peaks that
pass the Peak Hit criterion, and the Peak Hit count must ALWAYS be reported
alongside them. A Timing of 0.0 must NEVER silently mask missed peaks.

This test feeds a synthetic ground-truth / prediction pair whose peaks do NOT
overlap (so Peak Hit = 0/n). It asserts:
  (a) peak_hit_count is reported as "0/<n>", never omitted.
  (b) mean_abs_delta_t is None (unmatched), NOT 0.0.
  (c) mean_peak_magnitude_rel_err_pct is None (unmatched), NOT 0.0.
  (d) the unmatched true peaks are recorded with status "Missed".

Run:  python -m pytest tests/test_timing_metric.py -v
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "scripts"))
from compute_miflu_indicators import compute_peak_indicators


def test_timing_is_null_when_no_peaks_matched():
    # Ground truth: a clear peak at index 20.
    gt = [0.0] * 40
    gt[20] = 100.0
    # Prediction: peak shifted far away (index 5) → does NOT match within tol=2.
    pred = [0.0] * 40
    pred[5] = 100.0

    peak_df, agg = compute_peak_indicators(
        __import__("numpy").array(gt, dtype=float),
        __import__("numpy").array(pred, dtype=float),
        match_tol=2)

    # (a) Peak Hit count must be co-reported and reflect 0 hits / 1 true peak.
    assert "peak_hit_count" in agg, "peak_hit_count missing from aggregate"
    assert agg["peak_hit_count"] == "0/1", (
        f"expected '0/1' (missed peak), got {agg['peak_hit_count']!r}")
    assert agg["n_hit"] == 0
    assert agg["n_missed"] == 1

    # (b) Timing must be None (unmatched), NEVER 0.0.
    assert agg["mean_abs_delta_t"] is None, (
        f"Timing must be null when no peaks matched, got {agg['mean_abs_delta_t']!r}")
    # (c) Intensity must be None (unmatched), NEVER 0.0.
    assert agg["mean_peak_magnitude_rel_err_pct"] is None, (
        f"Intensity must be null when no peaks matched, "
        f"got {agg['mean_peak_magnitude_rel_err_pct']!r}")

    # (d) The unmatched true peak recorded as Missed, not as a Timing=0 hit.
    missed = peak_df[peak_df["status"] == "Missed"]
    assert len(missed) == 1, "expected exactly one Missed true peak"
    assert missed.iloc[0]["delta_t_weeks"] == "", (
        "Missed peak must not carry a fake delta_t")


def test_timing_reflects_nonzero_offset_on_matched_peak():
    # Both have a peak, prediction shifted by +3 weeks (within tol=4 → matched).
    gt = [0.0] * 40
    gt[20] = 100.0
    pred = [0.0] * 40
    pred[23] = 100.0   # +3 weeks offset

    peak_df, agg = compute_peak_indicators(
        __import__("numpy").array(gt, dtype=float),
        __import__("numpy").array(pred, dtype=float),
        match_tol=4)

    assert agg["peak_hit_count"] == "1/1", (
        f"expected '1/1' (matched), got {agg['peak_hit_count']!r}")
    # Timing must reflect the +3 offset, NOT 0.0.
    assert agg["mean_abs_delta_t"] == 3.0, (
        f"Timing should be 3.0 (offset), got {agg['mean_abs_delta_t']!r}")


if __name__ == "__main__":
    test_timing_is_null_when_no_peaks_matched()
    test_timing_reflects_nonzero_offset_on_matched_peak()
    print("\n[PASS] Timing metric regression tests passed.")
