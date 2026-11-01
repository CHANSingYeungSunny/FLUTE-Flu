#!/bin/bash
# Submit the NLinear A100 re-run (task 2) and show the queue. Login-node safe (sbatch/squeue only).
set -u
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
cd "${CODE}" || exit 1
echo "=== md5 of submit_nlinear_a100.sh ==="
md5sum submit_nlinear_a100.sh
echo "=== squeue before ==="
squeue -u sychan552 -o '%.8i %.14j %.8P %.8T %.10M'
echo "=== sbatch ==="
sbatch submit_nlinear_a100.sh 2>&1
echo "sbatch_rc=$?"
sleep 2
echo "=== squeue after ==="
squeue -u sychan552 -o '%.8i %.14j %.8P %.8T %.10M %.30R'
