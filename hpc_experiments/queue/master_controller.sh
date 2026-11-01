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
# master_controller.sh (QUEUE v2) -- ONE controller per lane, disjoint stripes,
#                                     indefinite via requeue/successor, and an
#                                     EXPLICIT decision for every branch.
# ============================================================================
#
# WHAT CHANGED IN v2 (the three gaps that could have produced nothing overnight)
# -----------------------------------------------------------------------------
# GAP 1  Finalisation is now real queue work. F1-F5 are ordinary rows with their
#        own kinds (`f1_import_miflu` ... `f5_llm_import`), executed by the same
#        runner, under the same timeout and attempt rules as a training cell, and
#        RE-ARMED after every FINALISE_EVERY (default 4) completed cells, again
#        when the queue drains, and once more at the end. A night that trains and
#        stops leaves npz files and no tables; that is exactly the failure this
#        removes. They tolerate partial data: every table the data supports is
#        emitted, with n_cells/n_arms recorded, and a missing arm never aborts.
# GAP 2  Every row names its interpreter (`env` column: hpc|llm) and the runner
#        launches master_task.py with THAT interpreter. A missing interpreter is
#        SKIPPED `env-missing` with no retry -- a binary that does not exist
#        cannot appear on the next attempt.
# GAP 3  The first completed Qwen2.5-1.5B cell is measured; its wall time goes
#        into queue_state.tsv and cost_model.py projects S/M/L classes onto the
#        REMAINING allocation (read from the real submitted jobs). If the
#        projection does not fit, arms are DEFERRED_COST in a logged order:
#        keep all P0, keep P1, then smallest-first, arithmetic in the note.
#
# DECISION TREE (every branch logs `BRANCH=<name>` into queue_events.log and the
# `branch` column of queue_state.tsv, so the morning report can name what fired)
# -----------------------------------------------------------------------------
# scheduling  sched.pending-far-start   PD with a far StartTime -> do nothing
#             sched.preempted           CANCELLED/PREEMPTED -> TODO, attempts+1
#             sched.stale-running       RUNNING at start-up -> TODO, attempts kept
#             sched.claim-busy          another lane holds the per-task lock
#             sched.no-window           too little wall left to start the task
#             sched.chain-dead          no successor and no watcher -> CHAIN_DEAD
# hardware    hw.not-a100              FAILED + node excluded
#             hw.cuda-busy              node excluded at runtime, retry elsewhere
#             hw.oom-halved             --encoder-batch-size halved, retry
#             hw.node-down              DOWN/DRAIN/NOT_RESPONDING excluded
# training    train.nan               FAILED, no retry (it reproduces)
#             train.timeout             kill, attempt+1, SKIPPED at MAXATT
#             train.oracle-mismatch     retry once, then SKIPPED; never accepted
#             skip.attempts-exhausted   SKIPPED with the last branch/reason
# weights     w.blocked-missing-weights / skip.download-* / skip.no-revision
#             skip.no-hidden-state / skip.arch-unsupported / w.arch-fallback
# data        d.partial-mode / d.refreeze / d.rows-lost / d.arms-changed
#             d.miflu-row-missing / d.disk-pressure / d.no-table
# termination term.halt / term.drained / term.idle-no-work / CHAIN_DEAD
#
# USAGE
#   sbatch --partition=gpu_a100 --export=ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100 master_controller.sh
#   sbatch --partition=stingy   --export=ALL,QUEUE_STRIPE=0,QUEUE_PARTITION=stingy   master_controller.sh
#   bash master_controller.sh --dry-run     # stripe partition + assertions, no work
#   bash master_controller.sh --selftest    # crash/oracle/env/claim proofs
set -uo pipefail

SELF=$(readlink -f "$0" 2>/dev/null || echo "$0")
QDIR=${QUEUE_DIR:-$(dirname "${SELF}")}
# ---- CRITICAL: `sbatch` SPOOLS the script -----------------------------------
# Slurm copies the batch script to /var/spool/slurmd/job<N>/slurm_script and runs
# THAT, so `$0` is the spool path and `dirname $0` is NOT the queue directory.
# Deriving QDIR from $0 alone therefore makes a submitted controller die on its
# first line ("missing queue file /var/spool/.../master_queue.tsv"). Fall back to
# the real path whenever the derived one does not contain the queue.
[ -f "${QDIR}/master_queue.tsv" ] || QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
CODE=$(dirname "${QDIR}")
QUEUE=${QDIR}/master_queue.tsv
EVENTS=${QDIR}/queue_events.log
STATE_TSV=${QDIR}/queue_state.tsv
HALT=${QDIR}/HALT
LOCK=${QDIR}/.queue.lock
LOCKDIR=${QDIR}/locks
LOGDIR=${QDIR}/logs
EXCLFILE=${QDIR}/exclude_nodes.txt

PY_HPC=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
PY_LLM=/home/sychan552/.venvs/mlflu_llm/bin/python
RUNS_EXPANDED=/gpfs1/home/sychan552/stage5_a2_durable/expanded_runs
RUNS_AUTHOR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
ANALYSIS=/gpfs1/home/sychan552/stage5_a2_durable/analysis

STRIPE=${QUEUE_STRIPE:-}
PART=${QUEUE_PARTITION:-${SLURM_JOB_PARTITION:-stingy}}
WALL=${QUEUE_WALL_SECONDS:-14400}
SLACK=${QUEUE_SLACK_SECONDS:-900}
TASK_TIMEOUT=${QUEUE_TASK_TIMEOUT:-2700}
ALLOW_CPU=${QUEUE_ALLOW_CPU_KINDS:-0}
CPU_ONLY=${QUEUE_CPU_ONLY:-0}
HW_ASSERT=${QUEUE_HW_ASSERT:-1}
MAXTASKS=${QUEUE_MAX_TASKS:-0}
FORCE_FAIL=${QUEUE_FORCE_FAIL:-}
FORCE_OK=${QUEUE_FORCE_OK:-}
FORCE_ORACLE=${QUEUE_FORCE_ORACLE:-}
MAXGEN=${QUEUE_MAXGEN:-0}
EXCLUDE=${QUEUE_EXCLUDE:-gpu-a100-05,gpu-a100-09}
IDLE_POLL=${QUEUE_IDLE_POLL:-300}
MAXATT=${QUEUE_MAX_ATTEMPTS:-2}
FINALISE_EVERY=${QUEUE_FINALISE_EVERY:-4}
SELFTEST=${QUEUE_SELFTEST:-0}
#: SINGLE-WRITER DESIGN. Exactly one process in the whole night may execute F1-F5
#: and therefore write paper_tables/, results/bench_figures/ or
#: hpc_results/expanded_runs/**. The two GPU lanes are CELL PRODUCERS ONLY: two
#: lanes concurrently rebuilding the tables from different partial subsets would
#: produce plausible-looking, wrong tables with no error anywhere. So finalisation
#: is gated on WRITE_ONLY=1, which only the dedicated `writer.sh` lane sets.
WRITE_ONLY=${QUEUE_WRITE_ONLY:-0}
WRITE_POLL=${QUEUE_WRITE_POLL:-120}
WRITE_MAX=${QUEUE_WRITE_MAX_SECONDS:-43200}
WRITER_ONCE=${QUEUE_WRITER_ONCE:-0}
#: lane scoping. `QUEUE_ONLY_PRIORITY=P1` makes a lane take ONLY those priorities,
#: which is how a second GPU lane is given a DISJOINT task set instead of
#: duplicating the first lane's cells (P0 MIFlu belongs to 719833).
ONLY_PRI=${QUEUE_ONLY_PRIORITY:-}
#: accept "P1,P2" as well as "P1 P2" so the scope survives `sbatch --export`
ONLY_PRI=$(printf '%s' "${ONLY_PRI}" | tr ',' ' ')
#: `QUEUE_SMOKE_ABORT=1`: the FIRST cell of each arm is that arm's smoke test. If it
#: fails, every remaining cell of THAT arm is marked SKIPPED reason=adapter-failed
#: and the lane moves on to the next arm (a lane with several arms must not die on
#: one bad adapter). `=2` additionally aborts the whole lane, which is what a
#: single-arm lane wants.
SMOKE_ABORT=${QUEUE_SMOKE_ABORT:-0}
ABORT_LANE=0
MODE=run

#: kinds that run on a CPU node only (rule 13(b))
CPU_KINDS="llm_probe"
#: the F1-F5 task kinds (GAP 1). They are ordinary rows: same timeout, same
#: attempts, same state machine -- only their body differs.
FINALISE_KINDS="f1_import_miflu f2_miflu_oracle f3_analysis_chain f4_verify f5_llm_import finalise"
#: the order a drain-time finalisation pass runs them in (import -> verify ->
#: rebuild -> verify-frozen -> per-LLM refresh)
FINALISE_ORDER="f1_import_miflu f2_miflu_oracle f3_analysis_chain f4_verify f5_llm_import"

while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)       MODE=dry-run ;;
    --selftest)      MODE=selftest ;;
    --writer)        MODE=writer ;;
    --writer-once)   MODE=writer; WRITER_ONCE=1 ;;
    --claim-test)    MODE=claim-test; CLAIM_ID=$2; shift ;;
    --stripe)        STRIPE=$2; shift ;;
    --partition)     PART=$2; shift ;;
    --max-tasks)     MAXTASKS=$2; shift ;;
    --no-hw-assert)  HW_ASSERT=0 ;;
    --no-idle-wait)  IDLE_POLL=0 ;;
    --allow-cpu-kinds) ALLOW_CPU=1 ;;
    -h|--help)       sed -n '5,60p' "${SELF}" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
  shift
done

mkdir -p "${QDIR}" "${LOGDIR}" "${LOCKDIR}"
TAG="stripe=${STRIPE:-all} part=${PART} job=${SLURM_JOB_ID:-local}"

say() {
  local line
  line="[$(date '+%F %T')] ${TAG} $*"
  printf '%s\n' "${line}"
  printf '%s\n' "${line}" >> "${EVENTS}"
}
die() { say "FATAL: $*"; exit 1; }
branch_event() { printf '[%s] %s BRANCH %s\n' "$(date '+%F %T')" "${TAG}" "$*" >> "${EVENTS}"; }

GENFILE=${QDIR}/.gen_s${STRIPE:-all}
GEN=$(( $(cat "${GENFILE}" 2>/dev/null || echo 0) + 1 ))
echo "${GEN}" > "${GENFILE}"

[ -f "${QUEUE}" ] || die "missing queue file ${QUEUE}"

# ---- interpreter routing (GAP 2) ------------------------------------------
env_py() {   # $1 = env name -> interpreter path ("" if unknown)
  case "${1:-}" in
    hpc|"") echo "${PY_HPC}" ;;
    llm)    echo "${PY_LLM}" ;;
    *)      echo "" ;;
  esac
}
env_ok() {   # $1 = env name ; 0 iff the interpreter exists and is executable
  local p; p=$(env_py "$1")
  [ -n "${p}" ] && [ -x "${p}" ]
}
is_finalise_kind() { case " ${FINALISE_KINDS} " in *" $1 "*) return 0 ;; esac; return 1; }

# ---- stripe of every task, computed once (stable: cksum(task_id) % 2) ------
declare -A STRIPE_OF
mapfile -t LINES < <(tail -n +2 "${QUEUE}")
for line in "${LINES[@]}"; do
  tid=${line%%$'\t'*}
  [ -n "${tid}" ] || continue
  STRIPE_OF[${tid}]=$(printf '%s' "${tid}" | cksum | awk '{print $1 % 2}')
done

declare -A CLAIM_BUSY=()     # task ids another lane holds this generation

is_mine() {   # $1 = task_id, $2 = kind
  [ "${SELFTEST}" = "1" ] && return 0
  local k=$2
  # ---- SINGLE WRITER: F1-F5 belong to the writer lane and to nothing else ----
  # A compute lane that also rebuilt the tables would race the writer, and the
  # loser of that race would leave a table built from a partial cell set with no
  # error anywhere. So the GPU lanes (and the CPU download lane) never touch them.
  if is_finalise_kind "${k}"; then
    [ "${WRITE_ONLY}" = "1" ] && return 0
    return 1
  fi
  if [ "${WRITE_ONLY}" = "1" ]; then return 1; fi   # the writer never trains
  # A priority-scoped lane owns EVERY cell in its scope, not one cksum half:
  # the exclusion mechanism between lanes is now the atomic per-task claim, not
  # the stripe. Without this a P0-only lane would silently drop the 13 P0 cells
  # that hash to the other stripe.
  if [ -n "${ONLY_PRI}" ]; then return 0; fi
  if [ "${CPU_ONLY}" = "1" ]; then
    case " ${CPU_KINDS} " in *" ${k} "*) return 0 ;; esac
    return 1
  fi
  case " ${CPU_KINDS} " in *" ${k} "*) return 1 ;; esac   # never on a GPU allocation
  [ "${STRIPE_OF[$1]:-}" = "${STRIPE}" ]
}

# ---- atomic row update (flock shared with queue_store.py) -----------------
row_set() {  # id state attempts last_job note [env]
  local id=$1 st=$2 att=$3 lj=$4 note=$5 envn=${6:-}
  exec 200>>"${LOCK}"
  flock 200
  awk -F'\t' -v OFS='\t' -v id="${id}" -v st="${st}" -v att="${att}" -v lj="${lj}" \
      -v note="${note}" -v envn="${envn}" '
    NR==1 {print; next}
    $1==id { $8=st; $9=att; $10=lj; $11=note; if (envn!="") $7=envn; print; next }
    {print}
  ' "${QUEUE}" > "${QUEUE}.tmp.$$" && mv -f "${QUEUE}.tmp.$$" "${QUEUE}"
  flock -u 200
  exec 200>&-
}

state_row() {  # id state attempts wall gate last_job branch
  local id=$1 st=$2 att=$3 wall=$4 gate=$5 lj=$6 brn=${7:-"-"}
  exec 201>>"${LOCK}"
  flock 201
  [ -f "${STATE_TSV}" ] || printf 'task_id\tstate\tattempts\twall_seconds\tgate\tlast_job\tbranch\tupdated\n' > "${STATE_TSV}"
  { awk -F'\t' -v id="${id}" 'NR==1 || $1!=id' "${STATE_TSV}"
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' "${id}" "${st}" "${att}" "${wall}" "${gate}" "${lj}" "${brn}" "$(date '+%F %T')"
  } > "${STATE_TSV}.tmp.$$" && mv -f "${STATE_TSV}.tmp.$$" "${STATE_TSV}"
  flock -u 201
  exec 201>&-
}

# ---- per-task atomic claim (PID + job id), so two lanes never run one task --
claim_task() {   # $1 = task id ; 0 = claimed, 1 = somebody else holds it
  local id=$1 lf="${LOCKDIR}/${id}.lock" pid job host ts
  mkdir -p "${LOCKDIR}"
  if ( set -o noclobber; printf '%s\t%s\t%s\t%s\n' "$$" "${SLURM_JOB_ID:-local}" \
         "$(hostname)" "$(date '+%F %T')" > "${lf}" ) 2>/dev/null; then
    return 0
  fi
  IFS=$'\t' read -r pid job host ts < "${lf}" 2>/dev/null || true
  # Owner alive? on THIS host a live pid counts; across hosts only a live job does.
  if [ -n "${pid:-}" ] && [ "${host:-}" = "$(hostname)" ] && kill -0 "${pid}" 2>/dev/null; then
    say "CLAIM ${id}: held by live pid ${pid} on $(hostname) (job ${job:-?}) - skipping"
    return 1
  fi
  if [ -n "${job:-}" ] && [ "${job}" != "local" ] && job_alive "${job}"; then
    say "CLAIM ${id}: held by live job ${job} - skipping"
    return 1
  fi
  say "CLAIM ${id}: stale lock (pid=${pid:-?} job=${job:-?} host=${host:-?}) - stealing"
  rm -f "${lf}.new" 2>/dev/null
  if ( set -o noclobber; printf '%s\t%s\t%s\t%s\n' "$$" "${SLURM_JOB_ID:-local}" \
         "$(hostname)" "$(date '+%F %T')" > "${lf}.new" ) 2>/dev/null; then
    mv -f "${lf}.new" "${lf}"
    return 0
  fi
  return 1
}
release_claim() { rm -f "${LOCKDIR}/$1.lock" "${LOCKDIR}/$1.lock.new" 2>/dev/null; }

# ---- helpers --------------------------------------------------------------
job_state() { sacct -j "$1" -n -X -o State 2>/dev/null | head -1 | tr -d ' '; }
job_alive() {
  case "$(job_state "$1")" in
    RUNNING|PENDING|RESIZING|COMPLETING|CONFIGURING|REQUEUED|RESUBMITTED|SUSPENDED) return 0 ;;
  esac
  return 1
}
global_count() { awk -F'\t' -v want="$1" 'NR>1 && $8==want {n++} END{print n+0}' "${QUEUE}"; }
missing_weights_count() { global_count BLOCKED_MISSING_WEIGHTS; }
own_todo_count() {   # TODO/RUNNING rows this lane may execute (finalise excluded)
  local tid kind model L seed pri envr st att lj note n=0
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    case "${st}" in TODO|RUNNING) ;; *) continue ;; esac
    is_finalise_kind "${kind}" && continue
    if [ -n "${ONLY_PRI}" ]; then
      case " ${ONLY_PRI} " in *" ${pri} "*) : ;; *) continue ;; esac
    fi
    is_mine "${tid}" "${kind}" && n=$((n+1))
  done < "${QUEUE}"
  echo "${n}"
}
deadline_epoch() { echo $(( $(date +%s) + WALL - SLACK )); }

exclude_list() {
  local base="${EXCLUDE}" extra=""
  if [ -f "${EXCLFILE}" ]; then
    extra=$(tr '\n' ',' < "${EXCLFILE}" | sed 's/,,*/,/g; s/^,//; s/,$//')
  fi
  if [ -n "${extra}" ]; then
    printf '%s,%s\n' "${base}" "${extra}" | tr ',' '\n' | sed '/^$/d' | sort -u | paste -sd, -
  else
    printf '%s\n' "${base}"
  fi
}
note_exclude_node() {   # $1 = node, $2 = why
  local n=$1
  [ -n "${n}" ] && [ "${n}" != "None" ] || return 0
  grep -qxF "${n}" "${EXCLFILE}" 2>/dev/null || printf '%s\n' "${n}" >> "${EXCLFILE}"
  say "EXCLUDE ${n} for the rest of the night (${2})"
}
harvest_down_nodes() {
  local n st
  while read -r n st; do
    [ -n "${n}" ] || continue
    case "${st}" in
      *DOWN*|*DRAIN*|*NOT_RESP*|*FAIL*) note_exclude_node "${n}" "state=${st}" ;;
    esac
  done < <(sinfo -h -p gpu_a100,stingy -o '%N %t' 2>/dev/null)
}

# ============================== DRY RUN ====================================
do_dry_run() {
  echo "=== master_controller.sh --dry-run (queue v2) ========================="
  echo "queue        : ${QUEUE}"
  echo "columns      : task_id kind model L seed priority env state attempts last_job note"
  echo "stripe map   : cksum(task_id) % 2          (stable; disjoint by construction)"
  echo "partition A  : gpu_a100   -> stripe 1"
  echo "partition B  : stingy     -> stripe 0"
  echo "cpu kinds    : ${CPU_KINDS}  (never in a GPU allocation; QUEUE_CPU_ONLY=1 elsewhere)"
  echo "finalise     : ${FINALISE_KINDS}"
  echo "               every lane may run them; re-armed after ${FINALISE_EVERY} completed cells"
  echo "exclude      : $(exclude_list)"
  echo
  printf '%-6s %-4s %-8s %-26s %-18s %-5s %s\n' STRIPE PRI STATE TASK_ID KIND ENV NOTE
  local tid kind model L seed pri envr st att lj note s n0=0 n1=0 ntodo=0 nfinal=0 fail=0
  local -a ids0=() ids1=() idsf=()
  declare -A in0=() in1=() seen=()
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    s=${STRIPE_OF[${tid}]:-X}
    printf '%-6s %-4s %-8s %-26s %-18s %-5s %s\n' "${s}" "${pri}" "${st}" "${tid}" "${kind}" "${envr}" "${note:0:44}"
    [ -n "${seen[${tid}]:-}" ] && { echo "ASSERT FAIL: duplicate task_id ${tid}"; fail=1; }
    seen[${tid}]=1
    if is_finalise_kind "${kind}"; then
      nfinal=$((nfinal+1)); idsf+=("${tid}")
    else
      case "${s}" in
        0) n0=$((n0+1)); ids0+=("${tid}"); in0[${tid}]=1 ;;
        1) n1=$((n1+1)); ids1+=("${tid}"); in1[${tid}]=1 ;;
        *) echo "ASSERT FAIL: ${tid} has no stripe"; fail=1 ;;
      esac
    fi
    [ "${st}" = "TODO" ] && ntodo=$((ntodo+1))
    if [ -n "${envr}" ] && [ "${envr}" != "-" ] && [ "${envr}" != "hpc" ] && [ "${envr}" != "llm" ]; then
      echo "ASSERT FAIL: ${tid} has unknown env ${envr}"; fail=1
    fi
  done < "${QUEUE}"

  echo
  echo "tasks in queue       : ${#STRIPE_OF[@]}"
  echo "stripe 0 (stingy)    : ${n0}"
  echo "stripe 1 (gpu_a100)  : ${n1}"
  echo "F1-F5 rows           : ${nfinal}  (any lane may run them; excluded from the split)"
  echo "TODO rows            : ${ntodo}   (BLOCKED_MISSING_WEIGHTS: $(missing_weights_count))"
  echo "DEFERRED_COST rows   : $(global_count DEFERRED_COST)"

  local t
  for t in "${ids1[@]:-}"; do
    [ -n "${t}" ] || continue
    [ -n "${in0[${t}]:-}" ] && { echo "ASSERT FAIL: ${t} appears in BOTH stripes"; fail=1; }
  done
  if [ $(( n0 + n1 )) -ne $(( ${#STRIPE_OF[@]} - nfinal )) ]; then
    echo "ASSERT FAIL: n0+n1=$(( n0 + n1 )) != tasks=$(( ${#STRIPE_OF[@]} - nfinal ))"; fail=1
  fi
  local claimed=0
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${st}" = "TODO" ] || continue
    if is_finalise_kind "${kind}"; then claimed=$((claimed+1)); continue; fi
    if [ -z "${STRIPE_OF[${tid}]:-}" ]; then echo "ASSERT FAIL: TODO ${tid} unclaimed"; fail=1
    else claimed=$((claimed+1)); fi
  done < "${QUEUE}"
  if [ "${claimed}" -ne "${ntodo}" ]; then
    echo "ASSERT FAIL: claimed=${claimed} != TODO=${ntodo}"; fail=1
  fi
  for t in "${ids0[@]:-}" "${ids1[@]:-}"; do
    [ -n "${t}" ] || continue
    local again; again=$(printf '%s' "${t}" | cksum | awk '{print $1 % 2}')
    [ "${again}" = "${STRIPE_OF[${t}]}" ] || { echo "ASSERT FAIL: ${t} hash unstable"; fail=1; }
  done
  local k
  for k in ${FINALISE_ORDER}; do
    awk -F'\t' -v k="${k}" 'NR>1 && $2==k {f=1} END{exit !f}' "${QUEUE}" \
      || { echo "ASSERT FAIL: no queue row of kind ${k}"; fail=1; }
  done
  if [ "${fail}" -eq 0 ]; then
    echo "ASSERT OK: the two stripes are disjoint, their union is every non-finalisation"
    echo "           task, every TODO row is claimed by exactly one lane, every env is"
    echo "           hpc|llm|-, and all five F1-F5 kinds exist in the queue."
    return 0
  fi
  echo "ASSERTIONS FAILED"; return 1
}

# ============================== SELFTEST ===================================
do_selftest() {
  local SBX; SBX=$(mktemp -d "${QDIR}/selftest.XXXXXX")
  say "SELFTEST sandbox ${SBX}"
  {
    printf 'task_id\tkind\tmodel\tL\tseed\tpriority\tenv\tstate\tattempts\tlast_job\tnote\n'
    printf 'selftest_broken1\tmiflu_cell\tMIFlu\t24\t2021\tP0\thpc\tRUNNING\t1\t721999\tleft RUNNING by a simulated crash (dead job)\n'
    printf 'selftest_broken2\tmiflu_cell\tMIFlu\t24\t2022\tP0\thpc\tTODO\t0\t-\tforced failure\n'
    printf 'selftest_oracle\tmiflu_cell\tMIFlu\t24\t2023\tP0\thpc\tTODO\t0\t-\tforced oracle mismatch\n'
    printf 'selftest_ok1\tmiflu_cell\tMIFlu\t24\t2024\tP0\thpc\tTODO\t0\t-\tforced success\n'
    printf 'selftest_locked\tmiflu_cell\tMIFlu\t24\t2025\tP0\thpc\tTODO\t0\t-\tclaimed by another lane\n'
    printf 'selftest_envbogus\tllm_cell\tQwen/Qwen2.5-1.5B\t24\t42\tP0\tbogus\tTODO\t0\t-\tunknown env -> env-missing\n'
  } > "${SBX}/master_queue.tsv"
  mkdir -p "${SBX}/locks"
  # a claim owned by THIS live shell: the controller must refuse to steal it
  printf '%s\t%s\t%s\t%s\n' "$$" "local" "$(hostname)" "$(date '+%F %T')" \
    > "${SBX}/locks/selftest_locked.lock"

  echo "--- sandbox queue BEFORE (selftest_broken1 is RUNNING: the simulated crash) ---"
  column -t -s$'\t' "${SBX}/master_queue.tsv"

  QUEUE_DIR="${SBX}" QUEUE_FORCE_FAIL="selftest_broken2" QUEUE_FORCE_OK="selftest_ok1" \
  QUEUE_FORCE_ORACLE="selftest_oracle" QUEUE_SELFTEST=1 QUEUE_HW_ASSERT=0 \
  QUEUE_MAX_TASKS=12 QUEUE_IDLE_POLL=0 QUEUE_STRIPE=0 QUEUE_PARTITION=selftest \
  QUEUE_MAXGEN=0 QUEUE_EXCLUDE="-" \
      bash "${SELF}" --stripe 0 --no-hw-assert --no-idle-wait --partition selftest
  local rc=$?

  echo "--- sandbox queue AFTER ---"
  column -t -s$'\t' "${SBX}/master_queue.tsv"
  echo "--- queue_state.tsv (state, attempts, wall, gate, branch) ---"
  column -t -s$'\t' "${SBX}/queue_state.tsv" 2>/dev/null
  echo "--- branches recorded ---"
  grep -o 'BRANCH [a-z0-9.-]*' "${SBX}/queue_events.log" 2>/dev/null | sort | uniq -c

  echo "--- assertions ---"
  local bad=0 st att brn
  st=$(awk -F'\t' '$1=="selftest_broken1"{print $8}' "${SBX}/master_queue.tsv")
  att=$(awk -F'\t' '$1=="selftest_broken1"{print $9}' "${SBX}/master_queue.tsv")
  echo "selftest_broken1 (crash mid-task): state=${st} attempts=${att}"
  [ "${st}" = "SKIPPED" ] || { echo "FAIL: crash row not SKIPPED (state=${st})"; bad=1; }
  [ "${att}" = "2" ] || { echo "FAIL: crash row attempts=${att}, expected 2 (1 preserved + 1 retry)"; bad=1; }

  st=$(awk -F'\t' '$1=="selftest_broken2"{print $8}' "${SBX}/master_queue.tsv")
  att=$(awk -F'\t' '$1=="selftest_broken2"{print $9}' "${SBX}/master_queue.tsv")
  echo "selftest_broken2 (generic failure): state=${st} attempts=${att}"
  [ "${st}" = "SKIPPED" ] || { echo "FAIL: broken2 not SKIPPED"; bad=1; }
  [ "${att}" = "2" ] || { echo "FAIL: broken2 attempts=${att}, expected 2"; bad=1; }

  st=$(awk -F'\t' '$1=="selftest_oracle"{print $8}' "${SBX}/master_queue.tsv")
  att=$(awk -F'\t' '$1=="selftest_oracle"{print $9}' "${SBX}/master_queue.tsv")
  brn=$(awk -F'\t' '$1=="selftest_oracle"{print $7}' "${SBX}/queue_state.tsv")
  echo "selftest_oracle (oracle mismatch): state=${st} attempts=${att} branch=${brn}"
  [ "${st}" = "SKIPPED" ] || { echo "FAIL: oracle row not SKIPPED after 2 attempts"; bad=1; }
  [ "${att}" = "2" ] || { echo "FAIL: oracle row attempts=${att}, expected 2"; bad=1; }
  case "${brn}" in train.oracle-mismatch*) : ;; *) echo "FAIL: oracle branch=${brn}"; bad=1 ;; esac

  st=$(awk -F'\t' '$1=="selftest_ok1"{print $8}' "${SBX}/master_queue.tsv")
  echo "selftest_ok1: state=${st} (the queue moved past every broken task)"
  [ "${st}" = "DONE" ] || { echo "FAIL: selftest_ok1 not DONE"; bad=1; }

  st=$(awk -F'\t' '$1=="selftest_locked"{print $8}' "${SBX}/master_queue.tsv")
  att=$(awk -F'\t' '$1=="selftest_locked"{print $9}' "${SBX}/master_queue.tsv")
  echo "selftest_locked (claimed by another lane): state=${st} attempts=${att} (must be untouched)"
  [ "${st}" = "TODO" ] || { echo "FAIL: locked row was executed (state=${st})"; bad=1; }
  [ "${att}" = "0" ] || { echo "FAIL: locked row attempts=${att}"; bad=1; }

  st=$(awk -F'\t' '$1=="selftest_envbogus"{print $8}' "${SBX}/master_queue.tsv")
  brn=$(awk -F'\t' '$1=="selftest_envbogus"{print $7}' "${SBX}/queue_state.tsv")
  echo "selftest_envbogus: state=${st} branch=${brn} (env-missing, no retry)"
  [ "${st}" = "SKIPPED" ] || { echo "FAIL: bogus env not SKIPPED"; bad=1; }
  case "${brn}" in skip.env-missing*) : ;; *) echo "FAIL: bogus env branch=${brn}"; bad=1 ;; esac

  grep -q "selftest_broken1" "${SBX}/queue_events.log" || { echo "FAIL: no event log"; bad=1; }
  if [ "${bad}" = "0" ]; then
    echo "SELFTEST PASS: crash-resume (RUNNING->TODO, attempts preserved); a generic failure"
    echo "               AND an oracle mismatch each become SKIPPED after exactly 2 attempts"
    echo "               with their branch recorded, without blocking the queue; a task"
    echo "               claimed by another lane is never executed; an unknown env is"
    echo "               SKIPPED env-missing and not retried."
  else
    echo "SELFTEST FAIL"; return 1
  fi
  return 0
}

# ============================ START-UP RECOVERY ============================
reset_running() {
  local tid kind model L seed pri envr st att lj note moved=0 live="" jst newatt
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${st}" = "RUNNING" ] || continue
    if [ "${lj}" != "${SLURM_JOB_ID:-}" ] && [ -n "${lj}" ] && [ "${lj}" != "-" ] && job_alive "${lj}"; then
      live="${lj}"; continue
    fi
    # A preempted/cancelled job means the attempt really happened: count it, so a
    # cell that keeps dying cannot retry forever. A job that simply vanished (no
    # sacct record) is not counted -- it may never have started.
    jst=$(job_state "${lj}")
    newatt=${att}
    case "${jst}" in
      CANCELLED|PREEMPTED|NODE_FAIL|TIMEOUT|FAILED|OUT_OF_MEMORY)
        newatt=$(( ${att:-0} + 1 ))
        branch_event "sched.preempted task=${tid} job=${lj} state=${jst} attempts ${att}->${newatt}" ;;
      *) branch_event "sched.stale-running task=${tid} job=${lj:-none} sacct=${jst:-none} attempts=${att}-preserved" ;;
    esac
    row_set "${tid}" "TODO" "${newatt}" "${lj}" \
      "reset to TODO at gen=${GEN} start-up (was RUNNING; previous job ${lj:-none} ${jst:-gone}); attempts ${att}->${newatt}"
    release_claim "${tid}"
    say "RECOVER ${tid}: RUNNING -> TODO (attempts ${att}->${newatt}, last_job=${lj:-none} state=${jst:-gone})"
    moved=$((moved+1))
  done < "${QUEUE}"
  [ -n "${live}" ] && die "another controller of my lane is alive (job ${live}); refusing to duplicate work"
  say "recovery: ${moved} RUNNING row(s) returned to TODO"
}

# ============================== PICK NEXT ==================================
scan_pending() {
  local tid kind model L seed pri envr st att lj note
  P0P=0; P1P=0; P2P=0; P012_ANY=0
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${st}" = "TODO" ] || [ "${st}" = "RUNNING" ] || continue
    is_finalise_kind "${kind}" && continue
    [ -n "${CLAIM_BUSY[${tid}]:-}" ] && continue
    if [ -n "${ONLY_PRI}" ]; then
      case " ${ONLY_PRI} " in *" ${pri} "*) : ;; *) continue ;; esac
    fi
    local mine=0
    is_mine "${tid}" "${kind}" && mine=1
    case "${pri}" in
      P0) [ "${mine}" = "1" ] && P0P=$((P0P+1)) ;;
      P1) [ "${mine}" = "1" ] && P1P=$((P1P+1)) ;;
      P2) [ "${mine}" = "1" ] && P2P=$((P2P+1)) ;;
    esac
    [ "${pri}" != "P3" ] && [ "${pri}" != "P4" ] && P012_ANY=$((P012_ANY+1))
  done < "${QUEUE}"
}

pick_next() {   # echoes a task id, or nothing
  local tid kind model L seed pri envr st att lj note
  scan_pending
  # GAP 1: a periodic finalisation interrupts the training stream on purpose.
  # Without this the P4 rows would only ever run when everything else is done,
  # i.e. after the window that was supposed to use them has closed.
  if [ "${FINALISE_DUE:-0}" = "1" ]; then
    while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
      [ "${tid}" = "task_id" ] && continue
      [ "${st}" = "TODO" ] || continue
      is_finalise_kind "${kind}" || continue
      [ -n "${CLAIM_BUSY[${tid}]:-}" ] && continue
      echo "${tid}"; return 0
    done < "${QUEUE}"
  fi
  while IFS=$'\t' read -r tid kind model L seed pri envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${st}" = "TODO" ] || continue
    is_mine "${tid}" "${kind}" || continue
    [ -n "${CLAIM_BUSY[${tid}]:-}" ] && continue
    if [ -n "${ONLY_PRI}" ]; then
      case " ${ONLY_PRI} " in *" ${pri} "*) : ;; *) continue ;; esac
    fi
    if is_finalise_kind "${kind}"; then
      # only when no training work for this lane is left, unless FINALISE_DUE
      [ "${P0P}" -eq 0 ] && [ "${P1P}" -eq 0 ] && [ "${P2P}" -eq 0 ] && { echo "${tid}"; return 0; }
      continue
    fi
    case "${pri}" in
      P0) echo "${tid}"; return 0 ;;
      P1) [ "${P0P}" -eq 0 ] && { echo "${tid}"; return 0; } ;;
      P2) [ "${P0P}" -eq 0 ] && [ "${P1P}" -eq 0 ] && { echo "${tid}"; return 0; } ;;
      P3) [ "${P012_ANY}" -eq 0 ] && { echo "${tid}"; return 0; } ;;
      P4) [ "${P012_ANY}" -eq 0 ] && { echo "${tid}"; return 0; } ;;
    esac
  done < "${QUEUE}"
  return 1
}

# ============================== RUN ONE TASK ===============================
log_field() { sed -n "s/^$2=//p" "$1" 2>/dev/null | tail -1; }

branch_for_rc() {   # only used when master_task printed no BRANCH line
  case "$1" in
    0) echo "ok.done" ;;
    3) echo "skip.impossible" ;;
    4) echo "train.failed" ;;
    7) echo "hw.not-a100" ;;
    9) echo "train.oracle-mismatch" ;;
    124) echo "train.timeout" ;;
    *) echo "retry.generic" ;;
  esac
}

run_task() {
  local id=$1
  local _ kind model L seed pri envr st att lj note
  IFS=$'\t' read -r _ kind model L seed pri envr st att lj note \
    < <(awk -F'\t' -v id="${id}" '$1==id' "${QUEUE}")

  if ! claim_task "${id}"; then
    CLAIM_BUSY[${id}]=1
    state_row "${id}" "${st:-TODO}" "${att:-0}" 0 "-" "${lj:-"-"}" "sched.claim-busy"
    branch_event "sched.claim-busy task=${id}"
    return 4
  fi

  local att2=$(( ${att:-0} + 1 ))
  local t0; t0=$(date +%s)
  local py; py=$(env_py "${envr}")
  local hwflag=1
  if is_finalise_kind "${kind}" || [ "${kind}" = "llm_probe" ]; then hwflag=0; fi

  # ---- GAP 2: a missing interpreter is terminal, never a retry -----------
  if ! env_ok "${envr}"; then
    row_set "${id}" "SKIPPED" "${att2}" "${SLURM_JOB_ID:-local}" \
      "env-missing: no interpreter for env '${envr}' (hpc=${PY_HPC} llm=${PY_LLM})"
    state_row "${id}" SKIPPED "${att2}" 0 "n/a" "${SLURM_JOB_ID:-local}" "skip.env-missing"
    branch_event "skip.env-missing task=${id} env=${envr}"
    say "TASK SKIPPED ${id} skip.env-missing (env='${envr}' has no interpreter) - no retry"
    release_claim "${id}"
    return 0
  fi

  row_set "${id}" "RUNNING" "${att2}" "${SLURM_JOB_ID:-local}" \
    "started $(date '+%F %T') on $(hostname) gen=${GEN} attempt ${att2}/${MAXATT} env=${envr}"
  say "TASK START ${id} kind=${kind} env=${envr} attempt=${att2}/${MAXATT}"

  local rc=0 reason="" gate="" brn="" envused=""
  local logf="${LOGDIR}/${id}.log"
  if printf ' %s ' "${FORCE_OK}" | grep -q " ${id} "; then
    gate="1.000000"; reason="selftest-forced-ok"; brn="ok.done"
  elif printf ' %s ' "${FORCE_ORACLE}" | grep -q " ${id} "; then
    rc=9; reason="selftest-forced-oracle-mismatch"
  elif printf ' %s ' "${FORCE_FAIL}" | grep -q " ${id} "; then
    rc=2; reason="selftest-forced-failure"
  else
    local now remain to
    now=$(date +%s); remain=$(( DEADLINE - now - 60 )); to=${TASK_TIMEOUT}
    [ "${remain}" -lt "${to}" ] && to=${remain}
    if [ "${to}" -lt 120 ]; then
      say "only ${to}s left in this window - not starting ${id}"
      row_set "${id}" "TODO" "${att}" "${lj}" "not started: only ${to}s left in this window"
      state_row "${id}" TODO "${att}" 0 "-" "${lj:-"-"}" "sched.no-window"
      branch_event "sched.no-window task=${id} left=${to}s"
      release_claim "${id}"
      return 3
    fi
    # ---- GAP 2: launch with the ROW's interpreter ------------------------
    timeout --kill-after=30 "${to}" "${py}" -u "${QDIR}/master_task.py" run \
        --task-id "${id}" --kind "${kind}" --model "${model}" \
        --L "${L}" --seed "${seed}" --env "${envr}" --require-a100 "${hwflag}" \
        > "${logf}" 2>&1
    rc=$?
    gate=$(log_field "${logf}" GATE)
    reason=$(log_field "${logf}" REASON)
    [ -z "${reason}" ] && reason=$(log_field "${logf}" SKIP_REASON)
    brn=$(log_field "${logf}" BRANCH)
    envused=$(log_field "${logf}" ENV_USED)
    if [ "${rc}" = "137" ]; then rc=124; fi
  fi

  local wall=$(( $(date +%s) - t0 ))
  [ -z "${gate}" ] && gate="-"
  [ -z "${brn}" ] && brn=$(branch_for_rc "${rc}")
  branch_event "${brn} task=${id} rc=${rc} wall=${wall}s"

  case "${rc}" in
    0)
      row_set "${id}" "DONE" "${att2}" "${SLURM_JOB_ID:-local}" \
        "gate=${gate} wall=${wall}s ${reason}" "${envused}"
      state_row "${id}" DONE "${att2}" "${wall}" "${gate}" "${SLURM_JOB_ID:-local}" "${brn}"
      say "TASK DONE  ${id} gate=${gate} wall=${wall}s branch=${brn}"
      if [ "${kind}" = "miflu_cell" ] || [ "${kind}" = "llm_cell" ]; then
        CELLS_DONE=$(( CELLS_DONE + 1 ))
        CELLS_SINCE_FINAL=$(( CELLS_SINCE_FINAL + 1 ))
        if [ "${CELLS_SINCE_FINAL}" -ge "${FINALISE_EVERY}" ]; then
          FINALISE_DUE=1
          say "FINALISE DUE: ${CELLS_SINCE_FINAL} cells completed since the last rebuild"
          rearm_finalise "${id}"
        fi
      fi
      ;;
    3)
      row_set "${id}" "SKIPPED" "${att2}" "${SLURM_JOB_ID:-local}" "skipped: ${reason}"
      state_row "${id}" SKIPPED "${att2}" "${wall}" "n/a" "${SLURM_JOB_ID:-local}" "${brn}"
      say "TASK SKIPPED ${id} branch=${brn} reason=${reason}"
      ;;
    4)
      row_set "${id}" "FAILED" "${att2}" "${SLURM_JOB_ID:-local}" "failed (no retry): ${reason}"
      state_row "${id}" FAILED "${att2}" "${wall}" "n/a" "${SLURM_JOB_ID:-local}" "${brn}"
      say "TASK FAILED ${id} branch=${brn} reason=${reason} - terminal, not retried"
      ;;
    7)
      local node; node=$(hostname)
      note_exclude_node "${node}" "not-a100"
      row_set "${id}" "FAILED" "${att2}" "${SLURM_JOB_ID:-local}" \
        "not-a100 on ${node} (${reason}); rule 13, cell withheld, node excluded"
      state_row "${id}" FAILED "${att2}" "${wall}" "not-a100" "${SLURM_JOB_ID:-local}" "hw.not-a100"
      say "TASK FAILED ${id} hw.not-a100 on ${node} - cell withheld, node excluded, controller continues"
      ;;
    9)
      if [ "${att2}" -ge "${MAXATT}" ]; then
        row_set "${id}" "SKIPPED" "${att2}" "${SLURM_JOB_ID:-local}" \
          "oracle mismatch after ${att2} attempts, artefact never accepted: ${reason}"
        state_row "${id}" SKIPPED "${att2}" "${wall}" "oracle-mismatch" "${SLURM_JOB_ID:-local}" "train.oracle-mismatch"
        say "TASK SKIPPED ${id} train.oracle-mismatch after ${att2} attempts (queue advances)"
      else
        row_set "${id}" "TODO" "${att2}" "${SLURM_JOB_ID:-local}" \
          "oracle mismatch on attempt ${att2}/${MAXATT} (${reason}); artefact withheld, retrying"
        state_row "${id}" TODO "${att2}" "${wall}" "oracle-mismatch" "${SLURM_JOB_ID:-local}" "train.oracle-mismatch-retry"
        say "TASK RETRY ${id} train.oracle-mismatch attempt ${att2}/${MAXATT} - artefact withheld"
      fi
      ;;
    124)
      if [ "${att2}" -ge "${MAXATT}" ]; then
        row_set "${id}" "SKIPPED" "${att2}" "${SLURM_JOB_ID:-local}" \
          "per-task timeout after ${TASK_TIMEOUT}s on ${att2} attempts"
        state_row "${id}" SKIPPED "${att2}" "${wall}" "timeout" "${SLURM_JOB_ID:-local}" "train.timeout"
        say "TASK SKIPPED ${id} train.timeout after ${att2} attempts"
      else
        row_set "${id}" "TODO" "${att2}" "${SLURM_JOB_ID:-local}" \
          "per-task timeout on attempt ${att2}/${MAXATT}; requeued"
        state_row "${id}" TODO "${att2}" "${wall}" "timeout" "${SLURM_JOB_ID:-local}" "train.timeout-retry"
        say "TASK RETRY ${id} train.timeout attempt ${att2}/${MAXATT}"
      fi
      ;;
    *)
      # a node-level CUDA failure follows the node, not the data: exclude it so
      # the retry lands elsewhere (and it still costs an attempt).
      case "${brn}" in
        hw.cuda-busy) note_exclude_node "$(hostname)" "cuda-busy" ;;
        hw.oom-halved) say "TASK RETRY ${id} hw.oom-halved: --encoder-batch-size halved for the retry" ;;
        *) ;;
      esac
      if [ "${att2}" -ge "${MAXATT}" ]; then
        row_set "${id}" "SKIPPED" "${att2}" "${SLURM_JOB_ID:-local}" \
          "skipped after ${att2} failed attempts; last branch=${brn} reason: ${reason:-rc=${rc}}"
        state_row "${id}" SKIPPED "${att2}" "${wall}" "n/a" "${SLURM_JOB_ID:-local}" \
          "skip.attempts-exhausted"
        say "TASK SKIPPED ${id} skip.attempts-exhausted after ${att2}: ${reason:-rc=${rc}}"
      else
        row_set "${id}" "TODO" "${att2}" "${SLURM_JOB_ID:-local}" \
          "attempt ${att2} failed (rc=${rc}) branch=${brn}: ${reason:-unknown}; will retry"
        state_row "${id}" TODO "${att2}" "${wall}" "n/a" "${SLURM_JOB_ID:-local}" "${brn}"
        say "TASK RETRY ${id} attempt ${att2} failed rc=${rc} branch=${brn} reason=${reason:-unknown}"
      fi
      ;;
  esac
  release_claim "${id}"

  # ---- smoke abort: a never-exercised adapter must not burn 12 attempts -----
  # Per ARM: the arm whose first cell just failed is skipped wholesale, and the
  # lane continues with the next arm. QUEUE_SMOKE_ABORT=2 additionally kills the
  # lane (right for a single-arm lane, wrong for a mixed part-two lane).
  if [ "${SMOKE_ABORT}" != "0" ] && [ "${kind}" = "llm_cell" ] && [ "${rc}" != "0" ]; then
    if ! arm_has_done_cell "${model}"; then
      smoke_abort_arm "${model}" "adapter-failed: first cell ${id} rc=${rc} branch=${brn} ${reason}"
      [ "${SMOKE_ABORT}" = "2" ] && ABORT_LANE=1
    fi
  fi
  return 0
}

arm_has_done_cell() {   # $1 = model hf id ; 0 iff an earlier cell of this arm is DONE
  awk -F'\t' -v m="$1" 'NR>1 && $2=="llm_cell" && $3==m && $8=="DONE"{f=1} END{exit !f}' "${QUEUE}"
}

smoke_abort_arm() {   # $1 = model hf id, $2 = reason
  local m=$1 why=$2
  exec 206>>"${LOCK}"
  flock 206
  awk -F'\t' -v OFS='\t' -v m="${m}" -v why="${why}" '
    NR==1 {print; next}
    $2=="llm_cell" && $3==m && ($8=="TODO"||$8=="BLOCKED_MISSING_WEIGHTS"||$8=="RUNNING") {
      $8="SKIPPED"; $11="SKIPPED reason=adapter-failed - " why; print; next }
    {print}
  ' "${QUEUE}" > "${QUEUE}.tmp.$$" && mv -f "${QUEUE}.tmp.$$" "${QUEUE}"
  flock -u 206
  exec 206>&-
  say "SMOKE ABORT: every remaining cell of ${m} -> SKIPPED reason=adapter-failed (${why})"
}

# ---- re-arm the F1-F5 rows after new cells landed (atomic, locked) --------
rearm_finalise() {
  local why=$1
  exec 202>>"${LOCK}"
  flock 202
  awk -F'\t' -v OFS='\t' -v why="${why}" -v kinds=" ${FINALISE_KINDS} " '
    NR==1 {print; next}
    (index(kinds, " " $2 " ")>0) && $8=="DONE" { $8="TODO"; $11="re-armed after " why; n++ ; print; next }
    {print}
  ' "${QUEUE}" > "${QUEUE}.tmp.$$" && mv -f "${QUEUE}.tmp.$$" "${QUEUE}"
  flock -u 202
  exec 202>&-
  CELLS_SINCE_FINAL=0
  FINALISE_DUE=0
  say "re-armed F1-F5 finalisation after ${why}"
}

# ---- one full finalisation pass (F1 -> F5 order), used at drain/HALT/end ---
finalise_pass() {   # $1 = reason, [$2 = order override]
  local why=$1 order=${2:-${FINALISE_ORDER}} k id st ran=0
  say "FINALISATION PASS (${why}): ${order}"
  rearm_finalise_all "${why}"
  for k in ${order}; do
    id=$(awk -F'\t' -v k="${k}" 'NR>1 && $2==k {print $1; exit}' "${QUEUE}")
    [ -n "${id}" ] || { say "  kind ${k}: no queue row"; continue; }
    st=$(awk -F'\t' -v id="${id}" 'NR>1 && $1==id {print $8}' "${QUEUE}")
    run_task "${id}"
    ran=$((ran+1))
  done
  say "FINALISATION PASS done: ${ran} task(s) attempted"
  FINALISE_DONE_AT_END=1
}

rearm_finalise_all() {
  local why=$1
  exec 202>>"${LOCK}"
  flock 202
  awk -F'\t' -v OFS='\t' -v why="${why}" -v kinds=" ${FINALISE_KINDS} " '
    NR==1 {print; next}
    (index(kinds, " " $2 " ")>0) && ($8=="DONE" || $8=="TODO" || $8=="SKIPPED" || $8=="FAILED") { $8="TODO"; $11="re-armed for " why; print; next }
    {print}
  ' "${QUEUE}" > "${QUEUE}.tmp.$$" && mv -f "${QUEUE}.tmp.$$" "${QUEUE}"
  flock -u 202
  exec 202>&-
}

# ---- GAP 3: measure, project, degrade ------------------------------------
cost_guard() {   # $1 = trigger
  [ "${CPU_ONLY}" = "1" ] && return 0
  [ -x "${PY_HPC}" ] || return 0
  local out rc ndef
  out=$(cd "${QDIR}" && timeout 300 "${PY_HPC}" -u "${QDIR}/cost_model.py" --apply 2>&1)
  rc=$?
  printf '%s\n' "${out}" | sed 's/^/    [cost] /' >> "${EVENTS}"
  ndef=$(printf '%s\n' "${out}" | grep -c 'DEFER ' || true)
  say "COST GUARD (${1}) rc=${rc}: projection written to queue_state.tsv + cost_projection.txt; deferred_arms=${ndef:-0}"
  [ "${rc}" -ne 0 ] && say "COST GUARD failed rc=${rc} (advisory only - work continues)"
  COST_APPLIED=1
  return 0
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
      # QOS: stingy is MaxSubmitJobsPerUser=1, so a running job cannot queue a
      # successor. `scontrol requeue` keeps the id and resets Elapsed (measured).
      scontrol requeue "${SLURM_JOB_ID}" >> "${EVENTS}" 2>&1
      sleep 3
      st=$(job_state "${SLURM_JOB_ID}")
      case "${st}" in PENDING|REQUEUED|RESUBMITTED|RUNNING|CONFIGURING) ok=1 ;; esac
      if [ "${ok}" = "1" ]; then
        say "SELF-REQUEUE VERIFIED: job ${SLURM_JOB_ID} state=${st} (same id, fresh wall) -> gen=$((GEN+1))"
        return 0
      fi
      say "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      say "!! SELF-REQUEUE FAILED on ${PART}: job ${SLURM_JOB_ID} state='${st:-gone}'"
      say "!! The tiny watcher must resubmit this lane; it polls runner_s${STRIPE}.job"
      say "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      return 1 ;;
    *)
      local -a a=(--parsable --partition="${PART}" --cpus-per-task=8 --mem=48G
                  --time="$(( WALL / 3600 )):00:00" --requeue
                  --dependency="afterany:${SLURM_JOB_ID}"
                  --export="ALL,QUEUE_STRIPE=${STRIPE},QUEUE_PARTITION=${PART},QUEUE_CPU_ONLY=${CPU_ONLY},QUEUE_ALLOW_CPU_KINDS=${ALLOW_CPU},QUEUE_WALL_SECONDS=${WALL}")
      case "${PART}" in
        gpu_a100|stingy) a+=(--gres=gpu:a100:1 --exclude="$(exclude_list)") ;;
      esac
      out=$(sbatch "${a[@]}" "${SELF}" 2>&1)
      sid=${out%%;*}
      if printf '%s' "${sid}" | grep -qE '^[0-9]+$' && scontrol show job "${sid}" > /dev/null 2>&1; then
        say "SUCCESSOR REGISTERED: job ${sid} dependency=afterany:${SLURM_JOB_ID} (stripe ${STRIPE}, ${PART})"
        printf '%s\n' "${sid}" >> "${QDIR}/runner_s${STRIPE}.job"
        return 0
      fi
      say "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      say "!! SUCCESSOR SUBMISSION FAILED on ${PART}: ${out}"
      say "!! The tiny watcher must resubmit this lane"
      say "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
      return 1 ;;
  esac
}

chain_dead() {
  printf '%s %s\n' "$(date '+%F %T')" "$1" > "${QDIR}/CHAIN_DEAD"
  say "CHAIN_DEAD written ($1)"
}

# ============================ SINGLE WRITER ================================
#: cheap identity of the on-disk cell population: count + newest mtime. The
#: writer rebuilds only when this changes, so an idle poll is ~1 s of `ls`.
cell_signature() {
  local ne na nm newest
  ne=$(ls -1 "${RUNS_EXPANDED}"/*/pred_*.npz 2>/dev/null | wc -l)
  na=$(ls -1 "${RUNS_AUTHOR}"/L*_all7/pred_*.npz 2>/dev/null | wc -l)
  nm=$(ls -1 "${RUNS_AUTHOR}/.miflu_verify" 2>/dev/null | wc -l)
  # The newest-mtime term must EXCLUDE the MIFlu cells, because F1 (the import)
  # rewrites those files on every pass. Including them made the signature change
  # after every cycle, which re-armed the writer and produced an endless rebuild
  # loop instead of a 1 s no-op.
  newest=$(find "${RUNS_EXPANDED}" -maxdepth 2 -name 'pred_*.npz' \
             -not -path '*miflu_L*' -printf '%T@\n' 2>/dev/null \
           | sort -n | tail -1 | cut -d. -f1)
  printf 'exp=%s all7=%s markers=%s newest=%s' "${ne}" "${na}" "${nm}" "${newest:-0}"
}

do_writer_loop() {
  local sig last="" t0 el todo blk
  t0=$(date +%s)
  # The writer is the ONLY F1-F5 executor, and it holds this lock for its whole
  # life: a second writer can never start, so paper_tables/ has exactly one
  # writer process all night.
  exec 205>>"${QDIR}/.writer.lock"
  if ! flock -n 205; then
    say "WRITER: another writer holds .writer.lock - exiting (single-writer invariant)"
    exit 0
  fi
  say "WRITER pid=$$ job=${SLURM_JOB_ID:-local} is the ONLY F1-F5 executor (poll=${WRITE_POLL}s, max=${WRITE_MAX}s)"
  while :; do
    if [ -f "${HALT}" ]; then
      say "WRITER: HALT present (term.halt) - final pass then exit"
      finalise_pass "HALT"
      echo done > "${QDIR}/runner_sw.halted"
      exit 0
    fi
    date +%s > "${QDIR}/runner_sw.alive"
    sig=$(cell_signature)
    if [ "${sig}" != "${last}" ]; then
      say "WRITER: cell signature ${sig} (was '${last}') -> rebuilding (pid=$$)"
      # per cycle: import -> oracle -> full analysis chain -> verify/freeze.
      # F5 is the per-LLM-group refresh and is folded into the drain pass, because
      # F3 already rebuilds every table and figure for every arm present.
      finalise_pass "writer: cell signature changed" \
        "f1_import_miflu f2_miflu_oracle f3_analysis_chain f4_verify"
      last="${sig}"
      date +%s > "${QDIR}/runner_sw.alive"
    fi
    todo=$(global_count TODO)
    blk=$(missing_weights_count)
    if [ "${todo}" -eq 0 ] && [ "${blk}" -eq 0 ]; then
      say "WRITER: term.drained (nothing TODO, nothing BLOCKED) - final pass then exit"
      finalise_pass "writer: drained"
      echo done > "${QDIR}/COMPLETE"
      echo done > "${QDIR}/runner_sw.done"
      echo "0 $(date +%s)" > "${QDIR}/runner_sw.idle"
      exit 0
    fi
    if [ "${WRITER_ONCE}" = "1" ]; then
      say "WRITER: --writer-once done (${todo} TODO / ${blk} BLOCKED remain for the compute lanes)"
      echo done > "${QDIR}/runner_sw.done"
      exit 0
    fi
    el=$(( $(date +%s) - t0 ))
    if [ "${el}" -ge "${WRITE_MAX}" ]; then
      say "WRITER: lifetime ${el}s >= ${WRITE_MAX}s - final pass, then self-requeue"
      finalise_pass "writer: lifetime cap" "f1_import_miflu f2_miflu_oracle f3_analysis_chain f4_verify f5_llm_import"
      # keep the writer alive for the whole sleep: requeue keeps the job id and
      # resets Elapsed (measured on job 719816), and re-enters the queue -- which
      # is why the watchdog also knows this lane and will resubmit if it dies.
      scontrol requeue "${SLURM_JOB_ID}" >> "${EVENTS}" 2>&1
      sleep 3
      st=$(job_state "${SLURM_JOB_ID}")
      case "${st}" in
        PENDING|REQUEUED|RESUBMITTED|RUNNING|CONFIGURING)
          say "WRITER SELF-REQUEUE VERIFIED job=${SLURM_JOB_ID} state=${st}"; exit 0 ;;
      esac
      say "WRITER: self-requeue failed (state='${st:-gone}') - exiting for the watchdog"
      exit 0
    fi
    sleep "${WRITE_POLL}"
  done
}

do_claim_test() {   # $1 = task id : proves the claim is atomic across processes
  local id=$1
  if claim_task "${id}"; then
    echo "CLAIMED ${id} by pid=$$ job=${SLURM_JOB_ID:-local}"
    sleep "${QUEUE_CLAIM_HOLD:-3}"
    release_claim "${id}"
    exit 0
  fi
  echo "ALREADY-CLAIMED ${id} (pid=$$ refused)"
  exit 5
}

# ================================ MAIN =====================================
[ "${MODE}" = "dry-run" ]  && { do_dry_run;  exit $?; }
[ "${MODE}" = "selftest" ] && { do_selftest; exit $?; }
[ "${MODE}" = "claim-test" ] && { DEADLINE=$(deadline_epoch); do_claim_test "${CLAIM_ID:?}"; }
[ "${MODE}" = "writer" ] && {
  DEADLINE=$(( $(date +%s) + WRITE_MAX ))
  CELLS_DONE=0; CELLS_SINCE_FINAL=0; FINALISE_DUE=1
  FINALISE_DONE_AT_END=0; COST_APPLIED=1; NTASKS=0
  say "START writer pid=$$ part=${PART} job=${SLURM_JOB_ID:-local} deadline=$(date -d "@${DEADLINE}" '+%F %T')"
  do_writer_loop; exit $?
}

if [ "${SELFTEST}" != "1" ]; then
  [ -n "${STRIPE}" ] || die "QUEUE_STRIPE must be set for a real run (0, 1, or cpu with QUEUE_CPU_ONLY=1; --dry-run prints the split)"
  { [ "${STRIPE}" = "0" ] || [ "${STRIPE}" = "1" ] || { [ "${STRIPE}" = "cpu" ] && [ "${CPU_ONLY}" = "1" ]; }; } \
    || die "QUEUE_STRIPE must be 0, 1, or cpu (cpu requires QUEUE_CPU_ONLY=1)"
fi

if [ -f "${HALT}" ]; then
  say "HALT present (term.halt) - exiting at the task boundary"
  if [ "${WRITE_ONLY}" = "1" ]; then
    DEADLINE=$(deadline_epoch); CELLS_DONE=0; CELLS_SINCE_FINAL=0
    FINALISE_DUE=1; FINALISE_DONE_AT_END=0; COST_APPLIED=1
    finalise_pass "HALT"
  fi
  echo done > "${QDIR}/runner_s${STRIPE}.halted"
  exit 0
fi

say "START gen=${GEN} host=$(hostname) node=${SLURM_NODELIST:-?} part=${PART} wall=${WALL}s slack=${SLACK}s cpu_only=${CPU_ONLY} finalise_every=${FINALISE_EVERY}"

if [ "${HW_ASSERT}" = "1" ] && [ "${CPU_ONLY}" != "1" ]; then
  "${PY_HPC}" - <<'PYEOF'
import sys
import torch
if not torch.cuda.is_available():
    print("[a100] FATAL: no CUDA device"); sys.exit(3)
name = torch.cuda.get_device_name(0)
cap = torch.cuda.get_device_capability(0)
vram = torch.cuda.get_device_properties(0).total_memory / 2**30
print("[a100] MEASURED gpu=%s capability=%s vram=%.1fGiB" % (name, cap, vram))
if "A100" not in name:
    print("[a100] FATAL: expected an A100, got %r; a non-A100 cell would confound "
          "the benchmark (rules 12-13). Refusing to work." % (name,))
    sys.exit(4)
PYEOF
  if [ $? -ne 0 ]; then
    say "HARDWARE ASSERTION FAILED (hw.not-a100) - aborting this allocation, no cell touched"
    chain_dead "hardware-assert-failed on $(hostname)"
    exit 1
  fi
fi

DEADLINE=$(deadline_epoch)
say "deadline=$(date -d "@${DEADLINE}" '+%F %T') = ${WALL}s wall - ${SLACK}s slack; cpus=$(nproc)"
harvest_down_nodes
reset_running

CELLS_DONE=0
CELLS_SINCE_FINAL=0
FINALISE_DUE=0
FINALISE_DONE_AT_END=0
COST_APPLIED=0
NTASKS=0

while :; do
  if [ -f "${HALT}" ]; then
    say "HALT appeared (term.halt) - exiting at the task boundary"
    if [ "${WRITE_ONLY}" = "1" ]; then finalise_pass "HALT"; fi
    echo done > "${QDIR}/runner_s${STRIPE}.halted"
    exit 0
  fi
  date +%s > "${QDIR}/runner_s${STRIPE}.alive"

  if [ "${MAXTASKS}" -gt 0 ] && [ "${NTASKS}" -ge "${MAXTASKS}" ]; then
    say "MAXTASKS=${MAXTASKS} reached - stopping this generation"
    continue_chain "max-tasks reached"; exit $?
  fi

  ID=$(pick_next || true)
  if [ -z "${ID}" ]; then
    local_todo=$(global_count TODO)
    local_blk=$(missing_weights_count)
    local_defer=$(global_count DEFERRED_COST)
    local_skip=$(global_count SKIPPED)
    local_fail=$(global_count FAILED)
    local_own=$(own_todo_count)

    # ---- GAP 1: the WRITER finalises once when the queue drains ----------
    # Compute lanes never do this: they are cell producers only (single writer).
    if [ "${FINALISE_DONE_AT_END}" != "1" ] && [ "${WRITE_ONLY}" = "1" ]; then
      finalise_pass "queue drained"
      continue
    fi
    if [ "${CPU_ONLY}" = "1" ]; then
      say "CPU worker: no llm_probe rows left (${local_todo} TODO / ${local_blk} BLOCKED remain for the GPU lanes)"
      echo done > "${QDIR}/runner_scpu.done"
      echo "0 $(date +%s)" > "${QDIR}/runner_scpu.idle"
      exit 0
    fi

    if [ "${local_todo}" -eq 0 ] && [ "${local_blk}" -eq 0 ]; then
      say "TERM term.drained: nothing TODO and nothing BLOCKED anywhere; finalised; no successor"
      echo done > "${QDIR}/COMPLETE"; echo done > "${QDIR}/runner_s${STRIPE}.done"
      echo "0 $(date +%s)" > "${QDIR}/runner_s${STRIPE}.idle"
      say "SUMMARY cells_done=${CELLS_DONE} skipped=${local_skip} failed=${local_fail} deferred=${local_defer} BLOCKED=${local_blk}"
      exit 0
    fi
    if [ "${local_own}" -eq 0 ] && [ "${local_todo}" -gt 0 ]; then
      # every remaining TODO belongs to the other lane: burning a GPU slot here
      # would only delay that lane. Record it and stand down cleanly.
      say "TERM term.idle-no-work: my lane has nothing left (${local_todo} TODO belongs to the other stripe; ${local_blk} BLOCKED)"
      echo "0 $(date +%s)" > "${QDIR}/runner_s${STRIPE}.idle"
      echo done > "${QDIR}/runner_s${STRIPE}.done"
      exit 0
    fi
    if [ "$(date +%s)" -ge "${DEADLINE}" ]; then
      if continue_chain "wall-clock guard; ${local_todo} TODO / ${local_blk} BLOCKED remain"; then exit 0; fi
      chain_dead "wall-clock guard and no successor on ${PART}"
      exit 1
    fi
    if [ "${IDLE_POLL}" -gt 0 ]; then
      say "nothing runnable in my scope (${local_todo} TODO globally, ${local_blk} BLOCKED, ${local_defer} DEFERRED, ${local_skip} SKIPPED) - re-scanning in ${IDLE_POLL}s"
      sleep "${IDLE_POLL}"
      continue
    fi
    say "TERM term.idle-no-work: nothing runnable in my scope and idle-wait disabled"
    echo "0 $(date +%s)" > "${QDIR}/runner_s${STRIPE}.idle"
    echo done > "${QDIR}/runner_s${STRIPE}.done"
    exit 0
  fi

  if [ "$(date +%s)" -ge "${DEADLINE}" ]; then
    if continue_chain "wall-clock guard before ${ID}"; then exit 0; fi
    chain_dead "wall-clock guard before ${ID}"
    exit 1
  fi

  run_task "${ID}"
  NTASKS=$((NTASKS + 1))

  if [ "${ABORT_LANE}" = "1" ]; then
    say "LANE ABORT (smoke test failed): exiting cleanly so the watchdog does not respawn a doomed lane"
    echo "0 $(date +%s)" > "${QDIR}/runner_s${STRIPE}.idle"
    echo done > "${QDIR}/runner_s${STRIPE}.done"
    exit 0
  fi

  # GAP 3: after the first completed LLM cell (and every 4th thereafter) turn
  # the measurement into a projection and, if needed, a logged degradation.
  if [ "${COST_APPLIED}" = "0" ] && [ "${CELLS_DONE}" -ge 1 ]; then
    cost_guard "first completed cell"
  elif [ "${CELLS_DONE}" -gt 0 ] && [ $(( CELLS_DONE % 4 )) -eq 0 ]; then
    cost_guard "every 4 completed cells"
  fi
done
