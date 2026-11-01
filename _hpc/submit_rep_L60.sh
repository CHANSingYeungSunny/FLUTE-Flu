#!/bin/bash -l
#SBATCH --job-name=miflu_L60reps
#SBATCH --partition=gpu_v100s
#SBATCH --exclude=gpu-v100s-06
#SBATCH --gres=gpu:v100s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=slurm-miflu-L60reps-%j.out
#
# L=60 reproduction protocol: the 9 missing reps (seed 2025 already exists as
# ckpt_L60_s2021/best_miflu_L60.pth and is reused, not retrained).
set -uo pipefail
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
export MH_BUDGET=24000
bash "${CODE}/miflu_rep_driver.sh" \
  60:2021 60:2022 60:2023 60:2024 60:2026 60:2027 60:2028 60:2029 60:2030
