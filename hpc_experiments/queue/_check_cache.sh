#!/bin/bash
# _unblock_llm_cells.sh -- (1) verify each arm's weights are really LOCAL,
# (2) pin its revision sha, (3) flip its 12 llm_cell rows BLOCKED -> TODO in place.
# Registry is edited with python's json module; the queue with .tmp + mv.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
CACHE=/home/sychan552/scratch/hf_cache
cd "$Q" || exit 1

echo "=== 0. which arms have a local HF snapshot? ==="
for m in tencent/Hunyuan-1.8B-Instruct tencent/WeMM-Embedding-2B \
         tencent/Hunyuan-4B-Instruct tencent/WeMM-Embedding-4B \
         tencent/ContextPilot-8B tencent/Hunyuan-7B-Instruct \
         tencent/ContextPilot-14B deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
         tencent/KaLM-Embedding-Gemma3-12B tencent/Penguin-Encoder tencent/Youtu-HiChunk \
         Qwen/Qwen2.5-1.5B deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B Qwen/Qwen3.8-27B-FP8; do
  d="$CACHE/models--${m//\//--}"
  if [ -d "$d" ]; then
    n=$(ls -1 "$d/snapshots" 2>/dev/null | wc -l)
    sz=$(du -sh "$d" 2>/dev/null | cut -f1)
    printf '  %-44s LOCAL snapshots=%s size=%s\n' "$m" "$n" "$sz"
  else
    printf '  %-44s ABSENT\n' "$m"
  fi
done
