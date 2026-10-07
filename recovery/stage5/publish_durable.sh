#!/bin/bash
# Stage 5 A2 — publish the round's key artefacts to a persistent location.
# scratch (/gpfs1/scratch) has a 10-day grace period; home is the durable store.
# Checkpoints (5.0 GB) are NOT copied — their full SHA-256 is already recorded in
# CHECKPOINT_LOCK.json, and the files stay available on scratch meanwhile.
set -e
SRC=/scratch/sychan552/a2_stage5
DST=/home/sychan552/stage5_a2_durable
mkdir -p "$DST"/{scoring,logs,per_run}

cp -a "$SRC"/results/stage5/scoring/. "$DST/scoring/"
cp -a "$SRC"/results/stage5/logs/run_ledger.csv "$DST/logs/"
cp -a "$SRC"/results/stage5/logs/run_ledger_pre_fix.csv "$DST/logs/" 2>/dev/null || true
cp -a "$SRC"/results/stage5/logs/dispatch_log.txt "$DST/logs/" 2>/dev/null || true
cp -a "$SRC"/results/stage5/logs/dispatch_notext_topup.out "$DST/logs/" 2>/dev/null || true
cp -a "$SRC"/results/stage5/logs/gpu_ledger.txt "$DST/logs/" 2>/dev/null || true
cp -a "$SRC"/results/stage5/logs/task_5858*.out "$DST/logs/" 2>/dev/null || true
cp -a "$SRC"/results/stage5/logs/score_585883.out "$DST/logs/" 2>/dev/null || true
cp -a "$SRC"/results/stage5/logs/score_585883.err "$DST/logs/" 2>/dev/null || true
cp -a "$SRC"/results/stage5/logs/preflight_584886.out "$DST/logs/" 2>/dev/null || true

# per-run validation-selection evidence
for m in miflu notext nlinear naive; do
  mkdir -p "$DST/per_run/$m"
  cp -a "$SRC"/results/stage5/author_966/$m/metrics.csv "$DST/per_run/$m/" 2>/dev/null || true
  cp -a "$SRC"/results/stage5/author_966/$m/training_*.txt "$DST/per_run/$m/" 2>/dev/null || true
  cp -a "$SRC"/results/stage5/author_966/$m/training_ablation.log "$DST/per_run/$m/" 2>/dev/null || true
done

# data + code identity actually used
mkdir -p "$DST/data"
cp -a "$SRC"/data/raw/*.csv "$DST/data/" 2>/dev/null || true
cp -a "$SRC"/data/scaler_miflu_author966.json "$DST/data/" 2>/dev/null || true
cp -a "$SRC"/recovery/stage5/frozen_protocol_stage5.md "$DST/" 2>/dev/null || true
cp -a "$SRC"/recovery/stage5/hashes_stage5.json "$DST/" 2>/dev/null || true
cp -a "$SRC"/recovery/stage5/final_run_matrix.csv "$DST/" 2>/dev/null || true

# code actually executed
mkdir -p "$DST/code"
for f in train_miflu.py train_ablation.py train_nlinear_966.py train_naive_966.py \
         score_test_stage5.py build_lock_stage5.py configs.py textual_embedder.py \
         scaler_utils.py cdc_calendar.py miflu_model.py early_stopping.py; do
  cp -a "$SRC/scripts/$f" "$DST/code/" 2>/dev/null || true
done
cp -a "$SRC"/recovery/stage5/recompute_from_artifacts.py "$DST/code/" 2>/dev/null || true
cp -a "$SRC"/recovery/stage5/run_task.sh "$DST/code/" 2>/dev/null || true
cp -a "$SRC"/recovery/stage5/score_all.sh "$DST/code/" 2>/dev/null || true
cp -a "$SRC"/recovery/stage5/dispatch_notext_topup.sh "$DST/code/" 2>/dev/null || true
( cd "$DST/code" && sha256sum * > CODE_SHA256SUMS.txt )

( cd "$DST" && find . -type f -exec sha256sum {} + | sort -k2 > STAGE5_A2_DURABLE_SHA256SUMS.txt )

echo "=== published ==="
du -sh "$DST"
find "$DST" -maxdepth 2 -type d | sort
wc -l "$DST/STAGE5_A2_DURABLE_SHA256SUMS.txt"
