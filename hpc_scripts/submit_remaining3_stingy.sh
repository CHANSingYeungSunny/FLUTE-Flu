#!/bin/bash
#SBATCH --job-name=remaining3
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job%j_%x.out
#SBATCH --error=hpc_results/journal_evidence/logs/job%j_%x.err

# Train the 3 remaining variants (full recipes) sequentially in ONE stingy job.
# Avoids the 1-job-per-user QOS limit and the currently broken gpu_a100 partition.
module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs

echo "JOB start $(date) on $(hostname) | remaining3: huber_clip, earlystop, adamw_cosine"

echo "===== [1/3] full + huber_clip ====="
python scripts/train_ablation.py --variant full --recipe huber_clip --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/full__huber_clip/reps_1_to_10

echo "===== [2/3] full + early_stop ====="
python scripts/train_ablation.py --variant full --early-stop --patience 5 --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/full__earlystop/reps_1_to_10

echo "===== [3/3] full + adamw_cosine ====="
python scripts/train_ablation.py --variant full --recipe adamw_cosine --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/full__adamw_cosine/reps_1_to_10

echo "JOB DONE $(date) | remaining3"
