#!/bin/bash -l
#SBATCH --job-name=miflu_seedA
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-miflu-seedA-%j.out
#
# Job A -- benchmark-protocol MIFlu fits, seeds 42/43/44:
#   L=24 x {42,43,44}  and  L=36 x {42,43,44}   (6 runs, ~55 min on A100)
#
# These are NOT the reproduction protocol (that is seed 2021..2030, 10 reps).
# They exist so the MIFlu row in the benchmark uses the same 3 seeds as the
# other 16 arms, one validation-selected checkpoint per (L, seed).
set -uo pipefail
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
export MH_BUDGET=11400          # 3h10m inside the 4h wall
bash "${CODE}/miflu_seed_driver.sh" 24:42 24:43 24:44 36:42 36:43 36:44
