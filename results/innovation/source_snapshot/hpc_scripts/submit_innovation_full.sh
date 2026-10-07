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

# FULL SWEEP: all L x seeds 42..51 (guarded; auto chain).
set -u
SPECS=(  "dlinear none identity 24 42 20 full"  "dlinear none identity 24 43 20 full"  "dlinear none identity 24 44 20 full"  "dlinear none identity 24 45 20 full"  "dlinear none identity 24 46 20 full"  "dlinear none identity 24 47 20 full"  "dlinear none identity 24 48 20 full"  "dlinear none identity 24 49 20 full"  "dlinear none identity 24 50 20 full"  "dlinear none identity 24 51 20 full"  "dlinear none identity 36 42 20 full"  "dlinear none identity 36 43 20 full"  "dlinear none identity 36 44 20 full"  "dlinear none identity 36 45 20 full"  "dlinear none identity 36 46 20 full"  "dlinear none identity 36 47 20 full"  "dlinear none identity 36 48 20 full"  "dlinear none identity 36 49 20 full"  "dlinear none identity 36 50 20 full"  "dlinear none identity 36 51 20 full"  "dlinear none identity 48 42 20 full"  "dlinear none identity 48 43 20 full"  "dlinear none identity 48 44 20 full"  "dlinear none identity 48 45 20 full"  "dlinear none identity 48 46 20 full"  "dlinear none identity 48 47 20 full"  "dlinear none identity 48 48 20 full"  "dlinear none identity 48 49 20 full"  "dlinear none identity 48 50 20 full"  "dlinear none identity 48 51 20 full"  "dlinear none identity 60 42 20 full"  "dlinear none identity 60 43 20 full"  "dlinear none identity 60 44 20 full"  "dlinear none identity 60 45 20 full"  "dlinear none identity 60 46 20 full"  "dlinear none identity 60 47 20 full"  "dlinear none identity 60 48 20 full"  "dlinear none identity 60 49 20 full"  "dlinear none identity 60 50 20 full"  "dlinear none identity 60 51 20 full"  "patchtst none identity 24 42 20 full"  "patchtst none identity 24 43 20 full"  "patchtst none identity 24 44 20 full"  "patchtst none identity 24 45 20 full"  "patchtst none identity 24 46 20 full"  "patchtst none identity 24 47 20 full"  "patchtst none identity 24 48 20 full"  "patchtst none identity 24 49 20 full"  "patchtst none identity 24 50 20 full"  "patchtst none identity 24 51 20 full"  "patchtst none identity 36 42 20 full"  "patchtst none identity 36 43 20 full"  "patchtst none identity 36 44 20 full"  "patchtst none identity 36 45 20 full"  "patchtst none identity 36 46 20 full"  "patchtst none identity 36 47 20 full"  "patchtst none identity 36 48 20 full"  "patchtst none identity 36 49 20 full"  "patchtst none identity 36 50 20 full"  "patchtst none identity 36 51 20 full"  "patchtst none identity 48 42 20 full"  "patchtst none identity 48 43 20 full"  "patchtst none identity 48 44 20 full"  "patchtst none identity 48 45 20 full"  "patchtst none identity 48 46 20 full"  "patchtst none identity 48 47 20 full"  "patchtst none identity 48 48 20 full"  "patchtst none identity 48 49 20 full"  "patchtst none identity 48 50 20 full"  "patchtst none identity 48 51 20 full"  "patchtst none identity 60 42 20 full"  "patchtst none identity 60 43 20 full"  "patchtst none identity 60 44 20 full"  "patchtst none identity 60 45 20 full"  "patchtst none identity 60 46 20 full"  "patchtst none identity 60 47 20 full"  "patchtst none identity 60 48 20 full"  "patchtst none identity 60 49 20 full"  "patchtst none identity 60 50 20 full"  "patchtst none identity 60 51 20 full"  "itransformer none identity 24 42 20 full"  "itransformer none identity 24 43 20 full"  "itransformer none identity 24 44 20 full"  "itransformer none identity 24 45 20 full"  "itransformer none identity 24 46 20 full"  "itransformer none identity 24 47 20 full"  "itransformer none identity 24 48 20 full"  "itransformer none identity 24 49 20 full"  "itransformer none identity 24 50 20 full"  "itransformer none identity 24 51 20 full"  "itransformer none identity 36 42 20 full"  "itransformer none identity 36 43 20 full"  "itransformer none identity 36 44 20 full"  "itransformer none identity 36 45 20 full"  "itransformer none identity 36 46 20 full"  "itransformer none identity 36 47 20 full"  "itransformer none identity 36 48 20 full"  "itransformer none identity 36 49 20 full"  "itransformer none identity 36 50 20 full"  "itransformer none identity 36 51 20 full"  "itransformer none identity 48 42 20 full"  "itransformer none identity 48 43 20 full"  "itransformer none identity 48 44 20 full"  "itransformer none identity 48 45 20 full"  "itransformer none identity 48 46 20 full"  "itransformer none identity 48 47 20 full"  "itransformer none identity 48 48 20 full"  "itransformer none identity 48 49 20 full"  "itransformer none identity 48 50 20 full"  "itransformer none identity 48 51 20 full"  "itransformer none identity 60 42 20 full"  "itransformer none identity 60 43 20 full"  "itransformer none identity 60 44 20 full"  "itransformer none identity 60 45 20 full"  "itransformer none identity 60 46 20 full"  "itransformer none identity 60 47 20 full"  "itransformer none identity 60 48 20 full"  "itransformer none identity 60 49 20 full"  "itransformer none identity 60 50 20 full"  "itransformer none identity 60 51 20 full"  "gpt2_miflu gpt2 concat_projection 24 42 20 full"  "gpt2_miflu gpt2 concat_projection 24 43 20 full"  "gpt2_miflu gpt2 concat_projection 24 44 20 full"  "gpt2_miflu gpt2 concat_projection 24 45 20 full"  "gpt2_miflu gpt2 concat_projection 24 46 20 full"  "gpt2_miflu gpt2 concat_projection 24 47 20 full"  "gpt2_miflu gpt2 concat_projection 24 48 20 full"  "gpt2_miflu gpt2 concat_projection 24 49 20 full"  "gpt2_miflu gpt2 concat_projection 24 50 20 full"  "gpt2_miflu gpt2 concat_projection 24 51 20 full"  "gpt2_miflu gpt2 concat_projection 36 42 20 full"  "gpt2_miflu gpt2 concat_projection 36 43 20 full"  "gpt2_miflu gpt2 concat_projection 36 44 20 full"  "gpt2_miflu gpt2 concat_projection 36 45 20 full"  "gpt2_miflu gpt2 concat_projection 36 46 20 full"  "gpt2_miflu gpt2 concat_projection 36 47 20 full"  "gpt2_miflu gpt2 concat_projection 36 48 20 full"  "gpt2_miflu gpt2 concat_projection 36 49 20 full"  "gpt2_miflu gpt2 concat_projection 36 50 20 full"  "gpt2_miflu gpt2 concat_projection 36 51 20 full"  "gpt2_miflu gpt2 concat_projection 48 42 20 full"  "gpt2_miflu gpt2 concat_projection 48 43 20 full"  "gpt2_miflu gpt2 concat_projection 48 44 20 full"  "gpt2_miflu gpt2 concat_projection 48 45 20 full"  "gpt2_miflu gpt2 concat_projection 48 46 20 full"  "gpt2_miflu gpt2 concat_projection 48 47 20 full"  "gpt2_miflu gpt2 concat_projection 48 48 20 full"  "gpt2_miflu gpt2 concat_projection 48 49 20 full"  "gpt2_miflu gpt2 concat_projection 48 50 20 full"  "gpt2_miflu gpt2 concat_projection 48 51 20 full"  "gpt2_miflu gpt2 concat_projection 60 42 20 full"  "gpt2_miflu gpt2 concat_projection 60 43 20 full"  "gpt2_miflu gpt2 concat_projection 60 44 20 full"  "gpt2_miflu gpt2 concat_projection 60 45 20 full"  "gpt2_miflu gpt2 concat_projection 60 46 20 full"  "gpt2_miflu gpt2 concat_projection 60 47 20 full"  "gpt2_miflu gpt2 concat_projection 60 48 20 full"  "gpt2_miflu gpt2 concat_projection 60 49 20 full"  "gpt2_miflu gpt2 concat_projection 60 50 20 full"  "gpt2_miflu gpt2 concat_projection 60 51 20 full")
# Chain: submit one at a time, waiting for the single stingy slot.
for spec in "${SPECS[@]}"; do
  set -- $spec
  while [ "$(squeue -u $USER -h -p stingy | wc -l)" -ge 1 ]; do sleep 60; done
  echo "[chain] submitting $spec at $(date)"
  sbatch hpc_scripts/innovation_worker.sh "$@"
done
echo "[chain] all submitted at $(date)"
