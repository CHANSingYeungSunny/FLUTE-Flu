#!/bin/bash
#SBATCH --job-name=t3_restore_final
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:40:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/t3restore_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/t3restore_%j.err
set -u
echo "host=$(hostname) date=$(date -u +%FT%TZ)"
bash /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/t3_restore_final.sh
echo "T3_RESTORE_SCRIPT_RC=$?"
