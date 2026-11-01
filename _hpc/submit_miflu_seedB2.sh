#!/bin/bash -l
#SBATCH --job-name=miflu_seedB2
#SBATCH --partition=gpu_v100s
#SBATCH --exclude=gpu-v100s-06
#SBATCH --gres=gpu:v100s:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=06:00:00
#SBATCH --output=slurm-miflu-seedB2-%j.out
#
# Job B2 -- resubmission of 718930, which produced ZERO lines after
# "[A2] run_config" for 11 minutes on gpu-v100s-06 (AGENTS.md section 4
# gotcha 3: a V100 node whose GPU is wedged in uninterruptible sleep hangs the
# job forever and `timeout` cannot kill it). gpu-v100s-06 is excluded here.
#
# Same six cells as B: L=48 x {42,43,44} and L=60 x {42,43,44}.
set -uo pipefail
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
export MH_BUDGET=15000
bash "${CODE}/miflu_seed_driver.sh" 48:42 48:43 48:44 60:42 60:43 60:44
