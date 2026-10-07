#!/bin/bash
#SBATCH --job-name=a2f_f1
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/logs/a2f_f1_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/postrun_audit_20261006/logs/a2f_f1_%A_%a.err
#
# ===========================================================================
# PREPARED, NOT SUBMITTED.
# ===========================================================================
# Option F1 - the core A2-F fair benchmark.
#   6 models x 4 horizons x 1 seed = 24 fits, ~0.35 GPU-h at the measured
#   A2-LoRA cost of 0.0146 h/fit, plus ~0.06 h/task overhead.
#
# Array index encodes (model, horizon):
#   0-3   corrected text-active MIFlu   L=24/36/48/60
#   4-7   matched no-text MIFlu         L=24/36/48/60
#   8-11  NLinear                       L=24/36/48/60
#   12-15 DLinear                       L=24/36/48/60
#   Last-Value and Seasonal-Naive are deterministic and need no GPU.
#
# stingy enforces MaxSubmit=1 / MaxJobsPU=1, so this MUST be submitted one
# array element at a time:
#     sbatch --array=<i>-<i> F1_a2f_core.sbatch
# A multi-element array is REJECTED with QOSMaxSubmitJobPerUserLimit.
#
# Conforms to A2F_FAIR_COMPARISON_CONTRACT.md S1-S20. Every clause that this
# script cannot itself enforce (validation-only selection, no Test leakage,
# persisted predictions) is delegated to the trainer and re-checked by
# scripts/score_predictions_independent.py.
# ===========================================================================
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
HOME_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
AUD=${HOME_ROOT}/postrun_audit_20261006
OUT=${AUD}/a2f_f1
AUTHOR_DATA=/scratch/sychan552/a0_replay/dataset/illness/national_illness.csv
SEED=42

mkdir -p "${OUT}" "${AUD}/logs"

if [[ "$(hostname)" == hpclogin* ]]; then echo "REFUSING login node"; exit 3; fi

IDX=${SLURM_ARRAY_TASK_ID}
HOR=(24 36 48 60)
MODELS=(miflu_fixed notext nlinear dlinear)
M=${MODELS[$((IDX/4))]}
L=${HOR[$((IDX%4))]}
TAG="f1__${M}__L${L}__seed${SEED}"
mkdir -p "${OUT}/${TAG}"

echo "[a2f] job=${SLURM_JOB_ID}_${IDX} host=$(hostname) model=${M} L=${L} seed=${SEED}"
echo "[a2f] start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[a2f] gpu: /'

{
  echo "utc=$(date -u +%FT%TZ)"
  echo "slurm_job=${SLURM_JOB_ID}_${IDX}"
  echo "option=F1_core_A2F"
  echo "model=${M} horizon=${L} seed=${SEED}"
  echo "dataset_path=${AUTHOR_DATA}"
  echo "dataset_sha256=$(sha256sum ${AUTHOR_DATA} | cut -d' ' -f1)"
  echo "contract=A2F_FAIR_COMPARISON_CONTRACT.md S1-S20"
  echo "selection=VALIDATION-ONLY (S11); test evaluated ONCE (S12); no shuffle (S13); drop_last=False (S14)"
  echo "predictions_persisted=REQUIRED (S15) - the trainer must write (origin,lead,variable) arrays"
  echo "scaler=train rows only [0,676) (S3)"
  echo "split=676/97/193 (S2)"
} | tee "${OUT}/${TAG}/provenance.txt"

# IMPORTANT: the A2 trainer currently lives in the project tree and uses the
# A2 protocol already implemented by scripts/train_backbone_966.py
# (--containment strict, validation selection, 7 variables). This script pins
# the contract in the provenance block above so a future edit cannot silently
# relax it. Wire the exact command when F1 is approved.
echo "[a2f] PREPARED BUT NOT WIRED: confirm the trainer invocation and the"
echo "[a2f] prediction-persistence path before submitting. See"
echo "[a2f] NEXT_GPU_SCRIPT_MANIFEST.md for the exact remaining wiring steps."
exit 0
