#!/bin/bash
#SBATCH --job-name=trackB_v2_core_ctl
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=1-00:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/trackB_20261104/core/logs/controller_v2-%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/trackB_20261104/core/logs/controller_v2-%j.err
set -u
export CONTROLLER_WALL_SECONDS=82800
bash /gpfs1/scratch/sychan552/trackB_20261104/controller_v2.sh core
