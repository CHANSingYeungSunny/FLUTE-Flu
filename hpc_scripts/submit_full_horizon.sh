#!/bin/bash
#SBATCH --job-name=full_L
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:30:00
#SBATCH --output=hpc_results/journal_evidence/logs/job%j_full_horizon.out
#SBATCH --error=hpc_results/journal_evidence/logs/job%j_full_horizon.err

# Trains the `full` MIFlu variant for a SINGLE horizon L (passed as $1),
# 10 reps x 20 epochs on the 1025-row window (train_end=717, val_end=819).
# Checkpoint is saved as best_model_L{L}.pt (per-horizon, no overwrite).
#
# Usage:
#   sbatch --job-name=full_L24 hpc_scripts/submit_full_horizon.sh 24
#   sbatch --job-name=full_L36 hpc_scripts/submit_full_horizon.sh 36
#   sbatch --job-name=full_L48 hpc_scripts/submit_full_horizon.sh 48
#   sbatch --job-name=full_L60 hpc_scripts/submit_full_horizon.sh 60

module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs
H="$1"
echo "=== HORIZON L=$H start $(date) ==="
python scripts/train_ablation.py --variant full --horizon "$H" --reps 10 \
    --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/full_H${H}/reps_1_to_10
echo "=== HORIZON L=$H done  $(date) ==="
