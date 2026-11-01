#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""stepwise_pte_pie_and_plots.py — PTE/PIE per-step analysis + denormalized plots.

For each step s in {0, 1, 2, 3} (1/2/3/4 weeks ahead):
  - Build aligned time series: prediction at forecast_lead = s+1 for each origin
  - 7-variable aggregate: mean of 7 de-normalized variables (physical units)
  - PTE = |predicted_peak_week - observed_peak_week| (weeks)
  - PIE = |predicted_peak - observed_peak| / observed_peak * 100 (%)
  - Kramer & Shaman (2019): PTE <= 1 week AND PIE <= 25%
  - Plot: GT vs Predicted curves (y=denormalized 7-var aggregate, x=test time)

Usage:
  python stepwise_pte_pie_and_plots.py --pred-dir results/v3_clean/analysis/peak_criteria/miflu
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCALER_PATH = os.path.join(ROOT, "data", "scaler_miflu_author966.json")

def load_scaler(path=SCALER_PATH):
    with open(path) as f:
        sc = json.load(f)
    return np.array(sc["mean"]), np.array(sc["std"])  # (7,), (7,)

def load_predictions(pred_dir, L, seed):
    """Load test predictions CSV. Returns (origins, leads, feat_idx, pred_z, true_z)."""
    pattern = f"test_predictions_*L{L}*seed{seed}*.csv"
    import glob
    paths = glob.glob(os.path.join(pred_dir, "**", pattern), recursive=True)
    if not paths:
        raise FileNotFoundError(f"No prediction file found: {pred_dir}/{pattern}")
    df = pd.read_csv(paths[0])
    return df

def build_step_series(df, step, mean, std):
    """Build aligned time series for a given step (0-indexed).

    step=0 -> forecast_lead=1 (1 week ahead)
    step=1 -> forecast_lead=2 (2 weeks ahead)
    etc.

    Returns (target_times, gt_agg, pred_agg) where agg = mean of 7 denormalized vars.
    """
    lead = step + 1
    d = df[df["forecast_lead"] == lead].copy()
    if len(d) == 0:
        raise ValueError(f"No rows for forecast_lead={lead}")
    
    # Pivot: for each origin, get all 7 features
    # target_time = forecast_origin + lead
    d["target_time"] = d["forecast_origin"] + lead
    
    # De-normalize: physical = z * std + mean
    # Per feature
    for feat in range(7):
        mask = d["feature_index"] == feat
        d.loc[mask, "pred_phys"] = d.loc[mask, "y_pred_z"] * std[feat] + mean[feat]
        d.loc[mask, "true_phys"] = d.loc[mask, "y_true_z"] * std[feat] + mean[feat]
    
    # 7-variable aggregate: mean across features for each target_time
    agg = d.groupby("target_time").agg(
        pred_agg=("pred_phys", "mean"),
        true_agg=("true_phys", "mean"),
    ).reset_index()
    
    return agg["target_time"].values, agg["true_agg"].values, agg["pred_agg"].values

def compute_pte_pie(gt_series, pred_series, times):
    """Compute PTE (weeks) and PIE (%) from aligned time series."""
    # Find peaks
    gt_peak_idx = np.argmax(gt_series)
    pred_peak_idx = np.argmax(pred_series)
    
    gt_peak_time = times[gt_peak_idx]
    pred_peak_time = times[pred_peak_idx]
    gt_peak_val = gt_series[gt_peak_idx]
    pred_peak_val = pred_series[pred_peak_idx]
    
    # PTE: peak timing error in weeks
    pte = abs(pred_peak_time - gt_peak_time)
    
    # PIE: peak intensity error in %
    if gt_peak_val > 0:
        pie = abs(pred_peak_val - gt_peak_val) / gt_peak_val * 100.0
    else:
        pie = float("inf")
    
    return {
        "PTE_weeks": float(pte),
        "PIE_pct": float(pie),
        "gt_peak_time": int(gt_peak_time),
        "pred_peak_time": int(pred_peak_time),
        "gt_peak_val": float(gt_peak_val),
        "pred_peak_val": float(pred_peak_val),
        "PTE_le_1wk": bool(pte <= 1.0),
        "PIE_le_25pct": bool(pie <= 25.0),
        "kramer_shaman_pass": bool(pte <= 1.0 and pie <= 25.0),
    }

def plot_step(ax, times, gt, pred, step, pte_pie):
    """Plot GT vs Predicted for one step."""
    ax.plot(times, gt, "b-", linewidth=1.5, label="Ground Truth", alpha=0.8)
    ax.plot(times, pred, "r--", linewidth=1.5, label="Predicted", alpha=0.8)
    
    # Mark peaks
    gt_peak_idx = np.argmax(gt)
    pred_peak_idx = np.argmax(pred)
    ax.plot(times[gt_peak_idx], gt[gt_peak_idx], "b^", markersize=10, zorder=5)
    ax.plot(times[pred_peak_idx], pred[pred_peak_idx], "rv", markersize=10, zorder=5)
    
    status = "PASS" if pte_pie["kramer_shaman_pass"] else "FAIL"
    ax.set_title(
        f"Step {step} ({step+1} week{'s' if step > 0 else ''} ahead) — "
        f"PTE={pte_pie['PTE_weeks']:.0f}wk, PIE={pte_pie['PIE_pct']:.1f}% [{status}]",
        fontsize=11, fontweight="bold",
    )
    ax.set_xlabel("Test Time (weeks from start)", fontsize=10)
    ax.set_ylabel("Denormalized 7-Var Aggregate", fontsize=10)
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(times.min(), times.max())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pred-dir", default=os.path.join(ROOT, "results", "v3_clean", "analysis", "peak_criteria", "miflu"))
    parser.add_argument("--L", type=int, default=24, help="Horizon (24/36/48/60)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out-dir", default=os.path.join(ROOT, "results", "stepwise_pte_pie"))
    args = parser.parse_args()
    
    os.makedirs(args.out_dir, exist_ok=True)
    mean, std = load_scaler()
    
    print(f"Loading predictions: L={args.L}, seed={args.seed}")
    df = load_predictions(args.pred_dir, args.L, args.seed)
    print(f"  Loaded {len(df)} rows")
    
    # ── Per-step analysis ──
    results = []
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = axes.flatten()
    
    for step in range(4):
        times, gt, pred = build_step_series(df, step, mean, std)
        pte_pie = compute_pte_pie(gt, pred, times)
        pte_pie["step"] = step
        pte_pie["horizon_L"] = args.L
        results.append(pte_pie)
        
        print(f"\n  Step {step} ({step+1} week{'s' if step > 0 else ''} ahead):")
        print(f"    PTE = {pte_pie['PTE_weeks']:.1f} weeks {'<= 1 PASS' if pte_pie['PTE_le_1wk'] else '> 1 FAIL'}")
        print(f"    PIE = {pte_pie['PIE_pct']:.1f}% {'<= 25% PASS' if pte_pie['PIE_le_25pct'] else '> 25% FAIL'}")
        print(f"    Kramer & Shaman: {'PASS' if pte_pie['kramer_shaman_pass'] else 'FAIL'}")
        print(f"    GT peak: week {pte_pie['gt_peak_time']}, value {pte_pie['gt_peak_val']:.1f}")
        print(f"    Pred peak: week {pte_pie['pred_peak_time']}, value {pte_pie['pred_peak_val']:.1f}")
        
        plot_step(axes[step], times, gt, pred, step, pte_pie)
    
    fig.suptitle(
        f"MIFlu Step-wise PTE/PIE Analysis — L={args.L}, seed={args.seed}\n"
        f"y-axis: Denormalized 7-Variable Aggregate (physical units)",
        fontsize=13, fontweight="bold",
    )
    plt.tight_layout()
    plot_path = os.path.join(args.out_dir, f"stepwise_pte_pie_L{args.L}_seed{args.seed}.png")
    plt.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"\n  Plot saved: {plot_path}")
    
    # ── Summary table ──
    summary = pd.DataFrame(results)
    csv_path = os.path.join(args.out_dir, f"stepwise_pte_pie_L{args.L}_seed{args.seed}.csv")
    summary.to_csv(csv_path, index=False)
    print(f"  CSV saved: {csv_path}")
    
    # ── Combined figure: all steps overlay ──
    fig2, ax2 = plt.subplots(1, 1, figsize=(14, 6))
    colors = ["blue", "green", "orange", "red"]
    for step in range(4):
        times, gt, pred = build_step_series(df, step, mean, std)
        ax2.plot(times, pred, color=colors[step], linewidth=1.2,
                 label=f"Step {step} ({step+1}wk ahead)", alpha=0.7)
    # GT in black
    times0, gt0, _ = build_step_series(df, 0, mean, std)
    ax2.plot(times0, gt0, "k-", linewidth=2, label="Ground Truth", alpha=0.9)
    ax2.set_xlabel("Test Time (weeks from start)", fontsize=11)
    ax2.set_ylabel("Denormalized 7-Variable Aggregate", fontsize=11)
    ax2.set_title(f"MIFlu: GT vs Predicted (all steps) — L={args.L}", fontsize=12, fontweight="bold")
    ax2.legend(loc="upper left", fontsize=10)
    ax2.grid(True, alpha=0.3)
    overlay_path = os.path.join(args.out_dir, f"stepwise_overlay_L{args.L}_seed{args.seed}.png")
    plt.savefig(overlay_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  Overlay plot saved: {overlay_path}")
    
    # ── Kramer & Shaman summary ──
    print("\n" + "=" * 70)
    print(f"  KRAMER & SHAMAN (2019) SUMMARY — L={args.L}, seed={args.seed}")
    print(f"  Criterion: PTE <= 1 week AND PIE <= 25%")
    print("=" * 70)
    print(f"  {'Step':>4} {'Horizon':>10} {'PTE_wk':>8} {'PIE_%':>8} {'PTE<=1':>8} {'PIE<=25':>8} {'PASS':>6}")
    print("  " + "-" * 56)
    for r in results:
        pte_ok = "PASS" if r['PTE_le_1wk'] else "FAIL"
        pie_ok = "PASS" if r['PIE_le_25pct'] else "FAIL"
        ks = "PASS" if r['kramer_shaman_pass'] else "FAIL"
        print(f"  {r['step']:>4} {r['step']+1:>8}wk {r['PTE_weeks']:>7.1f} {r['PIE_pct']:>7.1f} "
              f"{pte_ok:>8} {pie_ok:>8} {ks:>6}")
    print("=" * 70)

if __name__ == "__main__":
    main()
