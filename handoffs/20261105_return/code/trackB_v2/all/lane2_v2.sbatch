#!/bin/bash
#SBATCH --job-name=trackB_v2_all_l2
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=48G
#SBATCH --time=06:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/trackB_20261104/all/logs/lane2_v2-%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/trackB_20261104/all/logs/lane2_v2-%j.err
set -u
bash /gpfs1/scratch/sychan552/trackB_20261104/run_lane_v2.sh 2 3 all
