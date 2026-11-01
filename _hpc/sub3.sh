#!/bin/bash
set -u
CD=/gpfs1/home/sychan552/stage5_a2_durable/code
echo "=== now $(date -Is) ==="
sacct -j 719030,719042 -o JobID,JobName%16,State,Elapsed 2>&1 | head -8
echo
echo "=== bisection output ==="
cat "${CD}"/slurm-bisect-719042.out 2>/dev/null
echo
echo "=== try NLinear A100 submission (QOS permitting) ==="
sbatch "${CD}/submit_nlinear_a100.sh" 2>&1 || true
echo
squeue -u sychan552 -h -o "%.10i %.10P %.16j %.9T" 2>&1 | head
