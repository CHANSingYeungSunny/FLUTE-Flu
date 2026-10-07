#!/bin/bash
#SBATCH --job-name=s5_verify
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=8G
#SBATCH --time=00:05:00
#SBATCH --output=results/stage5/logs/verify_%j.out
#SBATCH --error=results/stage5/logs/verify_%j.err
set -eo pipefail
cd /scratch/sychan552/a2_stage5
export PYTHONPATH=/scratch/sychan552/a2_stage5/scripts
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
mkdir -p results/stage5/logs
/home/sychan552/.conda/envs/mlflu_hpc/bin/python recovery/stage5/verify_imports.py
