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
# watchdog.sh (queue v2) -- the persistence layer. CPU only, cheap, outlives the
#                           GPUs. It never does science; it only restarts a lane
#                           that has VANISHED.
# ============================================================================
#
# WHY A WATCHER IS REQUIRED (measured)
# ------------------------------------
# `stingy` is `PreemptMode=CANCEL`: a higher-tier job kills a stingy job outright
# and Slurm does NOT requeue it (job 719030, 2026-11-01: PREEMPTED, exit 0:15).
# Nothing inside a killed process can save itself, and `stingy` allows only ONE
# job per user, so a dead stingy controller cannot be replaced from inside
# another stingy job. Only a job on a DIFFERENT partition can do it.
#
# THE SCHEDULING RULE THIS ENCODES
# --------------------------------
# * a job that is PENDING with a far-away StartTime is NOT a problem: pending
#   costs nothing, so the watchdog leaves it alone and only intervenes when a
#   recorded job has DISAPPEARED (no live state at all);
# * a lane that stood down on purpose (`runner_s<lane>.idle` says 0 undone tasks,
#   or `.halted`, or `.done`) is never resurrected -- otherwise a finished lane
#   would be resubmitted forever and burn the queue;
# * a preempted controller leaves RUNNING rows behind; the controller itself
#   resets them to TODO on start-up (attempts preserved, +1 if the job was really
#   CANCELLED/PREEMPTED). The watchdog only needs to get a controller running again.
#
# CAPS: 30 submissions, 5 days of lifetime. On exhaustion it writes CHAIN_DEAD and
# exits -- a watchdog that keeps resubmitting into a full queue is not help.
set -uo pipefail

SELF=$(readlink -f "$0" 2>/dev/null || echo "$0")
QDIR=${QUEUE_DIR:-$(dirname "${SELF}")}
# `sbatch` spools this script to /var/spool/slurmd/job<N>/slurm_script, so $0 is
# the SPOOL path: fall back to the real queue dir when the derived one is empty.
[ -f "${QDIR}/master_queue.tsv" ] || QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
CODE=$(dirname "${QDIR}")
QUEUE=${QDIR}/master_queue.tsv
EVENTS=${QDIR}/queue_events.log
COMPLETE=${QDIR}/COMPLETE
HALT=${QDIR}/HALT
CTRL=${QDIR}/master_controller.sh
CPUW=${QDIR}/cpu_worker.sh
EXCLFILE=${QDIR}/exclude_nodes.txt
#: PART TWO: when the P0 lane finishes and frees the single `stingy` slot, ONE
#: successor lane must already be alive to claim it (`stingy` is
#: MaxSubmitJobsPerUser=1, so nothing else can). The gate and the O_EXCL sentinel
#: live in successor_lib.sh, shared with the dedicated `successor_watch.sh` job,
#: so the successor can only ever be submitted once however many watchers run.
# shellcheck source=/dev/null
. "${QDIR}/successor_lib.sh"

MAX_SUBMITS=${QUEUE_WD_MAX_SUBMITS:-30}
MAX_SECONDS=${QUEUE_WD_MAX_SECONDS:-432000}
POLL=${QUEUE_WD_POLL:-300}
EXCLUDE_A100=${QUEUE_WD_EXCLUDE_A100:-gpu-a100-05,gpu-a100-09}
WALL_A=${QUEUE_WD_WALL_A:-12:00:00};   SECS_A=${QUEUE_WD_SECS_A:-43200}
WALL_B=${QUEUE_WD_WALL_B:-12:00:00};   SECS_B=${QUEUE_WD_SECS_B:-43200}
WALL_C=${QUEUE_WD_WALL_C:-5-00:00:00}; SECS_C=${QUEUE_WD_SECS_C:-432000}

mkdir -p "${QDIR}" "${QDIR}/locks"
GEN=$(( $(cat "${QDIR}/.wd_gen" 2>/dev/null || echo 0) + 1 ))
echo "${GEN}" > "${QDIR}/.wd_gen"
TAG="watchdog job=${SLURM_JOB_ID:-local} gen=${GEN}"

say() {
  local line
  line="[$(date '+%F %T')] ${TAG} $*"
  printf '%s\n' "${line}"
  printf '%s\n' "${line}" >> "${EVENTS}"
}
chain_dead() { printf '%s %s\n' "$(date '+%F %T')" "$1" > "${QDIR}/CHAIN_DEAD"; say "CHAIN_DEAD ($1)"; }

job_state() { sacct -j "$1" -n -X -o State 2>/dev/null | head -1 | tr -d ' '; }
job_alive() {
  case "$(job_state "$1")" in
    RUNNING|PENDING|RESIZING|COMPLETING|CONFIGURING|REQUEUED|RESUBMITTED|SUSPENDED) return 0 ;;
  esac
  return 1
}
exclude_list() {
  local base="${EXCLUDE_A100}" extra=""
  [ -f "${EXCLFILE}" ] && extra=$(tr '\n' ',' < "${EXCLFILE}" | sed 's/,,*/,/g; s/^,//; s/,$//')
  if [ -n "${extra}" ]; then
    printf '%s,%s\n' "${base}" "${extra}" | tr ',' '\n' | sed '/^$/d' | sort -u | paste -sd, -
  else
    printf '%s\n' "${base}"
  fi
}

submit_lane() {   # $1 = 0 | 1 | cpu
  local s=$1 out id script
  local -a extra=()
  case "${s}" in
    0)   extra=(--partition=stingy --gres=gpu:a100:1 --exclude=gpu-a100-05
                --cpus-per-task=8 --mem=48G --time="${WALL_B}"
                --export="ALL,QUEUE_STRIPE=0,QUEUE_PARTITION=stingy,QUEUE_WALL_SECONDS=${SECS_B}")
         script=${CTRL} ;;
    1)   extra=(--partition=gpu_a100 --gres=gpu:a100:1 --exclude="$(exclude_list)"
                --cpus-per-task=8 --mem=48G --time="${WALL_A}"
                --export="ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS=${SECS_A}")
         script=${CTRL} ;;
    cpu) extra=(--partition=tiny --cpus-per-task=8 --mem=8G --time="${WALL_C}")
         script=${CPUW} ;;
    w)   script=${WRITER} ;;   # the SINGLE result-writer lane (F1-F5 only)
    *)   return 1 ;;
  esac
  out=$(sbatch --parsable "${extra[@]}" --requeue "${script}" 2>&1)
  id=${out%%;*}
  if printf '%s' "${id}" | grep -qE '^[0-9]+$' && scontrol show job "${id}" > /dev/null 2>&1; then
    printf '%s\n' "${id}" >> "${QDIR}/runner_s${s}.job"
    say "SUBMITTED lane=${s} job=${id} (state=$(job_state "${id}"))"
    return 0
  fi
  say "submit lane=${s} FAILED: ${out}"
  return 1
}

count_submits() { cat "${QDIR}/.wd_submits" 2>/dev/null || echo 0; }
bump_submits() { echo $(( $(count_submits) + 1 )) > "${QDIR}/.wd_submits"; }

lane_idle_on_purpose() {   # $1 = lane ; 0 = deliberately stood down
  local s=$1 f="${QDIR}/runner_s$1.idle" n
  [ -f "${QDIR}/runner_s$1.halted" ] && return 0
  if [ "${s}" = "cpu" ] && [ -f "${QDIR}/runner_scpu.done" ]; then return 0; fi
  if [ -f "${f}" ]; then
    n=$(awk '{print $1}' "${f}" 2>/dev/null)
    [ "${n:-1}" = "0" ] && return 0
  fi
  return 1
}

T0=$(date +%s)
say "START host=$(hostname) cap=${MAX_SUBMITS} submits / ${MAX_SECONDS}s lifetime, poll=${POLL}s exclude=$(exclude_list)"

while :; do
  if [ -f "${COMPLETE}" ]; then say "queue COMPLETE marker present - exiting"; exit 0; fi
  if [ -f "${HALT}" ]; then say "HALT present - exiting (the controller finalises)" ; exit 0; fi

  todo=$(awk -F'\t' 'NR>1 && ($8=="TODO"||$8=="RUNNING"||$8=="BLOCKED_MISSING_WEIGHTS"){n++}END{print n+0}' "${QUEUE}")
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
    if lane_idle_on_purpose "${s}"; then
      say "lane ${s} stood down on purpose - not restarting"
      continue
    fi
    if [ "$(count_submits)" -ge "${MAX_SUBMITS}" ]; then
      say "submit cap ${MAX_SUBMITS} reached - NOT resubmitting lane ${s}"
      chain_dead "watchdog submit cap ${MAX_SUBMITS} reached with ${todo} row(s) still pending"
      exit 1
    fi
    say "lane ${s}: no live job (disappeared or preempted) - resubmitting; work remains=${todo}"
    if submit_lane "${s}"; then bump_submits; fi
  done

  # ---- PART TWO: reuse the freed `stingy` slot, exactly once ---------------
  if succ_out=$(successor_evaluate 2>&1); then
    say "SUCCESSOR: ${succ_out}"
  fi

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
    say "!!!!!!!! WATCHDOG CANNOT CONTINUE: ${out}"
    chain_dead "watchdog could not continue itself"
    exit 1
  fi

  sleep "${POLL}"
done
