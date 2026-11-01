#!/bin/bash -l
#SBATCH --job-name=miflu_qwen
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-%x-%j.out
set -euo pipefail
MIFLU_ROOT="${MIFLU_PROJECT_ROOT:-/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030}"
exec bash -l "${MIFLU_ROOT}/hpc/run_llm_job.sh" qwen "${1:?horizon}" "${2:?mode}"
