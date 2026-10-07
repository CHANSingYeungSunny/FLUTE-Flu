#!/bin/bash
#SBATCH --job-name=probe_text_cmp
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=00:10:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/probe_cmp_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/probe_cmp_%j.err
#
# Pure JSON comparison of the CPU and GPU probe outputs. No model, no GPU.
set -uo pipefail
H=/gpfs1/home/sychan552/official_repo_reproduction_20261006
mkdir -p "${H}/probe"
python3 "${H}/slurm/probe_text_path_compare.py" --out "${H}/probe"
