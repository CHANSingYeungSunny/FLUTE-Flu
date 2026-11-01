#!/bin/bash
# _ls_cache2.sh -- the other plausible HF homes, checked by ls (find cannot see
# through the scratch symlink and missed depth-4 paths).
set -uo pipefail
echo "=== ~/.cache/huggingface ==="
ls -1 /home/sychan552/.cache/huggingface 2>/dev/null | sed 's/^/  /' || echo "  absent"
echo "  --- hub/models--* ---"
ls -1 /home/sychan552/.cache/huggingface/hub 2>/dev/null | grep '^models--' | sed 's/^/    /' || echo "    none"
echo
echo "=== /scratch/sychan552 top level ==="
ls -1 /scratch/sychan552 2>/dev/null | sed 's/^/  /' | head -20
echo
echo "=== /scratch/sychan552/hf_cache/models--* ==="
ls -1 /scratch/sychan552/hf_cache 2>/dev/null | grep '^models--' | sed 's/^/  /' || echo "  none"
echo
echo "=== any tencent weights anywhere obvious (bounded, no recursion into gpfs) ==="
for base in /scratch/sychan552 /home/sychan552/scratch /home/sychan552/.cache /home/sychan552/scratch/MLFLU; do
  [ -d "$base" ] || continue
  echo "  --- $base (depth 4, following symlinks) ---"
  find -L "$base" -maxdepth 4 -type d -name 'models--tencent--*' -printf '    %p\n' 2>/dev/null | head -12
done
echo
echo "=== disk headroom for a ~60 GB download ==="
df -h /scratch/sychan552 /gpfs1/home/sychan552 2>/dev/null | sed 's/^/  /'
