#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=01:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --output=hpc_results/innovation/logs/slurm_%j_screening_gate.out
#SBATCH --error=hpc_results/innovation/logs/slurm_%j_screening_gate.err

# v3.4 PRE-SCREENING GATE — exercises all eight model families end to end and
# validates the new formal Screening artifacts. Runs stage=validation with tiny
# limits so a Gate run can never enter the formal Screening set.
set -euo pipefail
module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME

: "${INNOVATION_DEPLOYMENT_ROOT:?INNOVATION_DEPLOYMENT_ROOT must be set}"
DEPLOYMENT_ROOT="$(cd "$INNOVATION_DEPLOYMENT_ROOT" && pwd -P)"
FORBIDDEN_ROOT="$(readlink -f /home/sychan552/scratch/CHATTIME/Chattime 2>/dev/null || true)"
if [ -n "$FORBIDDEN_ROOT" ]; then
  if [ "$DEPLOYMENT_ROOT" = "$FORBIDDEN_ROOT" ] || [ "${DEPLOYMENT_ROOT#"$FORBIDDEN_ROOT/"}" != "$DEPLOYMENT_ROOT" ]; then
    echo "FORBIDDEN_ORIGINAL_REPOSITORY_RUNTIME_IMPORT" >&2
    exit 2
  fi
fi
cd "$DEPLOYMENT_ROOT"
mkdir -p hpc_results/innovation/logs
echo "[gate] job=${SLURM_JOB_ID} node=${SLURMD_NODENAME} root=$DEPLOYMENT_ROOT"

python scripts/innovation/runtime_guard.py --deployment-root "$DEPLOYMENT_ROOT"
echo "[gate] runtime guard violations = 0"

python scripts/innovation/verify_source_snapshot.py \
    --deployment-root "$DEPLOYMENT_ROOT" \
    --manifest results/innovation/source_snapshot_manifest.json

python hpc_scripts/v3_screening/screening_gate.py
RC=$?
echo "[gate] screening_gate.py rc=$RC"
exit $RC
