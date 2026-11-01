#!/bin/bash
set -u
cd /gpfs1/home/sychan552/stage5_a2_durable/code
echo "--- training jobs (9 reps each for L36/L48/L60) ---"
sbatch submit_rep_L36.sh
sbatch submit_rep_L48.sh
sbatch submit_rep_L60.sh
echo "--- all7 export jobs (CPU, tiny): one per horizon ---"
sbatch --export=ALL,LH=24 submit_export_all7.sh
sbatch --export=ALL,LH=36 submit_export_all7.sh
sbatch --export=ALL,LH=48 submit_export_all7.sh
sbatch --export=ALL,LH=60 submit_export_all7.sh
sleep 15
echo "--- queue ---"
squeue -u sychan552 -h -o "%.10i %.12P %.18j %.9T"
