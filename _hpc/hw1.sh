#!/bin/bash
set -u
echo "=== cancelling V100 training jobs (hardware confound) ==="
scancel 718999 719000 2>&1
sleep 6
sacct -j 718998,718999,719000,719001 -o JobID,JobName%16,Partition,State,Elapsed 2>&1 | head -10
echo
echo "=== L24 export job progress ==="
grep -E "MSE_7var_z|MSE_ILITOTAL_z|\] L=24|skip|MISSING|ERROR|PASS|FAIL" /gpfs1/home/sychan552/stage5_a2_durable/code/slurm-miflu-all7-719001.out 2>/dev/null | tail -20
echo
echo "=== L24 all7 artifacts so far ==="
ls -1 /gpfs1/home/sychan552/stage5_a2_durable/author_runs/L24_all7/ 2>/dev/null | head -20
echo
echo "=== which nodes did the ORIGINAL 192-cell jobs use? (sample) ==="
sacct -u sychan552 -S 2026-10-25 -o JobID,JobName%24,Partition,State,NodeList 2>&1 | grep -iE "patchtst|nlinear|dlinear|timecma|qwen_time|calf|dnn|cnn|rnn|lstm|gru|decision|random_forest|gradient|svr|knn" | head -20
echo
echo "=== node -> GPU model map ==="
sinfo -N -o "%.18N %.10P %G" 2>&1 | head -40
