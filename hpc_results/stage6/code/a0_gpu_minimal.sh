#!/bin/bash
#SBATCH --job-name=a0_gpu
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --mem=24G
#SBATCH --time=00:30:00
#SBATCH --output=/scratch/sychan552/a0_runs/logs/a0_%j.out
#SBATCH --error=/scratch/sychan552/a0_runs/logs/a0_%j.err
#
# A0 — minimal executable diagnostic of the AUTHOR'S RELEASED CODE.
# Authorized 2026-09-26 as part of the 2.3 GPU-hour round (A0 sub-budget 0.5).
#
# WHAT THIS IS, AND IS NOT
#   * It replays `main_ILI_lora.py` VERBATIM. The author's tree is verified
#     byte-for-byte unmodified (`git status` shows only regenerated __pycache__
#     .pyc); the compatibility layer lives in a separate sys.path directory.
#   * EVERY argument below is the author's own argparse DEFAULT (read from
#     main_ILI_lora.py lines 34-85 and printed in the provenance header). The
#     paper states no epochs and no learning rate, so the released defaults
#     (train_epochs=1, learning_rate=0.0001) are the only defensible choice.
#   * It therefore CANNOT reproduce the paper's Table V. Its Test numbers are
#     NOT a new independent generalisation result: the released code scores
#     feature 0 only and selects its checkpoint by Test MSE.
#   * MODE=0 -> released default (multimodal=0). MODE=1 -> multimodal=1, which
#     is numerically expected to be IDENTICAL because the CPU proof already
#     measured a text gradient of exactly 0 and a text-substitution output
#     difference of exactly 0.
set -uo pipefail
A0=/scratch/sychan552/a0_replay
SHIM=/scratch/sychan552/a0_compat_shim
OUT=/scratch/sychan552/a0_runs
LEDGER=/scratch/sychan552/a2_stage5/results/stage7/GPU_LEDGER_stage7.tsv
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1
export PYTHONPATH="$SHIM:$A0"
mkdir -p "$OUT/logs" "$OUT/runs" "$SHIM"

# ---- build the compatibility layer (idempotent; author's tree untouched) ----
# einops: the released model uses exactly 3 rearrange patterns.
printf 'from a0_compat import rearrange\n__all__ = ["rearrange"]\n' > "$SHIM/einops.py"
# embed.py: imported at GPT4TS_lora.py line 10 and then NEVER referenced (the real
# projection is nn.Linear(patch_size, d_model)). a0_compat carries the structures
# recovered from the author's own __pycache__/embed.cpython-39.pyc.
printf 'from a0_compat import DataEmbedding, DataEmbedding_wo_pos, DataEmbedding_wo_time\n' \
  > "$SHIM/embed.py"
# NumPy 2.0 alias restoration + the peft symbol removed in >=0.8.
cp -f /scratch/sychan552/a2_stage5/recovery/a0/a0_sitecustomize.py "$SHIM/sitecustomize.py"
cp -f /scratch/sychan552/a2_stage5/recovery/a0/a0_compat.py      "$SHIM/a0_compat.py"
echo "[a0gpu] compat layer sha256:"
sha256sum "$SHIM/a0_compat.py" "$SHIM/sitecustomize.py" | sed 's/^/  /'

MODE=${MODE:-0}
TAG=$([ "$MODE" = "1" ] && echo "multimodal1" || echo "default")
LOG="$OUT/logs/${TAG}_stdout.txt"

echo "[a0gpu] mode=$MODE tag=$TAG job=$SLURM_JOB_ID start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[a0gpu] gpu: /'

# ---- provenance: everything needed to re-identify this run later ----------
{
  echo "utc=$(date -u +%FT%TZ)"
  echo "slurm_job=$SLURM_JOB_ID"
  echo "author_commit=$(cd $A0 && git rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "author_source_modified=$(cd $A0 && git status --porcelain | grep -v '\.pyc$' | wc -l) non-pyc entries"
  for f in main_ILI_lora.py models/GPT4TS_lora.py models/GPT4TS.py \
           data_provider/data_loader.py data_provider/data_factory.py; do
    echo "author_src_$(echo $f | tr '/' '_')=$(sha256sum $A0/$f | cut -d' ' -f1)"
  done
  echo "compat_layer_sha256=$(sha256sum $SHIM/a0_compat.py | cut -d' ' -f1)"
  echo "compat_sitecustomize_sha256=$(sha256sum $SHIM/sitecustomize.py | cut -d' ' -f1)"
  echo "compat_non_behavioural_evidence=np.Inf restored as the IDENTICAL np.inf object (asserted at import); peft symbol appears only inside a comment in the released code; DataEmbedding imported but never referenced"
  echo "data_sha256=$(sha256sum $A0/dataset/illness/national_illness.csv | cut -d' ' -f1)"
  echo "text_asset_sha256=$(sha256sum $A0/dataset/illness/text_emb/text_emb_label_0507_24.txt | cut -d' ' -f1)"
  echo "config=ALL ARGUMENTS ARE THE AUTHOR'S ARGPARSE DEFAULTS (main_ILI_lora.py L34-85)"
  echo "mode=$MODE multimodal=$MODE train_epochs=1 learning_rate=0.0001 batch_size=16 itr=1 pred_len=24"
  echo "note=AUTHOR CODE REPLAYED VERBATIM under a recorded compatibility layer;"
  echo "     NOT the A2 corrected reconstruction; NOT comparable to Table V or A2"
} | tee "$OUT/runs/${TAG}_provenance.txt"

cd "$A0" || exit 2
# main_ILI_lora.py line 251 hard-codes './results/'+setting+'.csv' for its summary
# write, ignoring --checkpoints. A0 MODE=0 (job 587059) died there with
# OSError: Cannot save file into a non-existent directory: 'results' AFTER the
# train/val/test numbers had already been printed. Creating the directory is the
# minimal, non-behavioural change that lets the released code run to completion.
mkdir -p results
$PY -u main_ILI_lora.py \
    --model_id "a0_$TAG" \
    --checkpoints "$OUT/runs/" \
    --multimodal "$MODE" \
    --root_path './dataset/illness/' \
    --data_path 'national_illness.csv' \
    --data 'custom' --features 'M' --target 'OT' --embed 'timeF' --freq 0 \
    --percent 100 --max_len -1 --hid_dim 16 \
    --seq_len 104 --label_len 18 --pred_len 24 \
    --patch_size 24 --stride 2 --kernel_size 25 \
    --d_model 768 --n_heads 4 --e_layers 3 --d_ff 768 --dropout 0.2 \
    --gpt_layers 6 --backbone 'gpt2' --textmodel 'gpt2' \
    --enc_in 862 --c_out 862 --model 'model' \
    --lora_r 4 --PEFT 0 --freeze 1 --pretrain 1 \
    --learning_rate 0.0001 --batch_size 16 --num_workers 10 \
    --train_epochs 1 --patience 3 --lradj 'type1' --cos 0 --tmax 10 --decay_fac 0.75 \
    --loss_func 'mse' --itr 1 2>&1 | tee "$LOG"
rc=${PIPESTATUS[0]}

echo
echo "[a0gpu] released entry point exit=$rc  $(date -u +%FT%TZ)"
echo "[a0gpu] files produced under $OUT/runs:"
find "$OUT/runs" -newermt '-2 hours' -type f | sed 's/^/  /'
echo
echo "[a0gpu] ---- key evidence lines from the released run ----"
grep -n -E "^(train|val|test) [0-9]+ |Epoch|mse|MSE|MAE|Best performance|Args in experiment" "$LOG" \
  | tail -40 | sed 's/^/  /'
echo
echo "[a0gpu] REMINDER: whatever this prints is (a) feature-0 Test only,"
echo "          (b) selected by Test MSE, (c) 1 epoch at lr 1e-4, and"
echo "          (d) therefore NOT comparable to the paper's Table V nor to A2."

# ---- append this job's real GPU charge to the round ledger -----------------
mkdir -p "$(dirname "$LEDGER")"
elapsed_h=$(sacct -j "$SLURM_JOB_ID" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
printf 'A0_GPU_MINIMAL\t%s\t%s\t%s\t%s\n' \
  "$SLURM_JOB_ID" "$TAG" "${elapsed_h:-unknown}" "author_code_verbatim_replay" >> "$LEDGER"
echo "[a0gpu] charged ${elapsed_h} (job $SLURM_JOB_ID) appended to $LEDGER"

# The released entry point exits non-zero even when the diagnostic itself
# succeeded (MODE=0 job 587059 raised at main_ILI_lora.py:251). The diagnostic
# outcome is judged by whether the evidence was produced, not by the author's
# exit code, so report success here and keep the author's code untouched.
if [ -s "$LOG" ] && grep -qE "mse" "$LOG"; then
  echo "[a0gpu] diagnostic evidence present; reporting job success (author rc=$rc)"
  exit 0
fi
echo "[a0gpu] NO diagnostic evidence in $LOG; reporting failure (author rc=$rc)"
exit 1
