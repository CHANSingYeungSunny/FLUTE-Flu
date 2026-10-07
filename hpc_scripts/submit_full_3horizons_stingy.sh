#!/bin/bash
#SBATCH --job-name=full_3h
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job%j_full_3h.out
#SBATCH --error=hpc_results/journal_evidence/logs/job%j_full_3h.err

# Single chained job on a FREE idle A100 (stingy/gpu-a100-05) that trains the
# `full` MIFlu variant for L=36, 48, 60 SEQUENTIALLY.
# stingy QOS allows only 1 running job -> chaining avoids QOSMaxSubmitJobPerUserLimit
# that a 3-separate-job submission would hit. The 1025-row window (717/819) and
# the `*_ili_phys` export are hard-coded in configs.py / train_ablation.py.
# Outputs land in hpc_results/journal_evidence/full/reps_1_to_10/rep_01/.

module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs
for L in 36 48 60; do
  echo "=== HORIZON L=$L start $(date) ==="
  python scripts/train_ablation.py --variant full --horizon "$L" --reps 10 \
      --epochs 20 --batch 16 --seed 42 --force \
      --export-dir hpc_results/journal_evidence/full/reps_1_to_10
  echo "=== HORIZON L=$L done  $(date) ==="
done
echo "ALL THREE HORIZONS DONE $(date)"
