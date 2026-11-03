#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v319_finalize
#SBATCH --output=/scratch/sychan552/_v319d/logs/slurm_%j_finalize_%x.out
#SBATCH --error=/scratch/sychan552/_v319d/logs/slurm_%j_finalize_%x.err

# v3.19 per-row durable finalization. The acceptance path is decided by the
# frozen spec's `arm` inside the FROZEN finalize_row.py (baseline -> no-checkpoint
# branch; otherwise -> compact+restore+publish+cleanup). This wrapper only wires
# paths and preserves the ORIGINAL training job identity.
#   usage: sbatch v319_row_finalize.sh <run_key> <run_dir> <original_job_id>
set -uo pipefail

KEY="${1:-}"; RUN_DIR="${2:-}"; ORIGINAL_JOB_ID="${3:-}"
[ -n "$KEY" ] || { echo "FAIL-STOP: run key required"; exit 2; }
[ -n "$RUN_DIR" ] || { echo "FAIL-STOP: run dir required"; exit 2; }
[ -n "$ORIGINAL_JOB_ID" ] || { echo "FAIL-STOP: original job id required"; exit 2; }

module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_CACHE=$HF_HOME
export PYTHONUNBUFFERED=1

BASE=/scratch/sychan552/_v319d
R=/scratch/sychan552/innovation_deploy_root_v3_clean14
mkdir -p "$BASE/logs" "$BASE/finalize"
cd "$R"
export PYTHONPATH="$R/scripts"
export INNOVATION_DEPLOYMENT_ROOT="$R"

python -u "$R/scripts/innovation/finalize_row.py" \
  --run-key "$KEY" \
  --deployment-root "$R" \
  --run-dir "$RUN_DIR" \
  --durable-root /home/sychan552/innovation_durable/screening \
  --original-job-id "$ORIGINAL_JOB_ID" \
  --out "$BASE/finalize/$KEY.storage_verification.json"
rc=$?
echo "FINALIZE_DONE key=$KEY rc=$rc"
exit $rc
