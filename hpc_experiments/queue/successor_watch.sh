#!/bin/bash -l
#SBATCH --job-name=mlflu_successor_watch
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=12:00:00
#SBATCH --requeue
#SBATCH --output=queue/slurm-SW-%j.out
#
# successor_watch.sh -- the part-two slot re-user. Cheap CPU job, no GPU, no
# science: every QUEUE_SUCC_POLL seconds (default 120) it evaluates the successor
# gate and, the first time the gate says `ready`, submits ONE successor lane into
# the freed `stingy` slot. It then exits.
#
# Why a separate job rather than a new generation of watchdog: the RUNNING
# watchdog `720004` was spooled by `sbatch` at 22:56, so it executes the code of
# that moment and can never learn new logic. `watchdog.sh` itself now also carries
# this same gate (via `successor_lib.sh`) so any FUTURE watchdog keeps the
# behaviour, and both paths are protected by the same O_EXCL sentinel, so the
# successor can still only ever be submitted once.
#
# Every refusal is written to `queue/successor.log` with its reason
# (`p0-active:720083:PENDING`, `stingy-busy:<id>:RUNNING`, `past-cutoff:0700`,
# `runway-too-short:...`, `already-fired`) so the morning report can say why it
# did or did not fire.
set -uo pipefail
SELF=$(readlink -f "$0" 2>/dev/null || echo "$0")
QDIR=${QUEUE_DIR:-$(dirname "${SELF}")}
# `sbatch` spools the script to /var/spool/slurmd/job<N>/slurm_script, so $0 is the
# SPOOL path and successor_lib.sh is not beside it. This exact failure was measured
# (job 720102: "successor_lib.sh: No such file or directory"), hence the fallback.
[ -f "${QDIR}/master_queue.tsv" ] || QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
. "${QDIR}/successor_lib.sh"

POLL=${QUEUE_SUCC_POLL:-120}
say() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "${SUCC_LOG}"; }

say "SUCCESSOR-WATCH START job=${SLURM_JOB_ID:-local} pid=$$ poll=${POLL}s cutoff=${SUCC_CUTOFF} runway>=${SUCC_MIN_RUNWAY}s p0=$(head -1 "${P0_LANE_FILE}" 2>/dev/null)"
last=""
while :; do
  if [ -f "${QDIR}/HALT" ]; then say "HALT present - stopping without firing"; exit 0; fi
  # a successor already exists: nothing left to do
  if [ -f "${SUCC_SENTINEL}" ]; then
    say "sentinel present ($(head -1 "${SUCC_SENTINEL}" 2>/dev/null)) - exiting"
    exit 0
  fi
  if out=$(successor_evaluate); then
    say "OK ${out}"
    exit 0
  fi
  # log a change of reason only, so a 7-hour poll does not write megabytes
  case "${out}" in
    *"past-cutoff"*) say "STOP ${out} - the night is over, no successor"; exit 0 ;;
  esac
  [ "${out}" != "${last}" ] && { say "${out}"; last="${out}"; }
  sleep "${POLL}"
done
