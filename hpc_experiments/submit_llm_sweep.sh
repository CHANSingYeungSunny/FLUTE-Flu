#!/bin/bash
# Login-node SUBMISSION controller only. No model compute here.
# Usage: bash hpc/submit_llm_sweep.sh qwen|deepseek
# Poll existing stingy jobs; submit a single job, wait for completion, then next.
set -euo pipefail
MIFLU_ROOT="${MIFLU_PROJECT_ROOT:-/home/sychan552/scratch/MLFLU/MIFlu_Continuation_20261030}"
MIFLU_ALIAS="${1:?qwen or deepseek}"
case "${MIFLU_ALIAS}" in qwen|deepseek) ;; *) exit 2;; esac
mkdir -p "${MIFLU_ROOT}/logs"
for MIFLU_L in 24 36 48 60; do
  for MIFLU_ARM in encoding_only generation_augmented; do
    if [[ -f "${MIFLU_ROOT}/runs/llm/${MIFLU_ALIAS}/L${MIFLU_L}/${MIFLU_ARM}/COMPLETE.json" ]]; then continue; fi
    while true; do
      if ! MIFLU_QUEUE="$(squeue -h -u sychan552 -p stingy -o '%i')"; then
        echo 'Queue query failed; refusing to guess availability.'; exit 3
      fi
      [[ -z "${MIFLU_QUEUE}" ]] && break
      sleep 30
    done
    MIFLU_JOB="$(sbatch --parsable --chdir="${MIFLU_ROOT}" "${MIFLU_ROOT}/hpc/submit_${MIFLU_ALIAS}.sh" "${MIFLU_L}" "${MIFLU_ARM}")"
    MIFLU_JOB="${MIFLU_JOB%%;*}"
    printf '%s\t%s\t%s\t%s\n' "${MIFLU_ALIAS}" "${MIFLU_L}" "${MIFLU_ARM}" "${MIFLU_JOB}" >> "${MIFLU_ROOT}/logs/llm_submissions.tsv"
    while true; do
      if ! MIFLU_QUEUE="$(squeue -h -j "${MIFLU_JOB}" -o '%i')"; then
        echo "Job query failed for ${MIFLU_JOB}; inspect it before resubmitting."; exit 3
      fi
      [[ -z "${MIFLU_QUEUE}" ]] && break
      sleep 30
    done
    sacct -j "${MIFLU_JOB}" -X --noheader --parsable2 -o JobID,State,ElapsedRaw,AllocTRES >> "${MIFLU_ROOT}/logs/llm_resource_ledger.psv"
    if [[ ! -f "${MIFLU_ROOT}/runs/llm/${MIFLU_ALIAS}/L${MIFLU_L}/${MIFLU_ARM}/COMPLETE.json" ]]; then
      echo "Incomplete job ${MIFLU_JOB}; inspect logs/pilot/resource demand before rerunning. No automatic parameter changes."
      exit 1
    fi
  done
done
"${LLM_PYTHON:-/home/sychan552/.conda/envs/mlflu_llm_20261030/bin/python}" \
  "${MIFLU_ROOT}/code/aggregate_llm.py" --runs "${MIFLU_ROOT}/runs/llm" --out "${MIFLU_ROOT}/paper_tables/llm_measured"
