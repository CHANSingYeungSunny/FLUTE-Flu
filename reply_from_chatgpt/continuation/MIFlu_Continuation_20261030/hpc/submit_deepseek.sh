#!/bin/bash -l
#SBATCH --job-name=miflu_deepseek
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=slurm-%x-%j.out
set -euo pipefail
MIFLU_ROOT="${MIFLU_PROJECT_ROOT:-/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030}"
exec bash -l "${MIFLU_ROOT}/hpc/run_llm_job.sh" deepseek "${1:?horizon}" "${2:?mode}"
