#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=04:00:00
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_%x.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_%x.err
#SBATCH --signal=B:USR1@120

# NOTE: --mem must be explicit (the default is reset to ~1024MB and loading
# GPT-2 would OOM). Never request a generic single GPU on stingy (it may land
# on a V100 and OOM); always pin the a100 flavour exactly as below.
# --time is capped at 4h; jobs are intentionally small, one-run-per-job and
# resumable, so 4h is NOT assumed sufficient for a whole sweep.

set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME

# ── DEPLOYMENT ROOT: EXPLICIT, never a silent fallback ──────────────────────
# The innovation experiment may only run from an ISOLATED deployment root. The
# original reproduction repository is forbidden as an execution path
# (incident 2026-09-15). A missing variable must FAIL CLOSED, never fall back to
# the submitter's current directory.
: "${INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be set to the isolated deployment root}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"

# The forbidden root is resolved WITHOUT cd-ing into it (readlink only), so this
# line can never execute anything inside the original repository.
FORBIDDEN_ROOT_RAW="/home/sychan552/scratch/CHATTIME/Chattime"
FORBIDDEN_ROOT="$(readlink -f "$FORBIDDEN_ROOT_RAW" 2>/dev/null || true)"
if [ -n "$FORBIDDEN_ROOT" ]; then
  if [ "$DEPLOYMENT_ROOT" = "$FORBIDDEN_ROOT" ] || [ "${DEPLOYMENT_ROOT#"$FORBIDDEN_ROOT/"}" != "$DEPLOYMENT_ROOT" ]; then
    echo "FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT" >&2
    exit 2
  fi
fi

cd "$DEPLOYMENT_ROOT"
echo "[deployment_root] $DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs

# Preemption notice: record it; the python process still writes run_status.json.
trap 'echo "[preempt] SIGUSR1 at $(date)"; export INNOVATION_PREEMPTED=1' USR1

# ── CONFIRMATION GUARD (pre-HPC clarification 6) ────────────────────────────
# Nothing is submitted unless the operator explicitly opts in. During the
# verification phase this ALWAYS reports submission_attempted=false.
: "${CONFIRM_INNOVATION_SUBMIT:=NO}"
if [ "$CONFIRM_INNOVATION_SUBMIT" != "YES" ]; then
  echo "[guard] REFUSED to submit: export CONFIRM_INNOVATION_SUBMIT=YES to proceed."
  echo "[guard] submission_attempted=false"
  exit 0
fi
echo "[guard] submission_attempted=true"

# Pilot job (INFRASTRUCTURE VERIFICATION ONLY — never a ranking).
echo "[pilot] start $(date) | pilot_dlinear_L24_seed42.sh"

# ── 1. RUNTIME PATH GUARD (original reproduction repo is OUT of exec path) ──
python scripts/innovation/runtime_guard.py \
    --deployment-root "$DEPLOYMENT_ROOT" || {
  echo "[abort] FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT"
  exit 1
}

# ── 2. SOURCE FREEZE STARTUP CHECK (explicit root; abort on drift) ──────────
python scripts/innovation/verify_source_snapshot.py \
    --deployment-root "$DEPLOYMENT_ROOT" \
    --manifest results/innovation/source_snapshot_manifest.json || {
  echo "[abort] source snapshot verification FAILED — refusing to run"
  exit 1
}

# ── 3. v2.4 hash + test-access / eligibility assertion ─────────────────────

python - <<'PY'
import json, os, sys
want = "dlinear"
stage = "pilot"
man = json.load(open("results/innovation/source_snapshot_manifest.json", encoding="utf-8"))
agg = man["aggregate_sha256"]
bad = []
if stage == "pilot":
    specs = json.load(open("hpc_scripts/pilot_specs.json", encoding="utf-8"))
    rec = next((s for s in specs.get("specs", []) if s.get("model") == want), None)
    if rec is None:
        print("[abort] no pilot spec for " + want); sys.exit(1)
    if rec.get("source_snapshot_sha256") != agg:
        bad.append("source_snapshot_sha256 mismatch spec=%s manifest=%s" % (rec.get("source_snapshot_sha256"), agg))
    for k in ("test_access_allowed", "selection_eligible", "paper_result_eligible"):
        if rec.get(k) is not False:
            bad.append("%s is not false" % k)
    if rec.get("experiment_stage") != "pilot" or rec.get("purpose") != "infrastructure_verification_only":
        bad.append("experiment_stage/purpose mismatch")
print("[startup] stage=" + str(stage))
print("[startup] expected_aggregate_sha256=" + agg)
if bad:
    for b in bad:
        print("[abort] " + b)
    sys.exit(1)
print("[startup] governance check OK")
PY
RC=$?
if [ "$RC" -ne 0 ]; then
  echo "[abort] startup governance check FAILED"
  exit 1
fi

python scripts/innovation/runner.py \
    --model "dlinear" --text-encoder "none" \
    --fusion "identity" --horizon 24 \
    --seed 42 --epochs 20 --experiment-stage pilot \
    --max-seconds 12600 --skip-if-done || {
  RC=$?
  echo "[pilot] FAILED rc=$RC at $(date)"
  exit $RC
}
echo "[pilot] python rc=0 at $(date)"
