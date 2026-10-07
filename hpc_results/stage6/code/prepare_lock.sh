#!/bin/bash
# Stage 6 step-0: make the A2 trio visible under the stage6 roots so that the
# eight-model lock and the unified Test scoring see one single set of files.
#
# Nothing is copied: the A2 checkpoints and their validation evidence already
# exist under results/stage5 and are covered by the durable archive
# (/home/sychan552/stage5_a2_durable). Symlinks keep a single source of truth,
# so the SHA-256 recorded in CHECKPOINT_LOCK.json is the A2 hash, not a copy's.
set -eo pipefail
cd /scratch/sychan552/a2_stage5

CK6=results/stage6/ckpt/author_966
EX6=results/stage6/author_966
CK5=results/stage5/ckpt/author_966
EX5=results/stage5/author_966
mkdir -p "$CK6" "$EX6"

link_model() {   # $1 = model dir name
  local m="$1" n f
  mkdir -p "$CK6/$m" "$EX6/$m"
  # every A2 checkpoint, by symlink, so hashing follows the real file
  for f in "$CK5/$m"/*.pth "$CK5/$m"/*.frozen_keys.json; do
    [ -e "$f" ] || continue
    n=$(basename "$f")
    [ -e "$CK6/$m/$n" ] || ln -s "$(readlink -f "$f")" "$CK6/$m/$n"
  done
  # validation-selection evidence: metrics.csv, and the miflu training logs
  if [ -e "$EX5/$m/metrics.csv" ]; then
    ln -sf "$(readlink -f "$EX5/$m/metrics.csv")" "$EX6/$m/metrics.csv"
  fi
  if [ "$m" = "miflu" ]; then
    for f in "$EX5/$m"/training_miflu_log_*.txt; do
      [ -e "$f" ] || continue
      ln -sf "$(readlink -f "$f")" "$EX6/$m/$(basename "$f")"
    done
  fi
  echo "  linked $m: $(find "$CK6/$m" -name '*.pth' | wc -l) ckpt"
}

echo "[prep] linking the A2 trio into the stage6 roots"
for m in miflu notext nlinear; do link_model "$m"; done

echo "[prep] staging lock template"
mkdir -p results/stage6
cp -f recovery/stage6/lock_templates.json results/stage6/lock_templates.json
python3 -c "import json,sys; d=json.load(open('results/stage6/lock_templates.json')); print('  template models:', len(d['templates']))"

echo "[prep] A2 models that are still short of 12 fits (expected: none)"
for m in miflu notext nlinear dlinear patchtst itransformer qwen_time_llm calf_llm timecma_llm; do
  n=$(find "$CK6/$m" -name '*.pth' 2>/dev/null | wc -l)
  [ "$n" -eq 12 ] || echo "  WARNING: $m has $n/12 checkpoints"
done
echo "[prep] done"
