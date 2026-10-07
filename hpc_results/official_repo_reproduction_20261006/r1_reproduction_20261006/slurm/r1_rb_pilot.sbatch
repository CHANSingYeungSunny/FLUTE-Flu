#!/bin/bash
#SBATCH --job-name=r1_rb_pilot
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/logs/r1_pilot_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/logs/r1_pilot_%A_%a.err
#
# ===========================================================================
# R1-B  PAPER-INTENDED RECONSTRUCTION PILOT      PREPARED - NOT SUBMITTED
# ===========================================================================
# 4 fits: one declared configuration x horizons 24/36/48/60 x 1 repetition.
# Requires a reproduction-specific GPU authorization AND a working R1-B trainer.
#
# The B-1..B-7 restoration this run must implement:
#   B-1 seven-channel multivariate windows (not feat_id:feat_id+1)
#   B-2 FUNCTIONAL text pathway (text prefixed; patches read after it)
#   B-3 PEFT=1 so LoRA is actually applied; do NOT pass --target_modules
#       (argparse declares type=str with a LIST default; an override breaks peft)
#   B-4 an EFFECTIVE freeze, with the trainable count printed and recorded
#   B-5 validation-only checkpoint selection (released code selects on Test)
#   B-6 persist predictions AND targets (released np.save calls are commented out)
#   B-7 declared training configuration (epochs/lr are undisclosed by the paper)
#
# Every B-item is a DECLARED deviation from released behaviour and must appear in
# the deviation ledger. This run is NOT R1-A (that is already done) and NOT F1.
# ===========================================================================
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
F1ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1=${F1ROOT}/r1
DATA_SHA_EXPECT=2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5

mkdir -p "${R1}"/{logs,ckpt,preds,scoring,manifests}

if [[ "$(hostname)" == hpclogin* ]]; then echo "[r1] REFUSING login node"; exit 3; fi

IDX=${SLURM_ARRAY_TASK_ID}
HOR=(24 36 48 60); L=${HOR[$IDX]}

echo "[r1] job=${SLURM_JOB_ID}_${IDX} host=$(hostname) L=${L} track=R1-B start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[r1] gpu: /'

DATA=/scratch/sychan552/a0_replay/dataset/illness/national_illness.csv
GOT=$(sha256sum "$DATA" | cut -d' ' -f1)
[[ "$GOT" != "$DATA_SHA_EXPECT" ]] && { echo "[r1] FATAL dataset sha ${GOT}"; exit 4; }

{
  echo "track=R1-B paper-intended reconstruction (PILOT, 1 repetition)"
  echo "slurm_job=${SLURM_JOB_ID}_${IDX} horizon=${L} repetition=1"
  echo "dataset=${DATA}"; echo "dataset_sha256=${GOT}"
  echo "contract=B-1 seven channels | B-2 functional prefixed text | B-3 PEFT=1 |"
  echo "         B-4 effective freeze | B-5 validation-only selection |"
  echo "         B-6 persisted predictions | B-7 declared configuration"
  echo "not_R1A=1  not_F1=1"
  echo "verdict_ceiling=PARTIAL_REPRODUCTION (one repetition cannot exceed this)"
} | tee "${R1}/manifests/r1__L${L}.txt"

echo "[r1] BLOCKED: the R1-B trainer does not exist yet."
echo "[r1] Build it (pilot plan option 4a) before enabling this script."
echo "[r1] This stub pins the contract so it cannot be silently relaxed."
exit 0
