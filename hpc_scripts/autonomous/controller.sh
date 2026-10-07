#!/bin/bash
# ============================================================================
# controller.sh — persistent login-node controller for the innovation autonomy.
#
# Policy: HPC_GUIDE.md §3b / §11 explicitly allow a "background auto-submit loop"
# on the login node. This script IS that loop. It requests NO GPU; it only polls
# `squeue` / `sacct` and issues `sbatch`, one job at a time, waiting for a
# terminal state before the next. It therefore never occupies the single stingy
# slot (which the chain-driver `submit_innovation_pilot.sh` would otherwise
# consume — see decision_log D1).
#
# Implements the 12 hard requirements of the persistent-overnight contract:
#   1 single-instance lock          9 resume without duplicate submission
#   2 record job id before polling  10 never beyond authorized ceiling
#   3 at most one job at a time     11 heartbeat + current_state.json
#   4 poll terminal Slurm state     12 copy back durable artifacts
#   5 validate artifacts first       + per-stage budgeting / Test gate
#   6 fail-stop on defect
#   7 never silently retry
#   8 append-only ledger
#
# Launch (login node, NOT as an #SBATCH job):
#   export INNOVATION_DEPLOYMENT_ROOT=/path/to/isolated/root
#   nohup bash hpc_scripts/autonomous/controller.sh > controller.log 2>&1 &
# ============================================================================
set -u
export DRYRUN="${DRYRUN:-0}"

# ── paths ──────────────────────────────────────────────────────────────────────
AUTON_DIR="$(cd "$(dirname "$0")" && pwd)"
STATE_PY="$AUTON_DIR/state.py"

: "${INNOVATION_DEPLOYMENT_ROOT:?set INNOVATION_DEPLOYMENT_ROOT to the isolated deployment root}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"
export DEPLOYMENT_ROOT

PARTITION="${INNOVATION_PARTITION:-stingy}"
export PARTITION

AC_DIR="$DEPLOYMENT_ROOT/results/innovation/autonomous_completion"
PLAN="$AC_DIR/stage_plan.json"
JOB_LEDGER="$AC_DIR/job_ledger.csv"
CURRENT_STATE="$AC_DIR/current_state.json"
BUDGET_LEDGER="$AC_DIR/budget_ledger.csv"
COMPLETION_MATRIX="$AC_DIR/completion_matrix.json"
FREEZE_AUDIT="$AC_DIR/freeze_audit.json"
LOCK="$AC_DIR/.controller.lock"
DURABLE_ROOT="${INNOVATION_DURABLE_ROOT:-$HOME/innovation_durable}"
export DURABLE_ROOT

CONTROLLER_PID="$$"
export CONTROLLER_PID CURRENT_STATE JOB_LEDGER BUDGET_LEDGER FREEZE_AUDIT COMPLETION_MATRIX DRYRUN

# ── source helpers ─────────────────────────────────────────────────────────────
# shellcheck source=lib.sh
. "$AUTON_DIR/lib.sh"

# ── single-instance lock (requirement 1) ──────────────────────────────────────
exec 9>"$LOCK"
acquire_lock

CEILING="$(python3 -c "import json;print(json.load(open('$PLAN'))['authorization_ceiling'])")"
echo "[controller] started pid=$CONTROLLER_PID deployment=$DEPLOYMENT_ROOT partition=$PARTITION ceiling=$CEILING dryrun=$DRYRUN"

# ── dry-run: enumerate the full authorized sequence without submitting ──────────
if [ "$DRYRUN" = "1" ]; then
  echo "[controller][DRY-RUN] authorized sequence (ceiling=$CEILING):"
  python3 "$STATE_PY" plan-sequence --plan "$PLAN" --ledger "$JOB_LEDGER" --ceiling "$CEILING"
  echo "[controller][DRY-RUN] no jobs submitted. Exiting."
  exit 0
fi

# ── main loop ──────────────────────────────────────────────────────────────────
LAST_STAGE=""
LAST_JOB_KEY=""
while true; do
  heartbeat "${LAST_STAGE:-boot}" "${LAST_JOB_KEY:-none}"

  NEXT="$(python3 "$STATE_PY" next-job --plan "$PLAN" --ledger "$JOB_LEDGER" --ceiling "$CEILING")"
  if echo "$NEXT" | grep -q '^RESULT=NONE'; then
    echo "[controller] no pending authorized jobs up to ceiling '$CEILING' — authorized work complete"
    # if Test is the only remaining stage and the gate is open, note it explicitly
    break
  fi

  STAGE_KEY="$(echo "$NEXT"   | grep '^STAGE_KEY='  | cut -d= -f2-)"
  JOB_KEY="$(echo "$NEXT"     | grep '^JOB_KEY='    | cut -d= -f2-)"
  STAGE_MODE="$(echo "$NEXT"  | grep '^STAGE_MODE=' | cut -d= -f2-)"
  RUN_ID="$(echo "$NEXT"      | grep '^RUN_ID='     | cut -d= -f2-)"
  RUN_PREFIX="$(echo "$NEXT"  | grep '^RUN_PREFIX=' | cut -d= -f2-)"
  ARGS="$(echo "$NEXT"        | grep '^ARGS='       | cut -d= -f2-)"
  MODEL="$(echo "$ARGS"  | cut -d' ' -f1)"
  ENC="$(echo "$ARGS"   | cut -d' ' -f2)"
  FUSION="$(echo "$ARGS" | cut -d' ' -f3)"
  L="$(echo "$ARGS"      | cut -d' ' -f4)"
  SEED="$(echo "$ARGS"   | cut -d' ' -f5)"
  EPOCHS="$(echo "$ARGS" | cut -d' ' -f6)"
  STAGE="$(echo "$ARGS"  | cut -d' ' -f7)"

  # ── one-time Test gate (requirement: Test NEVER runs just because time remains)
  if [ "$STAGE_KEY" = "L" ]; then
    GATE="$(python3 "$STATE_PY" gate --completion "$COMPLETION_MATRIX" --freeze-audit "$FREEZE_AUDIT")"
    if ! echo "$GATE" | grep -q '^GATE=open'; then
      fail_stop "TEST_GATE_CLOSED: completion matrix unresolved or freeze audit failed; will not launch Test"
    fi
  fi

  # ── per-stage budgeting when a NEW stage begins (record queued/deferred) ──────
  if [ "$STAGE_KEY" != "$LAST_STAGE" ]; then
    JOB_COUNT="$(python3 -c "import sys; sys.path.insert(0,'$AUTON_DIR'); from state import load_stage_plan,get_stage,generate_stage_jobs; print(len(generate_stage_jobs(get_stage(load_stage_plan('$PLAN'),'$STAGE_KEY'))))")"
    AVG_MIN=30
    STORAGE="$(df -P "$DEPLOYMENT_ROOT" 2>/dev/null | awk 'NR==2{printf "%.1f",$4/1024/1024}')"
    QUEUE_OK=1
    SRC_VER="$(python3 -c "import json;print(json.load(open('$PLAN'))['implementation_source_version'])")"
    REQ_VER="$SRC_VER"
    DEPS_OK=1
    BUDGET="$(python3 "$STATE_PY" budget --job-count "$JOB_COUNT" --avg-min "$AVG_MIN" \
        --storage-gb "$STORAGE" --queue-ok "$QUEUE_OK" --source-ver "$SRC_VER" \
        --req-ver "$REQ_VER" --deps-ok "$DEPS_OK" --repair-used 0 --repair-max 4 \
        --amend-used 0 --amend-max 1)"
    WITHIN="$(echo "$BUDGET" | grep '^WITHIN_LIMITS=' | cut -d= -f2)"
    GPUH="$(echo "$BUDGET" | grep '^gpu_hours_estimate=' | cut -d= -f2)"
    write_budget "$STAGE_KEY" "$WITHIN" "$JOB_COUNT" "$GPUH" "$STAGE_MODE"
    if [ "$WITHIN" != "yes" ]; then
      fail_stop "STAGE_BUDGET_EXCEEDED: stage $STAGE_KEY does not fit authorization (within=$WITHIN); recorded as deferred"
    fi
    LAST_STAGE="$STAGE_KEY"
  fi

  # ── local (non-Slurm) stage: A verify / K freeze ─────────────────────────────
  if [ "$STAGE_MODE" = "local" ]; then
    echo "[controller] local stage $STAGE_KEY ($JOB_KEY)"
    run_local_stage "$STAGE_KEY" || fail_stop "LOCAL_STAGE_FAILED: $STAGE_KEY"
    # record the gate as COMPLETED so resume skips it (local gates are
    # deterministic and idempotent, but must not re-run on every restart)
    append_ledger "LOCAL-$STAGE_KEY" "$STAGE_KEY" "local" "na" "na" \
      "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "COMPLETED" "0:0" "" "$RUN_ID" "KEY=$JOB_KEY"
    echo "[controller] local stage $STAGE_KEY OK"
    heartbeat "$STAGE_KEY" "$JOB_KEY"
    LAST_JOB_KEY="$JOB_KEY"
    continue
  fi

  # ── slurm stage: ensure the single slot is free BEFORE submitting (req 3) ─────
  if ! squeue_empty; then
    echo "[controller] waiting for the single $PARTITION slot to free"
    for ((w=0; w<240; w++)); do squeue_empty && break; sleep 60; done
    if ! squeue_empty; then
      fail_stop "STINGY_SLOT_BLOCKED: could not obtain the single slot within the wait window"
    fi
  fi

  # ── submit a SINGLE job, recording the id BEFORE polling (req 2 & 3) ─────────
  cd "$DEPLOYMENT_ROOT"
  JOBID="$(INNOVATION_DEPLOYMENT_ROOT="$DEPLOYMENT_ROOT" CONFIRM_INNOVATION_SUBMIT=YES \
            sbatch --parsable hpc_scripts/innovation_worker.sh $ARGS)"
  if [ -z "$JOBID" ]; then
    fail_stop "SUBMIT_FAILED: sbatch returned no job id for $JOB_KEY"
  fi
  append_ledger "$JOBID" "$STAGE_KEY" "$MODEL" "$L" "$SEED" \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "PD" "" "" "$RUN_ID" "KEY=$JOB_KEY"
  echo "[controller] submitted stage=$STAGE_KEY job=$JOBID key=$JOB_KEY run_id=$RUN_ID"

  # ── poll terminal state (requirement 4) ───────────────────────────────────────
  RESULT="$(poll_terminal "$JOBID")"
  STATE="${RESULT%%|*}"; EC="${RESULT##*|}"
  NODE="$(sacct -j "$JOBID" -X -n -o NodeList 2>/dev/null | head -n1 | tr -d ' ')"
  set_ledger_state "$JOBID" "$STATE" "$EC" "$NODE"
  if [ "$STATE" != "COMPLETED" ] || [ "${EC%%:*}" != "0" ]; then
    fail_stop "JOB_FAILED: key=$JOB_KEY job=$JOBID state=$STATE exit=$EC"
  fi

  # ── validate artifacts before advancing (requirements 5 & 6) ──────────────────
  # The runner's run_id embeds a UTC timestamp + git sha, so the exact directory
  # cannot be predicted at submit time. Resolve it by the deterministic PREFIX
  # (dataset__model__encoder__fusion__L{h}__seed{s}) and take the NEWEST match
  # (so a prior failed attempt's directory is never mistaken for this run's).
  RUN_DIR=""
  if [ -n "$RUN_PREFIX" ]; then
    RUN_DIR="$(python3 "$STATE_PY" resolve-run \
        --runs-root "$DEPLOYMENT_ROOT/results/innovation/runs" \
        --prefix "$RUN_PREFIX" --stage "$STAGE" | grep '^RUN_DIR=' | cut -d= -f2-)"
  fi
  if [ -z "$RUN_DIR" ] || [ "$RUN_DIR" = "NONE" ]; then
    fail_stop "ARTIFACT_VALIDATION_FAILED: key=$JOB_KEY reason=run_dir_not_found prefix=$RUN_PREFIX stage=$STAGE"
  fi
  RUN_ID="$(basename "$RUN_DIR")"
  MANIFEST_AGG="$(python3 -c "import json;print(json.load(open('$DEPLOYMENT_ROOT/results/innovation/source_snapshot_manifest.json'))['aggregate_sha256'])")"
  VAL="$(python3 "$STATE_PY" validate-run --run-dir "$RUN_DIR" \
      --manifest-aggregate "$MANIFEST_AGG" --expected-stage "$STAGE")"
  if ! echo "$VAL" | grep -q '^OK=yes'; then
    REASON="$(echo "$VAL" | grep '^reason=' | cut -d= -f2-)"
    fail_stop "ARTIFACT_VALIDATION_FAILED: key=$JOB_KEY reason=$REASON"
  fi

  # ── copy essential scratch artifacts back to durable storage (requirement 12) ──
  LAST_JOB_ID="$JOBID" copy_back "$RUN_ID"

  heartbeat "$STAGE_KEY" "$JOB_KEY"
  LAST_JOB_KEY="$JOB_KEY"
  echo "[controller] advanced past $JOB_KEY (ok)"
done

echo "[controller] controller loop ended cleanly at $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
