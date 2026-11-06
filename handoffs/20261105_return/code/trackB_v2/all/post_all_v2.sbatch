#!/bin/bash
#SBATCH --job-name=trackB_v2_post_all
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=1
#SBATCH --mem=2G
#SBATCH --time=5-00:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/trackB_20261104/all/logs/post_all_v2-%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/trackB_20261104/all/logs/post_all_v2-%j.err
set -u
bash /gpfs1/scratch/sychan552/trackB_20261104/post_all_v2.sh
