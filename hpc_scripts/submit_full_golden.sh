#!/bin/bash
# submit_full_golden.sh — auto-submit loop for the GOLDEN artifact structure.
# Submits `full` variant for L=24,36,48,60, each as its own job, waiting for a
# free `stingy` slot between submissions (QOS caps 1 running + 1 pending).
# export-dir = journal_evidence/full  ->  NEW layout
#   journal_evidence/full/horizon_L{L}/rep_{rep}/checkpoints/best_model_full_L{L}_rep{rep}.pt
# (NOTE: gpu_a100 is congested ~3.5h PD; stingy has idle A100s, so we use stingy
#  to actually materialize the clean checkpoints promptly.)
module unload default && module load old_modules
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
cd /home/sychan552/scratch/CHATTIME/Chattime
mkdir -p hpc_results/journal_evidence/logs

JOUT=hpc_results/journal_evidence/logs
for H in 24 36 48 60; do
  while true; do
    n=$(squeue -u "$USER" -h -p stingy -t PD,R | wc -l)
    if [ "$n" -lt 2 ]; then break; fi
    sleep 60
  done
  echo "=== submitting full golden L=$H at $(date) ==="
  sbatch --job-name=full_golden_L${H} \
    --partition=stingy --gres=gpu:a100:1 --cpus-per-task=8 --mem=32G --time=01:30:00 \
    --output=${JOUT}/job%j_full_golden_L${H}.out \
    --error=${JOUT}/job%j_full_golden_L${H}.err \
    --wrap="python scripts/train_ablation.py --variant full --horizon $H --reps 10 --epochs 20 --batch 16 --seed 42 --force --export-dir hpc_results/journal_evidence/full"
done
echo "ALL GOLDEN JOBS SUBMITTED"
