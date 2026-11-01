#!/bin/bash
# Inventory + cluster preemption policy + who preempted 719030.
set -u
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
cd "${CODE}" || exit 1

echo "=== partition stingy ==="
scontrol show partition stingy 2>/dev/null | tr ' ' '\n' | grep -Ei 'PartitionName|PreemptMode|PriorityTier|MaxTime|State|QoS|OverSubscribe|GraceTime' | head -20
echo
echo "=== qos list ==="
sacctmgr -n -P show qos format=Name,Priority,PreemptMode,MaxSubmitJobsPerUser,MaxJobsPerUser,MaxWall 2>/dev/null | head -20
echo
echo "=== preemptor search: jobs on gpu-a100-04 18:45-19:10 (all users) ==="
sacct -a -S 2026-11-01T18:45:00 -E 2026-11-01T19:10:00 -P \
  --format=JobID,JobName%22,User,Partition,State,Start,End,NodeList 2>/dev/null | grep -i 'gpu-a100-04' | head -20
echo
echo "=== artefact inventory: L*_all7 ==="
for L in 24 36 48 60; do
  echo "--- L=${L} ---"
  ls -la "${OUT}/L${L}_all7" 2>/dev/null | head -6
  echo "npz=$(ls "${OUT}"/L${L}_all7/pred_miflu_L${L}_seed*.npz 2>/dev/null | wc -l) manifest=$(ls "${OUT}"/L${L}_all7/manifest_miflu_L${L}_seed*.json 2>/dev/null | wc -l) csvwide=$(ls "${OUT}"/L${L}_all7/predictions_miflu_L${L}_seed*.csv 2>/dev/null | wc -l) results=$(ls "${OUT}"/L${L}_all7/results_miflu_L${L}_seed*.csv 2>/dev/null | wc -l)"
  ls "${OUT}"/L${L}_all7/pred_miflu_L${L}_seed*.npz 2>/dev/null | sed 's/.*seed/  seed/' | tr '\n' ' '; echo
done
echo
echo "=== checkpoint inventory ==="
for L in 24 36 48 60; do
  echo "L=${L}: $(ls "${OUT}"/ckpt_L${L}_s2021/*.pth 2>/dev/null | wc -l) ckpts"
done
echo
echo "=== _seedruns ==="
ls "${OUT}/_seedruns" 2>/dev/null | tr '\n' ' '; echo
echo
echo "=== squeue now ==="
squeue -u sychan552 -o '%.10i %.14j %.9P %.8T %.10M %.20R' 2>/dev/null
