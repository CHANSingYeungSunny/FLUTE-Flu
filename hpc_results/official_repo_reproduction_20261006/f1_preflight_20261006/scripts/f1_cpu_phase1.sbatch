#!/bin/bash
#SBATCH --job-name=f1_phase1
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/logs/f1_phase1_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/logs/f1_phase1_%j.err
#
# ===========================================================================
# A2-F CORE FAIR-BENCHMARK PILOT -- PHASE 1 - CPU validation only
# ===========================================================================
# CPU-ONLY, ZERO GPU-HOURS by construction (no gres/gpu requested).
#
# Phase 1 tail : NLinear x4, DLinear x4, Last Value x4, leakage-safe Seasonal Naive x4
# Phase 3      : reload validation-selected checkpoints, evaluate Test ONCE,
#                dump predictions/targets/forecast-key metadata, then run the
#                independent scorer and the F1 success gates.
#
# CHECKPOINT LAYOUT: <F1_ROOT>/ckpt/{miflu,notext,nlinear,dlinear}/ so that
# score_test_stage5.py --ckpt-root <F1_ROOT>/ckpt resolves every arm.
#
# Phase 3 uses score_test_stage5.py, whose --stage6 flag adds the six stage-6
# backbones. Only `dlinear` exists in this ckpt root; the others are reported as
# SKIP and are never averaged in.
#
# SEASONAL NAIVE: uses naive_leakage_safe.py, NOT train_naive_966.py. The legacy
# form ref = ts + s - 52 reads 8 actual target rows at L=60.
#
# Runs FIRST, before any GPU time: it validates the contract cheaply.
# ===========================================================================
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CODE_ROOT=/scratch/sychan552/a2_stage5
F1_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1
F1PRE=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1_preflight_20261006
SEED=42

mkdir -p "${F1_ROOT}"/{logs,preds,ckpt,manifests,scoring}

if [[ "$(hostname)" == hpclogin* ]]; then
  echo "[f1cpu] REFUSING to run on a login node"; exit 3
fi
echo "[f1cpu] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"
echo "[f1cpu] GPU REQUIRED: NO   (no gres/gpu in this job's AllocTRES by construction)"

export F1_CODE_ROOT="${CODE_ROOT}"
export PYTHONPATH="${CODE_ROOT}/scripts:${F1PRE}"
export ACTIVE_PROFILE=author_966
export A2_REQUIRE_STRICT=1
export DEFER_TEST=1
export MPLBACKEND=Agg
export OMP_NUM_THREADS=4
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

cd "${CODE_ROOT}" || exit 2
FAIL=0
run() { echo "[f1cpu] $*"; "$@" || { echo "[f1cpu] FAILED: $*"; FAIL=$((FAIL+1)); }; }

# ── Phase 1 tail: dedicated non-LLM arms (CPU) ──────────────────────────────
for L in 24 36 48 60; do
  run $PY -u scripts/train_nlinear_966.py --horizon $L --seed $SEED \
      --profile author_966 --containment strict \
      --ckpt-dir "${F1_ROOT}/ckpt/nlinear/" \
      --export-dir "${F1_ROOT}/logs/f1__nlinear__L${L}/" 2>&1 | tail -4
done

for L in 24 36 48 60; do
  mkdir -p "${F1_ROOT}/ckpt/dlinear" "${F1_ROOT}/logs/f1__dlinear__L${L}"
  run $PY -u scripts/train_backbone_966.py --backbone dlinear --horizon $L \
      --seed $SEED --profile author_966 --containment strict \
      --ckpt-dir "${F1_ROOT}/ckpt/dlinear/" \
      --export-dir "${F1_ROOT}/logs/f1__dlinear__L${L}/" 2>&1 | tail -4
done

# ── Phase 1 tail: leakage-safe deterministic references ─────────────────────
for L in 24 36 48 60; do
  for NAME in last_value_naive seasonal_naive; do
    run $PY -u "${F1PRE}/f1_naive_runner.py" --name $NAME --horizon $L \
        --seed $SEED --profile author_966 --containment strict \
        --insufficient-history-policy invalid \
        --export-dir "${F1_ROOT}/preds/f1__${NAME}__L${L}__seed${SEED}/" 2>&1 | tail -3
  done
done


# ── Phase 1 gate: scorer contract check on what exists so far ──────────────
echo "[f1cpu] === Phase 1 scorer/contract check (partial, integrity-only) ==="
$PY -u "${F1PRE}/f1_score_all.py"     --pred-root "${F1_ROOT}/preds"     --out-dir "${F1_ROOT}/scoring_phase1"     --expect-seed $SEED --allow-partial 2>&1 | tail -30 || true
echo "  (PARTIAL_DRY_RUN_INTEGRITY_OK is the expected Phase-1 status: the GPU arms have not run yet)"

echo "[f1cpu] Phase 1 failures=${FAIL}"
echo "[f1cpu] Phase 1 end=$(date -u +%FT%TZ)"
exit $(( FAIL > 0 ? 1 : 0 ))
