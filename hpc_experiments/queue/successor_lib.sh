#!/bin/bash
# successor_lib.sh -- PART-TWO SUCCESSOR submission, shared by `watchdog.sh` and
# `successor_watch.sh`. Sourced, never executed.
#
# WHY THIS EXISTS
# ---------------
# The P0 lane `720083` owns the 02:36 `stingy` slot and will finish its 22 MIFlu
# cells (or die) somewhere around 06:30. `stingy` is `MaxSubmitJobsPerUser=1`, so
# the ONLY way to use the slot that frees up is to have something already alive
# that can `sbatch` into it the moment it goes idle. That is this code: a
# one-shot successor lane that continues into part two (P1 then P2).
#
# ONE-SHOT GUARANTEE
# ------------------
# The sentinel `queue/SUCCESSOR_SUBMITTED` is created with `noclobber` (O_EXCL),
# so even though the watchdog AND the dedicated watcher both evaluate the same
# gate, exactly one process can ever create it. The loser sees the sentinel and
# logs `already-fired`.
#
# GATE (all four must hold; every refusal is logged with its reason)
#   1. the designated P0 lane is no longer RUNNING/PENDING/CONFIGURING/...
#   2. no other job of ours is alive on `stingy`
#   3. no SUCCESSOR_SUBMITTED sentinel yet
#   4. the clock is before QUEUE_SUCCESSOR_CUTOFF (default 07:00 local) AND at
#      least QUEUE_SUCCESSOR_MIN_RUNWAY seconds (default 1800) remain before it,
#      so the successor has runway for at least a few cells.

P0_LANE_FILE="${QDIR}/P0_LANE.job"
SUCC_SENTINEL="${QDIR}/SUCCESSOR_SUBMITTED"
SUCC_LOG="${QDIR}/successor.log"
SUCC_CUTOFF=${QUEUE_SUCCESSOR_CUTOFF:-0700}
SUCC_MIN_RUNWAY=${QUEUE_SUCCESSOR_MIN_RUNWAY:-1800}
SUCC_CTRL=${SUCC_CTRL:-${QDIR}/successor_lane.sh}

slog() { printf '[%s] %s\n' "$(date '+%F %T')" "$*" | tee -a "${SUCC_LOG}"; }

succ_cutoff_epoch() {   # next occurrence of HHMM (local) as an epoch
  local hh=${SUCC_CUTOFF:0:2} mm=${SUCC_CUTOFF:2:2} today now
  now=$(date +%s)
  today=$(date -d "$(date +%F) ${hh}:${mm}:00" +%s 2>/dev/null) || { echo "$now"; return; }
  if [ "${now}" -ge "${today}" ]; then
    date -d "tomorrow ${hh}:${mm}:00" +%s
  else
    echo "${today}"
  fi
}

succ_alive_state() {   # 0 = this job is in a live state
  case "$1" in
    RUNNING|PENDING|CONFIGURING|COMPLETING|REQUEUED|RESUBMITTED|SUSPENDED) return 0 ;;
  esac
  return 1
}

successor_gate() {   # prints the decision on stdout; 0 = FIRE, 1 = do not fire (yet)
  local p0 st j js now cut
  if [ -f "${SUCC_SENTINEL}" ]; then echo "already-fired"; return 1; fi
  p0=$(head -1 "${P0_LANE_FILE}" 2>/dev/null | tr -d ' ')
  if [ -z "${p0}" ]; then echo "no-p0-lane-recorded"; return 1; fi
  st=$(scontrol show job "${p0}" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p')
  if succ_alive_state "${st}"; then echo "p0-active:${p0}:${st}"; return 1; fi
  # `stingy` is MaxSubmitJobsPerUser=1: any live job of ours there blocks us, and
  # squeue alone is not authoritative on this cluster, so every id is re-checked
  # with scontrol before it is believed.
  for j in $(squeue -u "${USER}" -h -p stingy -o '%i' 2>/dev/null | tr -d ' '); do
    [ -n "${j}" ] || continue
    js=$(scontrol show job "${j}" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p')
    if succ_alive_state "${js}"; then echo "stingy-busy:${j}:${js}"; return 1; fi
  done
  now=$(date +%s); cut=$(succ_cutoff_epoch)
  if [ "${now}" -ge "${cut}" ]; then echo "past-cutoff:${SUCC_CUTOFF}"; return 1; fi
  if [ $(( cut - now )) -lt "${SUCC_MIN_RUNWAY}" ]; then
    echo "runway-too-short:$(( cut - now ))s<${SUCC_MIN_RUNWAY}s"; return 1
  fi
  echo "ready:p0=${p0}:state=${st}:runway=$(( cut - now ))s"
  return 0
}

successor_fire() {   # $1 = the gate's ready-line ; 0 = submitted
  local why=$1 out id
  # ---- atomic one-shot: exactly one process in the whole night can win ------
  if ! ( set -o noclobber; printf '%s pid=%s gate=%s\n' "$(date '+%F %T')" "$$" "${why}" \
           > "${SUCC_SENTINEL}" ) 2>/dev/null; then
    slog "SUCCESSOR not fired: another process created ${SUCC_SENTINEL} first"
    return 1
  fi
  out=$(sbatch --parsable --partition=stingy --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
        --time=04:00:00 --requeue --exclude=gpu-a100-05 \
        --output="${QDIR}/slurm-S-%j.out" --export=ALL \
        "${SUCC_CTRL}" 2>&1)
  id=${out%%;*}
  if printf '%s' "${id}" | grep -qE '^[0-9]+$' && scontrol show job "${id}" > /dev/null 2>&1; then
    printf '%s\n' "${id}" > "${QDIR}/runner_s0.job"
    slog "SUCCESSOR SUBMITTED job=${id} partition=stingy wall=04:00:00 start=$(scontrol show job "${id}" 2>/dev/null | tr ' ' '\n' | sed -n 's/^StartTime=//p') gate=${why}"
    return 0
  fi
  rm -f "${SUCC_SENTINEL}"      # do not burn the one shot on a failed submit
  slog "SUCCESSOR SUBMIT FAILED: ${out}"
  return 1
}

successor_evaluate() {   # prints the decision and, when ready, fires it. 0 = fired now
  local why
  why=$(successor_gate)
  case "${why}" in
    ready:*) successor_fire "${why}"; return $? ;;
    *)       echo "not yet: ${why}"; return 1 ;;
  esac
}
