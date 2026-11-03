#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=110G
#SBATCH --time=03:50:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v315_migrate
#SBATCH --output=/scratch/sychan552/_v315d/logs/slurm_%j_v315_migrate.out
#SBATCH --error=/scratch/sychan552/_v315d/logs/slurm_%j_v315_migrate.err

# Migrate 205 rows (204 accepted + job 571472) to the v3.15 compact durable
# policy. NO retraining: every row is converted from its existing completed
# evidence, verified, atomically published, and only then has its redundant
# full checkpoint removed.
set -uo pipefail

module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_CACHE=$HF_HOME
export PYTHONUNBUFFERED=1

BASE=/scratch/sychan552/_v315d
R=/scratch/sychan552/innovation_deploy_root_v3_clean9
OUT=$BASE/migration
mkdir -p "$OUT" "$BASE/logs"
cd "$R"
export PYTHONPATH="$R/scripts"
export INNOVATION_DEPLOYMENT_ROOT="$R"

echo "=== SCHEMA PRECHECK (dry: no writes) ==="
echo "rows=$(grep -c . $BASE/migrate_rows.tsv)"

python -u "$BASE/migrate_accepted_rows.py" \
  --deployment-root "$R" \
  --rows "$BASE/migrate_rows.tsv" \
  --out-dir "$OUT"
rc=$?

echo "=== SUMMARY ==="
echo "ok=$(grep -c '\"ok\": true' $OUT/migration_ledger.jsonl 2>/dev/null)"
echo "failed=$(grep -c '\"ok\": false' $OUT/migration_ledger.jsonl 2>/dev/null)"
echo "MIGRATE_DONE rc=$rc"
exit $rc
