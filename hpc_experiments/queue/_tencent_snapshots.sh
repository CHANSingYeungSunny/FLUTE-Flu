#!/bin/bash
# _tencent_snapshots.sh -- the tencent weights ARE on disk, under the nested
# hf_cache/hub layout (runbook gotcha 1, in reverse). Which are complete, and what
# revision does each snapshot directory name?
set -uo pipefail
H=/home/sychan552/scratch/hf_cache
echo "=== hf_cache/hub/models--* (nested layout) ==="
ls -1 "$H/hub" 2>/dev/null | grep '^models--' | sed 's/^/  /'
echo
for d in "$H"/hub/models--*; do
  [ -d "$d" ] || continue
  m=${d##*/models--}; m=${m//--//}
  sz=$(du -sh "$d" 2>/dev/null | cut -f1)
  snaps=$(ls -1 "$d/snapshots" 2>/dev/null | tr '\n' ' ')
  cfg=no
  for s in "$d"/snapshots/*/; do [ -f "$s/config.json" ] && cfg=yes; done
  wt=$(ls -1 "$d"/snapshots/*/*.safetensors "$d"/snapshots/*/*.bin 2>/dev/null | wc -l)
  printf '  %-44s size=%-7s config=%-4s weight_files=%-3s snapshots=%s\n' \
    "$m" "$sz" "$cfg" "$wt" "${snaps:-none}"
done
echo
echo "=== also the flat layout (old 4) ==="
for d in "$H"/models--*; do
  [ -d "$d" ] || continue
  m=${d##*/models--}; m=${m//--//}
  printf '  %-44s size=%-7s snapshots=%s\n' "$m" "$(du -sh "$d" 2>/dev/null | cut -f1)" \
    "$(ls -1 "$d/snapshots" 2>/dev/null | tr '\n' ' ')"
done
