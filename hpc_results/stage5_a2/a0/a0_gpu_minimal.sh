#!/bin/bash
#SBATCH --job-name=a0_gpu
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=24G
#SBATCH --time=00:40:00
#SBATCH --output=/scratch/sychan552/a0_runs/logs/a0_%j.out
#SBATCH --error=/scratch/sychan552/a0_runs/logs/a0_%j.err
#
# A0 — minimal executable diagnostic of the AUTHOR'S RELEASED CODE.
#
# NOT SUBMITTED. Held pending an explicit additional compute authorization
# (see recovery/stage6/cost_and_matrix_zh.md, A0 row: ~0.5 GPU-h for both runs).
#
# WHAT THIS IS, AND IS NOT
#   * It replays `main_ILI_lora.py` VERBATIM (the author's tree is not modified;
#     the compatibility layer lives in a separate sys.path directory).
#   * It uses the author's argparse DEFAULTS, including train_epochs=1 and
#     learning_rate=0.0001, because the paper does not state either value.
#   * It therefore CANNOT reproduce the paper's Table V, and its Test numbers
#     are NOT a new independent generalisation result: the released code scores
#     feature 0 only and selects its checkpoint by Test MSE.
#   * MODE=0 -> released default (multimodal=0). MODE=1 -> multimodal=1, which
#     is numerically expected to be IDENTICAL because the CPU proof already
#     showed a text gradient of exactly 0 and a text-substitution output
#     difference of exactly 0.
set -uo pipefail
A0=/scratch/sychan552/a0_replay
SHIM=/scratch/sychan552/a0_compat_shim
OUT=/scratch/sychan552/a0_runs
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
export PYTHONPATH="$SHIM:$A0"
mkdir -p "$OUT/logs" "$OUT/runs"

MODE=${MODE:-0}
TAG=$([ "$MODE" = "1" ] && echo "multimodal1" || echo "default")

echo "[a0gpu] mode=$MODE tag=$TAG job=$SLURM_JOB_ID start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[a0gpu] gpu: /'

# Recorded provenance of the replayed tree, so the run cannot be mistaken for
# a modified author implementation.
{
  echo "utc=$(date -u +%FT%TZ)"
  echo "author_commit=$(cd $A0 && git rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "author_tree_sha256_main=$(sha256sum $A0/main_ILI_lora.py | cut -d' ' -f1)"
  echo "author_tree_sha256_model=$(sha256sum $A0/models/GPT4TS_lora.py | cut -d' ' -f1)"
  echo "author_tree_sha256_loader=$(sha256sum $A0/data_provider/data_loader.py | cut -d' ' -f1)"
  echo "compat_layer_sha256=$(sha256sum $SHIM/a0_compat.py | cut -d' ' -f1)"
  echo "data_sha256=$(sha256sum $A0/dataset/illness/national_illness.csv | cut -d' ' -f1)"
  echo "note=AUTHOR CODE REPLAYED VERBATIM under a recorded compatibility layer; NOT the A2 corrected reconstruction"
} | tee "$OUT/runs/${TAG}_provenance.txt"

cd "$A0" || exit 2
$PY -u main_ILI_lora.py \
    --model_id "a0_$TAG" \
    --root_path './dataset/illness/' \
    --data_path 'national_illness.csv' \
    --checkpoints "$OUT/runs/" \
    --multimodal "$MODE" \
    --seq_len 104 --label_len 18 --pred_len 24 \
    --patch_size 24 --stride 2 \
    --d_model 768 --n_heads 4 --e_layers 3 --d_ff 768 --dropout 0.2 \
    --gpt_layers 6 --backbone gpt2 --textmodel gpt2 \
    --enc_in 7 --c_out 7 --features M --target OT --embed timeF \
    --freeze 1 --pretrain 1 --PEFT 0 --lora_r 4 \
    --learning_rate 0.0001 --batch_size 16 --num_workers 4 \
    --train_epochs 1 --patience 3 --itr 1 --cos 0 \
    --loss_func mse --decay_fac 0.75 --tmax 10 --hid_dim 16 --max_len -1
rc=$?

echo
echo "[a0gpu] released entry point exit=$rc  $(date -u +%FT%TZ)"
echo "[a0gpu] produced:"
ls -la "$OUT/runs/" | sed 's/^/  /'
echo
echo "[a0gpu] REMINDER: whatever this prints is (a) feature-0 Test only,"
echo "          (b) selected by Test MSE, (c) 1 epoch at lr 1e-4, and"
echo "          (d) therefore NOT comparable to the paper's Table V nor to A2."
exit $rc
