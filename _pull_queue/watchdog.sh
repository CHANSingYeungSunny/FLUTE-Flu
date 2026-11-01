#!/bin/bash -l
#SBATCH --job-name=mlflu_watchdog
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=2
#SBATCH --mem=2G
#SBATCH --time=5-00:00:00
#SBATCH --requeue
#SBATCH --output=queue/slurm-D-%j.out
#
# ============================================================================
# watchdog.sh -- the persistence layer. CPU only, cheap, outlives the GPUs.
#                It never does science; it only restarts vanished workers.
# ============================================================================
#
# WHY A WATCHER IS REQUIRED (measured)
# ------------------------------------
# `stingy` is `PreemptMode=CANCEL`: a higher-tier job kills a stingy job outright
# and Slurm does NOT requeue it (job 719030, 2026-11-01: PREEMPTED, exit 0:15,
# 13 min in). Nothing inside a killed process can save itself, and `stingy`
# allows only ONE job per user, so a dead stingy controller cannot be replaced
# from inside another stingy job. Only a job on a DIFFERENT partition can do it.
#
# WHAT IT DOES
# ------------
# Every QUEUE_WD_POLL seconds (300), for each lane (0 = stingy controller,
# 1 = gpu_a100 controller, cpu = the CPU probe worker):
#   * read every job id recorded in queue/runner_s<lane>.job (several are
#     allowed: a 4 h, a 6 h and a 12 h variant can all be queued at once);
#   * if ANY of them is alive (PENDING/RUNNING/REQUEUED/RESUBMITTED) -> nothing;
#   * else, if work remains and there is no queue/COMPLETE marker -> resubmit.
# Caps: QUEUE_WD_MAX_SUBMITS (default 30) submissions total and
# QUEUE_WD_MAX_SECONDS (default 172800 = 2 days) of lifetime. At the end of its
# life it requeues ITSELF (`scontrol requeue`), and if that fails it submits a
# fresh copy of itself -- so a long watch is not limited by one allocation.
set -uo pipefail

SELF=$(readlink -f "$0")
QDIR=${QUEUE_DIR:-$(dirname "${SELF}")}
CODE=$(dirname "${QDIR}")
QUEUE=${QDIR}/master_queue.tsv
EVENTS=${QDIR}/queue_events.log
COMPLETE=${QDIR}/COMPLETE
HALT=${QDIR}/HALT
CTRL=${QDIR}/master_controller.sh
CPUW=${QDIR}/cpu_worker.sh

MAX_SUBMITS=${QUEUE_WD_MAX_SUBMITS:-30}
MAX_SECONDS=${QUEUE_WD_MAX_SECONDS:-172800}
POLL=${QUEUE_WD_POLL:-300}
EXCLUDE_A100=${QUEUE_WD_EXCLUDE_A100:-gpu-a100-05,gpu-a100-09}

mkdir -p "${QDIR}"
GEN=$(( $(cat "${QDIR}/.wd_gen" 2>/dev/null || echo 0) + 1 ))
echo "${GEN}" > "${QDIR}/.wd_gen"
TAG="watchdog job=${SLURM_JOB_ID:-local} gen=${GEN}"

say() {
  local line
  line="[$(date '+%F %T')] ${TAG} $*"
  printf '%s\n' "${line}"
  printf '%s\n' "${line}" >> "${EVENTS}"
}

job_state() { sacct -j "$1" -n -X -o State 2>/dev/null | head -1 | tr -d ' '; }
job_alive() {
  case "$(job_state "$1")" in
    RUNNING|PENDING|RESIZING|COMPLETING|CONFIGURING|REQUEUED|RESUBMITTED|SUSPENDED) return 0 ;;
  esac
  return 1
}

submit_lane() {   # $1 = 0 | 1 | cpu
  local s=$1 out id script
  local -a extra=()
  case "${s}" in
    0)   extra=(--partition=stingy --gres=gpu:a100:1 --exclude=gpu-a100-05
                --cpus-per-task=8 --mem=48G --time=04:00:00
                --export=ALL,QUEUE_STRIPE=0,QUEUE_PARTITION=stingy,QUEUE_WALL_SECONDS=14400)
         script=${CTRL} ;;
    1)   extra=(--partition=gpu_a100 --gres=gpu:a100:1 --exclude="${EXCLUDE_A100}"
                --cpus-per-task=8 --mem=48G --time=12:00:00
                --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS=43200)
         script=${CTRL} ;;
    cpu) extra=(--partition=tiny --cpus-per-task=8 --mem=8G --time=5-00:00:00)
         script=${CPUW} ;;
    *)   return 1 ;;
  esac
  out=$(sbatch --parsable "${extra[@]}" --requeue "${script}" 2>&1)
  id=${out%%;*}
  if printf '%s' "${id}" | grep -qE '^[0-9]+$' && scontrol show job "${id}" > /dev/null 2>&1; then
    echo "${id}" >> "${QDIR}/runner_s${s}.job"
    say "SUBMITTED lane=${s} job=${id} (state=$(job_state "${id}"))"
    return 0
  fi
  say "submit lane=${s} FAILED: ${out}"
  return 1
}

count_submits() { cat "${QDIR}/.wd_submits" 2>/dev/null || echo 0; }
bump_submits() { echo $(( $(count_submits) + 1 )) > "${QDIR}/.wd_submits"; }

T0=$(date +%s)
say "START host=$(hostname) cap=${MAX_SUBMITS} submits / ${MAX_SECONDS}s lifetime, poll=${POLL}s"

while :; do
  if [ -f "${COMPLETE}" ]; then say "queue COMPLETE marker present - exiting"; exit 0; fi
  if [ -f "${HALT}" ]; then say "HALT present - exiting"; exit 0; fi

  todo=$(awk -F'\t' 'NR>1 && ($7=="TODO"||$7=="RUNNING"||$7=="BLOCKED_MISSING_WEIGHTS"){n++}END{print n+0}' "${QUEUE}")
  if [ "${todo}" -eq 0 ]; then
    say "no TODO/RUNNING/BLOCKED rows left - exiting"
    exit 0
  fi

  for s in 0 1 cpu; do
    any_alive=0
    for id in $(cat "${QDIR}/runner_s${s}.job" 2>/dev/null); do
      if job_alive "${id}"; then any_alive=1; fi
    done
    if [ "${any_alive}" = "1" ]; then
      continue
    fi
    if [ -f "${QDIR}/runner_s${s}.halted" ]; then
      say "lane ${s} halted deliberately - not restarting"; continue
    fi
    if [ "${s}" = "cpu" ] && [ -f "${QDIR}/runner_scpu.done" ]; then
      say "CPU worker stood down on purpose (all probes attempted) - not restarting"; continue
    fi
    rm -f "${QDIR}/runner_s${s}.done"
    if [ "$(count_submits)" -ge "${MAX_SUBMITS}" ]; then
      say "submit cap ${MAX_SUBMITS} reached - not resubmitting lane ${s}"
      continue
    fi
    say "lane ${s}: no live job - resubmitting (work remains: ${todo} rows)"
    if submit_lane "${s}"; then bump_submits; fi
  done

  el=$(( $(date +%s) - T0 ))
  if [ "${el}" -ge "${MAX_SECONDS}" ]; then
    say "lifetime ${el}s reached - continuing the watch with a fresh allocation"
    scontrol requeue "${SLURM_JOB_ID}" >> "${EVENTS}" 2>&1
    sleep 3
    st=$(job_state "${SLURM_JOB_ID}")
    case "${st}" in
      PENDING|REQUEUED|RESUBMITTED|RUNNING|CONFIGURING)
        say "WATCHDOG SELF-REQUEUE VERIFIED (job ${SLURM_JOB_ID} state=${st})"; exit 0 ;;
    esac
    say "self-requeue failed (state='${st:-gone}') - submitting a fresh watchdog copy"
    out=$(sbatch --parsable --partition=tiny --cpus-per-task=2 --mem=2G --time=5-00:00:00 \
                 --requeue --export=ALL "${SELF}" 2>&1)
    if printf '%s' "${out%%;*}" | grep -qE '^[0-9]+$'; then
      say "watchdog successor job ${out%%;*} registered"; exit 0
    fi
    say "!!!!!!!! WATCHDOG CANNOT CONTINUE: ${out}"; exit 1
  fi

  sleep "${POLL}"
done
