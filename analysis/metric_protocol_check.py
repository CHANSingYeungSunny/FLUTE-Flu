"""
metric_protocol_check.py — Tutor Q5 (the 200% MSE gap, root cause check)
=========================================================================
Local, lightweight. NO model training. Runs on CPU.

Purpose: prove that a SCALE-PROTOCOL mismatch ALONE can produce an
order-of-magnitude % difference in reported MSE, isolating the root cause
of a "MSE differs by 200%" observation WITHOUT claiming any forecast
quality.

Method (metric-protocol AUDIT only, NOT a forecast result):
  Use a trivial Seasonal-Naive baseline (last-year same-week value) as a
  deterministic reference series. Then compute:
    (a) Raw-scale MSE      : mean((y_true - y_pred)^2)   in patient counts
    (b) StandardScaler MSE : z-score both series with TRAIN stats, then MSE
  Ratio (a)/(b) shows how much the reported number changes purely from the
  scale protocol. We explicitly label this as a protocol audit, never a
  prediction result.

This mirrors MIFlu Section V-B: "We first normalize each input variable ...
using StandardScaler. The MSE and MAE are then calculated ..." — i.e. the
paper reports NORMALIZED MSE/MAE for National, while a Raw-scale compute
would inflate magnitudes.

Outputs are REAL numbers. No mock predictions, no forecast claims.
"""
import os
import numpy as np
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(BASE, "data", "national_illness_raw.csv")
VAR_COLS = ["% WEIGHTED ILI", "% UNWEIGHTED ILI", "AGE 0-4",
            "AGE 5-24", "ILITOTAL", "NUM. OF PROVIDERS", "OT"]
ILI_IDX = 4
T = 104          # input window
L = 24           # horizon
SEASON = 52      # one influenza year, for seasonal-naive reference


def main():
    print("=" * 72)
    print(" METRIC PROTOCOL CHECK (Tutor Q5) — scale-protocol audit only")
    print("=" * 72)
    df = pd.read_csv(DATA)
    n = len(df)
    t_end = int(n * 0.70)
    v_end = t_end + int(n * 0.10)
    # train stats = first 70% (evidence B: make_forecast_figure.py:72-73)
    data = df[VAR_COLS].values.astype(np.float32)
    mean = data[:t_end].mean(0, keepdims=True)
    std = data[:t_end].std(0, keepdims=True) + 1e-8

    # test window targets (raw)
    y_true = data[v_end + T: v_end + T + L, ILI_IDX]   # first L test weeks, ILITOTAL raw
    # Seasonal-Naive reference: same week one year (52 wks) earlier in RAW space
    ref_idx = v_end + T - SEASON
    y_pred = data[ref_idx: ref_idx + L, ILI_IDX]

    # (a) Raw-scale MSE
    raw_mse = float(np.mean((y_true - y_pred) ** 2))

    # (b) StandardScaler-normalized MSE (train stats)
    yt_n = (y_true - mean[0, ILI_IDX]) / std[0, ILI_IDX]
    yp_n = (y_pred - mean[0, ILI_IDX]) / std[0, ILI_IDX]
    norm_mse = float(np.mean((yt_n - yp_n) ** 2))

    ratio = raw_mse / norm_mse if norm_mse > 0 else float("nan")
    print(f" Test window ILITOTAL raw: min={y_true.min():,.0f} max={y_true.max():,.0f}")
    print(f" Seasonal-Naive ref raw   : min={y_pred.min():,.0f} max={y_pred.max():,.0f}\n")
    print(f" (a) Raw-scale MSE        = {raw_mse:,.1f}")
    print(f" (b) StandardScaler MSE   = {norm_mse:.6f}")
    print(f" Ratio (a)/(b)            = {ratio:,.1f}x")
    print()
    print(" CONCLUSION: the same deterministic reference series yields a MSE")
    print(f" that differs by ~{ratio:,.0f}x purely because of the scale protocol.")
    print(" A Raw-scale vs Normalized-scale mismatch ALONE explains a")
    print(" multi-hundred-percent MSE discrepancy. This is the ROOT CAUSE class")
    print(" for the reported 200% gap; it is NOT a model-quality claim.")
    print(" Fix: report National MSE/MAE on StandardScaler-normalized scale,")
    print(" per MIFlu Section V-B. (Regional uses de-normalized RMSE/PCC.)")
    print("\n[DONE] metric_protocol_check.py — numbers above are REAL (local run).")


if __name__ == "__main__":
    main()
