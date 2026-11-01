#!/bin/bash -l
# Explicit one-time setup on an approved software-install/staging node.
# Does not alter mlflu_hpc or install into its site-packages.
set -euo pipefail
module unload default
module load old_modules
MIFLU_ENV=/home/sychan552/.conda/envs/mlflu_llm_20261030
if [[ ! -x "${MIFLU_ENV}/bin/python" ]]; then
  conda create -y -p "${MIFLU_ENV}" python=3.10
fi
"${MIFLU_ENV}/bin/python" -m pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cu121
"${MIFLU_ENV}/bin/python" -m pip install \
  transformers==4.46.3 tokenizers==0.20.3 huggingface-hub==0.36.2 accelerate==1.1.1 \
  safetensors==0.4.5 sentencepiece==0.2.0 einops==0.8.0 \
  numpy==1.26.4 pandas==2.2.3 scipy==1.13.1 scikit-learn==1.6.1
"${MIFLU_ENV}/bin/python" -m pip freeze
