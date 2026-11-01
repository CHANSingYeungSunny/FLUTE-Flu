#!/bin/bash
set -u
CD=/gpfs1/home/sychan552/stage5_a2_durable/code
echo "=== accounting dump (jobs since 2026-10-25) ==="
sacct -u sychan552 -S 2026-10-25 -P -o JobID,JobIDRaw,JobName%40,Partition,State,NodeList,Start,End,Elapsed 2>/dev/null > "${CD}/_sacct_dump.csv"
wc -l "${CD}/_sacct_dump.csv"
echo "--- head ---"; head -3 "${CD}/_sacct_dump.csv"
echo
echo "=== gpu node -> gres ==="
sinfo -N -o "%.20N %.12P %G" 2>&1 | grep -E "gpu|GRES" > "${CD}/_node_gres.csv"
cat "${CD}/_node_gres.csv"
echo
echo "=== controller 719030 status ==="
sacct -j 719030 -o JobID,State,Elapsed,NodeList 2>&1 | head -4
squeue -u sychan552 -o "%.10i %.10P %.16j %.9T %R %.20E" 2>&1 | head -6
echo
echo "=== checkpoints now ==="
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
for L in 24 36 48 60; do
  s2021=$(ls "${AR}"/ckpt_L${L}_s2021/_rep_miflu_L${L}_seed20*.pth 2>/dev/null | wc -l)
  best=$([ -f "${AR}/ckpt_L${L}_s2021/best_miflu_L${L}.pth" ] && echo 1 || echo 0)
  new=$(ls -d "${AR}"/ckpt_L${L}_s20*/ 2>/dev/null | grep -v "_s2021/$" | wc -l)
  echo "  L=$L: s2021 rep=$s2021 best=$best new_seed_dirs=$new"
done
ls -1 "${AR}"/L36_all7/ 2>/dev/null | head
