#!/bin/bash
#SBATCH --job-name=wf_fix218
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --array=0-1
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/slurm_%A_%a.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/slurm_%A_%a.err
set -u
echo "host=$(hostname) shard=${SLURM_ARRAY_TASK_ID} date=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
bash /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/lane.sh "${SLURM_ARRAY_TASK_ID}" 4
