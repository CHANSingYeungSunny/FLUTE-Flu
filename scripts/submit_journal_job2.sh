#!/bin/bash
#SBATCH --job-name=miflu_j2
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job2_%j.out
#SBATCH --error=hpc_results/journal_evidence/logs/job2_%j.err

module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export TRANSFORMERS_CACHE=$HF_HOME
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs
echo "JOB2 start $(date) on $(hostname)"

# Recipe sweep on `full`
for spec in "adamw_cosine full__adamw_cosine" "huber_clip full__huber_clip"; do
  recipe=$(echo $spec | cut -d' ' -f1)
  name=$(echo $spec | cut -d' ' -f2)
  echo "===== [$(date)] recipe $recipe ($name) ====="
  python scripts/train_ablation.py --variant full --recipe $recipe --horizon 24 \
      --reps 10 --epochs 20 --batch 16 --seed 42 \
      --export-dir hpc_results/journal_evidence/$name/reps_1_to_10
  echo "===== [$(date)] recipe $recipe exit=$? ====="
done

# Early stopping on validation loss, on `full`
echo "===== [$(date)] early-stop full ====="
python scripts/train_ablation.py --variant full --horizon 24 --reps 10 \
    --epochs 20 --batch 16 --seed 42 --early-stop --patience 5 \
    --export-dir hpc_results/journal_evidence/full__earlystop/reps_1_to_10
echo "===== [$(date)] early-stop exit=$? ====="

echo "JOB2 DONE $(date)"
