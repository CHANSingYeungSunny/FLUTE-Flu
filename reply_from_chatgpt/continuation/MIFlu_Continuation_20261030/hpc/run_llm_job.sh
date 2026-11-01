#!/bin/bash
# Shared compute-node entry; submit through a model-specific sbatch wrapper.
set -euo pipefail
module unload default
module load old_modules
MIFLU_ROOT="${MIFLU_PROJECT_ROOT:-/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030}"
MIFLU_MODEL="${1:?qwen or deepseek}"; MIFLU_L="${2:?24/36/48/60}"; MIFLU_MODE="${3:?encoding_only or generation_augmented}"
MIFLU_PYTHON="${LLM_PYTHON:-/home/sychan552/.conda/envs/mlflu_llm_20261030/bin/python}"
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
unset TRANSFORMERS_CACHE
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=4 MKL_NUM_THREADS=4
MIFLU_ASSET="${MIFLU_ROOT}/assets/${MIFLU_MODEL}.json"
MIFLU_SNAPSHOT="$("${MIFLU_PYTHON}" -c 'import json,sys; print(json.load(open(sys.argv[1]))["snapshot_path"])' "${MIFLU_ASSET}")"
MIFLU_OUT="${MIFLU_ROOT}/runs/llm/${MIFLU_MODEL}/L${MIFLU_L}/${MIFLU_MODE}"
mkdir -p "${MIFLU_OUT}" "${MIFLU_ROOT}/logs"
exec > >(tee -a "${MIFLU_ROOT}/logs/${MIFLU_MODEL}_L${MIFLU_L}_${MIFLU_MODE}_${SLURM_JOB_ID:?}.log") 2>&1
"${MIFLU_PYTHON}" "${MIFLU_ROOT}/code/hpc_preflight.py" --root "${MIFLU_ROOT}" --kind llm --out "${MIFLU_OUT}/preflight_${SLURM_JOB_ID}.json"
MIFLU_PILOT_ARGS=()
if [[ "${LLM_PILOT_WINDOWS:-0}" != 0 ]]; then MIFLU_PILOT_ARGS=(--pilot-windows "${LLM_PILOT_WINDOWS}"); fi
"${MIFLU_PYTHON}" -u "${MIFLU_ROOT}/code/run_llm_features.py" \
  --registry "${MIFLU_ROOT}/protocol/llm_registry.json" --handoff "${MIFLU_ROOT}/inputs/handoff" \
  --model "${MIFLU_MODEL}" --horizon "${MIFLU_L}" --mode "${MIFLU_MODE}" \
  --snapshot "${MIFLU_SNAPSHOT}" --out "${MIFLU_OUT}" --device cuda "${MIFLU_PILOT_ARGS[@]}"
