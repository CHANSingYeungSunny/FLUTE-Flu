#!/bin/bash
# ===========================================================================
# run_f1_sequential.sh -- A2-F CORE FAIR-BENCHMARK PILOT launcher
#                         AUTHORIZED: 0.60 GPU-hours, independent of the
#                         closed 2.3 round (remainder NOT carried over).
# ===========================================================================
# Enforces, in this order:
#   1. stingy MaxSubmit=1 / MaxJobsPU=1 -> one job at a time, no arrays >1 element
#   2. the 0.60 GPU-h hard cap -> checked from `sacct` BEFORE every submission
#   3. the 0.05639 remainder of the previous round is NEVER added to the cap
#
# Budget rule: before submitting GPU element i, sum the GPU-hours actually
# charged to F1 jobs so far, add the projected cost of this element, and if the
# total would exceed F1_CAP_GPU_H, STOP and report.
#
# This script submits nothing on its own; it is the launcher used once the final
# execution gate has passed.
#
# USAGE: bash run_f1_sequential.sh <official_repo_reproduction_root>
set -uo pipefail

ROOT=${1:?usage: run_f1_sequential.sh <official_repo_reproduction_root>}
F1PRE="${ROOT}/f1_preflight_20261006"
F1="${ROOT}/f1"

F1_CAP_GPU_H=0.60            # the NEW, independent authorization
GPU_FIT_COST_H=0.0533        # measured per MIFlu fit (192 s incl. startup)
MAX_ELAPSED_STOP_S=288       # 1.5x expected -> stop rule

mkdir -p "${F1}/logs" "${F1}/manifests"
LEDGER="${F1}/manifests/SUBMISSION_LOG.tsv"

# ---- GPU-hours actually charged to F1 so far (from sacct, not from a file) --
f1_gpu_hours_used () {
  local ids_hours
  # collect this session's F1 job ids from the launch ledger
  [ -f "${LEDGER}" ] || { echo "0"; return; }
  local total=0
  while IFS=$'\t' read -r ts label jid; do
    [ -z "${jid:-}" ] && continue
    case "${jid}" in ''|*[!0-9]*) continue;; esac
    local el gpus h
    el=$(sacct -j "${jid}" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
    gpus=$(sacct -j "${jid}" -X --noheader -o AllocTRES 2>/dev/null | grep -o 'gres/gpu:[a-z0-9]*=[0-9]*' | head -1 | cut -d= -f2)
    [ -z "${gpus:-}" ] && gpus=$(sacct -j "${jid}" -X --noheader -o AllocTRES 2>/dev/null | grep -c 'gres/gpu=' )
    [ -z "${gpus:-}" ] && gpus=0
    if [[ "${el}" =~ ^([0-9]+)-([0-9]+):([0-9]+):([0-9]+)$ ]]; then
      h=$(echo "scale=6; ($((10#${BASH_REMATCH[1]}))*86400 + $((10#${BASH_REMATCH[2]}))*3600 + $((10#${BASH_REMATCH[3]}))*60 + $((10#${BASH_REMATCH[4]})))/3600*${gpus}" | bc)
    elif [[ "${el}" =~ ^([0-9]+):([0-9]+):([0-9]+)$ ]]; then
      h=$(echo "scale=6; ($((10#${BASH_REMATCH[1]}))*3600 + $((10#${BASH_REMATCH[2]}))*60 + $((10#${BASH_REMATCH[3]})))/3600*${gpus}" | bc)
    else
      h=0
    fi
    total=$(echo "scale=6; ${total} + ${h}" | bc)
  done < "${LEDGER}"
  echo "${total}"
}

budget_allows () {
  local used projected
  used=$(f1_gpu_hours_used)
  projected=$(echo "scale=6; ${used} + ${GPU_FIT_COST_H}" | bc)
  echo "[budget] F1 used so far = ${used} GPU-h ; this element projects ${projected} GPU-h ; cap = ${F1_CAP_GPU_H}"
  if (( $(echo "${projected} > ${F1_CAP_GPU_H}" | bc -l) )); then
    echo "[budget] STOP - projected total would exceed the 0.60 GPU-h authorization."
    return 1
  fi
  return 0
}

submit_and_wait () {
  local label="$1"; shift
  local jid
  jid=$(sbatch --parsable "$@") || { echo "[seq] SUBMIT FAILED: ${label}"; return 1; }
  echo "[seq] ${label}: job ${jid} submitted"
  printf '%s\t%s\t%s\n' "$(date -u +%FT%TZ)" "${label}" "${jid}" >> "${LEDGER}"
  while true; do
    local st
    st=$(sacct -j "${jid}" -X --noheader -o State 2>/dev/null | head -1 | tr -d ' ')
    case "${st}" in
      COMPLETED) echo "[seq] ${label}: COMPLETED"; return 0;;
      FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL)
        echo "[seq] ${label}: ${st} -> F1_FAILURE_AND_RETRY_POLICY.md (do NOT silently retry)"; return 2;;
      "") sleep 15;;
      *)  sleep 20;;
    esac
  done
}

echo "=== A2-F Core Fair-Benchmark Pilot (one seed) ==="
echo "root=${ROOT}"
echo "authorized F1 cap = ${F1_CAP_GPU_H} GPU-h (previous round remainder NOT carried over)"
echo

echo "--- Phase 1: CPU validation (scorer + contract checks, Last Value, Seasonal Naive, NLinear, DLinear) ---"
submit_and_wait "phase1_cpu_validation" "${F1PRE}/scripts/f1_cpu_phase1.sbatch"   || echo "[seq] Phase 1 reported a failure - inspect before spending GPU time"

echo
echo "--- Phase 2: GPU arms (corrected MIFlu first: the primary arm) ---"
for i in 0 1 2 3 4 5 6 7; do
  if ! budget_allows; then
    echo "[seq] halting the GPU wave on budget grounds"; break
  fi
  submit_and_wait "gpu_index_${i}" --array="${i}-${i}" "${F1PRE}/scripts/f1_gpu_fit.sbatch"     || echo "[seq] continuing after non-zero outcome at index ${i}"
done

echo
echo "--- Phase 3: Test evaluation, prediction dump, independent scoring, text-path probe ---"
submit_and_wait "phase3_evaluation" "${F1PRE}/scripts/f1_cpu_phase3.sbatch"   || echo "[seq] Phase 3 failed - see the log"

echo
echo "=== launcher finished $(date -u +%FT%TZ) ==="
echo "[seq] F1 GPU-hours used = $(f1_gpu_hours_used) of ${F1_CAP_GPU_H}"
echo "[seq] gate report: ${F1}/scoring/f1_gate_report.json"