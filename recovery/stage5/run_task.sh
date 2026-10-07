#!/bin/bash
#SBATCH --job-name=s5_task
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=results/stage5/logs/task_%j.out
#SBATCH --error=results/stage5/logs/task_%j.err
#
# Stage 5 A2 — one (model, horizon) task.
#   miflu / notext / nlinear : 3 frozen seeds, ONE process per seed so that the
#                              model, optimizer, scheduler and selection state
#                              are re-initialised per seed (never a "best seed").
#   naive                    : all 4 horizons x 2 deterministic baselines.
# Test isolation: DEFER_TEST=1 for every learned fit -> no Test number exists
# until the checkpoint list is locked (naive runs in the locked-batch step).
set -eo pipefail

cd /scratch/sychan552/a2_stage5

export PYTHONPATH=/scratch/sychan552/a2_stage5/scripts
export HF_HOME=/home/sychan552/.cache/huggingface
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export ACTIVE_PROFILE=author_966
export A2_REQUIRE_STRICT=1
export MPLBACKEND=Agg
export DEFER_TEST=1

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
LEDGER=results/stage5/logs/run_ledger.csv
mkdir -p results/stage5/logs results/stage5/author_966/miflu results/stage5/author_966/notext \
         results/stage5/author_966/nlinear results/stage5/author_966/naive \
         results/stage5/ckpt/author_966/miflu results/stage5/ckpt/author_966/notext \
         results/stage5/ckpt/author_966/nlinear

record () {  # $1=run_id $2=exit_code
  echo "$1,$SLURM_JOB_ID,$MODEL,$L,$SEED,$1_start=$(date -u +%FT%TZ),exit=$2" >> "$LEDGER"
}

echo "[task] MODEL=$MODEL L=$L job=$SLURM_JOB_ID start=$(date -u +%FT%TZ)"

case "$MODEL" in
  miflu)
    for S in 42 43 44; do
      SEED=$S
      /usr/bin/time -f "miflu_L${L}_S${S} wall=%e s" $PY scripts/train_miflu.py \
        --horizon "$L" --seed "$S" --reps 1 --epochs 20 --batch 16 \
        --profile author_966 --containment strict \
        --export-dir results/stage5/author_966/miflu/ \
        --ckpt-dir   results/stage5/ckpt/author_966/miflu/ 2>&1 | tail -40
      record "A2-MIFlu-L${L}-S${S}" "${PIPESTATUS[0]}"
    done ;;
  notext)
    for S in 42 43 44; do
      SEED=$S
      /usr/bin/time -f "notext_L${L}_S${S} wall=%e s" $PY scripts/train_ablation.py \
        --variant no_multi --horizon "$L" --seed "$S" --reps 1 --epochs 20 --batch 16 \
        --profile author_966 --containment strict \
        --export-dir results/stage5/author_966/notext/ \
        --ckpt-dir   results/stage5/ckpt/author_966/notext/ 2>&1 | tail -40
      record "A2-NOTEXT-L${L}-S${S}" "${PIPESTATUS[0]}"
    done ;;
  nlinear)
    for S in 42 43 44; do
      SEED=$S
      /usr/bin/time -f "nlinear_L${L}_S${S} wall=%e s" $PY scripts/train_nlinear_966.py \
        --horizon "$L" --seed "$S" --profile author_966 --containment strict \
        --export-dir results/stage5/author_966/nlinear/ \
        --ckpt-dir   results/stage5/ckpt/author_966/nlinear/ 2>&1 | tail -40
      record "A2-NLIN-L${L}-S${S}" "${PIPESTATUS[0]}"
    done ;;
  naive)
    export DEFER_TEST=0
    for LL in 24 36 48 60; do
      for NM in last_value_naive seasonal_naive; do
        SEED=42
        $PY scripts/train_naive_966.py --name "$NM" --horizon "$LL" \
          --profile author_966 --containment strict \
          --export-dir results/stage5/author_966/naive/ 2>&1 | tail -20
        record "A2-$(echo $NM | cut -c1-2 | tr a-z A-Z)-L${LL}" "${PIPESTATUS[0]}"
      done
    done ;;
  *)
    echo "[task] unknown MODEL=$MODEL"; exit 2 ;;
esac

echo "[task] MODEL=$MODEL L=$L end=$(date -u +%FT%TZ)"
