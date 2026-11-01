#!/bin/bash
set -u
CD=/gpfs1/home/sychan552/stage5_a2_durable/code
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "=== now $(date -Is) ==="
sacct -j 719030 -o JobID,State,Elapsed,NodeList 2>&1 | head -3
echo
echo "=== controller output (key lines) ==="
grep -E "a100\]|oracle|MSE_7var|artifact|FAIL|MISMATCH|ok\] wrote|L=[0-9]+ seed" "${CD}"/slurm-miflu-a100-719030.out 2>/dev/null | tail -25
echo
echo "=== artifacts ==="
for L in 24 36 48 60; do
  n=$(ls "${AR}"/L${L}_all7/pred_miflu_L${L}_seed20*.npz 2>/dev/null | wc -l)
  m=$(ls "${AR}"/L${L}_all7/manifest_miflu_L${L}_seed20*.json 2>/dev/null | wc -l)
  echo "  L=$L: npz=$n manifest=$m"
done
echo
echo "=== a manifest's provenance block ==="
f=$(ls "${AR}"/L24_all7/manifest_miflu_L24_seed202*.json 2>/dev/null | head -1)
[ -n "$f" ] && { echo "$f"; python3 -c "
import json,sys
d=json.load(open('$f'))
print(json.dumps({k:d.get(k) for k in ('seed','protocol','checkpoint','environment','wall_clock_seconds_export')}, indent=2)[:1400])
"; }
