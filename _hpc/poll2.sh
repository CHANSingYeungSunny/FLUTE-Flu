#!/bin/bash
set -u
CD=/gpfs1/home/sychan552/stage5_a2_durable/code
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "=== now $(date -Is) ==="
sacct -j 718998,718999,719000,719001 -o JobID,JobName%16,Partition,State,Elapsed 2>&1 | head -12
echo
echo "=== per-horizon checkpoints (need 10 each, incl. the s2021 best) ==="
for L in 24 36 48 60; do
  per=$(ls "${AR}"/ckpt_L${L}_s2021/_rep_miflu_L${L}_seed20*.pth 2>/dev/null | wc -l)
  best=$([ -f "${AR}/ckpt_L${L}_s2021/best_miflu_L${L}.pth" ] && echo 1 || echo 0)
  new=$(ls "${AR}"/ckpt_L${L}_s20*/best_miflu_L${L}.pth 2>/dev/null | grep -vc "_s2021$" || true)
  echo "  L=$L: s2021 _rep=$per best=$best  new_per_seed_ckpts=$new"
done
echo
echo "=== all7 artifacts ==="
for L in 24 36 48 60; do
  n=$(ls "${AR}"/L${L}_all7/predictions_miflu_L${L}_seed20*.csv 2>/dev/null | wc -l)
  z=$(ls "${AR}"/L${L}_all7/pred_miflu_L${L}_seed20*.npz 2>/dev/null | wc -l)
  r=$(ls "${AR}"/L${L}_all7/results_miflu_L${L}_seed20*.csv 2>/dev/null | wc -l)
  m=$(ls "${AR}"/L${L}_all7/manifest_miflu_L${L}_seed20*.json 2>/dev/null | wc -l)
  echo "  L=$L: csv=$n npz=$z results=$r manifest=$m"
done
echo
for j in 718998 718999 719000 719001; do
  f=$(ls -1 "${CD}"/slurm-miflu-*-${j}.out 2>/dev/null | head -1)
  echo "=== ${j} -> ${f} ==="
  [ -n "${f}" ] && { grep -E "MSE_7var_z|DONE: test_mse|artifact|FAIL|MISSING|\[ok\] wrote" "${f}" | tail -5; echo "  --tail--"; tail -2 "${f}"; }
done
