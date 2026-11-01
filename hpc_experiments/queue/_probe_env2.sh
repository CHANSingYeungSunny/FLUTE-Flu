#!/bin/bash
# Probe 2: where are the HF weights really, and what does the remote trainer look like.
set -uo pipefail
H=/gpfs1/home/sychan552
CODE=$H/stage5_a2_durable/code

echo "=== scratch symlink? ==="
ls -ld "$H/scratch" 2>/dev/null
readlink -f "$H/scratch" 2>/dev/null

echo "=== find HF cache dirs (depth-limited) ==="
for d in "$H/scratch/hf_cache" "$H/scratch" "$H/.cache/huggingface"; do
  [ -e "$d" ] && echo "EXISTS $d" && ls -1 "$d" | head -10
done

echo "=== scanned hub dirs, depth 3 ==="
find "$H" -maxdepth 4 -type d -name 'models--Qwen*' 2>/dev/null | head -20

echo "=== remote trainer md5 + llm files ==="
md5sum "$CODE/train_backbone_966.py" "$CODE/eval_windows.py" 2>/dev/null
ls -l "$CODE"/llm_encoder_backbone.py 2>/dev/null || echo "NO llm_encoder_backbone.py in code dir"

echo "=== hf_cache under scratch: is it populated? ==="
ls -1d "$H"/scratch/* 2>/dev/null | head -20
