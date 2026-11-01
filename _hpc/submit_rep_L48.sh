#!/bin/bash -l
#SBATCH --job-name=miflu_L48reps
#SBATCH --partition=gpu_v100s
#SBATCH --exclude=gpu-v100s-06
#SBATCH --gres=gpu:v100s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --output=slurm-miflu-L48reps-%j.out
#
# L=48 reproduction protocol: the 9 missing reps (seed 2021 already exists as
# ckpt_L48_s2021/best_miflu_L48.pth and is reused, not retrained).
# gpu-v100s-06 excluded: it wedged job 718930 on 2026-11-01 (zero output for
# 11 min, AGENTS.md section 4 gotcha 3).
set -uo pipefail
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
export MH_BUDGET=24000
bash "${CODE}/miflu_rep_driver.sh" \
  48:2022 48:2023 48:2024 48:2025 48:2026 48:2027 48:2028 48:2029 48:2030
