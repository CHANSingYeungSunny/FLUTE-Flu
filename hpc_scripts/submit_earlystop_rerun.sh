#!/bin/bash
#SBATCH --job-name=earlystop_rerun
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/journal_evidence/logs/job%j_%x.out
#SBATCH --error=hpc_results/journal_evidence/logs/job%j_%x.err

# Re-run `full__earlystop` after the 2026-09 indicator change.
#
# WHY A RE-RUN IS REQUIRED
# ------------------------
# The early-stopping "dual gate" (checkpoint only when val_loss improves AND
# peak_hit_rate > 0.7) was REMOVED together with the peak_hit_rate indicator.
# Early stopping is now plain val_loss + patience. That changes training
# behaviour, so the pre-change `full__earlystop` numbers are NOT comparable and
# must be regenerated.
#
# Every other variant used the fixed 20-epoch protocol (no stopper) and is
# unaffected — do NOT re-run those.
#
# --force is ESSENTIAL: the old run left a metrics.csv behind, and without
# --force the resume logic would skip every rep and silently report the OLD
# (dual-gate) numbers.

module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime

mkdir -p hpc_results/journal_evidence/logs

echo "JOB start $(date) on $(hostname) | full__earlystop re-run (plain val_loss + patience)"

python scripts/train_ablation.py --variant full --early-stop --patience 5 \
    --horizon 24 --reps 10 --epochs 20 --batch 16 --seed 42 --force \
    --export-dir hpc_results/journal_evidence/full__earlystop/reps_1_to_10

echo "JOB DONE $(date) | full__earlystop re-run"
