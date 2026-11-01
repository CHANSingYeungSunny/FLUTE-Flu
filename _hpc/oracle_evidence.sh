#!/bin/bash
set -u
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "=== DONE lines in the fresh L36 runs ==="
for s in 2022 2023; do
  echo "--- L36 seed${s} ---"
  grep -h "DONE: test_mse\|kept rep seed\|BEST\|best_val" "${OUT}/_seedruns/L36_s${s}"/training_miflu_log_*.txt 2>/dev/null | tail -6
done
echo
echo "=== original 10-rep logs: kept rep seed per horizon ==="
for L in 24 36 48 60; do
  echo "--- L${L} ---"
  grep -h "kept rep seed" "${OUT}/L${L}_s2021"/training_*.txt 2>/dev/null | tail -2
done
echo
echo "=== which test_mse lines exist in L36_s2021 (empty dir?) ==="
ls -la "${OUT}/_seedruns/L36_s2021" 2>/dev/null
echo
echo "=== sha256 of the four original best ckpts + L24 rep2021 ==="
sha256sum "${OUT}/ckpt_L24_s2021/best_miflu_L24.pth" \
          "${OUT}/ckpt_L24_s2021/_rep_miflu_L24_seed2021.pth" \
          "${OUT}/ckpt_L36_s2021/best_miflu_L36.pth" \
          "${OUT}/ckpt_L48_s2021/best_miflu_L48.pth" \
          "${OUT}/ckpt_L60_s2021/best_miflu_L60.pth" 2>/dev/null
