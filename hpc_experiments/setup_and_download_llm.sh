#!/bin/bash -l
# One-time LLM environment setup + weight staging for the MIFlu innovation benchmark.
# Runs on a CPU staging node (no GPU needed for env build / weight download).
#SBATCH --job-name=miflu_llm_setup
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-llm-setup-%j.out

set -euo pipefail
module unload default
module load old_modules

MIFLU_ROOT=/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030
MIFLU_ENV=/home/sychan552/.conda/envs/mlflu_llm_20261030
mkdir -p "${MIFLU_ROOT}/protocol" "${MIFLU_ROOT}/assets" "${MIFLU_ROOT}/logs"

echo "[setup] env=${MIFLU_ENV}"
if [[ ! -x "${MIFLU_ENV}/bin/python" ]]; then
  conda create -y -p "${MIFLU_ENV}" python=3.10
fi

echo "[install] torch + transformers"
"${MIFLU_ENV}/bin/python" -m pip install --quiet torch==2.3.1 --index-url https://download.pytorch.org/whl/cu121
"${MIFLU_ENV}/bin/python" -m pip install --quiet \
  transformers==4.46.3 tokenizers==0.20.3 huggingface-hub==0.36.2 accelerate==1.1.1 \
  safetensors==0.4.5 sentencepiece==0.2.0 einops==0.8.0 \
  numpy==1.26.4 pandas==2.2.3 scipy==1.13.1 scikit-learn==1.6.1

echo "[download] weights"
for ALIAS in qwen deepseek; do
  echo "  -> ${ALIAS}"
  "${MIFLU_ENV}/bin/python" "${MIFLU_ROOT}/code/download_model_weights.py" \
    --registry "${MIFLU_ROOT}/protocol/llm_registry.json" \
    --model "${ALIAS}" \
    --cache-dir /gpfs1/scratch/sychan552/CHATTIME/.cache/hub \
    --out "${MIFLU_ROOT}/assets/${ALIAS}.json" || echo "  [warn] ${ALIAS} download failed"
done

echo "[done] LLM setup complete"
ls -la "${MIFLU_ROOT}/assets/"
