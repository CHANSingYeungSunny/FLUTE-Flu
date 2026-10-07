#!/bin/bash
# Read-only probes: local model caches, Qwen availability, and B-track measured costs.
echo "=== HF cache tree (top level) ==="
ls -1 /home/sychan552/.cache/huggingface/hub 2>/dev/null
echo
echo "=== models--* dirs with sizes ==="
for d in /home/sychan552/.cache/huggingface/hub/models--*; do
  [ -d "$d" ] || continue
  echo "$(du -sh $d 2>/dev/null | cut -f1)  $(basename $d)"
  ls -1 "$d/snapshots" 2>/dev/null | head -3 | sed 's/^/    snap: /'
done
echo
echo "=== any Qwen snapshot anywhere on scratch/home ==="
find /home/sychan552 /scratch/sychan552 -maxdepth 6 -iname "*Qwen*" -type d 2>/dev/null | head -20
echo
echo "=== assets.py registry: which model ids are declared ==="
grep -n -E "model_id|Qwen|gpt2|register|ASSETS" /scratch/sychan552/a2_stage5/scripts/innovation/assets.py | head -40
echo
echo "=== B-track (v3_clean) measured per-fit wall time evidence ==="
ls -1 /scratch/sychan552/ | head -40
