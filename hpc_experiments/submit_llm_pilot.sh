#!/bin/bash -l
#SBATCH --job-name=miflu_llm_pilot
#SBATCH --partition=gpu_a100
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --output=slurm-llm-pilot-%j.out

# Pilot run: Qwen L=24, encoding_only, few windows — verifies the LLM arm works
# before committing to the full 48-cell sweep.
#
# Key fix: run_llm_job.sh defaults to a NON-EXISTENT env (mlflu_llm_20261030).
# We point LLM_PYTHON at mlflu_hpc, which already has torch 2.5.1 + transformers.
set -euo pipefail
module unload default
module load old_modules

export MIFLU_PROJECT_ROOT=/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030
export LLM_PYTHON=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export LLM_PILOT_WINDOWS=8

echo "[pilot] python=${LLM_PYTHON}"
"${LLM_PYTHON}" -c "import torch, transformers; print('torch', torch.__version__, '| tf', transformers.__version__)"

bash -l "${MIFLU_PROJECT_ROOT}/hpc/run_llm_job.sh" qwen 24 encoding_only
echo "[pilot] DONE"
