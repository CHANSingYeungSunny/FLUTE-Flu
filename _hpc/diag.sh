#!/bin/bash
set -u
CD=/gpfs1/home/sychan552/stage5_a2_durable/code
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "=== now $(date -Is) ==="
sacct -j 718998,718999,719000,719001 -o JobID,JobName%16,Partition,State,Elapsed,ExitCode 2>&1 | head -10
echo
echo "=== why pending? ==="
squeue -u sychan552 -o "%.10i %.14P %.16j %.9T %.20r %.20E" 2>&1 | head -8
echo
echo "=== gpu_v100s node state ==="
sinfo -p gpu_v100s -N -o "%.16N %.9T %.8C %G %.14E" 2>&1 | head -10
echo
echo "=== L24 export job output (tail 40) ==="
grep -E "MSE_7var_z|MSE_ILITOTAL_z|\] L=24|skip|MISSING|ERROR|artifact|SUMMARY|PASS|FAIL" "${CD}/slurm-miflu-all7-719001.out" 2>/dev/null | tail -30
echo
echo "=== L24 all7 artifacts ==="
ls -la "${AR}/L24_all7/" 2>/dev/null | head -14
