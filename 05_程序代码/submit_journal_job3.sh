#!/bin/bash
#SBATCH --job-name=miflu_j3
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job3_%j.out
#SBATCH --error=hpc_results/journal_evidence/logs/job3_%j.err

module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export TRANSFORMERS_CACHE=$HF_HOME
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs
echo "JOB3 start $(date) on $(hostname)"
python scripts/train_ablation.py --variant no_text_ln --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 \
    --export-dir hpc_results/journal_evidence/no_text_ln/reps_1_to_10
echo "JOB3 DONE $(date)"
