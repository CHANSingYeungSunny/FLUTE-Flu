"""
verify_us_region.py
===================
Load the US-Region dataset, trim to paper-specified range (199740–202018),
perform 50:10:40 chronological split, compute training set statistics,
and compare against Table III gold standard.

Reference: MIFlu paper, Section V-A, Table III.
"""

import pandas as pd
import numpy as np
import os, sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INPUT_CSV = os.path.join(DATA_DIR, "us_region_raw.csv")
REPORT_TXT = os.path.join(DATA_DIR, "us_region_verification_report.txt")

# Paper-specified range
EPIWEEK_START = 199740
EPIWEEK_END = 202018

HHS_COLS = [f"HHS{i}" for i in range(1, 11)]

# Split ratios for US-Region
TRAIN_RATIO = 0.50
VAL_RATIO = 0.10
TEST_RATIO = 0.40

# Table III Gold Standard (from MIFlu paper — absolute ILI counts)
GOLD_STANDARD = {
    "HHS1":     {"mean": 444.586,  "max": 10890,  "std": 885.980},
    "HHS2":     {"mean": 1661.472, "max": 16433,  "std": 2314.758},
    "HHS3":     {"mean": 1574.766, "max": 18694,  "std": 2526.018},
    "HHS4":     {"mean": 2286.980, "max": 30282,  "std": 3515.544},
    "HHS5":     {"mean": 1178.448, "max": 11269,  "std": 1385.680},
    "HHS6":     {"mean": 1566.005, "max": 13616,  "std": 2193.085},
    "HHS7":     {"mean": 267.390,  "max": 4409,   "std": 435.360},
    "HHS8":     {"mean": 541.713,  "max": 7275,   "std": 869.223},
    "HHS9":     {"mean": 991.453,  "max": 5882,   "std": 911.894},
    "HHS10":    {"mean": 215.022,  "max": 5115,   "std": 486.705},
    "OVERALL":  {"mean": 1072.780, "max": 30282,  "std": 1949.170},
}


def load_and_trim():
    df = pd.read_csv(INPUT_CSV)
    # Trim to paper range
    mask = (df["epiweek"] >= EPIWEEK_START) & (df["epiweek"] <= EPIWEEK_END)
    df = df[mask].copy()
    n = len(df)
    print(f"[DATA] Trimmed to {n} weeks ({EPIWEEK_START}–{EPIWEEK_END})")
    return df


def chronological_split(df):
    n = len(df)
    t_end = int(n * TRAIN_RATIO)
    v_end = t_end + int(n * VAL_RATIO)
    train = df.iloc[:t_end]
    val = df.iloc[t_end:v_end]
    test = df.iloc[v_end:]
    print(f"[SPLIT] Train: {len(train)} ({len(train)/n*100:.0f}%) "
          f"epiweeks {train['epiweek'].iloc[0]}–{train['epiweek'].iloc[-1]}")
    print(f"[SPLIT] Val:   {len(val)} ({len(val)/n*100:.0f}%) "
          f"epiweeks {val['epiweek'].iloc[0]}–{val['epiweek'].iloc[-1]}")
    print(f"[SPLIT] Test:  {len(test)} ({len(test)/n*100:.0f}%) "
          f"epiweeks {test['epiweek'].iloc[0]}–{test['epiweek'].iloc[-1]}")
    return train, val, test


def compute_stats(train_df):
    """Compute per-region and overall statistics on training set."""
    stats = {}
    for col in HHS_COLS:
        s = train_df[col].dropna()
        stats[col] = {
            "mean": s.mean(),
            "std": s.std(ddof=1),
            "min": s.min(),
            "max": s.max(),
            "count": len(s),
        }

    # Overall: pool all regions
    all_vals = train_df[HHS_COLS].values.flatten()
    all_vals = all_vals[~np.isnan(all_vals)]
    stats["OVERALL"] = {
        "mean": np.mean(all_vals),
        "std": np.std(all_vals, ddof=1),
        "min": np.min(all_vals),
        "max": np.max(all_vals),
        "count": len(all_vals),
    }
    return stats


def print_stats(stats):
    """Print computed statistics table."""
    print(f"\n{'Region':<10s} {'Mean':>10s} {'Std':>10s} {'Min':>10s} {'Max':>10s}")
    print("-" * 52)
    for key in HHS_COLS + ["OVERALL"]:
        s = stats[key]
        print(f"{key:<10s} {s['mean']:>10.4f} {s['std']:>10.4f} {s['min']:>10.4f} {s['max']:>10.4f}")


def compare_with_gold(stats, gold_std):
    """Compare computed stats against Table III gold standard."""
    if gold_std is None:
        print("\n[INFO] No gold standard provided. Printing computed stats only.")
        return

    print(f"\n{'Region':<10s} {'Metric':>6s} {'Computed':>12s} {'Gold':>12s} "
          f"{'Abs Err':>10s} {'Rel%':>8s} {'Status':>8s}")
    print("-" * 78)

    all_pass = True
    for key in HHS_COLS + ["OVERALL"]:
        if key not in gold_std:
            continue
        gold = gold_std[key]
        comp = stats[key]
        for metric_key, gold_val in gold.items():
            computed_val = comp[metric_key]
            abs_err = abs(computed_val - gold_val)
            rel_err = (abs_err / abs(gold_val)) * 100 if abs(gold_val) > 1e-10 else 0.0
            threshold = 10.0 if metric_key == "max" else 5.0
            passed = rel_err <= threshold
            if not passed:
                all_pass = False
            status = "[PASS]" if passed else "[FAIL]"
            print(f"{key:<10s} {metric_key.upper():>6s} {computed_val:>12.4f} {gold_val:>12.4f} "
                  f"{abs_err:>10.4f} {rel_err:>7.2f}% {status:>8s}")

    if all_pass:
        print("\n[CONCLUSION] All metrics pass. Dataset verified against Table III.")
    else:
        print("\n[CONCLUSION] Some metrics fail — review discrepancies.")


def main():
    df = load_and_trim()
    train, val, test = chronological_split(df)
    stats = compute_stats(train)
    print_stats(stats)

    print("\n" + "=" * 60)
    print("  COMPARISON AGAINST TABLE III GOLD STANDARD")
    print("=" * 60)
    compare_with_gold(stats, GOLD_STANDARD)

    # Save report
    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write("US-Region Dataset — Computed Training Set Statistics\n")
        f.write(f"Range: {EPIWEEK_START}–{EPIWEEK_END}\n")
        f.write(f"Split: {TRAIN_RATIO:.0%}/{VAL_RATIO:.0%}/{TEST_RATIO:.0%}\n\n")
        f.write(f"{'Region':<10s} {'Mean':>10s} {'Std':>10s} {'Min':>10s} {'Max':>10s}\n")
        f.write("-" * 52 + "\n")
        for key in HHS_COLS + ["OVERALL"]:
            s = stats[key]
            f.write(f"{key:<10s} {s['mean']:>10.4f} {s['std']:>10.4f} "
                    f"{s['min']:>10.4f} {s['max']:>10.4f}\n")
    print(f"\n[REPORT] {REPORT_TXT}")

    return stats


if __name__ == "__main__":
    stats = main()
