#!/bin/bash
# screening_controller.sh — v3.5 formal Screening, STRICTLY SERIAL.
#
# LOGIN-NODE LIGHTWEIGHT CONTROLLER. It only:
#   submits one sbatch job, polls sacct, inspects small status/JSON/CSV files,
#   copies files, and hashes files. It NEVER imports Torch, never loads a model,
#   checkpoint or dataset, never computes metrics, and never inspects large
#   binary payloads (weight files are copied, not re-hashed here).
#
# One active Screening run at a time: submit -> record -> wait terminal ->
# verify artifacts -> copy to durable -> verify inventory -> accept -> next.
#
# Deterministic failure => stop immediately (no skip, no substitute, no impute).
# Only a proven transient scheduler/fs/node-init fault gets ONE retry.
set -uo pipefail

ROOT="${INNOVATION_DEPLOYMENT_ROOT:-/scratch/sychan552/innovation_deploy_root_v3_5}"
DURABLE=/home/sychan552/innovation_durable/screening
STATE="$DURABLE/_controller"
ORDER="$ROOT/hpc_scripts/v3_screening/screening_order.txt"
EXCLUDE=gpu-a100-05
SLEEP_POLL=20
MAX_POLL=1440          # 1440 * 20s = 8h ceiling per run (time limit is 4h)

mkdir -p "$STATE"
LEDGER="$STATE/screening_submission_ledger.jsonl"
STATUSCSV="$STATE/screening_run_status.csv"
PROGRESS="$STATE/progress.txt"
CTRLSTATE="$STATE/screening_controller_state.json"
RUNS="$ROOT/results/innovation/runs"

[ -f "$STATUSCSV" ] || echo "order,run_key,model,horizon,seed,job_id,attempt,state,exit_code,node,run_id,accepted,durable,artifacts" > "$STATUSCSV"

log() { echo "[$(date '+%F %T')] $*" >> "$PROGRESS"; }

ARTIFACTS=(
  config_resolved.yaml environment.txt git_commit.txt split_manifest.json
  scaler_metadata.json prompt_statistics_metadata.json
  checkpoints/best_val_mse.pt checkpoints/checkpoint_manifest.json
  logs/train_history.csv predictions/validation_predictions.csv
  metrics/validation_metrics.json metrics/fixed_step_metrics.json
  metrics/peak_metrics_by_season.csv run_status.json resource_usage.json
)

state_write() {
  { echo '{'
    echo "  \"updated\": \"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\","
    echo "  \"total\": $TOTAL, \"accepted\": $ACCEPTED, \"attempted\": $ATTEMPTED,"
    echo "  \"current_run_key\": \"${CUR_KEY:-}\","
    echo "  \"current_job_id\": \"${CUR_JOB:-}\","
    echo "  \"current_state\": \"${CUR_STATUS:-}\","
    echo "  \"stopped\": ${STOPPED:-false},"
    echo "  \"stop_reason\": \"${STOP_REASON:-}\","
    echo "  \"final_status\": \"${FINAL:-RUNNING}\","
    echo "  \"deployment_root\": \"$ROOT\","
    echo "  \"durable_root\": \"$DURABLE\""
    echo '}'
  } > "$CTRLSTATE.tmp" && mv "$CTRLSTATE.tmp" "$CTRLSTATE"
}

TOTAL=0
while IFS= read -r _l; do [ -n "$_l" ] && TOTAL=$((TOTAL + 1)); done < "$ORDER"
ACCEPTED=0; ATTEMPTED=0; STOPPED=false; STOP_REASON=""; FINAL=RUNNING
log "controller start: total=$TOTAL root=$ROOT"

submit_and_wait() {          # $1 = script basename, $2 = attempt number
  CUR_JOB=$(cd "$ROOT" && INNOVATION_DEPLOYMENT_ROOT="$ROOT" \
            CONFIRM_INNOVATION_SUBMIT=YES \
            sbatch --parsable --exclude="$EXCLUDE" \
            "hpc_scripts/v3_screening/$1" 2>>"$PROGRESS" | tail -n 1)
  if [ -z "${CUR_JOB:-}" ]; then CUR_STATUS="SUBMIT_FAILED"; return 1; fi
  echo "{\"utc\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"event\":\"submitted\",\"run_key\":\"$CUR_KEY\",\"script\":\"$1\",\"job_id\":\"$CUR_JOB\",\"attempt\":$2}" >> "$LEDGER"
  log "submitted $CUR_KEY job=$CUR_JOB attempt=$2"
  local n=0
  while [ $n -lt $MAX_POLL ]; do
    CUR_STATUS=$(sacct -j "$CUR_JOB" -X -n -o State 2>/dev/null | head -n 1 | tr -d ' ')
    case "$CUR_STATUS" in
      COMPLETED|FAILED|CANCELLED*|TIMEOUT|NODE_FAIL|OUT_OF_MEMORY|PREEMPTED) break ;;
    esac
    [ -z "$CUR_STATUS" ] && CUR_STATUS="UNKNOWN"
    sleep "$SLEEP_POLL"; n=$((n + 1)); state_write
  done
  CUR_EXIT=$(sacct -j "$CUR_JOB" -X -n -o ExitCode 2>/dev/null | head -n 1 | tr -d ' ')
  CUR_NODE=$(sacct -j "$CUR_JOB" -X -n -o NodeList 2>/dev/null | head -n 1 | tr -d ' ')
  log "terminal $CUR_KEY job=$CUR_JOB state=$CUR_STATUS exit=$CUR_EXIT node=$CUR_NODE"
  [ "$CUR_STATUS" = "COMPLETED" ] && [ "${CUR_EXIT%%:*}" = "0" ]
}

# frozen order: model -> horizon [24,60] -> seed [42,43,44]
while IFS= read -r script; do
  [ -z "$script" ] && continue
  base=$(basename "$script")
  CUR_KEY="${base%.sh}"
  NEW_MODEL=$(printf '%s' "$CUR_KEY" | sed -E 's/^screening_(.*)_L[0-9]+_seed[0-9]+$/\1/')
  NEW_H=$(printf '%s' "$CUR_KEY" | sed -E 's/^.*_L([0-9]+)_seed[0-9]+$/\1/')
  NEW_SEED=$(printf '%s' "$CUR_KEY" | sed -E 's/^.*_seed([0-9]+)$/\1/')
  ATTEMPTED=$((ATTEMPTED + 1))
  state_write

  # resume-safe: skip a run key that already has an accepted row
  if awk -F, -v k="$CUR_KEY" '$2==k && $12=="accepted"{f=1} END{exit !f}' "$STATUSCSV" 2>/dev/null; then
    log "skip already-accepted $CUR_KEY"; continue
  fi

  before=$(ls -1 "$RUNS" 2>/dev/null | sort)

  if ! submit_and_wait "$base" 1; then
    transient=0
    case "$CUR_STATUS" in
      NODE_FAIL|TIMEOUT|CANCELLED*|PREEMPTED|SUBMIT_FAILED) transient=1 ;;
      FAILED|OUT_OF_MEMORY) transient=0 ;;
      *) transient=0 ;;
    esac
    if [ "$transient" = "1" ]; then
      log "transient failure on $CUR_KEY ($CUR_STATUS); one retry"
      before=$(ls -1 "$RUNS" 2>/dev/null | sort)
      if ! submit_and_wait "$base" 2; then
        STOPPED=true; STOP_REASON="deterministic failure after retry: $CUR_KEY $CUR_STATUS exit=$CUR_EXIT"; break
      fi
    else
      STOPPED=true; STOP_REASON="deterministic failure: $CUR_KEY state=$CUR_STATUS exit=$CUR_EXIT"; break
    fi
  fi

  after=$(ls -1 "$RUNS" 2>/dev/null | sort)
  new=$(comm -13 <(echo "$before") <(echo "$after") | head -n 1)
  if [ -z "$new" ]; then
    STOPPED=true; STOP_REASON="no new run directory for $CUR_KEY"; break
  fi
  run_dir="$RUNS/$new"

  missing=""
  for a in "${ARTIFACTS[@]}"; do
    [ -e "$run_dir/$a" ] || missing="$missing $a"
  done
  [ -d "$run_dir/figures" ] || missing="$missing figures/"
  if [ -n "$missing" ]; then
    STOPPED=true; STOP_REASON="missing artifacts for $CUR_KEY:$missing"; break
  fi

  dst="$DURABLE/$CUR_KEY"
  mkdir -p "$dst"
  cp -r "$run_dir"/. "$dst"/ 2>>"$PROGRESS"
  mkdir -p "$dst/hpc_logs"
  cp "$ROOT/hpc_results/innovation/logs/slurm_${CUR_JOB}_${base}.out" "$dst/hpc_logs/" 2>/dev/null
  cp "$ROOT/hpc_results/innovation/logs/slurm_${CUR_JOB}_${base}.err" "$dst/hpc_logs/" 2>/dev/null

  dm=""
  for a in "${ARTIFACTS[@]}"; do
    [ -e "$dst/$a" ] || dm="$dm $a"
  done
  if [ -n "$dm" ]; then
    STOPPED=true; STOP_REASON="durable copy incomplete for $CUR_KEY:$dm"; break
  fi
  find "$dst" -type f ! -name '*.pt' -print0 2>/dev/null | xargs -0 sha256sum > "$dst/durable_sha256.txt" 2>/dev/null
  nfiles=$(find "$dst" -type f 2>/dev/null | wc -l)

  echo "$ATTEMPTED,$CUR_KEY,$NEW_MODEL,$NEW_H,$NEW_SEED,$CUR_JOB,1,$CUR_STATUS,$CUR_EXIT,$CUR_NODE,$new,accepted,$dst,$nfiles" >> "$STATUSCSV"
  echo "{\"utc\":\"$(date -u '+%Y-%m-%dT%H:%M:%SZ')\",\"event\":\"accepted\",\"run_key\":\"$CUR_KEY\",\"job_id\":\"$CUR_JOB\",\"run_id\":\"$new\",\"durable\":\"$dst\",\"durable_files\":$nfiles}" >> "$LEDGER"
  ACCEPTED=$((ACCEPTED + 1))
  log "ACCEPTED $CUR_KEY ($ACCEPTED/$TOTAL) durable_files=$nfiles"
  state_write
  sleep 5
done < "$ORDER"

if [ "$STOPPED" = "true" ]; then FINAL="STOPPED"; else
  if [ "$ACCEPTED" -eq "$TOTAL" ]; then FINAL="ALL_ACCEPTED"; else FINAL="INCOMPLETE"; fi
fi
state_write
log "controller end: accepted=$ACCEPTED/$TOTAL final=$FINAL reason=${STOP_REASON}"
