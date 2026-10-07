#!/bin/bash
# deploy_and_launch.sh — ship the deterministic bundle + controller + controller
# config to a fresh isolated HPC root, verify, dry-run, then launch the
# persistent login-node controller. Run from a host that can reach
# burgundy.hpc.cityu.edu.hk.
#
# Usage:
#   REMOTE_USER=sychan552 REMOTE_HOST=burgundy.hpc.cityu.edu.hk \
#     bash hpc_scripts/autonomous/deploy_and_launch.sh [--launch]
#   (without --launch it stops after the dry-run so a human can confirm)
set -u
REMOTE_USER="${REMOTE_USER:-sychan552}"
REMOTE_HOST="${REMOTE_HOST:-burgundy.hpc.cityu.edu.hk}"
LOCAL_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUNDLE="$LOCAL_ROOT/results/innovation/hpc_deployment/innovation_hpc_bundle.tar.gz"
CTRL_DIR="$LOCAL_ROOT/hpc_scripts/autonomous"
AC_LOCAL="$LOCAL_ROOT/results/innovation/autonomous_completion"
REMOTE_ROOT="${REMOTE_ROOT:-/scratch/sychan552/innovation_deploy_root_$(date +%Y%m%d_%H%M%S)}"

# HPC runtime env (HPC_GUIDE §4): prepend the conda env so `python`/`python3`
# resolve to mlflu_hpc; HF offline cache exports. This is intentional single-quoted
# so $PATH survives local expansion and is resolved on the remote login node.
HPC_ENV='export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH; export HF_HOME=/home/sychan552/.cache/huggingface; export TRANSFORMERS_OFFLINE=1; export HF_DATASETS_OFFLINE=1'

echo "[deploy] bundle : $BUNDLE"
echo "[deploy] remote : $REMOTE_USER@$REMOTE_HOST:$REMOTE_ROOT"

# 1) create fresh isolated root
ssh "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_ROOT/hpc_scripts/autonomous $REMOTE_ROOT/results/innovation/autonomous_completion" || {
  echo "[deploy] FATAL: cannot reach $REMOTE_HOST"; exit 1; }

# 2) ship bundle + controller (controller is NOT inside the bundle)
scp "$BUNDLE" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_ROOT/" || exit 1
scp "$CTRL_DIR"/{state.py,lib.sh,controller.sh} "$REMOTE_USER@$REMOTE_HOST:$REMOTE_ROOT/hpc_scripts/autonomous/" || exit 1

# 2b) ship the controller config (lives in results/, OUTSIDE the frozen bundle).
#     Explicit list only: never clobber the live current_state.json / ledgers.
scp "$AC_LOCAL/stage_plan.json" "$AC_LOCAL/completion_matrix.json" \
    "$AC_LOCAL/freeze_audit.json" "$AC_LOCAL/session_manifest.json" \
    "$AC_LOCAL/decision_log.md" "$AC_LOCAL/completion_matrix.md" \
    "$AC_LOCAL/resume_instructions.md" \
    "$REMOTE_USER@$REMOTE_HOST:$REMOTE_ROOT/results/innovation/autonomous_completion/" || {
  echo "[deploy] WARN: some config files did not copy"; }

# 3) extract + verify (explicit root, never a path containing Chattime)
echo "[deploy] extract + verify explicit root:"
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_ROOT && $HPC_ENV && \
  tar -xzf innovation_hpc_bundle.tar.gz && \
  python scripts/innovation/verify_source_snapshot.py \
    --deployment-root $REMOTE_ROOT \
    --manifest results/innovation/source_snapshot_manifest.json" || {
  echo "[deploy] FATAL: source verification failed"; exit 1; }

# 3b) provision the input dataset (data/ is OUTSIDE the frozen bundle but is
#     required by runner.py). Idempotent: only uploaded when absent.
if [ -d "$LOCAL_ROOT/data" ]; then
  if ssh "$REMOTE_USER@$REMOTE_HOST" "test -f $REMOTE_ROOT/data/raw/national_illness_raw.csv" 2>/dev/null; then
    echo "[deploy] dataset already present in root"
  else
    echo "[deploy] provisioning dataset -> $REMOTE_ROOT/data"
    scp -q -r "$LOCAL_ROOT/data" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_ROOT/data" || {
      echo "[deploy] WARN: dataset provisioning failed"; }
  fi
fi

# 4) dry-run (no Slurm submission)
echo "[deploy] DRY-RUN controller:"
ssh "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_ROOT && $HPC_ENV && \
  INNOVATION_DEPLOYMENT_ROOT=$REMOTE_ROOT DRYRUN=1 \
  bash hpc_scripts/autonomous/controller.sh" || exit 1

if [ "${1:-}" != "--launch" ]; then
  echo "[deploy] dry-run only. Re-run with --launch to start the persistent controller."
  exit 0
fi

# 5) launch the persistent login-node controller (env inherited by its children)
ssh -f "$REMOTE_USER@$REMOTE_HOST" "$HPC_ENV && cd $REMOTE_ROOT && \
  INNOVATION_DEPLOYMENT_ROOT=$REMOTE_ROOT \
  nohup bash hpc_scripts/autonomous/controller.sh > controller.log 2>&1 & \
  echo \$! > controller.pid"
echo "[deploy] launched. Tail with:"
echo "  ssh $REMOTE_USER@$REMOTE_HOST 'cat $REMOTE_ROOT/controller.log'"
echo "  ssh $REMOTE_USER@$REMOTE_HOST 'cat $REMOTE_ROOT/controller.pid'"
