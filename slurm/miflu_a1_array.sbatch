#!/bin/bash
#SBATCH --job-name=miflu_a1
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=04:00:00
#SBATCH --array=0-3
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/a1_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/a1_%A_%a.err
#
# A1 — reconstructed paper configuration, run on the AUTHOR's own released entry
# point `main_ILI_lora.py`. This is NOT a reproduction claim; the paper discloses
# no epochs and no learning rate, so 20 epochs / lr 5e-4 are a DECLARED
# RECONSTRUCTED ASSUMPTION (see HYPERPARAMETER_PROVENANCE.md).
#
# Array indices are the four horizons:
#   0 -> L=24, 1 -> L=36, 2 -> L=48, 3 -> L=60
#
# Repetitions: the paper says "mean of 10 repetitions". The author's own harness
# implements repetitions as `--itr`, so A1 uses --itr ${MIFLU_ITR} (default 3,
# matching the Track-A seed count so the two are directly comparable). Setting
# MIFLU_ITR=10 reproduces the paper's repetition count.
#
# KNOWN DEFECTS KEPT (author's code, not repaired at A1):
#   * Test MSE selects the best checkpoint every epoch (lines 211/225/264)
#   * early stopping instantiated but its call is commented out (lines 235-236)
#   * `freeze` loop only ever sets requires_grad=True -> everything trainable
#   A1 keeps these because A1 = author code + paper settings + minimal execution
#   fixes only. A2 is the corrected benchmark that repairs them.
#
# WRITES GO TO HOME: the scratch user quota is over its limit (grace expired),
# so /gpfs1/scratch writes fail. Scratch is READ-ONLY here.
#
# NEVER run this on the login node.
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
HOME_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
A0=/scratch/sychan552/a0_replay                 # author repo (READ ONLY)
COMPAT=${HOME_ROOT}/hpc_compat
WORK=${HOME_ROOT}/a1_work
ITR=${MIFLU_ITR:-3}

mkdir -p "${WORK}"/{results,checkpoints} "${HOME_ROOT}/logs"
# the released model reads its text assets through a RELATIVE path, so the CWD
# must expose dataset/illness/text_emb/. A symlink keeps that read-only.
ln -sfn "${A0}/dataset" "${WORK}/dataset"

HORIZONS=(24 36 48 60)
L=${HORIZONS[$SLURM_ARRAY_TASK_ID]}
VARIANT="a1_reconstructed"
TAG="${VARIANT}_L${L}_itr${ITR}"
OUTD=${HOME_ROOT}/a1/L${L}
mkdir -p "${OUTD}"

echo "[a1] job=${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID} host=$(hostname) L=${L} itr=${ITR}"
echo "[a1] start=$(date -u +%FT%TZ)"
if [[ "$(hostname)" == hpclogin* ]]; then echo "[a1] REFUSING to run on a login node"; exit 3; fi
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[a1] gpu: /'

{
  echo "utc=$(date -u +%FT%TZ)"
  echo "slurm_job=${SLURM_JOB_ID}_${SLURM_ARRAY_TASK_ID}"
  echo "author_commit=$(git -C ${A0} rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "author_source_modified=$(git -C ${A0} status --porcelain | grep -v '\.pyc$' | wc -l) non-pyc entries"
  echo "data_sha256=$(sha256sum ${A0}/dataset/illness/national_illness.csv | cut -d' ' -f1)"
  echo "text_asset_sha256=$(sha256sum ${A0}/dataset/illness/text_emb/text_emb_label_0507_${L}.txt | cut -d' ' -f1)"
  echo "horizon=${L} itr=${ITR} multimodal=1 PEFT=1 lora_r=4"
  echo "epochs=20 epochs_provenance=RECONSTRUCTED_paper_discloses_no_value"
  echo "learning_rate=5e-4 lr_provenance=RECONSTRUCTED_paper_discloses_no_value"
  echo "batch_size=16 batch_provenance=released_default_and_A2_value"
  echo "itr_provenance=paper_says_mean_of_10_repetitions_author_harness_implements_itr"
  echo "known_defects_kept=Test-selects-checkpoint; early_stopping_call_commented_out; freeze_is_noop"
} | tee "${OUTD}/provenance.txt"

cd "${WORK}" || exit 2
export PYTHONPATH="${COMPAT}:${A0}:${PYTHONPATH:-}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

START=$(date +%s)
$PY -u "${A0}/main_ILI_lora.py" \
    --model_id "${TAG}" \
    --checkpoints "${WORK}/checkpoints/" \
    --multimodal 1 \
    --root_path './dataset/illness/' \
    --data_path 'national_illness.csv' \
    --data 'custom' --features 'M' --target 'OT' --embed 'timeF' --freq 0 \
    --percent 100 --max_len -1 --hid_dim 16 \
    --seq_len 104 --label_len 18 --pred_len "${L}" \
    --patch_size 24 --stride 2 --kernel_size 25 \
    --d_model 768 --n_heads 4 --e_layers 3 --d_ff 768 --dropout 0.2 \
    --gpt_layers 6 --backbone 'gpt2' --textmodel 'gpt2' \
    --enc_in 862 --c_out 862 --model 'model' \
    --lora_r 4 --PEFT 1 --freeze 1 --pretrain 1 \
    `# --target_modules is deliberately NOT passed: main_ILI_lora.py declares` \
    `# it type=str with a LIST default (["c_attn"]), so any CLI override` \
    `# arrives as the bare string "c_attn", which peft 0.17.1 cannot resolve` \
    `# and get_peft_model raises "Target modules c_attn not found". Letting the` \
    `# author's own list default through keeps LoRA working (verified on CPU job` \
    `# 606362). Recorded in DEVIATION_LEDGER.` \
    --learning_rate 0.0005 --batch_size 16 --num_workers 4 \
    --train_epochs 20 --patience 3 --lradj 'type1' --cos 0 --tmax 10 --decay_fac 0.75 \
    --loss_func 'mse' --itr "${ITR}" 2>&1 | tee "${OUTD}/train.log"
rc=${PIPESTATUS[0]}
END=$(date +%s)
echo "[a1] author rc=${rc} wall_s=$((END-START)) end=$(date -u +%FT%TZ)"
echo "wall_seconds=$((END-START))" >> "${OUTD}/provenance.txt"
echo "author_exit_code=${rc}" >> "${OUTD}/provenance.txt"

# preserve the released code's own summary CSV (it writes ./results/<setting>.csv)
shopt -s nullglob
for f in "${WORK}"/results/*"${TAG}"*.csv; do cp -f "$f" "${OUTD}/" && echo "[a1] saved $(basename $f)"; done
for f in "${WORK}"/checkpoints/*"${TAG}"*/checkpoint.pth; do cp -f "$f" "${OUTD}/checkpoint.pth" && echo "[a1] saved checkpoint.pth"; done
shopt -u nullglob

# GPU charge for this array element
el=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
printf 'A1\t%s_%s\tL%s\titr%s\t%s\t%s\n' "${SLURM_JOB_ID}" "${SLURM_ARRAY_TASK_ID}" \
  "${L}" "${ITR}" "${el:-unknown}" "${rc}" >> "${HOME_ROOT}/a1/GPU_LEDGER_A1.tsv"

exit 0
