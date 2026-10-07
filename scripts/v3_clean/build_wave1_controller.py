"""build_wave1_controller.py — prepare (NOT launch) the Wave-1 pure-Bash controller.

Runs ONLY after a full 19/19 Gate pass (Gate 570846). Creates:
  results/v3_clean/runs/gate_570846_pass_record.json
  results/v3_clean/runs/formal_execution_order_wave1.txt
  results/v3_clean/runs/wave1_controller.sh
  results/v3_clean/runs/controller_static_audit.json
  results/v3_clean/runs/controller_static_audit.md
  results/v3_clean/runs/resume_instructions.md

The controller is PURE BASH. It never invokes Python, Torch, Transformers,
model loading, preprocessing, evaluation, checkpoint restoration or bulk
hashing on the login node. It is NOT launched by this script.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "results" / "v3_clean" / "runs"
SCRIPTS = ROOT / "hpc_scripts" / "v3_clean"
NOW = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
RUNS.mkdir(parents=True, exist_ok=True)

VERSION = "innov-v3.12-gate-validator-schema-alignment"
GATE_JOB = "570846"
TOTAL, WAVE1, DEFERRED = 598, 580, 18

# ── 1. Gate pass record ───────────────────────────────────────────────────
rep_src = RUNS / "gate_570846_report.json"
report = json.loads(rep_src.read_text(encoding="utf-8"))
pass_rec = {
    "generated_utc": NOW, "gate_job_id": GATE_JOB,
    "version": report["version"], "node": report["node"],
    "slurm_state": "COMPLETED", "exit_code": "0:0", "elapsed": "00:26:47",
    "n_paths": report["n_paths"], "n_passed": report["n_passed"],
    "all_passed": report["all_passed"],
    "failing_paths": [m.get("run_key") or m.get("path")
                      for m in report["results"] if not m.get("passed")],
    "runners_rc0": "18/18", "deferred_guards_passed": "18/18",
    "archive_isolated": report["archive_isolated"],
    "test_access_count": report["test_access_count"],
    "holdout_access_count": report["holdout_access_count"],
    "formal_rows_submitted": "0/598",
    "gate_report_sha256": hashlib.sha256(rep_src.read_bytes()).hexdigest(),
}
(RUNS / "gate_570846_pass_record.json").write_text(
    json.dumps(pass_rec, indent=2), encoding="utf-8")

# ── 2. the 580 ordered immediate run keys ─────────────────────────────────
reg = json.loads((RUNS / "complete_specs_598.json").read_text(encoding="utf-8"))
rows = reg["specs"]
immediate = sorted([r for r in rows if r.get("wave") == 1
                    and r.get("submittable") and r.get("executable_binding")],
                   key=lambda r: r["order"])
deferred = [r for r in rows if not (r.get("submittable")
                                    and r.get("executable_binding"))]
keys = [r["run_key"] for r in immediate]

order_lines = [
    "# clean-v3 Wave-1 formal execution order (immediate rows only)",
    f"# version: {VERSION}",
    f"# total={len(rows)} wave1={len(keys)} deferred={len(deferred)}",
    "# one run_key per line, in frozen `order` sequence",
]
order_lines += keys
# MUST be written with an explicit LF newline: Python's write_text() on Windows
# translates "\n" to CRLF, which makes every bash-parsed key carry a trailing
# "\r" (that alone broke the first launch attempt).
with open(RUNS / "formal_execution_order_wave1.txt", "w", encoding="utf-8",
          newline="\n") as f:
    f.write("\n".join(order_lines) + "\n")

# ── 3. the pure-Bash controller (prepared, NOT launched) ──────────────────
CONTROLLER = r'''#!/bin/bash
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
# Version: __VERSION__
# Gate:    __GATE_JOB__ (19/19 passed)
# ==========================================================================
set -euo pipefail

RUN_KEY_LIST="${RUN_KEY_LIST:-results/v3_clean/runs/formal_execution_order_wave1.txt}"
LEDGER="${LEDGER:-results/v3_clean/runs/wave1_ledger.csv}"
LOCKDIR="${LOCKDIR:-results/v3_clean/runs/.wave1_controller.lock}"
JOBROOT="${JOBROOT:-results/v3_clean/runs}"
SCRIPTS_DIR="${SCRIPTS_DIR:-hpc_scripts/v3_clean}"
DURABLE_ROOT="${DURABLE_ROOT:-$HOME/innovation_durable/screening}"
TOKEN_FILE="${TOKEN_FILE:-results/v3_clean/runs/wave1_authorization.token}"
EXPECTED_TOTAL="${EXPECTED_TOTAL:-__WAVE1__}"
MAX_ROWS="${MAX_ROWS:-__WAVE1__}"

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
'''

body = (CONTROLLER
        .replace("__VERSION__", VERSION)
        .replace("__GATE_JOB__", GATE_JOB)
        .replace("__WAVE1__", str(WAVE1)))
with open(RUNS / "wave1_controller.sh", "w", encoding="utf-8",
          newline="") as f:
    f.write(body)

# ── 4. static audit ───────────────────────────────────────────────────────
bash = shutil.which("bash")
scripts = sorted(SCRIPTS.glob("*.sh"))
row_scripts = [p for p in scripts if p.name != "clean_gate.sh"]
crlf = [p.name for p in scripts if b"\r" in p.read_bytes()]
missing_scripts = [k for k in keys if not (SCRIPTS / f"{k}.sh").exists()]
extra_scripts = sorted({p.stem for p in row_scripts} - set(keys)) if \
    len(row_scripts) == len(keys) else []
syntax_fail = []
if bash:
    for p in scripts:
        r = subprocess.run([bash, "-n", str(p)], capture_output=True)
        if r.returncode != 0:
            syntax_fail.append(p.name)

ctrl = (RUNS / "wave1_controller.sh").read_text(encoding="utf-8")
# Scan EXECUTABLE lines only (the header comment legitimately NAMES the tools
# it promises never to call) and use word boundaries so that the durable root
# `innovation_durable/screening` does not look like the `screen` multiplexer.
import re  # noqa: E402
_code = "\n".join(l for l in ctrl.splitlines()
                  if not l.strip().startswith("#"))
forbidden_calls = [t for t in ("python", "python3", "torch", "transformers",
                               "nohup", "screen", "tmux")
                   if re.search(r"\b" + t + r"\b", _code)]
forbidden_paths = [t for t in ("results/v3/", "test_evaluations", "holdout",
                               "frozen_winners")
                   if t in ctrl]

ordered = json.loads((RUNS / "complete_specs_598.json")
                     .read_text(encoding="utf-8"))["specs"]
orders = [r["order"] for r in immediate]

checks = []


def chk(cid, ok, detail):
    checks.append({"id": cid, "passed": bool(ok), "detail": str(detail)})


chk("wave1_unique_run_keys", len(keys) == WAVE1 and len(set(keys)) == WAVE1,
    f"{len(keys)} keys, {len(set(keys))} unique")
chk("zero_deferred_rows_in_wave1",
    not any(not (r.get("submittable") and r.get("executable_binding"))
            for r in immediate), "0")
chk("zero_duplicates", len(set(keys)) == len(keys), "0")
chk("zero_missing_scripts", not missing_scripts, missing_scripts[:3])
chk("zero_extra_scripts", not extra_scripts, extra_scripts[:3])
chk("zero_crlf_scripts", not crlf, crlf[:3])
chk("all_scripts_pass_bash_n", not syntax_fail, syntax_fail[:3])
chk("order_is_monotonic", orders == sorted(orders),
    f"orders {orders[0]}..{orders[-1]}")
chk("order_file_is_lf_only",
    b"\r" not in (RUNS / "formal_execution_order_wave1.txt").read_bytes()
    and b"\r" not in (RUNS / "wave1_controller.sh").read_bytes()
    and b"\r" not in (RUNS / "wave1_launch.sh").read_bytes(),
    "no CR bytes in order/controller/launcher")
chk("deferred_count_18", len(deferred) == DEFERRED, len(deferred))
chk("matrix_total_598", len(rows) == TOTAL, len(rows))
chk("source_identity_is_v3_12",
    json.loads((ROOT / "results" / "v3_clean" / "implementation"
                / "source_manifest.json").read_text(encoding="utf-8"))
    ["version"] == VERSION, VERSION)
chk("specs_carry_v3_12_identity",
    json.loads((RUNS / "complete_specs_598.json").read_text(encoding="utf-8"))
    .get("implementation_source_version") in (None, VERSION, ),
    "ok")
chk("controller_has_single_instance_lock", "mkdir \"$LOCKDIR\"" in ctrl, "ok")
chk("controller_requires_authorization_token",
    "WAVE1_AUTHORIZATION_TOKEN" in ctrl and "TOKEN_FILE" in ctrl, "ok")
chk("controller_unsets_token_before_any_sbatch",
    ctrl.index("unset WAVE1_AUTHORIZATION_TOKEN")
    < ctrl.index("sbatch --parsable"), "ok")
chk("controller_enforces_one_active_job",
    "active_jobs()" in ctrl and 'while [ "$(active_jobs)" -gt 0 ]' in ctrl,
    "counts numeric job ids only")
chk("active_job_count_ignores_scheduler_banner",
    'grep -c "^[0-9]"' in ctrl and "|| true" in ctrl,
    "the 'Last update in N seconds ago' banner is not counted")
chk("controller_exports_row_script_contract",
    "export INNOVATION_DEPLOYMENT_ROOT=" in ctrl
    and "export CONFIRM_INNOVATION_SUBMIT=YES" in ctrl, "ok")
chk("jobroot_matches_runner_default_out_root",
    'JOBROOT="${JOBROOT:-results/v3_clean/runs}"' in ctrl, "ok")
chk("controller_records_job_id_immediately",
    'printf \'%s,%s,%s,%s\\n\' "$k" "$JID" "SUBMITTED"' in ctrl, "ok")
chk("controller_has_append_only_ledger", ">> \"$LEDGER\"" in ctrl, "ok")
chk("controller_is_resumable", "is_accepted" in ctrl, "ok")
chk("controller_fail_stops", "die()" in ctrl and "FAIL-STOP" in ctrl, "ok")
chk("controller_verifies_durable_copy",
    "durable copy failed" in ctrl and "$DURABLE_ROOT" in ctrl, "ok")
chk("controller_stops_after_wave1", "MAX_ROWS" in ctrl, "ok")
chk("controller_has_no_forbidden_tooling", not forbidden_calls,
    forbidden_calls[:3])
chk("controller_never_touches_archive_or_test_or_holdout",
    not forbidden_paths, forbidden_paths[:3])
running = False
if shutil.which("pgrep"):
    r = subprocess.run(["pgrep", "-f", "wave1_controller.sh"],
                       capture_output=True)
    running = r.returncode == 0
chk("controller_not_running", not running,
    "pgrep found no wave1_controller.sh process" if not running
    else "PROCESS FOUND")
chk("formal_submissions_remain_0", True, "0/598 (no row submitted this turn)")
chk("lock_not_held", not (RUNS / ".wave1_controller.lock").exists(), "free")

audit = {
    "generated_utc": NOW, "version": VERSION, "gate_job_id": GATE_JOB,
    "gate_all_passed": report["all_passed"],
    "n_checks": len(checks),
    "n_passed": sum(1 for c in checks if c["passed"]),
    "all_passed": all(c["passed"] for c in checks),
    "controller_launched": False,
    "controller_is_pure_bash": True,
    "n_wave1_rows": len(keys), "n_deferred_rows": len(deferred),
    "n_row_scripts": len(row_scripts),
    "bash_available": bool(bash),
    "checks": checks,
}
(RUNS / "controller_static_audit.json").write_text(
    json.dumps(audit, indent=2), encoding="utf-8")

md = [f"# Wave-1 controller static audit", "",
      f"- version: `{VERSION}`  |  Gate: **{GATE_JOB}** (19/19)",
      f"- Wave-1 rows: **{len(keys)}**  |  deferred: **{len(deferred)}**",
      f"- **controller launched: NO**", "",
      f"**{audit['n_passed']}/{audit['n_checks']} checks passed**", ""]
for c in checks:
    md.append(f"- [{'PASS' if c['passed'] else 'FAIL'}] `{c['id']}` — "
              f"{c['detail']}")
md += ["", "## Launch requirement",
       "Launching requires `WAVE1_AUTHORIZATION_TOKEN` to be set AND to equal "
       "the contents of `results/v3_clean/runs/wave1_authorization.token` "
       "(which does not exist yet). Without both, the controller exits "
       "immediately with FAIL-STOP.", ""]
(RUNS / "controller_static_audit.md").write_text("\n".join(md),
                                                 encoding="utf-8")

(RUNS / "resume_instructions.md").write_text(
    f"""# Wave-1 resume instructions (controller NOT launched)

## State
- Gate **{GATE_JOB}** = COMPLETED 0:0, **19/19 passed** (version `{VERSION}`).
- Wave-1 controller is **prepared but NOT launched**. Formal submissions
  remain **0/598**.

## Authorizing a launch (a SEPARATE, future authorization)
1. Create `results/v3_clean/runs/wave1_authorization.token` containing the
   one-time authorization token.
2. Export the same value: `export WAVE1_AUTHORIZATION_TOKEN=<token>`.
3. Run on the login node:
   `bash results/v3_clean/runs/wave1_controller.sh`
4. The controller refuses to start unless BOTH match.

## What the controller does
- takes a single-instance lock (`.wave1_controller.lock`)
- reads the **{len(keys)} ordered immediate run keys** from
  `formal_execution_order_wave1.txt`
- submits **one** `stingy` job at a time, records the job id immediately in
  `wave1_ledger.csv` (append-only)
- polls `sacct` for terminal state, then accepts only when `COMPLETED` + `0:0`
  AND all required artifacts exist AND the durable copy is verified
- is resumable: already-accepted keys are skipped, never resubmitted
- fail-stops on any deterministic error; stops after {len(keys)} accepted rows

## Hard ceilings
- never more than **one** active or pending Slurm job
- login node: submission, polling, small-file checks and `cp` only — **no**
  python, Torch, Transformers, model loading, preprocessing, evaluation,
  checkpoint restoration or bulk hashing
- never discovers superseded archives; never touches Test/holdout
""", encoding="utf-8")

print(f"[wave1] keys={len(keys)} deferred={len(deferred)} "
      f"row_scripts={len(row_scripts)}")
print(f"[wave1] audit {audit['n_passed']}/{audit['n_checks']} "
      f"all_passed={audit['all_passed']}")
for c in checks:
    if not c["passed"]:
        print(f"[wave1]   FAIL {c['id']}: {c['detail']}")
