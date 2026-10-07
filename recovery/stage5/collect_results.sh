#!/bin/bash
cd /scratch/sychan552/a2_stage5 || exit 1
S=results/stage5/scoring
echo "=== average_mse_4L.csv ==="
cat $S/average_mse_4L.csv
echo
echo "=== score_summary.csv (model,L) ==="
cat $S/score_summary.csv
echo
echo "=== per-var MSE (mean over seeds) ==="
python - <<'PY'
import pandas as pd
d = pd.read_csv("results/stage5/scoring/score_matrix.csv")
v = [c for c in d.columns if c.startswith("mse_") and not c.startswith("mse_all")
     and c not in ("mse_ili",)]
pv = [c[4:] for c in v]
g = d.groupby("model")[v].mean()
print(g.round(4).to_string())
print()
print("=== per-var MAE (mean over seeds) ===")
v2 = [c for c in d.columns if c.startswith("mae_") and c not in ("mae_all", "mae_ili")]
g2 = d.groupby("model")[v2].mean()
print(g2.round(4).to_string())
print()
print("=== original-unit MAE per variable (mean over seeds & L) ===")
v3 = [c for c in d.columns if c.startswith("mae_phys_")]
print(d.groupby("model")[v3].mean().round(3).to_string())
print()
print("=== ILITOTAL (ch 4) mse/mae/pcc, mean over seeds, per L ===")
print(d.pivot_table(index="L", columns="model", values=["mse_ili", "mae_ili", "pcc_ili"],
                    aggfunc="mean").round(4).to_string())
PY
echo
echo "=== naive cross-check vs train_naive_966 metrics.csv ==="
cat results/stage5/author_966/naive/metrics.csv
echo
echo "=== checkpoint lock head ==="
head -40 $S/CHECKPOINT_LOCK.csv
echo
echo "=== scoring dir ==="
ls -la $S
ls $S/predictions | head -8
ls $S/predictions | wc -l
du -sh $S
