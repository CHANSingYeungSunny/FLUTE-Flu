#!/bin/bash
# wave1_controller_v319.sh — quota-safe pure-Bash Wave-1 controller (v3.19).
# Same hard invariants as v3.18 (atomic single-instance lock, at most one
# active/pending formal job, ledger IMMEDIATELY after sbatch, COMPLETED 0:0 is
# never acceptance, deterministic fail-stop, no wildcard deletion, never reads a
# superseded root, deferred rows refused, Test/holdout never touched), PLUS:
#   * D15 repair-finalize for the single already-trained baseline row
#     baseline__last_value_naive__L24__seedna__w1: it REUSES the successful
#     runner job 572649's artifacts (never re-trains), and passes
#     --original-job-id 572649 so provenance is preserved.
#   * every finalize job receives the row's ORIGINAL training job id.
set -uo pipefail

ROOT=/scratch/sychan552/innovation_deploy_root_v3_clean14
BASE=/scratch/sychan552/_v319d
ORDER="$BASE/formal_execution_order_wave1.txt"
ACCEPTED="$BASE/accepted_keys.txt"
LEDGER="$BASE/wave1_ledger.jsonl"
LOCK="$BASE/.wave1_controller.lock"
PIDF="$BASE/wave1_controller.pid"
TOKEN_FILE="$BASE/wave1_authorization.token"
DURABLE=/home/sychan552/innovation_durable/screening
FINALIZE_SH="$BASE/v319_row_finalize.sh"

# D15 repair-finalize (the ONLY row reused): successful runner job 572649 is
# already COMPLETED 0:0 and its artifacts live under the v3.18 root.
REPAIR_KEY="baseline__last_value_naive__L24__seedna__w1"
REPAIR_JOB_ID="572649"
REPAIR_SOURCE_ROOT=/scratch/sychan552/innovation_deploy_root_v3_clean12

log() { printf '[wave1] %s\n' "$*" >&2; }
die() { log "FAIL-STOP: $*"; exit 1; }

# ---- 0. authorization token --------------------------------------------
[ -f "$TOKEN_FILE" ] || die "authorization token missing"
[ -n "${WAVE1_AUTHORIZATION_TOKEN:-}" ] || die "WAVE1_AUTHORIZATION_TOKEN not set"
[ "$(cat "$TOKEN_FILE")" = "${WAVE1_AUTHORIZATION_TOKEN}" ] || die "token mismatch"
unset WAVE1_AUTHORIZATION_TOKEN || true

# ---- 1. atomic single-instance lock + traps ----------------------------
mkdir "$LOCK" 2>/dev/null || die "another controller instance holds $LOCK"
trap 'rmdir "$LOCK" 2>/dev/null || true' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
echo "$$" > "$PIDF"
log "controller pid=$$ lock=$LOCK"

[ -f "$ORDER" ] || die "order file missing: $ORDER"
[ -f "$ACCEPTED" ] || : > "$ACCEPTED"
[ -f "$LEDGER" ] || : > "$LEDGER"
[ -f "$FINALIZE_SH" ] || die "finalize wrapper missing"

cd "$ROOT" || die "cannot cd $ROOT"
export INNOVATION_DEPLOYMENT_ROOT="$ROOT"
export CONFIRM_INNOVATION_SUBMIT=YES
[ -f "scripts/innovation/clean_runner.py" ] || die "not a deployment root"

active_jobs() { squeue -u "$USER" -h -o "%i" 2>/dev/null | grep -c "^[0-9]" || true; }
slurm_state() { sacct -j "$1" --format=State --noheader -X 2>/dev/null | head -1 | tr -d ' '; }
slurm_exit() { sacct -j "$1" --format=ExitCode --noheader -X 2>/dev/null | head -1 | tr -d ' '; }
wait_terminal() {
  local jid="$1"
  while :; do
    case "$(slurm_state "$jid")" in
      COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|PREEMPTED) return 0 ;;
    esac
    sleep 20
  done
}
record() { printf '{"utc":"%s","run_key":"%s","job_id":"%s","event":"%s"}\n' \
    "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$2" "$3" "$1" >> "$LEDGER"; }

# ---- 2. quota preflight (fail-closed, never submits) -------------------
quota_preflight() { python3 "$BASE/quota_preflight.py" "$1" "$1"; }

submitted=0; accepted=0
while IFS= read -r key; do
  case "$key" in ''|\#*) continue ;; esac
  if grep -qxF "$key" "$ACCEPTED"; then continue; fi
  case "$key" in *deferred*) die "deferred row present in order: $key" ;; esac
  case "$key" in *..*|*/*) die "unsafe run key: $key" ;; esac
  [ -f "hpc_scripts/v3_clean/$key.sh" ] || die "row script missing: $key"

  log "QUOTA_PREFLIGHT $key"
  quota_preflight "$key" >/dev/null || die "quota preflight failed: $key"

  # ---- 3. train (or D15 repair-finalize reuse) -------------------------
  if [ "$key" = "$REPAIR_KEY" ]; then
    RUN_DIR="$REPAIR_SOURCE_ROOT/results/v3_clean/runs/$key"
    [ -f "$RUN_DIR/run_status.json" ] || die "repair run-dir missing: $key"
    python3 - "$RUN_DIR/run_status.json" <<'PY' || die "repair run_status not COMPLETED"
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
sys.exit(0 if d.get("state") == "COMPLETED" else 1)
PY
    ORIGINAL_JOB_ID="$REPAIR_JOB_ID"
    record "REPAIR_FINALIZE_SKIP_TRAINING" "$key" "$ORIGINAL_JOB_ID"
    log "REPAIR-FINALIZE $key (skip training, original_job_id=$ORIGINAL_JOB_ID)"
  else
    RUN_DIR="$ROOT/results/v3_clean/runs/$key"
    while [ "$(active_jobs)" -gt 0 ]; do sleep 20; done
    jid="$(sbatch --parsable "hpc_scripts/v3_clean/$key.sh")" || die "sbatch failed for $key"
    [ -n "$jid" ] || die "empty job id for $key"
    record SUBMITTED "$key" "$jid"
    submitted=$((submitted + 1))
    log "SUBMITTED $key -> $jid"
    wait_terminal "$jid"
    st="$(slurm_state "$jid")"; ec="$(slurm_exit "$jid")"
    record "SLURM_$st" "$key" "$jid"
    [ "$st" = "COMPLETED" ] || die "row $key state=$st (not accepted)"
    case "$ec" in 0:0) ;; *) die "row $key exit=$ec" ;; esac
    log "VERIFY_SLURM $key ok"
    ORIGINAL_JOB_ID="$jid"
  fi

  # ---- 4. finalize on a compute node -----------------------------------
  while [ "$(active_jobs)" -gt 0 ]; do sleep 20; done
  fid="$(sbatch --parsable "$FINALIZE_SH" "$key" "$RUN_DIR" "$ORIGINAL_JOB_ID")" \
    || die "finalize submit failed"
  record "FINALIZE_SUBMITTED" "$key" "$fid"
  wait_terminal "$fid"
  fst="$(slurm_state "$fid")"; fec="$(slurm_exit "$fid")"
  record "FINALIZE_$fst" "$key" "$fid"
  [ "$fst" = "COMPLETED" ] || die "finalize $key state=$fst"
  case "$fec" in 0:0) ;; *) die "finalize $key exit=$fec" ;; esac

  # ---- 5. storage-verification-v1 must pass (fail-closed) --------------
  rec="$BASE/finalize/$key.storage_verification.json"
  [ -f "$rec" ] || die "storage-verification record missing: $key"
  python3 - "$rec" <<'PY' || die "storage-verification-v1 FAILED for $key"
import json, os, sys
sys.path.insert(0, os.path.join(os.environ["INNOVATION_DEPLOYMENT_ROOT"], "scripts"))
from innovation import storage_verification as SV
d = json.load(open(sys.argv[1], encoding="utf-8"))
ok = SV.storage_verdict(d)
print(json.dumps({"code": d.get("code"), "detail": d.get("detail"), "passed": ok}))
sys.exit(0 if ok else 4)
PY

  echo "$key" >> "$ACCEPTED"
  accepted=$((accepted + 1))
  record ACCEPTED "$key" "$fid"
  log "ACCEPTED $key (accepted=$accepted submitted=$submitted)"

  if [ $((accepted % 25)) -eq 0 ]; then
    log "CHECKPOINT accepted=$accepted submitted=$submitted "
    log "  home=$(du -sh /home/sychan552 2>/dev/null | cut -f1) "
    log "  scratch=$(du -sh /gpfs1/scratch/sychan552 2>/dev/null | cut -f1) "
    log "  active=$(active_jobs)"
  fi
done < "$ORDER"

log "controller finished: submitted=$submitted accepted=$accepted"
exit 0
