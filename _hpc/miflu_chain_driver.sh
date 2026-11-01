#!/bin/bash -l
#SBATCH --job-name=miflu_chain
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=12:00:00
#SBATCH --output=slurm-miflu-chain-%j.out
#
# External chain driver for the MIFlu A100 export.
#
# WHY AN EXTERNAL DRIVER (measured 2026-11-01)
# -------------------------------------------
# `partition-stingy` has MaxSubmitJobsPerUser=1 and MaxJobsPerUser=1, so a
# RUNNING stingy job cannot submit its own successor: sbatch fails with
# `QOSMaxSubmitJobPerUserLimit` (verified 3x from job 719222 at 19:35:10-19:35:40).
# That is the structural reason a stingy job cannot self-requeue, and it is
# independent of the wall-clock guard. Controller 719030 additionally died by
# PREEMPTION (`PreemptMode=CANCEL`, `special_cs` landing on gpu-a100-04), which
# Slurm does not requeue either.
#
# This job runs on the CPU `tiny` partition (a different QOS, so it does not
# compete with the A100 slot) and simply keeps the chain alive:
#   * while a miflu_a100 job is RUNNING or PENDING -> sleep;
#   * if none is queued and fewer than 40 cells are verified -> sbatch the next
#     generation;
#   * stop when 40/40 are verified, on the HALT marker, or after MAX_SUBMITS.
# Every action is appended to miflu_a100_chain.log so the whole chain is one
# trace.
set -uo pipefail
module unload default 2>/dev/null
module load old_modules 2>/dev/null

CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
ADMIN="${CODE}/miflu_a100_chain.log"
MAX_SUBMITS=${MIFLU_MAX_SUBMITS:-14}
MAX_SECONDS=${MIFLU_MAX_SECONDS:-42000}
cd "${CODE}" || exit 1

say() { echo "[$(date '+%F %T')] chain job=${SLURM_JOB_ID:-?} $*" | tee -a "${ADMIN}"; }
say "CHAIN DRIVER START host=$(hostname) max_submits=${MAX_SUBMITS}"

n=0
t0=$(date +%s)
while :; do
  now=$(date +%s)
  if [ $((now - t0)) -gt "${MAX_SECONDS}" ]; then say "chain time cap reached"; exit 0; fi
  if [ -f "${OUT}/.MIFLU_HALT" ]; then say "HALT marker present - stopping chain"; exit 0; fi

  nver=$("${PY}" miflu_controller_v2.py --count 2>/dev/null | tail -1)
  if [ "${nver:-0}" -ge 40 ]; then
    say "ALL 40 CELLS VERIFIED - chain complete (${nver}/40)"
    exit 0
  fi

  q=$(squeue -u "${USER}" -h -o '%j %T' 2>/dev/null | awk '$1=="miflu_a100"{print $1" "$2}')
  if [ -n "${q}" ]; then
    say "waiting: miflu_a100 ${q} (verified ${nver}/40)"
    sleep 60
    continue
  fi

  if [ "${n}" -ge "${MAX_SUBMITS}" ]; then
    say "MAX_SUBMITS=${MAX_SUBMITS} reached with ${nver}/40 verified - stopping"
    exit 0
  fi

  out=$(sbatch --chdir="${CODE}" "${CODE}/miflu_a100_controller_v2.sh" 2>&1)
  n=$((n + 1))
  sid=$(printf '%s\n' "${out}" | sed -n 's/^Submitted batch job \([0-9][0-9]*\).*/\1/p')
  if [ -n "${sid}" ]; then
    say "submitted generation #${n}: job_id=${sid} (verified ${nver}/40)"
  else
    say "submission #${n} FAILED: ${out}"
    sleep 120
  fi
  sleep 45
done
