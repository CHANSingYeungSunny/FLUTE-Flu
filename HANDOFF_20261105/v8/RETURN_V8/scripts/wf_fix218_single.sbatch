#!/bin/bash
#SBATCH --job-name=wf_fix218
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/single_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/logs/single_%j.err
set -u
echo "host=$(hostname) date=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
bash /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/wf_fix218/lane.sh 0 1
