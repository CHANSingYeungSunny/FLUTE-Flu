#!/bin/bash
# ==========================================================================
# wave1_controller_v318.sh — quota-safe pure-Bash Wave-1 controller (v3.18)
#
# State machine per row:
#   RECONCILE -> QUOTA_PREFLIGHT -> SUBMIT_ONE -> RECORD_JOB_ID -> WAIT_TERMINAL
#   -> VERIFY_SLURM -> (finalize job) -> VERIFY_STORAGE -> ATOMIC_DURABLE_PUBLISH
#   -> REMOVE_REDUNDANT_FULL_SCRATCH_CHECKPOINT -> MARK_ACCEPTED -> NEXT_ROW
#
# Hard invariants:
#   * pure Bash orchestration; python is used ONLY for the lightweight quota
#     preflight and for reading the storage-verification-v1 record
#   * atomic single-instance lock
#   * at most ONE active/pending job at any time (numeric job-id counting)
#   * job id appended to the ledger IMMEDIATELY after sbatch
#   * COMPLETED 0:0 is NEVER acceptance: a passing storage-verification-v1
#     record (fail-closed) is required
#   * deterministic failure => fail-stop; never skip a row, never continue
#   * the full scratch checkpoint is removed only inside finalize_row.py,
#     i.e. after the compact package is verified and published
#   * no broad wildcard deletion anywhere
#   * never reads from a superseded deployment root
#   * deferred rows are refused; Test/holdout are never touched
# ==========================================================================
set -uo pipefail

ROOT=/scratch/sychan552/innovation_deploy_root_v3_clean12
BASE=/scratch/sychan552/_v318d
ORDER="$BASE/formal_execution_order_wave1.txt"
ACCEPTED="$BASE/accepted_keys.txt"
LEDGER="$BASE/wave1_ledger.jsonl"
LOCK="$BASE/.wave1_controller.lock"
PIDF="$BASE/wave1_controller.pid"
TOKEN_FILE="$BASE/wave1_authorization.token"
DURABLE=/home/sychan552/innovation_durable/screening
FINALIZE_SH="$BASE/v318_row_finalize.sh"

log() { printf '[wave1] %s\n' "$*" >&2; }
die() { log "FAIL-STOP: $*"; exit 1; }

# ---- 0. explicit authorization token -------------------------------------
[ -f "$TOKEN_FILE" ] || die "authorization token missing (launch not authorized)"
[ -n "${WAVE1_AUTHORIZATION_TOKEN:-}" ] || die "WAVE1_AUTHORIZATION_TOKEN not set"
[ "$(cat "$TOKEN_FILE")" = "${WAVE1_AUTHORIZATION_TOKEN}" ] || die "token mismatch"
# the token must never reach a sbatch child, a log or an artifact
unset WAVE1_AUTHORIZATION_TOKEN || true

# ---- 1. atomic single-instance lock + safe traps -------------------------
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

# numeric Slurm job-id counting only (the cluster prints a banner line that a
# naive `wc -l` would count as a job)
active_jobs() { squeue -u "$USER" -h -o "%i" 2>/dev/null | grep -c "^[0-9]" || true; }

slurm_state() {
  sacct -j "$1" --format=State --noheader -X 2>/dev/null | head -1 | tr -d ' '
}
slurm_exit() {
  sacct -j "$1" --format=ExitCode --noheader -X 2>/dev/null | head -1 | tr -d ' '
}
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

# ---- 2. quota preflight (fail-closed, never submits) ---------------------
# `os.statvfs` is unusable on this GPFS mount (it reports the whole filesystem),
# so the preflight parses `mmlsquota` via quota_preflight.py.
quota_preflight() {
  python3 "$BASE/quota_preflight.py" "$1" "$1"
}

submitted=0; accepted=0
while IFS= read -r key; do
  case "$key" in ''|\#*) continue ;; esac
  if grep -qxF "$key" "$ACCEPTED"; then continue; fi
  # deferred rows must never be submitted
  case "$key" in *deferred*) die "deferred row present in order: $key" ;; esac
  case "$key" in *..*|*/*) die "unsafe run key: $key" ;; esac
  [ -f "hpc_scripts/v3_clean/$key.sh" ] || die "row script missing: $key"

  log "QUOTA_PREFLIGHT $key"
  quota_preflight "$key" >/dev/null || die "quota preflight failed: $key"

  while [ "$(active_jobs)" -gt 0 ]; do sleep 20; done
  jid="$(sbatch --parsable "hpc_scripts/v3_clean/$key.sh")" \
    || die "sbatch failed for $key"
  [ -n "$jid" ] || die "empty job id for $key"
  record SUBMITTED "$key" "$jid"          # job id recorded IMMEDIATELY
  submitted=$((submitted + 1))
  log "SUBMITTED $key -> $jid"

  wait_terminal "$jid"
  st="$(slurm_state "$jid")"; ec="$(slurm_exit "$jid")"
  record "SLURM_$st" "$key" "$jid"
  [ "$st" = "COMPLETED" ] || die "row $key state=$st (not accepted)"
  case "$ec" in 0:0) ;; *) die "row $key exit=$ec" ;; esac
  log "VERIFY_SLURM $key ok"

  # ---- finalize on a compute node (compact + publish + cleanup) ---------
  while [ "$(active_jobs)" -gt 0 ]; do sleep 20; done
  fid="$(sbatch --parsable "$FINALIZE_SH" "$key")" || die "finalize submit failed"
  record "FINALIZE_SUBMITTED" "$key" "$fid"
  wait_terminal "$fid"
  fst="$(slurm_state "$fid")"; fec="$(slurm_exit "$fid")"
  record "FINALIZE_$fst" "$key" "$fid"
  [ "$fst" = "COMPLETED" ] || die "finalize $key state=$fst"
  case "$fec" in 0:0) ;; *) die "finalize $key exit=$fec" ;; esac

  # ---- storage-verification-v1 must pass (fail-closed) ------------------
  rec="$BASE/finalize/$key.storage_verification.json"
  [ -f "$rec" ] || die "storage-verification record missing: $key"
  python3 - "$rec" <<'PY' || die "storage-verification-v1 FAILED for $key"
import json, os, sys
sys.path.insert(0, os.path.join(os.environ["INNOVATION_DEPLOYMENT_ROOT"],
                                "scripts"))
from innovation import storage_verification as SV
d = json.load(open(sys.argv[1], encoding="utf-8"))
ok = SV.storage_verdict(d)
print(json.dumps({"code": d.get("code"), "detail": d.get("detail"),
                  "passed": ok}))
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
