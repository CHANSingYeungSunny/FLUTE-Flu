#!/bin/bash
set -u
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
PY=/home/sychan552/.conda/envs/mllflu_hpc/bin/python
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
"${PY}" - <<'PYEOF'
import numpy as np, pandas as pd, os
AR = "/gpfs1/home/sychan552/stage5_a2_durable/author_runs"
# Blockers A check: is the reported test_mse_all the metric over the FIRST 160
# windows (drop_last=True on a 170-window test set)?
ORACLE = {2022: 1.201078, 2023: 1.284212, 2024: 1.259462, 2025: 1.464643}
for seed, exp in ORACLE.items():
    p = os.path.join(AR, "L24_all7", f"predictions_miflu_L24_seed{seed}.csv")
    if not os.path.exists(p):
        print(f"seed {seed}: missing"); continue
    d = pd.read_csv(p)
    te = d[d.split == "test"]
    W = int(te["abs_week"].max() - te["step"].max())  # not needed
    wins = np.sort(te["abs_week"].sub(te["step"]).unique())
    n = len(wins)
    def mse7(sel):
        sub = te[te["abs_week"].sub(te["step"]).isin(sel)]
        return float(np.mean([(sub[f"prediction_{s}"] - sub[f"ground_truth_{s}"])**2
                              for s in ["wili","unwili","age_0_4","age_5_24","ili","num_providers","ot"]]))
    full = mse7(wins)
    # drop_last=True, batch 16 -> first (n//16)*16 windows
    keep = wins[:(n // 16) * 16]
    kept = mse7(keep)
    print(f"seed {seed}: windows={n}  all={full:.6f}  first{len(keep)}={kept:.6f}  oracle={exp:.6f}"
          f"  |all-oracle|={abs(full-exp):.2e}  |kept-oracle|={abs(kept-exp):.2e}")
PYEOF
