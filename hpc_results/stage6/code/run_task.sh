#!/bin/bash
#SBATCH --job-name=s6_task
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=24G
#SBATCH --time=01:00:00
#SBATCH --output=results/stage6/logs/task_%j.out
#SBATCH --error=results/stage6/logs/task_%j.err
#
# Stage 6 ??one (backbone, horizon) task for the eight-model comparison.
#   3 frozen seeds per task, ONE PROCESS PER SEED so the model, optimizer and
#   selection state are re-initialised per seed (never a "best seed").
# Test isolation: DEFER_TEST=1 for every learned fit, so no Test number exists
# until the 96 checkpoints are locked and the unified scoring entry runs.
#
# NOT SUBMITTED. Held pending an explicit additional compute authorization;
# see recovery/stage6/cost_and_matrix_zh.md for the measured cost.
set -eo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1

export PYTHONPATH=/scratch/sychan552/a2_stage5/scripts
export HF_HOME=/home/sychan552/.cache/huggingface
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
# Qwen2.5-1.5B is resolved through innovation/assets.py from the verified
# local snapshot (revision 8faed761d45a263340a0528343f099c05c9a4323),
# local_files_only=True. No network access is used or needed.
export ACTIVE_PROFILE=author_966
export A2_REQUIRE_STRICT=1
export MPLBACKEND=Agg
export DEFER_TEST=1
# Keep HF fully offline even if a code path tries to resolve a repo id.
export HF_HUB_DISABLE_TELEMETRY=1

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
LEDGER=results/stage6/logs/run_ledger.csv
R=results/stage6/author_966
C=results/stage6/ckpt/author_966
E=results/stage6/epoch_logs
mkdir -p results/stage6/logs "$R" "$C" "$E"

record () {  # $1=run_id $2=exit_code
  echo "$1,$SLURM_JOB_ID,$BACKBONE,$L,$SEED,$1_start=$(date -u +%FT%TZ),exit=$2" >> "$LEDGER"
}

echo "[s6] BACKBONE=$BACKBONE L=$L job=$SLURM_JOB_ID start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null | sed 's/^/[s6] gpu: /'

for S in ${SEEDS:-42 43 44}; do
  SEED=$S
  /usr/bin/time -f "$BACKBONE L${L} S${S} wall=%e s maxrss=%M KB" \
  $PY scripts/train_backbone_966.py \
      --backbone "$BACKBONE" --horizon "$L" --seed "$S" \
      --profile author_966 --containment strict \
      --epochs 20 --batch 16 \
      --export-dir "$R/$BACKBONE" \
      --ckpt-dir   "$C/$BACKBONE" \
      --epoch-log-dir "$E" 2>&1 | grep -v -E "^(Loading|Fetching)" | tail -30
  record "S6-$(echo $BACKBONE | tr a-z A-Z)-L${L}-S${S}" "${PIPESTATUS[0]}"
done

echo "[s6] BACKBONE=$BACKBONE L=$L end=$(date -u +%FT%TZ)"
