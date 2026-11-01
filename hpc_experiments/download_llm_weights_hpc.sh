#!/bin/bash -l
# Stage Qwen / DeepSeek weights for the MIFlu innovation benchmark.
# Reuses the EXISTING mlflu_hpc env (already has torch 2.5.1 + transformers 4.57.6),
# so no new conda env is needed. Runs on a CPU staging node.
#SBATCH --job-name=miflu_llm_dl
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-llm-dl-%j.out

set -euo pipefail
module unload default
module load old_modules

MIFLU_ROOT=/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030
MIFLU_PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
mkdir -p "${MIFLU_ROOT}/assets" "${MIFLU_ROOT}/logs"

echo "[env] reusing mlflu_hpc"
"${MIFLU_PY}" -c "import torch, transformers; print('torch', torch.__version__, '| transformers', transformers.__version__)"

for ALIAS in qwen deepseek; do
  echo "[download] ${ALIAS}"
  "${MIFLU_PY}" "${MIFLU_ROOT}/code/download_model_weights.py" \
    --registry "${MIFLU_ROOT}/protocol/llm_registry.json" \
    --model "${ALIAS}" \
    --cache-dir /gpfs1/scratch/sychan552/CHATTIME/.cache/hub \
    --out "${MIFLU_ROOT}/assets/${ALIAS}.json" || echo "  [warn] ${ALIAS} failed"
done

echo "[done]"
ls -la "${MIFLU_ROOT}/assets/"
