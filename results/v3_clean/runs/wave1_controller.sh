#!/bin/bash
# ==========================================================================
# clean-v3 Wave-1 CONTROLLER  (PREPARED — NOT LAUNCHED)
#
# Pure Bash. This script NEVER invokes python/python3, Torch, Transformers,
# model loading, preprocessing, evaluation, checkpoint restoration or bulk
# hashing on the login node. It only:
#   * submits ONE Slurm job at a time with `sbatch`
#   * polls terminal state with `sacct` / `squeue`
#   * inspects SMALL status/manifest files with grep/sed
#   * copies accepted outputs to the durable destination with `cp`
#
# Version: innov-v3.12-gate-validator-schema-alignment
# Gate:    570846 (19/19 passed)
# ==========================================================================
set -euo pipefail

RUN_KEY_LIST="${RUN_KEY_LIST:-results/v3_clean/runs/formal_execution_order_wave1.txt}"
LEDGER="${LEDGER:-results/v3_clean/runs/wave1_ledger.csv}"
LOCKDIR="${LOCKDIR:-results/v3_clean/runs/.wave1_controller.lock}"
JOBROOT="${JOBROOT:-results/v3_clean/runs}"
SCRIPTS_DIR="${SCRIPTS_DIR:-hpc_scripts/v3_clean}"
DURABLE_ROOT="${DURABLE_ROOT:-$HOME/innovation_durable/screening}"
TOKEN_FILE="${TOKEN_FILE:-results/v3_clean/runs/wave1_authorization.token}"
EXPECTED_TOTAL="${EXPECTED_TOTAL:-580}"
MAX_ROWS="${MAX_ROWS:-580}"

log() { printf '[wave1] %s\n' "$*" >&2; }
die() { log "FAIL-STOP: $*"; exit 1; }

# ---- 0. explicit future authorization token required before launch -------
[ -f "$TOKEN_FILE" ] || die "authorization token missing: $TOKEN_FILE (launch not authorized)"
[ -n "${WAVE1_AUTHORIZATION_TOKEN:-}" ] || die "WAVE1_AUTHORIZATION_TOKEN not set (launch not authorized)"
[ "$(cat "$TOKEN_FILE")" = "${WAVE1_AUTHORIZATION_TOKEN}" ] || die "authorization token mismatch"
# The token must NEVER reach a Slurm job environment, a log or an artifact.
unset WAVE1_AUTHORIZATION_TOKEN || true

# ---- 1. single-instance lock (atomic) -----------------------------------
if ! mkdir "$LOCKDIR" 2>/dev/null; then
  die "another controller instance holds the lock: $LOCKDIR"
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# ---- 2. load and validate the ordered immediate keys --------------------
[ -f "$RUN_KEY_LIST" ] || die "run-key list missing: $RUN_KEY_LIST"
mapfile -t KEYS < <(grep -v '^#' "$RUN_KEY_LIST" | grep -v '^[[:space:]]*$')
[ "${#KEYS[@]}" -eq "$EXPECTED_TOTAL" ] || die "expected $EXPECTED_TOTAL keys, got ${#KEYS[@]}"

# duplicates must be zero
DUPES=$(printf '%s\n' "${KEYS[@]}" | sort | uniq -d | wc -l)
[ "$DUPES" -eq 0 ] || die "duplicate run keys present: $DUPES"

# every key must be an immediate, non-deferred, executable row
for k in "${KEYS[@]}"; do
  case "$k" in
    *..*|*/*) die "unsafe run key: $k" ;;
  esac
  [ -f "$SCRIPTS_DIR/$k.sh" ] || die "missing Slurm script for: $k"
done

# deferred rows must never be present
for k in "${KEYS[@]}"; do
  echo "$k" | grep -q "deferred" && die "deferred row present: $k"
done

mkdir -p "$JOBROOT"
[ -f "$LEDGER" ] || printf 'run_key,job_id,state,rc\n' >> "$LEDGER"

# ---- 2b. run from the deployment root and export the row-script contract ---
export INNOVATION_DEPLOYMENT_ROOT="${INNOVATION_DEPLOYMENT_ROOT:-$PWD}"
export CONFIRM_INNOVATION_SUBMIT=YES
cd "$INNOVATION_DEPLOYMENT_ROOT"
[ -f "scripts/innovation/clean_runner.py" ] || die "not a deployment root: $PWD"
[ -f "results/v3_clean/runs/complete_specs_598.json" ] || die "registry missing"
log "deployment root: $INNOVATION_DEPLOYMENT_ROOT"

accepted_count() { awk -F, '$3=="COMPLETED" && $4=="0"{n++} END{print n+0}' "$LEDGER"; }
is_accepted()    { awk -F, -v k="$1" '$1==k && $3=="COMPLETED" && $4=="0"{f=1} END{exit !f}' "$LEDGER"; }

# NOTE: on this cluster `squeue` also prints a trailing
#   "Last update in N seconds ago"
# banner line, which a naive `| wc -l` counts as a job — that made the
# "wait for an empty queue" loop spin forever. Count NUMERIC job ids only.
active_jobs() { squeue -u "$USER" -h -o "%i" 2>/dev/null | grep -c "^[0-9]" || true; }

# ---- 3. main loop: strictly ONE active/pending job at a time ------------
SUBMITTED=0
for k in "${KEYS[@]}"; do
  A=$(accepted_count)
  [ "$A" -ge "$MAX_ROWS" ] && { log "reached $A accepted rows; stopping"; break; }
  if is_accepted "$k"; then log "already accepted, skipping: $k"; continue; fi

  # never more than one active or pending job
  while [ "$(active_jobs)" -gt 0 ]; do sleep 20; done

  JID=$(sbatch --parsable "$SCRIPTS_DIR/$k.sh")
  [ -n "$JID" ] || die "sbatch returned no job id for $k"
  printf '%s,%s,%s,%s\n' "$k" "$JID" "SUBMITTED" "" >> "$LEDGER"   # job id recorded IMMEDIATELY
  log "submitted $k -> $JID"
  SUBMITTED=$((SUBMITTED+1))

  # ---- terminal-state polling (light) ----------------------------------
  STATE=""; EXITCODE=""
  while :; do
    read -r STATE EXITCODE <<<"$(sacct -j "$JID" --format=State,ExitCode --noheader -X | head -1)"
    case "$STATE" in
      COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED) break ;;
    esac
    sleep 20
  done
  printf '%s,%s,%s,%s\n' "$k" "$JID" "$STATE" "$EXITCODE" >> "$LEDGER"

  [ "$STATE" = "COMPLETED" ] || die "deterministic failure: $k state=$STATE"
  case "$EXITCODE" in 0:0) ;; *) die "deterministic failure: $k exit=$EXITCODE" ;; esac

  # ---- small-file artifact acceptance (login-node safe) ----------------
  RD="$JOBROOT/$k"
  for f in run_status.json split_manifest.json scaler_metadata.json \
           resource_usage.json predictions/validation_predictions.csv \
           metrics/paper_aligned_full_output_metrics.json \
           metrics/ilitotal_fixed_step_metrics.json \
           metrics/ilitotal_full_horizon_metrics.json \
           metrics/pte_pie_metrics.json; do
    [ -f "$RD/$f" ] || die "artifact missing for $k: $f"
  done
  grep -q '"state": *"COMPLETED"' "$RD/run_status.json" || die "run_status not COMPLETED: $k"

  # ---- durable-copy acceptance before the next submission --------------
  DEST="$DURABLE_ROOT/$k"
  mkdir -p "$DEST"
  cp -r "$RD/." "$DEST/" 2>/dev/null || die "durable copy failed for $k"
  [ -f "$DEST/run_status.json" ] || die "durable copy incomplete for $k"
  log "accepted $k (durable copy verified)"
done

log "Wave-1 finished: accepted=$(accepted_count) submitted=$SUBMITTED"
exit 0
