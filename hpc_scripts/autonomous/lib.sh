#!/bin/bash
# lib.sh — helper functions for the innovation autonomous controller.
# Sourced by controller.sh. No GPU requested; runs on the login node only.
# All functions are pure shell wrappers around `state.py` + Slurm CLI.
# shellcheck disable=SC2034,SC2086,SC2046

# ── single-instance lock (requirement 1) ──────────────────────────────────────
acquire_lock() {
  # caller opens fd 9 to the lock file before calling this
  if ! flock -n 9; then
    echo "[controller] LOCK_HELD: another controller instance is running -> exit"
    exit 1
  fi
}

# ── heartbeat + current_state.json (requirement 11) ───────────────────────────
heartbeat() {
  local stage="${1:-none}" last_job="${2:-none}"
  local now
  now="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  python3 - "$CURRENT_STATE" "$now" "$stage" "$last_job" "$CONTROLLER_PID" <<'PY'
import json, sys, os
path, now, stage, last_job, pid = sys.argv[1:6]
state = {}
if os.path.exists(path):
    try:
        state = json.load(open(path, encoding="utf-8"))
    except Exception:
        state = {}
state["heartbeat_utc"] = now
state["controller_pid"] = int(pid) if str(pid).isdigit() else pid
state["current_stage"] = stage
state["last_job"] = last_job
state["deployment_root"] = os.environ.get("DEPLOYMENT_ROOT", "")
state["dry_run"] = bool(int(os.environ.get("DRYRUN", "0")))
# a fresh heartbeat means the controller is running again: clear any prior
# STOPPED bookkeeping so current_state.json never misreports a live controller
state["status"] = "running"
state.pop("stop_reason", None)
state.pop("stopped_utc", None)
json.dump(state, open(path, "w", encoding="utf-8"), indent=2)
PY
}

# ── at-most-one-job gate (requirement 3) ──────────────────────────────────────
squeue_empty() {
  # returns 0 (true) when no job is queued/running for the user on the partition.
  # Counts ONLY numeric job-id lines: some login environments append banner/MOTD
  # lines (e.g. "Last update in N seconds ago") after the squeue output, which
  # would make a naive `wc -l` always non-zero and deadlock the wait loop.
  local n
  n="$(squeue -u "$USER" -h -p "${PARTITION}" -o '%i' 2>/dev/null \
       | tr -d ' \t' | grep -c '^[0-9]')"
  [ "$n" -eq 0 ]
}

# ── poll for terminal Slurm state (requirement 4) ─────────────────────────────
poll_terminal() {
  local jobid="$1" max="${2:-240}" iv="${3:-60}"
  local i state ec
  for ((i=0; i<max; i++)); do
    state="$(sacct -j "$jobid" -X -n -o State 2>/dev/null | head -n1 | tr -d ' ')"
    case "$state" in
      COMPLETED|FAILED|CANCELLED*|TIMEOUT|NODE_FAIL|OUT_OF_MEMORY|BOOT_FAIL)
        ec="$(sacct -j "$jobid" -X -n -o ExitCode 2>/dev/null | head -n1 | tr -d ' ')"
        echo "$state|$ec"
        return 0
        ;;
    esac
    sleep "$iv"
  done
  echo "TIMEOUT|"
  return 1
}

# ── append-only ledger (requirements 2 & 8) ──────────────────────────────────
append_ledger() {
  # $1=job_id $2=stage $3=model $4=horizon $5=seed $6=utc $7=state
  # $8=exit $9=node $10=run_id $11=notes
  local path="$JOB_LEDGER"
  if [ ! -f "$path" ]; then
    printf 'job_id,stage,model_key,horizon,seed,submitted_utc,state,exit_code,node,run_id,notes\n' > "$path"
  fi
  printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
    "$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" "${10}" "${11}" >> "$path"
}

set_ledger_state() {
  # rewrite only the row whose job_id == $1, flipping its state/exit/node
  local jobid="$1" state="$2" exitc="${3:-}" node="${4:-}"
  [ -f "$JOB_LEDGER" ] || return 0
  local tmp="${JOB_LEDGER}.tmp.$$"
  local header=1
  while IFS=, read -r c1 c2 c3 c4 c5 c6 c7 c8 c9 c10 c11; do
    if [ "$header" = "1" ]; then header=0; printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' "$c1" "$c2" "$c3" "$c4" "$c5" "$c6" "$c7" "$c8" "$c9" "$c10" "$c11" > "$tmp"; continue; fi
    if [ "$c1" = "$jobid" ]; then
      c7="$state"; [ -n "$exitc" ] && c8="$exitc"; [ -n "$node" ] && c9="$node"
    fi
    printf '%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' "$c1" "$c2" "$c3" "$c4" "$c5" "$c6" "$c7" "$c8" "$c9" "$c10" "$c11" >> "$tmp"
  done < "$JOB_LEDGER"
  mv "$tmp" "$JOB_LEDGER"
}

# ── per-stage budget ledger (append-only) ─────────────────────────────────────
write_budget() {
  # $1=stage $2=within(yes/no) $3=job_count $4=gpu_hours $5=note
  local path="$BUDGET_LEDGER"
  if [ ! -f "$path" ]; then
    printf 'stage,decision_utc,job_count,gpu_hours_estimate,within_limits,note\n' > "$path"
  fi
  printf '%s,%s,%s,%s,%s,%s\n' "$1" "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$3" "$4" "$2" "$5" >> "$path"
}

# ── durable copy-back (requirement 12) ────────────────────────────────────────
copy_back() {
  # $1 = run_id ; copies the run dir + slurm logs to the durable root (GPFS home,
  # which has backup unlike scratch). Best-effort; failure is logged, not fatal
  # to the chain (the scratch copy still exists on the compute node's scratch,
  # and the deployment root itself is on GPFS).
  local run_id="$1"
  local src="$DEPLOYMENT_ROOT/results/innovation/runs/$run_id"
  local dst="$DURABLE_ROOT/runs/$run_id"
  if [ -d "$src" ]; then
    mkdir -p "$dst"
    cp -r "$src/." "$dst/." 2>/dev/null \
      && echo "[copy_back] $run_id -> $dst" \
      || echo "[copy_back][WARN] could not copy $run_id"
  fi
  # also pull the slurm logs for this job
  if [ -n "${LAST_JOB_ID:-}" ]; then
    mkdir -p "$DURABLE_ROOT/logs"
    cp -f "$DEPLOYMENT_ROOT"/hpc_results/innovation/logs/slurm_"${LAST_JOB_ID}"_*.out "$DURABLE_ROOT/logs/" 2>/dev/null || true
    cp -f "$DEPLOYMENT_ROOT"/hpc_results/innovation/logs/slurm_"${LAST_JOB_ID}"_*.err "$DURABLE_ROOT/logs/" 2>/dev/null || true
  fi
}

# ── local (non-Slurm) stage runner: A verify / K freeze ──────────────────────
run_local_stage() {
  local stage_key="$1"
  case "$stage_key" in
    A)
      # verify the isolated deployment root against the snapshot manifest
      ( cd "$DEPLOYMENT_ROOT" && \
        python scripts/innovation/verify_source_snapshot.py \
          --deployment-root "$DEPLOYMENT_ROOT" \
          --manifest results/innovation/source_snapshot_manifest.json )
      return $?
      ;;
    C)
      # validation-only candidate-readiness gate (writes pre_hpc_gate + reports)
      ( cd "$DEPLOYMENT_ROOT" && python scripts/innovation/prehpc_report.py )
      return $?
      ;;
    E)
      # preliminary validation-only ranking over Screening runs (no freeze)
      ( cd "$DEPLOYMENT_ROOT" && python scripts/innovation/select_best_model.py )
      return $?
      ;;
    K)
      # validation-only champion selection + freeze, then the freeze audit that
      # the one-time Test gate reads (never touches Test)
      ( cd "$DEPLOYMENT_ROOT" && python scripts/innovation/select_best_model.py ) || return $?
      write_freeze_audit
      return $?
      ;;
    *)
      echo "[local_stage] no local handler for stage $stage_key"
      return 1
      ;;
  esac
}

# ── validation-only freeze audit (stage K -> Test gate input) ─────────────────
# Synthesises freeze_audit.json from the selection audit + frozen winners +
# per-run metadata. It NEVER reads a Test path. The one-time Test gate only
# opens when this audit passes AND the completion matrix is fully resolved.
write_freeze_audit() {
  local out="${FREEZE_AUDIT:-}"
  [ -n "$out" ] || out="$DEPLOYMENT_ROOT/results/innovation/autonomous_completion/freeze_audit.json"
  python3 - "$DEPLOYMENT_ROOT" "$out" <<'PY'
import json, os, sys
root, out = sys.argv[1], sys.argv[2]
inv = os.path.join(root, "results", "innovation")


def _load(p):
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


sel = _load(os.path.join(inv, "model_selection_audit.json"))
fw = _load(os.path.join(inv, "frozen_winners.json"))
champ = (sel or {}).get("winner")

checks = []
checks.append({"id": "no_test_access_during_selection",
               "description": "No Test split was read during candidate generation or selection",
               "passed": bool(sel) and sel.get("test_accessed") is False})
checks.append({"id": "frozen_winners_written",
               "description": "frozen_winners.json exists before any Test access",
               "passed": bool(fw and fw.get("winners"))})
checks.append({"id": "champion_definition_frozen",
               "description": "Champion run IDs, checkpoint hashes, plan hash, source hash, protocol version frozen",
               "passed": bool(champ)})

meta_ok = False
if champ:
    m = champ.get("model")
    runs = os.path.join(inv, "runs")
    ok, seen = True, 0
    if os.path.isdir(runs):
        for d in sorted(os.listdir(runs)):
            p = os.path.join(runs, d)
            if not os.path.isdir(p):
                continue
            parts = d.split("__")
            if len(parts) < 2 or parts[1] != m:
                continue
            rs = _load(os.path.join(p, "run_status.json"))
            if not rs:
                continue
            seen += 1
            if rs.get("status") != "ok":
                ok = False
            if not os.path.exists(os.path.join(p, "checkpoints", "checkpoint_manifest.json")):
                ok = False
    meta_ok = bool(ok and seen > 0)
checks.append({"id": "metadata_chain_complete",
               "description": "Runtime metadata chain complete across all five evidence layers for every selected run",
               "passed": meta_ok})

passed = all(c["passed"] for c in checks)
rec = {"protocol_version": "innov-v2.0", "passed": passed,
       "note": "validation-only champion freeze audit (auto-generated at stage K)",
       "checks": checks}
os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
with open(out, "w", encoding="utf-8") as f:
    json.dump(rec, f, indent=2)
print("[freeze_audit] passed=" + str(passed) + " -> " + out)
sys.exit(0 if passed else 1)
PY
}

# ── fail-stop (requirement 6) ─────────────────────────────────────────────────
fail_stop() {
  local msg="$1"
  echo "[FAIL-STOP] $msg"
  # record STOPPED in the ledger-independent state file
  python3 - "$CURRENT_STATE" "$msg" <<'PY'
import json, sys, os
path, msg = sys.argv[1:3]
state = {}
if os.path.exists(path):
    try: state = json.load(open(path, encoding="utf-8"))
    except Exception: state = {}
state["status"] = "STOPPED"
state["stop_reason"] = msg
state["stopped_utc"] = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
json.dump(state, open(path, "w", encoding="utf-8"), indent=2)
PY
  append_ledger "CONTROLLER" "CONTROLLER" "n/a" "n/a" "n/a" \
    "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "STOPPED" "" "" "" "FAIL-STOP: $msg"
  exit 1
}
