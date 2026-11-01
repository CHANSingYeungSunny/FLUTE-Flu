#!/bin/bash
# Run on a network-enabled staging node after setup_llm_env.sh, not inside an offline GPU job.
set -euo pipefail
MIFLU_ROOT="${MIFLU_PROJECT_ROOT:-/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030}"
MIFLU_PYTHON="${LLM_PYTHON:-/home/sychan552/.conda/envs/mlflu_llm_20261030/bin/python}"
MIFLU_ALIAS="${1:?qwen or deepseek}"
"${MIFLU_PYTHON}" "${MIFLU_ROOT}/code/download_model_weights.py" \
  --registry "${MIFLU_ROOT}/protocol/llm_registry.json" --model "${MIFLU_ALIAS}" \
  --cache-dir /gpfs1/scratch/sychan552/CHATTIME/.cache/hub \
  --out "${MIFLU_ROOT}/assets/${MIFLU_ALIAS}.json"
