#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v318_finalize
#SBATCH --output=/scratch/sychan552/_v318d/logs/slurm_%j_finalize_%x.out
#SBATCH --error=/scratch/sychan552/_v318d/logs/slurm_%j_finalize_%x.err

# Per-row durable finalization (compact export + strict restoration +
# predictions/metrics + atomic publish + redundant full-checkpoint removal).
#   usage: sbatch v318_row_finalize.sh <run_key>
set -uo pipefail

KEY="${1:-}"
[ -n "$KEY" ] || { echo "FAIL-STOP: run key required"; exit 2; }

module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_CACHE=$HF_HOME
export PYTHONUNBUFFERED=1

BASE=/scratch/sychan552/_v318d
R=/scratch/sychan552/innovation_deploy_root_v3_clean12
mkdir -p "$BASE/logs" "$BASE/finalize"
cd "$R"
export PYTHONPATH="$R/scripts"
export INNOVATION_DEPLOYMENT_ROOT="$R"

mkdir -p "$BASE/finalize"
python -u "$BASE/finalize_row.py" \
  --run-key "$KEY" \
  --deployment-root "$R" \
  --run-dir "$R/results/v3_clean/runs/$KEY" \
  --durable-root /home/sychan552/innovation_durable/screening \
  --out "$BASE/finalize/$KEY.storage_verification.json"
rc=$?
echo "FINALIZE_DONE key=$KEY rc=$rc"
exit $rc
