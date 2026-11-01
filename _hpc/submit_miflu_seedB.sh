#!/bin/bash -l
#SBATCH --job-name=miflu_seedB
#SBATCH --partition=gpu_v100s
#SBATCH --gres=gpu:v100s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=slurm-miflu-seedB-%j.out
#
# Job B -- benchmark-protocol MIFlu fits, seeds 42/43/44:
#   L=48 x {42,43,44}  and  L=60 x {42,43,44}   (6 runs, ~60-90 min on V100)
#
# Runs on gpu_v100s in parallel with Job A on stingy so the 12 cells finish in
# about one hour of wall clock instead of two serial stingy slots.
set -uo pipefail
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
export MH_BUDGET=15000          # 4h10m inside the 6h wall
bash "${CODE}/miflu_seed_driver.sh" 48:42 48:43 48:44 60:42 60:43 60:44
