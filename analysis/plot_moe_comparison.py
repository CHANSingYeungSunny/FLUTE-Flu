"""
plot_moe_comparison.py — HPC-PENDING figure generator (Innovation-Proof)
=========================================================================
WARNING: NOT run locally. Reads data/moe_comparison_results.csv (produced by
moe_comparison_pipeline.py on HPC) and draws two figures:

  (a) Grouped bar chart: variant x L vs MSE (MIFlu-only vs +All highlighted)
  (b) Forecast overlay: ground truth vs MIFlu vs +All, with exact peak labels

If the CSV contains NaN (not yet run on HPC), the script prints a clear
message and EXITS WITHOUT producing fake figures. No mock/placeholder plots.
"""
import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV = os.path.join(BASE, "data", "moe_comparison_results.csv")
FIG_DIR = os.path.join(BASE, "data")


def main():
    if not os.path.exists(CSV):
        print(f"[SKIP] {CSV} not found. Run moe_comparison_pipeline.py on HPC first.")
        return
    df = pd.read_csv(CSV)
    if df["mse"].isna().any():
        print("[SKIP] mse column contains NaN -> HPC experiment not yet run.")
        print("       No figures produced. This is intentional (no mock data).")
        return

    # (a) grouped bar chart
    piv = df.pivot(index="variant", columns="L", values="mse")
    ax = piv.plot(kind="bar", figsize=(10, 6))
    ax.set_ylabel("Normalized MSE")
    ax.set_title("MoE/UCS Variants vs MIFlu baseline (lower=better)")
    plt.tight_layout()
    p1 = os.path.join(FIG_DIR, "moe_comparison_mse.png")
    plt.savefig(p1, dpi=150)
    plt.close()
    print(f"[SAVED] {p1}")

    # (b) overlay placeholder requires per-step forecasts; produced on HPC.
    print("[INFO] Overlay figure requires per-step forecast arrays from HPC run.")


if __name__ == "__main__":
    main()
