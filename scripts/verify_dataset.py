"""
verify_dataset.py
=================
Load the downloaded National-Illness dataset, compute descriptive statistics
on BOTH the training set (70% chronological split) and the full dataset,
then compare against Table II gold standard from the MIFlu paper.

Reference: MIFlu paper, Section V-A, Table II.
"""

import pandas as pd
import numpy as np
import os, sys

# Fix Windows encoding
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ── Paths ──────────────────────────────────────────────────────────────────
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
INPUT_CSV = os.path.join(DATA_DIR, "national_illness_raw.csv")
REPORT_TXT = os.path.join(DATA_DIR, "verification_report.txt")

# ── Table II Gold Standard (from MIFlu paper) ───────────────────────────────
GOLD_STANDARD = {
    "% WEIGHTED ILI":     {"avg": 1.851,      "max": 7.715,     "std": 1.342},
    "% UNWEIGHTED ILI":   {"avg": 1.845,      "max": 7.780,     "std": 1.308},
    "AGE 0-4":            {"avg": 3434.814,   "max": 24097,     "std": 3152.330},
    "AGE 5-24":           {"avg": 4981.128,   "max": 45513,     "std": 5950.799},
    "ILITOTAL":           {"avg": 13540.720,  "max": 111361,    "std": 15003.120},
    "NUM. OF PROVIDERS":  {"avg": 1608.262,   "max": 3453,      "std": 681.227},
    "OT":                 {"avg": 651497.500, "max": 1640587,   "std": 348838.200},
}

VAR_COLS = list(GOLD_STANDARD.keys())

EXPECTED_WEEKS = 20 * 52  # ~1040


def load_and_split(df_path):
    """Load CSV and perform chronological 70:10:20 split."""
    df = pd.read_csv(df_path)
    n = len(df)
    train_end = int(n * 0.70)
    val_end = train_end + int(n * 0.10)
    train = df.iloc[:train_end]
    val = df.iloc[train_end:val_end]
    test = df.iloc[val_end:]
    return df, train, val, test


def compute_stats(subset_df, label=""):
    """Compute descriptive statistics on a data subset."""
    stats = {}
    for col in VAR_COLS:
        series = subset_df[col]
        stats[col] = {
            "count": len(series),
            "mean": series.mean(),
            "std": series.std(ddof=1),
            "min": series.min(),
            "max": series.max(),
        }
    return stats


def build_comparison_table(stats_dict, gold_std):
    """Build comparison rows. stats_dict = {label: stats}."""
    rows = []
    for col in VAR_COLS:
        gold = gold_std[col]
        for label, stats in stats_dict.items():
            for metric_key in ["avg", "std", "max"]:
                gold_val = gold[metric_key]
                computed_key = {"avg": "mean", "std": "std", "max": "max"}[metric_key]
                computed_val = stats[col][computed_key]
                abs_err = abs(computed_val - gold_val)
                rel_err = (abs_err / abs(gold_val)) * 100 if abs(gold_val) > 1e-10 else 0.0
                rows.append({
                    "variable": col,
                    "subset": label,
                    "metric": metric_key.upper(),
                    "computed": computed_val,
                    "gold": gold_val,
                    "abs_err": abs_err,
                    "rel_err_pct": rel_err,
                })
    return rows


def generate_report(df, train_stats, full_stats, rows):
    """Generate full verification report."""
    lines = []
    def emit(s=""):
        lines.append(s)

    emit("=" * 100)
    emit("  MIFlu Step 1: National-Illness Dataset Verification Report")
    emit("  Comparison: Computed Stats vs. Table II Gold Standard")
    emit("=" * 100)
    emit()
    emit(f"  Data source:  CMU Delphi Epidata API (fluview, nat)")
    emit(f"  Total weeks:  {len(df)} (epiweeks {df['epiweek'].iloc[0]} – {df['epiweek'].iloc[-1]})")
    emit(f"  Train:        {int(len(df)*0.70)} weeks ({df['epiweek'].iloc[0]} – {df['epiweek'].iloc[int(len(df)*0.70)-1]})")
    emit(f"  Val:          {int(len(df)*0.10)} weeks")
    emit(f"  Test:         {len(df) - int(len(df)*0.70) - int(len(df)*0.10)} weeks")
    emit()

    # Determine which label has more passes
    def count_pass(rows_for_label):
        return sum(1 for r in rows_for_label if r["rel_err_pct"] <= (10 if r["metric"] == "MAX" else 5))

    train_rows = [r for r in rows if r["subset"] == "TRAIN"]
    full_rows = [r for r in rows if r["subset"] == "FULL"]

    emit("── Gold Standard vs. TRAINING SET (70%) ──")
    emit(f"{'Variable':<22s} {'Metric':>6s} {'Computed':>14s} {'Gold':>12s} "
         f"{'Abs Err':>10s} {'Rel%':>8s}")
    emit("-" * 100)
    for r in train_rows:
        emit(f"{r['variable']:<22s} {r['metric']:>6s} {r['computed']:>14.4f} "
             f"{r['gold']:>12.4f} {r['abs_err']:>10.4f} {r['rel_err_pct']:>7.2f}%")
    # Min values
    for col in VAR_COLS:
        emit(f"{col:<22s} {'MIN':>6s} {train_stats[col]['min']:>14.4f} {'(not in Table II)':>12s}")

    emit()
    emit("── Gold Standard vs. FULL DATASET (100%) ──")
    emit(f"{'Variable':<22s} {'Metric':>6s} {'Computed':>14s} {'Gold':>12s} "
         f"{'Abs Err':>10s} {'Rel%':>8s}")
    emit("-" * 100)
    for r in full_rows:
        emit(f"{r['variable']:<22s} {r['metric']:>6s} {r['computed']:>14.4f} "
             f"{r['gold']:>12.4f} {r['abs_err']:>10.4f} {r['rel_err_pct']:>7.2f}%")
    for col in VAR_COLS:
        emit(f"{col:<22s} {'MIN':>6s} {full_stats[col]['min']:>14.4f} {'(not in Table II)':>12s}")

    emit()
    emit("=" * 100)
    train_passes = count_pass(train_rows)
    full_passes = count_pass(full_rows)

    emit(f"  TRAIN SET: {train_passes}/{len(train_rows)} metrics within tolerance")
    emit(f"  FULL SET:  {full_passes}/{len(full_rows)} metrics within tolerance")
    emit()

    best_label = "TRAIN" if train_passes >= full_passes else "FULL"
    best_rows = train_rows if best_label == "TRAIN" else full_rows

    if best_label == "FULL" and full_passes > train_passes:
        emit("  [INFO] FULL dataset statistics match Table II better than train-only.")
        emit("  This suggests Table II reports descriptive statistics for the ENTIRE")
        emit("  dataset (2002-2021), not just the training partition.")
    elif best_label == "TRAIN" and train_passes > full_passes:
        emit("  [INFO] TRAIN set statistics match Table II better.")

    if max(train_passes, full_passes) == len(train_rows):
        emit()
        emit("  [CONCLUSION] All metrics within tolerance. Dataset verified.")
        emit("  Proceed to Step 2 (Textual Input Embedder).")
    else:
        emit()
        emit(f"  [CONCLUSION] {len(train_rows) - max(train_passes, full_passes)} metrics FAIL.")
        emit("  Possible causes for discrepancies:")
        emit("  1. CDC data revisions since paper publication (~2024)")
        emit("  2. Different epiweek range (paper may use flu season weeks)")
        emit("  3. Data revisions due to retrospective corrections by CDC")
        emit("  4. API field mapping differences (e.g., age group definitions)")
        emit()
        if full_passes > train_passes:
            emit("  Since FULL dataset is the better match, we will use full dataset")
            emit("  statistics for analysis. Training split stats will differ from Table II.")
        emit("  ACTION: Please review discrepancies above.")

    emit()
    emit("=" * 100)

    report = "\n".join(lines)
    print(report)

    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n[REPORT] Saved to: {REPORT_TXT}")

    return report


def main():
    if not os.path.exists(INPUT_CSV):
        raise FileNotFoundError(f"Input CSV not found: {INPUT_CSV}")

    df, train, val, test = load_and_split(INPUT_CSV)

    train_stats = compute_stats(train)
    full_stats = compute_stats(df)

    rows = build_comparison_table(
        {"TRAIN": train_stats, "FULL": full_stats},
        GOLD_STANDARD
    )

    generate_report(df, train_stats, full_stats, rows)


if __name__ == "__main__":
    main()
