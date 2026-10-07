#!/bin/bash
#SBATCH --job-name=no_lora_multi
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job%j_%x.out
#SBATCH --error=hpc_results/journal_evidence/logs/job%j_%x.err

# Re-run missing variant no_lora_multi (w/o LoRA + multimodality) with CURRENT code.
module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs
echo "JOB start $(date) on $(hostname) | variant=no_lora_multi"
python scripts/train_ablation.py --variant no_lora_multi --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/no_lora_multi/reps_1_to_10
echo "JOB DONE $(date) | variant=no_lora_multi"
