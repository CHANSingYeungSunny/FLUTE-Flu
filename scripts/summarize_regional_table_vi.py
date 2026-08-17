#!/usr/bin/env python
"""Aggregate MIFlu paper-protocol National-task results into a Table V style summary.

NOTE: This is the NATIONAL task (single series, L=24/36/48/60), corresponding to the
MIFlu paper's Table V (per-horizon MSE/MAE). It is NOT the Regional task (Table VI,
10 HHS regions, RMSE/PCC) — that task has NOT been started yet.

Reads:
  - results/ili/metrics/miflu_L{L}_ili_peak_trend_summary.json  (4 supplementary indicators)
  - hpc_results/data/results_miflu_paper_protocol_table_*.csv   (MSE/MAE per horizon)
Writes:
  - results/ili/National_Table_V_summary.csv
  - results/ili/National_Table_V_summary.md
"""
import os, json, glob
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(HERE)
MET_DIR = os.path.join(PROJECT_ROOT, "results", "ili", "metrics")
TABLE_DIR = os.path.join(PROJECT_ROOT, "hpc_results", "data")

# Map each horizon -> its table CSV by modification order isn't reliable; instead
# we read every table CSV and key by the Horizon column.
L_list = [24, 36, 48, 60]

# --- load MSE/MAE from table CSVs ---
mse_mae = {}
for fp in glob.glob(os.path.join(TABLE_DIR, "results_miflu_paper_protocol_table_*.csv")):
    try:
        df = pd.read_csv(fp)
    except Exception:
        continue
    for _, row in df.iterrows():
        L = int(row["Horizon"])
        mse_mae[L] = {
            "MSE_ILI_mean": float(row["MSE_ILI_mean"]),
            "MSE_ILI_std": float(row["MSE_ILI_std"]),
            "MAE_ILI_mean": float(row["MAE_ILI_mean"]),
            "MAE_ILI_std": float(row["MAE_ILI_std"]),
        }

# --- load supplementary indicators from per-L summary JSON ---
rows = []
for L in L_list:
    jp = os.path.join(MET_DIR, f"miflu_L{L}_ili_peak_trend_summary.json")
    with open(jp) as f:
        s = json.load(f)
    v = s["verdicts"]
    pa = s["peak_aggregate"]
    tr = s["trend_indicators"]
    mm = mse_mae.get(L, {})

    def g(d):
        val = d.get("value")
        if val is None:
            return "NA"
        if isinstance(val, float):
            return f"{val:.4f}"
        return str(val)

    rows.append({
        "Horizon (L)": L,
        "MSE_ILI": (f"{mm.get('MSE_ILI_mean', float('nan')):.4f}±{mm.get('MSE_ILI_std', float('nan')):.4f}"
                    if mm else "NA"),
        "MAE_ILI": (f"{mm.get('MAE_ILI_mean', float('nan')):.4f}±{mm.get('MAE_ILI_std', float('nan')):.4f}"
                    if mm else "NA"),
        # Supplementary (non-paper-protocol) indicators:
        "Peak Hit": f"{g(v['peak_hit_rate'])} (thr 0.75)",
        "Timing (wk)": f"{g(v['mean_abs_delta_t'])} (thr 2.0)",
        "Peak Int. (%)": f"{g(v['mean_peak_magnitude_rel_err'])} (thr 20.0)",
        "Direction": f"{g(v['directional_accuracy'])} (thr 0.60)",
        "Peak Hit count": pa.get("peak_hit_count", "NA"),
        "Missed peaks": pa.get("n_missed", "NA"),
    })

out_df = pd.DataFrame(rows)
csv_path = os.path.join(PROJECT_ROOT, "results", "ili", "National_Table_V_summary.csv")
md_path = os.path.join(PROJECT_ROOT, "results", "ili", "National_Table_V_summary.md")
out_df.to_csv(csv_path, index=False)

with open(md_path, "w") as f:
    f.write("# MIFlu Paper-Protocol Results — Regional/Table VI Summary\n\n")
    f.write("**Primary metrics (MIFlu paper protocol, Section V-B): MSE / MAE only.**\n\n")
    f.write("The four Peak/Timing/Intensity/Direction columns are **supplementary "
            "diagnostics** computed by this project (compute_miflu_indicators.py), "
            "NOT part of the MIFlu paper's reported metrics. Listed for insight only.\n\n")
    f.write("| " + " | ".join(out_df.columns) + " |\n")
    f.write("|" + "|".join(["---"] * len(out_df.columns)) + "|\n")
    for _, r in out_df.iterrows():
        f.write("| " + " | ".join(str(r[c]) for c in out_df.columns) + " |\n")
    f.write("\n## Verdicts (supplementary thresholds)\n")
    f.write("- Peak Hit >= 0.75, Timing <= 2.0 wk, Peak Intensity <= 20.0%, Direction >= 0.60\n")
    f.write("- 'not accurate' on Peak Hit / Peak Intensity reflects missed peaks and "
            "magnitude error at matched peaks (see Peak Hit count / Missed peaks).\n")

print(f"[out] {csv_path}")
print(f"[out] {md_path}")
print(out_df.to_string(index=False))
