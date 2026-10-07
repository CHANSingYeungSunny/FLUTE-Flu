#!/bin/bash
# Archive the Stage 6 eight-model results into the durable home directory,
# mirroring what was done for the A2 stage, and emit a SHA-256 manifest.
set -eo pipefail
SCR=/scratch/sychan552/a2_stage5
DUR=/home/sychan552/stage5_a2_durable/stage6
mkdir -p "$DUR"/{scoring,predictions,logs,per_run,ledgers}

echo "[arch] scoring tables"
cp -f "$SCR"/results/stage6/scoring/*.csv "$DUR/scoring/" 2>/dev/null || true
cp -f "$SCR"/results/stage6/scoring/CHECKPOINT_LOCK.json "$DUR/scoring/" 2>/dev/null || true
cp -f "$SCR"/results/stage6/lock_templates.json "$DUR/" 2>/dev/null || true

echo "[arch] prediction artefacts (NPZ) + manifest + scaler"
cp -f "$SCR"/results/stage6/scoring/predictions/*.npz "$DUR/predictions/" 2>/dev/null || true
cp -f "$SCR"/results/stage6/scoring/predictions/scaler_train_only.json "$DUR/predictions/" 2>/dev/null || true

echo "[arch] per-run validation evidence"
for m in miflu notext nlinear dlinear patchtst itransformer qwen_time_llm calf_llm timecma_llm; do
  mkdir -p "$DUR/per_run/$m"
  cp -f "$SCR"/results/stage6/author_966/$m/metrics.csv "$DUR/per_run/$m/" 2>/dev/null || true
done
cp -f "$SCR"/results/stage5/author_966/miflu/training_miflu_log_*.txt "$DUR/per_run/miflu/" 2>/dev/null || true

echo "[arch] ledgers and logs"
cp -f "$SCR"/results/stage6/logs/run_ledger.csv "$DUR/ledgers/" 2>/dev/null || true
cp -f "$SCR"/results/stage6/logs/pipeline_log.txt "$DUR/ledgers/" 2>/dev/null || true
cp -f "$SCR"/results/stage7/GPU_LEDGER_stage7.tsv "$DUR/ledgers/" 2>/dev/null || true
cp -f "$SCR"/results/stage6/logs/score_*.out "$DUR/logs/" 2>/dev/null || true
cp -f "$SCR"/results/stage6/logs/score_*.err "$DUR/logs/" 2>/dev/null || true

echo "[arch] the exact scripts that produced this, for reproducibility"
mkdir -p "$DUR/code"
for f in scripts/build_lock_stage5.py scripts/score_test_stage5.py \
         recovery/stage6/recompute_eight.py recovery/stage6/prepare_lock.sh \
         recovery/stage6/score_all.sh recovery/stage6/pipeline_stage6.sh \
         recovery/stage6/run_task.sh recovery/a0/a0_gpu_minimal.sh; do
  [ -e "$SCR/$f" ] && cp -f "$SCR/$f" "$DUR/code/$(basename "$f")"
done

echo "[arch] manifest"
cd "$DUR"
find . -type f ! -name 'STAGE6_SHA256SUMS.txt' -print0 \
  | sort -z | xargs -0 sha256sum > STAGE6_SHA256SUMS.txt
echo "  files = $(wc -l < STAGE6_SHA256SUMS.txt)"
du -sh "$DUR"

echo "[arch] spot-check the headline numbers survived the copy"
for f in average_mse_4L.csv CHECKPOINT_LOCK.csv score_summary.csv; do
  [ -e "$DUR/scoring/$f" ] && echo "  OK $f" || echo "  MISSING $f"
done
