#!/bin/bash
#SBATCH --job-name=f1_gpu
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/logs/f1_gpu_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1/logs/f1_gpu_%A_%a.err
#
# ===========================================================================
# A2-F CORE FAIR-BENCHMARK PILOT, ONE SEED   --  AUTHORIZED 0.60 GPU-h
# ===========================================================================
# Phase 2 of the approved sequence: the two LLM-based arms.
#   index 0-3 : corrected text-active MIFlu   L = 24/36/48/60
#   index 4-7 : matched no-text MIFlu         L = 24/36/48/60
#
# CHECKPOINT LAYOUT (verified against score_test_stage5.py's expectations):
#   ${F1_ROOT}/ckpt/<sub>/best_<file>_L<L>_seed<s>.pth
#   sub = miflu | notext | nlinear | dlinear
#   The Phase-3 scorer is invoked with --ckpt-root ${F1_ROOT}/ckpt and looks up
#   <root>/<sub>/<template>. The earlier draft wrote
#   ${F1_ROOT}/ckpt/f1__<model>__L<L>__seed<s>/ which the scorer CANNOT find;
#   that wiring defect was caught by the final execution gate and is fixed here.
#
# CONTRACT: A2-F corrected fair-comparison contract (see
# ../F1_SHARED_EVALUATION_CONTRACT.md). DEFER_TEST=1 means NO Test evaluation
# happens here - Test is evaluated once, in Phase 3.
#
# Authorization: 0.60 GPU-h max for the whole pilot. This element costs
# ~0.0533 GPU-h. Budget is checked by the launcher before every submission.
#
# WRITES GO TO HOME. Scratch is over quota and is used READ-ONLY for the code.
# ===========================================================================
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CODE_ROOT=/scratch/sychan552/a2_stage5          # READ-ONLY
F1_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006/f1
SEED=42
DATA_SHA_EXPECT=2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5

mkdir -p "${F1_ROOT}"/{logs,preds,ckpt,manifests}

if [[ "$(hostname)" == hpclogin* ]]; then
  echo "[f1] REFUSING to run on a login node"; exit 3
fi

IDX=${SLURM_ARRAY_TASK_ID}
HOR=(24 36 48 60)
if (( IDX < 4 )); then ARM="miflu"; L=${HOR[$IDX]}; else ARM="notext"; L=${HOR[$((IDX-4))]}; fi
TAG="f1__${ARM}__L${L}__seed${SEED}"
CKD="${F1_ROOT}/ckpt/${ARM}"                    # scorer-compatible subdirectory
METD="${F1_ROOT}/logs/${TAG}"
mkdir -p "${CKD}" "${METD}"

echo "[f1] job=${SLURM_JOB_ID}_${IDX} host=$(hostname) arm=${ARM} L=${L} seed=${SEED}"
echo "[f1] start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[f1] gpu: /'

DATA=/scratch/sychan552/a0_replay/dataset/illness/national_illness.csv
GOT_SHA=$(sha256sum "$DATA" | cut -d' ' -f1)
if [[ "$GOT_SHA" != "$DATA_SHA_EXPECT" ]]; then
  echo "[f1] FATAL: dataset sha256 ${GOT_SHA} != expected ${DATA_SHA_EXPECT}"; exit 4
fi
echo "[f1] dataset OK sha256=${GOT_SHA}"

export F1_CODE_ROOT="${CODE_ROOT}"
export PYTHONPATH="${CODE_ROOT}/scripts"
export HF_HOME=/home/sychan552/.cache/huggingface
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1
export ACTIVE_PROFILE=author_966
export A2_REQUIRE_STRICT=1
export DEFER_TEST=1
export MPLBACKEND=Agg

{
  echo "utc=$(date -u +%FT%TZ)"
  echo "slurm_job=${SLURM_JOB_ID}_${IDX}"
  echo "option=F1 core A2-F pilot (one seed)"
  echo "arm=${ARM} horizon=${L} seed=${SEED}"
  echo "code_root=${CODE_ROOT}"
  echo "dataset_path=${DATA}"
  echo "dataset_sha256=${GOT_SHA}"
  echo "checkpoint_dir=${CKD}"
  echo "checkpoint_file=best_$([ "${ARM}" = notext ] && echo ablation_no_multi || echo ${ARM})_L${L}_seed${SEED}.pth"
  echo "containment=strict"
  echo "checkpoint_selection=best VALIDATION mse_all"
  echo "test_evaluated_during_fit=NO (DEFER_TEST=1)"
  echo "shuffle=val:False test:False ; drop_last=False"
  echo "predictions_dumped_by=score_test_stage5.py in Phase 3"
  echo "epochs=20 batch=16 lr=5e-4 optimizer=Adam"
  echo "track=A2-F"
} | tee "${METD}/provenance.txt"

cd "${CODE_ROOT}" || exit 2
if [[ "${ARM}" == "miflu" ]]; then
  $PY -u scripts/train_miflu.py --horizon "${L}" --seed "${SEED}" --reps 1 \
      --epochs 20 --batch 16 --profile author_966 --containment strict \
      --export-dir "${METD}/" --ckpt-dir "${CKD}/" 2>&1 | tee "${METD}/train.log"
  rc=${PIPESTATUS[0]}
else
  $PY -u scripts/train_ablation.py --variant no_multi \
      --horizon "${L}" --seed "${SEED}" --reps 1 --epochs 20 --batch 16 \
      --profile author_966 --containment strict \
      --export-dir "${METD}/" --ckpt-dir "${CKD}/" 2>&1 | tee "${METD}/train.log"
  rc=${PIPESTATUS[0]}
fi

echo "[f1] fit rc=${rc} end=$(date -u +%FT%TZ)"

el=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
{
  echo "tag=${TAG}"; echo "arm=${ARM}"; echo "horizon=${L}"; echo "seed=${SEED}"
  echo "slurm_job=${SLURM_JOB_ID}_${IDX}"; echo "elapsed=${el:-unknown}"
  echo "fit_exit_code=${rc}"; echo "checkpoint_dir=${CKD}"; echo "test_deferred=1"
} > "${F1_ROOT}/manifests/${TAG}.txt"

printf 'F1_GPU\t%s_%s\t%s\tL%s\tseed%s\t%s\trc=%s\n' \
  "${SLURM_JOB_ID}" "${IDX}" "${ARM}" "${L}" "${SEED}" "${el:-unknown}" "${rc}" \
  >> "${F1_ROOT}/manifests/GPU_LEDGER_F1.tsv"

ls -1 "${CKD}" 2>/dev/null | sed 's/^/[f1] ckpt: /'
exit ${rc}