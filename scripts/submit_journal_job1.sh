#!/bin/bash
#SBATCH --job-name=miflu_j1
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job1_%j.out
#SBATCH --error=hpc_results/journal_evidence/logs/job1_%j.err

module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export TRANSFORMERS_CACHE=$HF_HOME
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs
echo "JOB1 start $(date) on $(hostname)"
for v in full no_multi no_lora no_lora_multi; do
  echo "===== [$(date)] variant $v ====="
  python scripts/train_ablation.py --variant $v --horizon 24 --reps 10 \
      --epochs 20 --batch 16 --seed 42 \
      --export-dir hpc_results/journal_evidence/$v/reps_1_to_10
  echo "===== [$(date)] variant $v exit=$? ====="
done
echo "JOB1 DONE $(date)"
