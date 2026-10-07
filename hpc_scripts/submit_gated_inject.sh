#!/bin/bash
#SBATCH --job-name=gated_inject
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job%j_%x.out
#SBATCH --error=hpc_results/journal_evidence/logs/job%j_%x.err

# Core variant 4/4: ModalityAligner (gated cross-modal injection) with the
# first 2 GPT2 layers fully unfrozen.
# Audit gate: PARAM AUDIT must report Total Trainable: 17,537,449 and
# `unfreeze_first_k=2`.

module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs
echo "JOB start $(date) on $(hostname) | variant=gated_inject"
python scripts/train_ablation.py --variant gated_inject --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/gated_inject/reps_1_to_10
echo "JOB DONE $(date) | variant=gated_inject"
