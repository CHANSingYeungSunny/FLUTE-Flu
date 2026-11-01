#!/bin/bash -l
#SBATCH --job-name=miflu_export
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:40:00
#SBATCH --output=slurm-export-%j.out
#
# Re-export the prediction artefacts for the supplementary evaluation only.
# The AUTHORITATIVE 10-repetition mean for L=24 came from job 714909
# (test MSE 1.3045, mean of 10 reps); that run crashed in the CSV export step
# because the author's raw file has `date` instead of `epiweek`. cdc_calendar.py
# is now tolerant of that, so this short 1-rep run re-produces the identical
# protocol and writes the per-week predictions used ONLY for the supplementary
# per-step / PTE-PIE plots (a representative seed, not the reported mean).
set -uo pipefail
module unload default
module load old_modules

CODE=/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/home/sychan552/stage5_a2_durable/author_runs
cd "${CODE}"

"${PY}" -u train_miflu.py \
  --profile author_repo_966 \
  --horizon 24 \
  --text-source author_file \
  --reps 1 \
  --epochs 20 \
  --batch 16 \
  --learning-rate 0.0001 \
  --containment strict \
  --export-dir "${OUT}/L24_s2021_pred" \
  --ckpt-dir   "${OUT}/ckpt_L24_s2021_pred"

echo "[export] DONE"
