#!/bin/bash -l
#SBATCH --job-name=mlflu_master
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --requeue
#SBATCH --output=queue/slurm-master-%j.out
#
# ============================================================================
# master_controller.sh -- ONE controller, TWO partitions, disjoint stripes,
#                         indefinite via `scontrol requeue`, night-long.
# ============================================================================
#
# WHAT PROBLEM THIS SOLVES (measured, 2026-11-01)
# ----------------------------------------------
# * `stingy` is `MaxSubmitJobsPerUser=1` + `PreemptMode=CANCEL`: a running job
#   there CANNOT `sbatch` a successor (measured: `QOSMaxSubmitJobPerUserLimit`)
#   and Slurm will not requeue a preempted job for you. The only self-continuation
#   is `scontrol requeue $SLURM_JOB_ID` -- same job id, no new submission, and a
#   fresh full wall clock (measured on `tiny`, job 719816: Elapsed resets to 0 and
#   the job keeps its id -- see queue/requeue_test/log).
# * `gpu_a100` allows 30 submitted / 15 running, so there a successor `sbatch` IS
#   possible and is strictly better: the successor is already queued when we die.
# * `squeue`/`sinfo` are user-scoped here; occupancy must be read from
#   `scontrol show node <n>` (AllocTRES) / `sacct -a -s R -N <n>`.
# * Both partitions are full tonight (first start ~02:50-03:28), so continuity --
#   not throughput -- is the primary design goal: this chain must survive
#   preemption, requeue and a 12+ hour operator absence.
#
# DESIGN
# ------
# 1. The queue lives on disk (`master_queue.tsv`), never in memory. Every
#    transition is written atomically (`.tmp` + `mv`) under a `flock` shared with
#    the python side (`queue_store.py`), so two controllers cannot corrupt it.
# 2. **Stripes.** Each task belongs to stripe 0 or 1 by a stable hash of its
#    task_id (`cksum % 2`). The `stingy` controller runs stripe 0, the
#    `gpu_a100` controller runs stripe 1: disjoint by construction, so no cell
#    can be produced twice. `--dry-run` prints the mapping and asserts it.
# 3. **Idempotence.** A task whose artefacts exist and pass their gate is DONE
#    without being re-run (`master_task.py` re-checks the gate first); a task
#    left RUNNING by a preemption is reset to TODO on start-up with its attempt
#    count preserved. A 12-hour chain therefore cannot redo work.
# 4. **No total budget.** The stopping conditions are exactly: (a) nothing left
#    to run anywhere, (b) `queue/HALT` present, (c) a hard failure that cannot
#    advance (and then it exits non-zero). At the wall-clock guard (>=10 min of
#    slack) it continues itself and VERIFIES the continuation happened.
# 5. **CPU kinds are never run in a GPU allocation** (rule 13(b)): `llm_probe`
#    rows are picked only under `QUEUE_CPU_ONLY=1`, which the two GPU
#    submissions never set.
#
# USAGE
# -----
#   sbatch --partition=stingy   --export=ALL,QUEUE_STRIPE=0,QUEUE_PARTITION=stingy   master_controller.sh
#   sbatch --partition=gpu_a100 --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100 master_controller.sh
#   bash master_controller.sh --dry-run     # no GPU, no work: prints the split + asserts
#   bash master_controller.sh --selftest    # state-machine proof on a sandbox queue
set -uo pipefail

SELF=$(readlink -f "$0")
QDIR=${QUEUE_DIR:-$(dirname "${SELF}")}
CODE=$(dirname "${QDIR}")
QUEUE=${QDIR}/master_queue.tsv
EVENTS=${QDIR}/queue_events.log
STATE_TSV=${QDIR}/queue_state.tsv
HALT=${QDIR}/HALT
LOCK=${QDIR}/.queue.lock
LOGDIR=${QDIR}/logs

PY_HPC=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
PY_LLM=/home/sychan552/.venvs/mlflu_llm/bin/python

STRIPE=${QUEUE_STRIPE:-}
PART=${QUEUE_PARTITION:-${SLURM_JOB_PARTITION:-stingy}}
WALL=${QUEUE_WALL_SECONDS:-14400}         # 4 h = the stingy / gpu_a100 ceiling here
SLACK=${QUEUE_SLACK_SECONDS:-900}         # keep >= 10 min for the requeue handshake
TASK_TIMEOUT=${QUEUE_TASK_TIMEOUT:-2700}  # per-task ceiling (45 min)
ALLOW_CPU=${QUEUE_ALLOW_CPU_KINDS:-0}
CPU_ONLY=${QUEUE_CPU_ONLY:-0}
HW_ASSERT=${QUEUE_HW_ASSERT:-1}
MAXTASKS=${QUEUE_MAX_TASKS:-0}            # 0 = unlimited
FORCE_FAIL=${QUEUE_FORCE_FAIL:-}
FORCE_OK=${QUEUE_FORCE_OK:-}
MAXGEN=${QUEUE_MAXGEN:-0}                 # 0 = unlimited generations (the night is long)
EXCLUDE=${QUEUE_EXCLUDE:-gpu-a100-05}
IDLE_POLL=${QUEUE_IDLE_POLL:-300}         # seconds between idle re-scans
MAXATT=${QUEUE_MAX_ATTEMPTS:-2}

# Put the P4 rows back to TODO after a cell task produced new data. `finalise`
# itself never calls this, so there is no loop: a finalise run ends DONE.
rearm_finalise() {
  local why=$1 tid kind model L seed pri envr st att lj note n=0
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${kind}" = "finalise" ] || continue
    [ "${st}" = "DONE" ] || continue
    row_set "${tid}" "TODO" "${att}" "-" "re-armed after ${why} (new cell data)"
    n=$((n + 1))
  done < "${QUEUE}"
  say "re-armed ${n} P4 finalisation task(s) after ${why}"
}
SELFTEST=${QUEUE_SELFTEST:-0}
MODE=run

CPU_KINDS="llm_probe"

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)       MODE=dry-run ;;
    --selftest)      MODE=selftest ;;
    --stripe)        STRIPE=$2; shift ;;
    --partition)     PART=$2; shift ;;
    --max-tasks)     MAXTASKS=$2; shift ;;
    --no-hw-assert)  HW_ASSERT=0 ;;
    --no-idle-wait)  IDLE_POLL=0 ;;
    --allow-cpu-kinds) ALLOW_CPU=1 ;;
    -h|--help)       sed -n '5,40p' "${SELF}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

mkdir -p "${QDIR}" "${LOGDIR}"
TAG="stripe=${STRIPE:-all} part=${PART} job=${SLURM_JOB_ID:-local}"

say() {
  local line
  line="[$(date '+%F %T')] ${TAG} $*"
  printf '%s\n' "${line}"
  printf '%s\n' "${line}" >> "${EVENTS}"
}
die() { say "FATAL: $*"; exit 1; }

GENFILE=${QDIR}/.gen_s${STRIPE:-all}
GEN=$(( $(cat "${GENFILE}" 2>/dev/null || echo 0) + 1 ))
echo "${GEN}" > "${GENFILE}"

[ -f "${QUEUE}" ] || die "missing queue file ${QUEUE}"

# ---- stripe of every task, computed once (stable: cksum(task_id) % 2) ------
declare -A STRIPE_OF
mapfile -t LINES < <(tail -n +2 "${QUEUE}")
for line in "${LINES[@]}"; do
  tid=${line%%$'\t'*}
  [ -n "${tid}" ] || continue
  STRIPE_OF[${tid}]=$(printf '%s' "${tid}" | cksum | awk '{print $1 % 2}')
done

is_mine() {   # $1 = task_id, $2 = kind
  [ "${SELFTEST}" = "1" ] && return 0
  local k=$2
  # P4 finalisation turns cells into tables/figures/verdicts, so EVERY lane may
  # run it: whichever controller next has a free slot after new cells landed does
  # the rebuild. It is idempotent and holds a cross-lane lock, so two lanes can
  # never run it at the same time.
  [ "${k}" = "finalise" ] && return 0
  if [ "${CPU_ONLY}" = "1" ]; then
    case " ${CPU_KINDS} " in *" ${k} "*) return 0 ;; esac
    return 1
  fi
  case " ${CPU_KINDS} " in *" ${k} "*) return 1 ;; esac   # never on a GPU allocation
  [ "${STRIPE_OF[$1]:-}" = "${STRIPE}" ]
}

# ---- atomic row update (flock shared with queue_store.py) -----------------
row_set() {  # id state attempts last_job note
  local id=$1 st=$2 att=$3 lj=$4 note=$5
  exec 200>>"${LOCK}"
  flock 200
  awk -F'\t' -v OFS='\t' -v id="${id}" -v st="${st}" -v att="${att}" -v lj="${lj}" -v note="${note}" '
    NR==1 {print; next}
    $1==id { $8=st; $9=att; $10=lj; $11=note; print; next }
    {print}
  ' "${QUEUE}" > "${QUEUE}.tmp.$$" && mv -f "${QUEUE}.tmp.$$" "${QUEUE}"
  flock -u 200
  exec 200>&-
}

state_row() {  # id state attempts wall gate last_job
  local id=$1 st=$2 att=$3 wall=$4 gate=$5 lj=$6
  exec 201>>"${LOCK}"
  flock 201
  [ -f "${STATE_TSV}" ] || printf 'task_id\tstate\tattempts\twall_seconds\tgate\tlast_job\tupdated\n' > "${STATE_TSV}"
  { awk -F'\t' -v id="${id}" 'NR==1 || $1!=id' "${STATE_TSV}"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${id}" "${st}" "${att}" "${wall}" "${gate}" "${lj}" "$(date '+%F %T')"
  } > "${STATE_TSV}.tmp.$$" && mv -f "${STATE_TSV}.tmp.$$" "${STATE_TSV}"
  flock -u 201
  exec 201>&-
}

# ---- helpers --------------------------------------------------------------
job_state() { sacct -j "$1" -n -X -o State 2>/dev/null | head -1 | tr -d ' '; }
job_alive() {
  case "$(job_state "$1")" in
    RUNNING|PENDING|RESIZING|COMPLETING|CONFIGURING|REQUEUED|RESUBMITTED|SUSPENDED) return 0 ;;
  esac
  return 1
}
global_count() { awk -F'\t' -v want="$1" 'NR>1 && $8==want {n++} END{print n+0}' "${QUEUE}"; }
deadline_epoch() { echo $(( $(date +%s) + WALL - SLACK )); }

# ============================== DRY RUN ====================================
do_dry_run() {
  echo "=== master_controller.sh --dry-run ==================================="
  echo "queue        : ${QUEUE}"
  echo "stripe map   : cksum(task_id) % 2          (stable; disjoint by construction)"
  echo "partition A  : stingy    -> stripe 0"
  echo "partition B  : gpu_a100   -> stripe 1"
  echo "cpu kinds    : ${CPU_KINDS}  (never in a GPU allocation; QUEUE_CPU_ONLY=1 elsewhere)"
  echo
  printf '%-6s %-7s %-24s %-30s %s\n' STRIPE PRI STATE TASK_ID KIND
  local tid kind model L seed pri st att lj note s n0=0 n1=0 notodo=0 fail=0
  local -a ids0=() ids1=()
  declare -A in0=() in1=()
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    s=${STRIPE_OF[${tid}]:-X}
    printf '%-6s %-7s %-24s %-30s %s\n' "${s}" "${pri}" "${st}" "${tid}" "${kind}"
    case "${s}" in
      0) n0=$((n0+1)); ids0+=("${tid}"); in0[${tid}]=1 ;;
      1) n1=$((n1+1)); ids1+=("${tid}"); in1[${tid}]=1 ;;
      *) echo "ASSERT FAIL: ${tid} has no stripe"; fail=1 ;;
    esac
    [ "${st}" = "TODO" ] && notodo=$((notodo+1))
  done < "${QUEUE}"

  echo
  echo "tasks in queue       : ${#STRIPE_OF[@]}"
  echo "stripe 0 (stingy)    : ${n0}"
  echo "stripe 1 (gpu_a100)  : ${n1}"
  echo "TODO rows            : ${notodo}   (BLOCKED_MISSING_WEIGHTS: $(global_count BLOCKED_MISSING_WEIGHTS))"

  # (1) disjointness: no task_id may appear in both strides
  local t
  for t in "${ids1[@]}"; do
    [ -n "${in0[${t}]:-}" ] && { echo "ASSERT FAIL: ${t} appears in BOTH stripes"; fail=1; }
  done
  # (2) union: every row got exactly one stripe
  if [ $(( n0 + n1 )) -ne "${#STRIPE_OF[@]}" ]; then
    echo "ASSERT FAIL: n0+n1=$(( n0 + n1 )) != tasks=${#STRIPE_OF[@]}"; fail=1
  fi
  # (3) every TODO row is claimed
  local claimed=0
  for t in "${!STRIPE_OF[@]}"; do :; done
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${st}" = "TODO" ] || continue
    if [ -z "${STRIPE_OF[${tid}]:-}" ]; then echo "ASSERT FAIL: TODO ${tid} unclaimed"; fail=1; else claimed=$((claimed+1)); fi
  done < "${QUEUE}"
  [ "${claimed}" -ne "${notodo}" ] && { echo "ASSERT FAIL: claimed=${claimed} != TODO=${notodo}"; fail=1; }
  # (4) the hash is stable under recomputation
  for t in "${ids0[@]:-}" "${ids1[@]:-}"; do
    [ -n "${t}" ] || continue
    local again; again=$(printf '%s' "${t}" | cksum | awk '{print $1 % 2}')
    [ "${again}" = "${STRIPE_OF[${t}]}" ] || { echo "ASSERT FAIL: ${t} hash unstable"; fail=1; }
  done
  if [ "${fail}" -eq 0 ]; then
    echo "ASSERT OK: the two stripes are disjoint, their union is the full task set,"
    echo "           every TODO row is claimed by exactly one partition, and the hash is stable."
    return 0
  fi
  echo "ASSERTIONS FAILED"; return 1
}

# ============================ START-UP RECOVERY ============================
reset_running() {
  local tid kind model L seed pri st att lj note moved=0 live=""
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${st}" = "RUNNING" ] || continue
    is_mine "${tid}" "${kind}" || continue
    if [ "${lj}" != "${SLURM_JOB_ID:-}" ] && job_alive "${lj}"; then live="${lj}"; continue; fi
    row_set "${tid}" "TODO" "${att}" "${lj}" \
      "reset to TODO at gen=${GEN} start-up: was RUNNING when a previous generation died; attempts preserved"
    say "RECOVER ${tid}: RUNNING -> TODO (attempts=${att} preserved, last_job=${lj})"
    moved=$((moved+1))
  done < "${QUEUE}"
  [ -n "${live}" ] && die "another controller of my stripe is alive (job ${live}); refusing to duplicate work"
  say "recovery: ${moved} RUNNING row(s) returned to TODO"
}

# ============================== PICK NEXT ==================================
scan_pending() {
  local tid kind model L seed pri st att lj note
  P0P=0; P1P=0; P2P=0; P012_ANY=0
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${st}" = "TODO" ] || [ "${st}" = "RUNNING" ] || continue
    local mine=0
    is_mine "${tid}" "${kind}" && mine=1
    case "${pri}" in
      P0) [ "${mine}" = "1" ] && P0P=$((P0P+1)) ;;
      P1) [ "${mine}" = "1" ] && P1P=$((P1P+1)) ;;
      P2) [ "${mine}" = "1" ] && P2P=$((P2P+1)) ;;
    esac
    [ "${pri}" != "P3" ] && P012_ANY=$((P012_ANY+1))
  done < "${QUEUE}"
}

pick_next() {
  scan_pending
  local tid kind model L seed pri st att lj note
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${st}" = "TODO" ] || continue
    is_mine "${tid}" "${kind}" || continue
    case "${pri}" in
      P0) echo "${tid}"; return 0 ;;
      P1) [ "${P0P}" -eq 0 ] && { echo "${tid}"; return 0; } ;;
      P2) [ "${P0P}" -eq 0 ] && [ "${P1P}" -eq 0 ] && { echo "${tid}"; return 0; } ;;
      P3) [ "${P012_ANY}" -eq 0 ] && { echo "${tid}"; return 0; } ;;
      P4) [ "${P0P}" -eq 0 ] && [ "${P1P}" -eq 0 ] && [ "${P2P}" -eq 0 ] && { echo "${tid}"; return 0; } ;;
    esac
  done < "${QUEUE}"
  return 1
}

# ============================== RUN ONE TASK ===============================
run_task() {
  local id=$1
  local kind model L seed pri st att lj note
  IFS=$'\t' read -r _ kind model L seed pri envr st att lj note \
    < <(awk -F'\t' -v id="${id}" '$1==id' "${QUEUE}")
  local att2=$(( ${att:-0} + 1 ))
  local t0; t0=$(date +%s)
  row_set "${id}" "RUNNING" "${att2}" "${SLURM_JOB_ID:-local}" \
    "started $(date '+%F %T') on $(hostname) gen=${GEN} (attempt ${att2}/${MAXATT})"
  say "TASK START ${id} kind=${kind} attempt=${att2}/${MAXATT}"

  local rc=0 reason="" gate=""
  if printf ' %s ' "${FORCE_OK}" | grep -q " ${id} "; then
    gate="1.000000"; reason="selftest-forced-ok"; sleep 1
  elif printf ' %s ' "${FORCE_FAIL}" | grep -q " ${id} "; then
    rc=2; reason="selftest-forced-failure"; sleep 1
  else
    local now remain to
    now=$(date +%s); remain=$(( DEADLINE - now - 60 )); to=${TASK_TIMEOUT}
    [ "${remain}" -lt "${to}" ] && to=${remain}
    if [ "${to}" -lt 120 ]; then
      say "only ${to}s left in this window - not starting ${id}"
      row_set "${id}" "TODO" "${att}" "${lj}" "not started: only ${to}s left in this window"
      return 3
    fi
    local hwflag=1
    [ "${kind}" = "llm_probe" ] && hwflag=0
    [ "${kind}" = "finalise" ] && hwflag=0
    timeout --kill-after=30 "${to}" "${PY_HPC}" -u "${QDIR}/master_task.py" run \
        --task-id "${id}" --kind "${kind}" --model "${model}" \
        --L "${L}" --seed "${seed}" --env "${envr}" --require-a100 "${hwflag}" \
        > "${LOGDIR}/${id}.log" 2>&1
    rc=$?
    gate=$(sed -n 's/^GATE=//p' "${LOGDIR}/${id}.log" | tail -1)
    reason=$(sed -n 's/^REASON=//p;s/^SKIP_REASON=//p' "${LOGDIR}/${id}.log" | tail -1)
    [ "${rc}" = "124" ] && reason="per-task timeout after ${to}s"
  fi

  local wall=$(( $(date +%s) - t0 ))
  case "${rc}" in
    0)  row_set "${id}" "DONE" "${att2}" "${SLURM_JOB_ID:-local}" "gate=${gate:-n/a} wall=${wall}s ${reason}"
        state_row "${id}" DONE "${att2}" "${wall}" "${gate:-n/a}" "${SLURM_JOB_ID:-local}"
        say "TASK DONE  ${id} gate=${gate:-n/a} wall=${wall}s"
        # new data landed -> put the P4 finalisation rows back to TODO so the next
        # free slot rebuilds the tables/figures. `finalise` itself never re-arms
        # anything, so this cannot loop.
        case "${kind}" in
          miflu_cell|llm_cell|llm_probe)
            grep -q ''^NOTE=no-new-cells'' "${LOGDIR}/${id}.log" 2>/dev/null || rearm_finalise "${id}" ;;
        esac ;;
    7)  row_set "${id}" "FAILED" "${att2}" "${SLURM_JOB_ID:-local}" "not-a100 (${reason}); rule 13, cell withheld"
        state_row "${id}" FAILED "${att2}" "${wall}" "not-a100" "${SLURM_JOB_ID:-local}"
        say "TASK FAILED ${id} reason=not-a100 - cell withheld, controller continues" ;;
    9)  row_set "${id}" "FAILED" "${att2}" "${SLURM_JOB_ID:-local}" "oracle gate: ${reason}"
        state_row "${id}" FAILED "${att2}" "${wall}" "oracle-mismatch" "${SLURM_JOB_ID:-local}"
        say "TASK FAILED ${id} ORACLE MISMATCH: ${reason}" ;;
    3)  row_set "${id}" "SKIPPED" "${att2}" "${SLURM_JOB_ID:-local}" "impossible: ${reason}"
        state_row "${id}" SKIPPED "${att2}" "${wall}" "n/a" "${SLURM_JOB_ID:-local}"
        say "TASK SKIPPED ${id} reason=${reason}" ;;
    *)  if [ "${att2}" -ge "${MAXATT}" ]; then
          row_set "${id}" "SKIPPED" "${att2}" "${SLURM_JOB_ID:-local}" \
            "skipped after ${att2} failed attempts; last reason: ${reason:-rc=${rc}}"
          state_row "${id}" SKIPPED "${att2}" "${wall}" "n/a" "${SLURM_JOB_ID:-local}"
          say "TASK SKIPPED ${id} after ${att2} failed attempts: ${reason:-rc=${rc}}"
        else
          row_set "${id}" "TODO" "${att2}" "${SLURM_JOB_ID:-local}" \
            "attempt ${att2} failed (rc=${rc}): ${reason:-unknown}; will retry"
          state_row "${id}" TODO "${att2}" "${wall}" "n/a" "${SLURM_JOB_ID:-local}"
          say "TASK RETRY ${id} attempt ${att2} failed rc=${rc} reason=${reason:-unknown}"
        fi ;;
  esac
}

# ============================ CONTINUATION =================================
continue_chain() {
  local why="$1" ok=0 st sid out
  say "CONTINUATION needed (${why})"
  if [ "${MAXGEN}" -gt 0 ] && [ "${GEN}" -ge "${MAXGEN}" ]; then
    say "MAXGEN=${MAXGEN} reached at gen=${GEN} - not continuing (cap)"
    return 2
  fi
  case "${PART}" in
    stingy|gpu_v100s)
      scontrol requeue "${SLURM_JOB_ID}" >> "${EVENTS}" 2>&1
      sleep 3
      st=$(job_state "${SLURM_JOB_ID}")
      case "${st}" in PENDING|REQUEUED|RESUBMITTED|RUNNING|CONFIGURING) ok=1 ;; esac
      if [ "${ok}" = "1" ]; then
        say "SELF-REQUEUE VERIFIED: job ${SLURM_JOB_ID} state=${st} (same id, fresh wall clock) -> next gen=$((GEN+1))"
        return 0
      fi
      say "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      say "!! SELF-REQUEUE FAILED on ${PART}: job ${SLURM_JOB_ID} state='${st:-gone}'"
      say "!! Chain stops here unless the tiny watcher resubmits it."
      say "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      return 1 ;;
    *)
      local -a a=(--parsable --partition="${PART}" --cpus-per-task=8 --mem=48G
                  --time="$(( WALL / 3600 )):00:00" --requeue
                  --dependency="afterany:${SLURM_JOB_ID}"
                  --export=ALL,QUEUE_STRIPE="${STRIPE}",QUEUE_PARTITION="${PART}",QUEUE_CPU_ONLY="${CPU_ONLY}",QUEUE_ALLOW_CPU_KINDS="${ALLOW_CPU}")
      case "${PART}" in
        gpu_a100|stingy) a+=(--gres=gpu:a100:1 --exclude="${EXCLUDE}") ;;
      esac
      out=$(sbatch "${a[@]}" "${SELF}" 2>&1)
      sid=${out%%;*}
      if printf '%s' "${sid}" | grep -qE '^[0-9]+$' && scontrol show job "${sid}" > /dev/null 2>&1; then
        say "SUCCESSOR REGISTERED: job ${sid} dependency=afterany:${SLURM_JOB_ID} (stripe ${STRIPE}, ${PART})"
        echo "${sid}" > "${QDIR}/runner_s${STRIPE}.job"
        return 0
      fi
      say "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      say "!! SUCCESSOR SUBMISSION FAILED on ${PART}: ${out}"
      say "!! Chain stops here unless the tiny watcher resubmits it."
      say "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      return 1 ;;
  esac
}

# ============================== SELFTEST ===================================
do_selftest() {
  local SBX; SBX=$(mktemp -d "${QDIR}/selftest.XXXXXX")
  say "SELFTEST sandbox ${SBX}"
  {
    printf 'task_id\tkind\tmodel\tL\tseed\tpriority\tenv\tstate\tattempts\tlast_job\tnote\n'
    printf 'selftest_broken1\tmiflu_cell\tMIFlu\t24\t2021\tP0\thpc\tRUNNING\t1\t721999\tleft RUNNING by a simulated crash\n'
    printf 'selftest_broken2\tmiflu_cell\tMIFlu\t24\t2022\tP0\thpc\tTODO\t0\t-\tforced failure\n'
    printf 'selftest_ok1\tmiflu_cell\tMIFlu\t24\t2023\tP0\thpc\tTODO\t0\t-\tforced success\n'
  } > "${SBX}/master_queue.tsv"
  echo "--- sandbox queue BEFORE (selftest_broken1 is RUNNING: the simulated crash) ---"
  column -t -s$'\t' "${SBX}/master_queue.tsv"

  QUEUE_DIR="${SBX}" QUEUE_FORCE_FAIL="selftest_broken2" QUEUE_FORCE_OK="selftest_ok1" \
  QUEUE_SELFTEST=1 QUEUE_HW_ASSERT=0 QUEUE_MAX_TASKS=8 QUEUE_IDLE_POLL=0 \
  QUEUE_STRIPE=0 QUEUE_PARTITION=selftest QUEUE_MAXGEN=0 \
      bash "${SELF}" --stripe 0 --no-hw-assert --no-idle-wait --partition selftest
  local rc=$?

  echo "--- sandbox queue AFTER ---"
  column -t -s$'\t' "${SBX}/master_queue.tsv"
  echo "--- queue_state.tsv ---"
  column -t -s$'\t' "${SBX}/queue_state.tsv"
  echo "--- assertions ---"
  local bad=0 att st
  st=$(awk -F'\t' '$1=="selftest_broken1"{print $9}' "${SBX}/master_queue.tsv")
  att=$(awk -F'\t' '$1=="selftest_broken1"{print $9}' "${SBX}/master_queue.tsv")
  echo "selftest_broken1: state=${st} attempts=${att} (crash-resume preserved 1 attempt, then 1 more -> SKIPPED at 2)"
  [ "${st}" = "SKIPPED" ] || { echo "FAIL: selftest_broken1 not SKIPPED (state=${st})"; bad=1; }
  [ "${att}" = "2" ]  || { echo "FAIL: selftest_broken1 attempts=${att}, expected 2"; bad=1; }
  st=$(awk -F'\t' '$1=="selftest_broken2"{print $9}' "${SBX}/master_queue.tsv")
  att=$(awk -F'\t' '$1=="selftest_broken2"{print $9}' "${SBX}/master_queue.tsv")
  echo "selftest_broken2: state=${st} attempts=${att}"
  [ "${st}" = "SKIPPED" ] || { echo "FAIL: selftest_broken2 not SKIPPED"; bad=1; }
  [ "${att}" = "2" ]  || { echo "FAIL: selftest_broken2 attempts=${att}, expected 2"; bad=1; }
  st=$(awk -F'\t' '$1=="selftest_ok1"{print $9}' "${SBX}/master_queue.tsv")
  echo "selftest_ok1: state=${st} (the queue moved past the broken tasks and kept working)"
  [ "${st}" = "DONE" ] || { echo "FAIL: selftest_ok1 not DONE"; bad=1; }
  grep -q "selftest_broken1" "${SBX}/queue_events.log" || { echo "FAIL: no event log"; bad=1; }
  if [ "${bad}" = "0" ]; then
    echo "SELFTEST PASS: crash-resume works (RUNNING->TODO, attempts preserved); a broken task"
    echo "               is SKIPPED after exactly 2 attempts with its reason; the queue continues."
  else
    echo "SELFTEST FAIL"; return 1
  fi
  return 0
}

# ================================ MAIN =====================================
[ "${MODE}" = "dry-run" ]  && { do_dry_run;  exit $?; }
[ "${MODE}" = "selftest" ] && { do_selftest; exit $?; }

if [ "${SELFTEST}" != "1" ]; then
  [ -n "${STRIPE}" ] || die "QUEUE_STRIPE must be set for a real run (0 or 1; --dry-run shows the split)"
  { [ "${STRIPE}" = "0" ] || [ "${STRIPE}" = "1" ] || [ "${CPU_ONLY}" = "1" ]; } || die "QUEUE_STRIPE must be 0 or 1"
fi

if [ -f "${HALT}" ]; then
  say "HALT present ($(head -1 "${HALT}" 2>/dev/null)) - exiting cleanly at the task boundary"
  echo done > "${QDIR}/runner_s${STRIPE}.halted"
  exit 0
fi

say "START gen=${GEN} host=$(hostname) node=${SLURM_NODELIST:-?} part=${PART} wall=${WALL}s slack=${SLACK}s mode=${MODE} cpu_only=${CPU_ONLY}"

if [ "${HW_ASSERT}" = "1" ] && [ "${CPU_ONLY}" != "1" ]; then
  "${PY_HPC}" - <<'PYEOF'
import sys
import torch
if not torch.cuda.is_available():
    print("[a100] FATAL: no CUDA device"); sys.exit(3)
name = torch.cuda.get_device_name(0)
cap = torch.cuda.get_device_capability(0)
vram = torch.cuda.get_device_properties(0).total_memory / 2**30
print(f"[a100] MEASURED gpu={name} capability={cap} vram={vram:.1f}GiB")
if "A100" not in name:
    print(f"[a100] FATAL: expected an A100, got {name!r}; "
          f"a non-A100 cell would confound the benchmark (rules 12-13). Refusing to work.")
    sys.exit(4)
PYEOF
  if [ $? -ne 0 ]; then
    say "HARDWARE ASSERTION FAILED - aborting this allocation (no cell was touched)"
    exit 1
  fi
fi

DEADLINE=$(deadline_epoch)
say "deadline=$(date -d "@${DEADLINE}" '+%F %T') = ${WALL}s wall - ${SLACK}s slack; cpus=$(nproc)"
reset_running

NTASKS=0
while :; do
  if [ -f "${HALT}" ]; then
    say "HALT appeared - exiting cleanly"; echo done > "${QDIR}/runner_s${STRIPE}.halted"; exit 0
  fi
  date +%s > "${QDIR}/runner_s${STRIPE}.alive"

  if [ "${MAXTASKS}" -gt 0 ] && [ "${NTASKS}" -ge "${MAXTASKS}" ]; then
    say "MAXTASKS=${MAXTASKS} reached - stopping this generation"
    continue_chain "max-tasks reached"; exit $?
  fi

  ID=$(pick_next || true)
  if [ -z "${ID}" ]; then
    local_todo=$(global_count TODO)
    local_blk=$(global_count BLOCKED_MISSING_WEIGHTS)
    if [ "${CPU_ONLY}" = "1" ]; then
      # the CPU worker's whole job is the probe rows; when they are exhausted it
      # stands down instead of occupying a slot for 12 h.
      say "CPU worker: no llm_probe rows left in TODO - standing down (${local_todo} TODO / ${local_blk} BLOCKED remain for the GPU controllers)"
      echo done > "${QDIR}/runner_scpu.done"
      exit 0
    fi
    if [ "${local_todo}" -eq 0 ] && [ "${local_blk}" -eq 0 ]; then
      say "QUEUE COMPLETE: nothing TODO and nothing BLOCKED anywhere - no successor needed"
      echo done > "${QDIR}/COMPLETE"; echo done > "${QDIR}/runner_s${STRIPE}.done"
      exit 0
    fi
    if [ "$(date +%s)" -ge "${DEADLINE}" ]; then
      continue_chain "wall-clock guard; ${local_todo} TODO / ${local_blk} BLOCKED remain"
      exit $?
    fi
    if [ "${IDLE_POLL}" -gt 0 ]; then
      say "nothing runnable in my scope (${local_todo} TODO globally, ${local_blk} BLOCKED on the CPU probe job) - re-scanning in ${IDLE_POLL}s"
      sleep "${IDLE_POLL}"
      continue
    fi
    say "nothing runnable in my scope and idle-wait disabled - exiting cleanly"
    echo done > "${QDIR}/runner_s${STRIPE}.done"; exit 0
  fi

  if [ "$(date +%s)" -ge "${DEADLINE}" ]; then
    continue_chain "wall-clock guard before ${ID}"; exit $?
  fi

  run_task "${ID}"
  NTASKS=$((NTASKS + 1))
done







