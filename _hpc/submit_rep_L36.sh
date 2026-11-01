#!/bin/bash -l
#SBATCH --job-name=miflu_L36reps
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-miflu-L36reps-%j.out
#
# L=36 reproduction protocol: the 9 missing reps (seed 2024 already exists as
# ckpt_L36_s2021/best_miflu_L36.pth and is reused, not retrained).
set -uo pipefail
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
export MH_BUDGET=12000
bash "${CODE}/miflu_rep_driver.sh" \
  36:2021 36:2022 36:2023 36:2025 36:2026 36:2027 36:2028 36:2029 36:2030
