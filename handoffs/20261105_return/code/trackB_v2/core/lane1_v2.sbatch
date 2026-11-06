#!/bin/bash
#SBATCH --job-name=trackB_v2_core_l1
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=1-00:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/trackB_20261104/core/logs/lane1_v2-%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/trackB_20261104/core/logs/lane1_v2-%j.err
set -u
bash /gpfs1/scratch/sychan552/trackB_20261104/run_lane_v2.sh 1 2 core
