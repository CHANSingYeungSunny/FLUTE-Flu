"""Step 2 of Ruthless Audit: Channel Isolation Test.
From the REAL model outputs in results_miflu.csv:
  mse_ili  = MSE on ILITOTAL only (column 5)  -> should match paper Table V (~1.5)
  mse_all  = MSE averaged over all 7 vars     -> paper Table VIII (~1.4-3.2)
We also compute, per rep, the gap between mse_all and mse_ili to see if a
single outlier channel (e.g. OT) is inflating the 7-channel average.
"""
import csv
import numpy as np

rows = list(csv.DictReader(open("data/results_miflu.csv")))

# ILITOTAL-only vs All-vars, per horizon (mean over 10 reps)
by_L = {}
for r in rows:
    by_L.setdefault(int(r["L"]), []).append(r)

print("=== Channel Isolation (National, normalized space) ===")
print(f"{'L':>4} | {'MSE_ILITOTAL':>13} | {'MSE_AllVars':>12} | {'All/ILI ratio':>13} | paper MIFlu ILI")
for L in [24, 36, 48, 60]:
    rs = by_L[L]
    mse_ili = np.mean([float(x["mse_ili"]) for x in rs])
    mse_all = np.mean([float(x["mse_all"]) for x in rs])
    ratio = mse_all / mse_ili
    print(f"{L:>4} | {mse_ili:>13.3f} | {mse_all:>12.3f} | {ratio:>13.2f}x | (Table V ~1.5)")

# Interpretation
print("\nINTERPRETATION:")
print("  - If MSE_ILITOTAL (~4.5) >> paper ILITOTAL (~1.5): the gap is in the MODEL's")
print("    prediction of ILITOTAL itself, NOT a data-mapping artifact of other channels.")
print("  - If MSE_AllVars >> MSE_ILITOTAL: another channel (likely OT) is inflating the avg.")
print(f"  - Here All/ILI ratio ~ {np.mean([np.mean([float(x['mse_all']) for x in by_L[L]])/np.mean([float(x['mse_ili']) for x in by_L[L]]) for L in [24,36,48,60]]):.2f}x")
