#!/bin/bash
#SBATCH --job-name=f1_phase3
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=02:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/logs/f1_phase3_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/logs/f1_phase3_%j.err
#
# ===========================================================================
# A2-F CORE FAIR-BENCHMARK PILOT -- PHASE 3
# Test evaluation (once), prediction dump, independent scoring, text-path probe
# ===========================================================================
# CPU-ONLY, ZERO GPU-HOURS (no gres/gpu requested).
#
# TWO DEFECTS FIXED HERE, both found by running Phase 3 once and inspecting it:
#
#  D1  the previous version contained an `exit` BEFORE the Phase 3b block, so
#      the text-path probe never executed (grep for its output returned 0 lines).
#      The exit now sits only at the very end.
#
#  D2  score_test_stage5.py ALSO dumps naive baselines of its own, computed with
#      the LEAKY naive_pred() inside that file (ref = ts + s - 52, which reads
#      actual target rows at L=60). Those 8 artefacts collided on
#      (model, L, seed) with the leakage-safe artefacts from f1_naive_runner.py,
#      and the aggregator would have MIXED a leaky reference with a corrected
#      one - the 2.245545 that appeared in the first run was exactly that
#      mixture, and it is meaningless. So the learner dump now goes to its own
#      directory and a curated 24-artefact set is assembled below.
#
# The four LEARNED models were unaffected by D2 and their GPU checkpoints are
# untouched; only this CPU stage is re-run.
# ===========================================================================
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CODE_ROOT=/scratch/sychan552/a2_stage5
F1_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1
F1PRE=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1_preflight_20261006
SEED=42

mkdir -p "${F1_ROOT}"/{logs,preds,preds_learned,ckpt,manifests,scoring}

if [[ "$(hostname)" == hpclogin* ]]; then
  echo "[f1cpu] REFUSING to run on a login node"; exit 3
fi
echo "[f1cpu] host=$(hostname) job=${SLURM_JOB_ID} start=$(date -u +%FT%TZ)"
echo "[f1cpu] GPU REQUIRED: NO (no gres/gpu in this job's AllocTRES by construction)"

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

# ── Phase 3a: reload validation-selected checkpoints, evaluate Test ONCE ────
echo "[f1cpu] === Phase 3a: Test evaluation + prediction dump ==="
run $PY -u scripts/score_test_stage5.py \
    --profile author_966 --containment strict \
    --ckpt-root "${F1_ROOT}/ckpt" \
    --export-dir "${F1_ROOT}/scoring" \
    --dump-dir "${F1_ROOT}/preds_learned" \
    --horizons 24,36,48,60 \
    --stage6 \
    --device cpu 2>&1 | tail -40

# ── Phase 3a2: assemble the curated scoring set ─────────────────────────────
# Exactly ONE artefact per (model, horizon):
#   the 4 learned models  <- preds_learned  (miflu, notext, nlinear, dlinear)
#   the 2 naive references <- preds/        (LEAKAGE-SAFE versions only)
echo "[f1cpu] === Phase 3a2: assembling the curated scoring set ==="
FINAL="${F1_ROOT}/preds_final"
rm -rf "${FINAL}"; mkdir -p "${FINAL}"
for L in 24 36 48 60; do
  for M in miflu notext nlinear dlinear; do
    SRC="${F1_ROOT}/preds_learned/pred_${M}_L${L}_s${SEED}.npz"
    if [[ -f "${SRC}" ]]; then cp -f "${SRC}" "${FINAL}/"
    else echo "  [WARN] missing learned artefact ${M} L=${L}"; FAIL=$((FAIL+1)); fi
  done
done
for L in 24 36 48 60; do
  for N in last_value_naive seasonal_naive; do
    SRC="${F1_ROOT}/preds/f1__${N}__L${L}__seed${SEED}/pred_${N}_L${L}_s${SEED}.npz"
    if [[ -f "${SRC}" ]]; then cp -f "${SRC}" "${FINAL}/"
    else echo "  [WARN] missing leakage-safe artefact ${N} L=${L}"; FAIL=$((FAIL+1)); fi
  done
done
echo "  curated set: $(ls -1 ${FINAL}/*.npz 2>/dev/null | wc -l) artefacts (expect 24)"

# ── Phase 3b: independent scoring + success gates ───────────────────────────
echo "[f1cpu] === Phase 3b: independent scoring ==="
run $PY -u "${F1PRE}/f1_score_all.py" \
    --pred-root "${FINAL}" \
    --out-dir "${F1_ROOT}/scoring" \
    --expect-seed $SEED 2>&1 | tail -50

# ── Phase 3c: text-path verification on the selected corrected-MIFlu ckpts ──
echo "[f1cpu] === Phase 3c: text-path probe on the corrected MIFlu checkpoints ==="
for L in 24 36 48 60; do
  CK="${F1_ROOT}/ckpt/miflu/best_miflu_L${L}_seed${SEED}.pth"
  if [[ -f "${CK}" ]]; then
    run $PY -u "${F1PRE}/f1_text_probe.py" \
        --ckpt "${CK}" --L ${L} --code-root "${CODE_ROOT}" \
        --out "${F1_ROOT}/scoring/text_path_probe_L${L}.json" 2>&1 | tail -6
  else
    echo "  [SKIP] no corrected-MIFlu checkpoint for L=${L}"
  fi
done

echo "[f1cpu] Phase 3 failures=${FAIL}"
echo "[f1cpu] Phase 3 end=$(date -u +%FT%TZ)"
exit $(( FAIL > 0 ? 1 : 0 ))