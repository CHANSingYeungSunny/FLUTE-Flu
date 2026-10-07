#!/bin/bash
# R1-C remaining-batch driver (revised).
#
# partition-stingy QOS is MaxJobsPU=1 / MaxSubmitJobsPU=1. An --array=0-3
# submission is therefore fragmented: Slurm accepts tasks only as slots free, so
# a "failed" submission may still have placed some tasks. This driver submits the
# REMAINING work explicitly and re-checks the skip guard in r1c_run.sbatch, which
# makes re-submission idempotent (completed cells print "complete - skip").
#
# Only `squeue` and `sbatch` run on the login node. All model fitting runs on
# compute nodes via Slurm. No computation is performed by this driver.
#
# Array index -> horizon: 0=L24 1=L36 2=L48 3=L60
#
# Already complete: C0 seed1000 (all L), C1 seed1000 (all L),
#                   C0 seed1001 L24 (610657_0), C0 seed1001 L36 (610665_1).

ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
VER=${ROOT}/r1_v2_verification_20261007
OUT=${ROOT}/r1c_bounded_20261007
LOG=${OUT}/logs/batch_driver.log

wait_idle() {
  while squeue -u sychan552 --noheader 2>/dev/null | grep -q .; do
    sleep 30
  done
}

submit() {
  local range=$1 seed=$2 arm=$3
  cd "${VER}" || exit 2
  sbatch --array="${range}" --export=ALL,SEED="${seed}",ARM="${arm}" r1c_run.sbatch >> "${LOG}" 2>&1
  sleep 5
}

echo "$(date -u +%FT%TZ) driver (revised) start" >> "${LOG}"

# step: array-range seed arm
for cfg in "2-3:1001:C0" "0-3:1002:C0" "0-3:1001:C1" "0-3:1002:C1"; do
  range=${cfg%%:*}
  rest=${cfg#*:}
  seed=${rest%%:*}
  arm=${rest##*:}
  wait_idle
  echo "$(date -u +%FT%TZ) submitting array=${range} seed=${seed} arm=${arm}" >> "${LOG}"
  submit "${range}" "${seed}" "${arm}"
done

echo "$(date -u +%FT%TZ) driver finished" >> "${LOG}"
