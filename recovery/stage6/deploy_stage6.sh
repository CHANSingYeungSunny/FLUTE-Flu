#!/bin/bash
# Stage 6 — deploy the eight-model runner + A0 author-repo replay to the HPC.
# Versioned deploy dir; never rsync --delete; never overwrite a running job's code.
set -euo pipefail
DST=/scratch/sychan552/a2_stage5
LOCAL=/scratch/sychan552/a2_stage5_local_stage6   # unused; keep single root

echo "=== 1. A0 author repo (verbatim, from the pinned commit) ==="
mkdir -p "$DST/a0_replay"
# The vendored copy already lives in the local repo at recovery/author_repo/.
# It is uploaded separately by the caller; here we only record the identity.
if [ -f "$DST/a0_replay/main_ILI_lora.py" ]; then
  echo "  a0_replay already present"
else
  echo "  ERROR: a0_replay/main_ILI_lora.py missing — upload recovery/author_repo first" >&2
  exit 2
fi

echo
echo "=== 2. eight-model runner + A2 protocol code it imports ==="
mkdir -p "$DST/scripts"
for f in train_backbone_966.py train_nlinear_966.py configs.py scaler_utils.py \
         cdc_calendar.py textual_embedder.py miflu_model.py; do
  [ -f "$DST/scripts/$f" ] && echo "  present: $f" || echo "  MISSING: $f"
done

echo
echo "=== 3. six backbone source files (must be present for the runner) ==="
for f in dlinear.py patchtst.py itransformer.py llm_inspired.py; do
  p="$DST/scripts/innovation/backbones/$f"
  [ -f "$p" ] && echo "  present: $f ($(stat -c%s "$p") bytes)" || echo "  MISSING: $f"
done
for f in __init__.py assets.py fidelity.py interfaces.py paths.py; do
  p="$DST/scripts/innovation/$f"
  [ -f "$p" ] && echo "  present: innovation/$f" || echo "  MISSING: innovation/$f"
done

echo
echo "=== 4. data + Qwen asset ==="
ls -la "$DST/data/raw/" 2>/dev/null | sed 's/^/  /'
echo "  --- Qwen snapshot (referenced by assets.py, local_files_only) ---"
ls -d /scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/snapshots/*/ 2>/dev/null | sed 's/^/  /'
echo "  --- gpt2 cache ---"
ls -d /home/sychan552/.cache/huggingface/hub/models--gpt2/snapshots/*/ 2>/dev/null | sed 's/^/  /'

echo
echo "=== 5. sha256 of everything the eight-model branch will execute ==="
cd "$DST"
sha256sum scripts/train_backbone_966.py scripts/train_nlinear_966.py \
          scripts/innovation/backbones/dlinear.py \
          scripts/innovation/backbones/patchtst.py \
          scripts/innovation/backbones/itransformer.py \
          scripts/innovation/backbones/llm_inspired.py \
          scripts/innovation/assets.py 2>&1 | sed 's/^/  /'
echo
echo "[deploy] ok"
