#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=02:00:00
#SBATCH --job-name=v3_prepilot_gate
# NODE EXCLUSION (evidence-backed, NOT a request for extra resources):
# jobs 563486 and 563498 both landed on gpu-a100-05 and both failed the very
# first CUDA allocation with "CUDA-capable device(s) is/are busy or unavailable",
# even though nvidia-smi shows the A100 and Slurm allocated gres/gpu:a100=1.
# The device is therefore held by a foreign context on that node. This retry
# requests the SAME resources (1 A100) and simply avoids the faulty node.
#SBATCH --exclude=gpu-a100-05
#SBATCH --output=hpc_results/innovation/logs/v3_gate_%j.out
#SBATCH --error=hpc_results/innovation/logs/v3_gate_%j.err

# COMPUTE-NODE pre-Pilot gate. This script must ONLY ever run via sbatch.
#
# Resource justification (HPC_GUIDE section 10 red line):
#   - 1x A100: every one of the eight models is constructed on CUDA and must run a
#     real forward + backward pass, including the 1.5B Qwen backbone.
#   - 8 CPUs / 32 GB: safetensors shard loading plus Qwen2.5-1.5B (bf16) residency
#     alongside the GPT-2 branch; the default ~1 GB memory limit would OOM.
#   - 02:00:00: bounded by the one-off ~3.1 GB pinned-revision asset download plus
#     eight model constructions and gradient checks. Not padding for queue priority.
set -euo pipefail

module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH

# ── explicit, fail-closed deployment root (no silent fallback) ───────────────
: "${INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be the isolated v3 root}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"
FORBIDDEN_ROOT_RAW="/home/sychan552/scratch/CHATTIME/Chattime"
FORBIDDEN_ROOT="$(readlink -f "$FORBIDDEN_ROOT_RAW" 2>/dev/null || true)"
if [ -n "$FORBIDDEN_ROOT" ]; then
  if [ "$DEPLOYMENT_ROOT" = "$FORBIDDEN_ROOT" ] || \
     [ "${DEPLOYMENT_ROOT#"$FORBIDDEN_ROOT/"}" != "$DEPLOYMENT_ROOT" ]; then
    echo "FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT" >&2
    exit 2
  fi
fi
cd "$DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs
echo "[gate] deployment_root=$DEPLOYMENT_ROOT host=$(hostname) job=${SLURM_JOB_ID:-none}"

# v2 verified cache: holds GPT-2, which CALF/TimeCMA use as their text backbone.
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_HUB_CACHE=$HF_HOME
export HF_DATASETS_CACHE=$HF_HOME
# Qwen is resolved through the absolute verified snapshot path recorded in
# innovation.assets, so its cache root is tracked separately for provenance only.
export V3_CACHE=/gpfs1/scratch/sychan552/v3_cache
export TOKENIZERS_PARALLELISM=false

# ── 1. runtime guard + source freeze verification ───────────────────────────
python scripts/innovation/runtime_guard.py --deployment-root "$DEPLOYMENT_ROOT"
python scripts/innovation/verify_source_snapshot.py \
    --deployment-root "$DEPLOYMENT_ROOT" \
    --manifest results/innovation/source_snapshot_manifest.json

# ── 2. the gate itself ──────────────────────────────────────────────────────
python -u hpc_scripts/v3_prepilot_gate.py
RC=$?
echo "[gate] python rc=$RC at $(date)"
exit $RC
