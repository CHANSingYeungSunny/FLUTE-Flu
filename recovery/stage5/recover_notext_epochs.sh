#!/bin/bash
# Recover the per-(L, seed) best VALIDATION epoch for the no-text fits from the
# scheduler stdout (train_ablation.py does not persist best_epoch in metrics.csv).
# Emits CSV: L,seed,best_val_mse_all,best_epoch,n_epochs
cd /scratch/sychan552/a2_stage5/results/stage5/logs || exit 1
echo "L,seed,best_val_mse_all,best_epoch,n_epochs"
python3 - <<'PY'
import re, glob, collections
best = {}
for f in sorted(glob.glob("task_5858*.out")):
    txt = open(f, encoding="utf-8", errors="replace").read()
    cur_L = None
    for line in txt.splitlines():
        m = re.search(r"horizon=(\d+) seed=(\d+)", line)
        if m:
            cur_L, cur_S = int(m.group(1)), int(m.group(2)); continue
        m = re.search(r"ep\s+(\d+)/(\d+) \| train_loss=([0-9.]+) \| val_mse=([0-9.]+)\(All\)", line)
        if m and cur_L is not None:
            ep, ne, tl, vm = int(m.group(1)), int(m.group(2)), float(m.group(3)), float(m.group(4))
            k = (cur_L, cur_S)
            if k not in best or vm < best[k][0]:
                best[k] = (vm, ep, ne)
for (L, s), (vm, ep, ne) in sorted(best.items()):
    print(f"{L},{s},{vm:.10f},{ep},{ne}")
PY
