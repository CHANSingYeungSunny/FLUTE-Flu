#!/bin/bash
# TRACK S batch driver (v3).
#
# Two scheduler quirks had to be worked around:
#
#  1. `squeue --noheader` prints "Last update in N seconds ago" on stdout even
#     when the queue is empty, so `grep -q .` is ALWAYS true and a plain
#     wait-loop never exits. Count numeric job ids instead.
#  2. partition-stingy sets MaxJobsPU=1 / MaxSubmitJobsPU=1. The submit limit is
#     also enforced while a job is in the COMPLETING state, which squeue does
#     not show as running -- so submissions fail intermittently. Retry.
#
# Only `squeue` and `sbatch` run on the login node. No computation runs here.
#
# Array index -> horizon: 0=L24 1=L36 2=L48 3=L60
# Plan: patience 5, seeds 42/43/44  ->  12 fits

ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
VER=${ROOT}/r1_v2_verification_20261007
OUT=${ROOT}/s1_earlystop_20261008
LOG=${OUT}/logs/batch_driver.log
mkdir -p "${OUT}/logs"

# squeue right-pads the job id column ("          610793_0"), so '^[0-9]' never
# matches and the count is always 0. Allow leading whitespace.
n_queued() {
  squeue -u sychan552 --noheader -o '%i' 2>/dev/null \
    | grep -cE '^[[:space:]]*[0-9]'
}

wait_idle() {
  while [ "$(n_queued)" -gt 0 ]; do
    sleep 30
  done
}

submit_one() {
  # $1 = array index, $2 = seed, $3 = patience
  local idx=$1 seed=$2 pat=$3 tries=0
  cd "${VER}" || exit 2
  while [ $tries -lt 40 ]; do
    if sbatch --array="${idx}-${idx}" --export=ALL,SEED="${seed}",PAT="${pat}" \
              s1_earlystop.sbatch >> "${LOG}" 2>&1; then
      return 0
    fi
    tries=$((tries + 1))
    echo "$(date -u +%FT%TZ)   retry ${tries} (idx=${idx} seed=${seed})" >> "${LOG}"
    sleep 30
  done
  echo "$(date -u +%FT%TZ)   GAVE UP idx=${idx} seed=${seed}" >> "${LOG}"
  return 1
}

echo "$(date -u +%FT%TZ) driver v3 start" >> "${LOG}"

for seed in 42 43 44; do
  for idx in 0 1 2 3; do
    wait_idle
    echo "$(date -u +%FT%TZ) submitting idx=${idx} seed=${seed} patience=5" >> "${LOG}"
    submit_one "${idx}" "${seed}" 5
    sleep 10
  done
done

echo "$(date -u +%FT%TZ) driver finished" >> "${LOG}"
