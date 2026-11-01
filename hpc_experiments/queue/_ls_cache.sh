#!/bin/bash
# _ls_cache.sh -- `find` did not follow the scratch symlink; use ls instead.
set -uo pipefail
C=/home/sychan552/scratch/hf_cache
echo "=== is scratch a symlink? ==="
ls -ld /home/sychan552/scratch
echo
echo "=== hf_cache contents (dir count) ==="
ls -1 "$C" 2>/dev/null | wc -l
echo
echo "=== every models--* entry in hf_cache ==="
ls -1 "$C" 2>/dev/null | grep '^models--' | sed 's/^/  /'
echo
echo "=== per-arm presence, by ls (authoritative here) ==="
for m in tencent/Hunyuan-1.8B-Instruct tencent/WeMM-Embedding-2B \
         tencent/Hunyuan-4B-Instruct tencent/WeMM-Embedding-4B \
         tencent/ContextPilot-8B tencent/Hunyuan-7B-Instruct \
         tencent/ContextPilot-14B deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
         tencent/KaLM-Embedding-Gemma3-12B tencent/Penguin-Encoder tencent/Youtu-HiChunk; do
  d="$C/models--${m//\//--}"
  if [ -d "$d" ]; then
    printf '  %-44s LOCAL snapshots=%s\n' "$m" "$(ls -1 "$d/snapshots" 2>/dev/null | wc -l)"
  else
    printf '  %-44s ABSENT\n' "$m"
  fi
done
