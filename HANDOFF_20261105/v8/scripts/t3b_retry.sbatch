#!/bin/bash
#SBATCH --job-name=t3b_llm_import_v8
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/t3b_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/t3b_%j.err
set -u
echo "host=$(hostname) date=$(date -u +%FT%TZ)"
bash /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/t3b_retry.sh
echo "T3B_SCRIPT_RC=$?"
