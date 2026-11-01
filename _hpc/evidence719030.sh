#!/bin/bash
# Evidence for the L24 seed-2021 miss + inventory of the half-finished run dirs.
set -u
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
cd "${CODE}" || exit 1

echo "=== 719030 log: L24 export section ==="
grep -n "L=24\|legacy\|ERROR\|MISSING\|skip\|Assertion" slurm-miflu-a100-719030.out 2>/dev/null | head -40

echo
echo "=== 719030 log: summary tail 45 ==="
tail -n 45 slurm-miflu-a100-719030.out 2>/dev/null

echo
echo "=== ckpt dirs for L36/L48/L60 per seed ==="
for L in 36 48 60; do
  echo "--- L=${L} ---"
  ls -d "${OUT}"/ckpt_L${L}_s* 2>/dev/null
  for d in "${OUT}"/ckpt_L${L}_s*/; do
    [ -d "${d}" ] || continue
    echo "  ${d}: $(ls "${d}"*.pth 2>/dev/null | wc -l) pth $(ls "${d}"*.pth 2>/dev/null | xargs -r -n1 basename | tr '\n' ' ')"
  done
done

echo
echo "=== _seedruns content ==="
for d in "${OUT}"/_seedruns/*/; do
  [ -d "${d}" ] || continue
  echo "  ${d}: $(ls "${d}" | tr '\n' ' ')"
done

echo
echo "=== all pred_miflu npz basenames (source of truth) ==="
ls "${OUT}"/L*_all7/pred_miflu_*.npz 2>/dev/null | xargs -r -n1 basename | sort
