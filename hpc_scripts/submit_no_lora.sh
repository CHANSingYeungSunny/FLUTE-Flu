#!/bin/bash
#SBATCH --job-name=no_lora
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job%j_%x.out
#SBATCH --error=hpc_results/journal_evidence/logs/job%j_%x.err

# Core variant 2/4: w/o LoRA.
# Audit gate: PARAM AUDIT must report `LoRA Tensors: 0 | LoRA Params: 0`
# (the LoRA modules are never created, not merely frozen).

module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs
echo "JOB start $(date) on $(hostname) | variant=no_lora"
python scripts/train_ablation.py --variant no_lora --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/no_lora/reps_1_to_10
echo "JOB DONE $(date) | variant=no_lora"
