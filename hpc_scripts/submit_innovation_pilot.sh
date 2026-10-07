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

# ── SERIAL SUBMISSION OF EXACTLY THE EIGHT AUTHORIZED PILOTS ────────────────
# pilot_gpt2_miflu_L24_seed42.sh / pilot_dlinear_L24_seed42.sh
# pilot_patchtst_L24_seed42.sh  / pilot_itransformer_L24_seed42.sh
# plus Qwen, CALF, and TimeCMA. Nothing else is ever queued: no generic worker,
# no other stage, no self-call,
# no re-submission of a failed job.
PILOTS=(
  "hpc_scripts/pilot_nlinear_L24_seed42.sh"
  "hpc_scripts/pilot_gpt2_miflu_L24_seed42.sh"
  "hpc_scripts/pilot_dlinear_L24_seed42.sh"
  "hpc_scripts/pilot_patchtst_L24_seed42.sh"
  "hpc_scripts/pilot_itransformer_L24_seed42.sh"
  "hpc_scripts/pilot_qwen_time_llm_L24_seed42.sh"
  "hpc_scripts/pilot_calf_llm_L24_seed42.sh"
  "hpc_scripts/pilot_timecma_llm_L24_seed42.sh"
)
PREV=""
for pilot in "${PILOTS[@]}"; do
  if [ -n "$PREV" ]; then
    echo "[chain] waiting for job $PREV to reach a terminal state"
    ST=""
    N=0
    while [ $N -lt 240 ]; do
      ST=$(sacct -j "$PREV" -X -n -o State 2>/dev/null | head -n 1 | tr -d ' ' || true)
      case "$ST" in
        COMPLETED|FAILED|CANCELLED*|TIMEOUT|NODE_FAIL|OUT_OF_MEMORY) break ;;
      esac
      sleep 30
      N=$((N + 1))
    done
    EC=$(sacct -j "$PREV" -X -n -o ExitCode 2>/dev/null | head -n 1 | tr -d ' ' || true)
    if [ "$ST" != "COMPLETED" ] || [ "${EC%%:*}" != "0" ]; then
      echo "[chain] FAIL-STOP: predecessor $PREV state=$ST exit=$EC - not submitting further pilots"
      exit 1
    fi
  fi
  if [ -z "$PREV" ]; then
    OUT=$(sbatch --parsable "$pilot")
  else
    OUT=$(sbatch --parsable --dependency=afterok:$PREV "$pilot")
  fi
  echo "[chain] submitted $pilot jobid=$OUT dependency=${PREV:-none}"
  PREV="$OUT"
done
echo "[chain] all eight authorized pilots submitted; last jobid=$PREV"
