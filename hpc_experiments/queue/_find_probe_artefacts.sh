#!/bin/bash
# _find_probe_artefacts.sh -- where did job 720218 / 720519 write their records,
# and what revision sha does each arm actually have? Read-only.
set -uo pipefail
R=/gpfs1/home/sychan552/stage5_a2_durable
Q=$R/code/queue

echo "=== candidate manifest paths ==="
for p in "$Q/weights_manifest_solo.json" "$R/code/weights_manifest_solo.json" \
         "$R/weights_manifest_solo.json" "$HOME/weights_manifest_solo.json" \
         "$Q/weights_manifest.json" "$R/code/queue/p2/weights_manifest_solo.json"; do
  [ -f "$p" ] && echo "  FOUND $p ($(stat -c %s "$p") bytes)"
done
echo "  --- any weights_manifest* under $R, depth 3 ---"
find "$R" -maxdepth 3 -name 'weights_manifest*' -printf '  %p (%s bytes)\n' 2>/dev/null | head

echo
echo "=== candidate probe-record dirs ==="
for p in "$Q/p2" "$R/code/p2" "$HOME/p2" "$Q/probe" "$R/code/probe"; do
  [ -d "$p" ] && echo "  DIR $p: $(ls -1 "$p" | wc -l) file(s)"
done
echo "  --- *.smoke.json anywhere under $R/code, depth 3 ---"
find "$R/code" -maxdepth 3 -name '*.smoke.json' -printf '  %p\n' 2>/dev/null | head

echo
echo "=== 720218 job output tail (what it printed) ==="
ls -t "$Q"/slurm-*720218* 2>/dev/null | head -1 | xargs -r tail -40

echo
echo "=== revision sha per arm, from the HF API (8 verified-OK arms) ==="
for m in tencent/Hunyuan-1.8B-Instruct tencent/WeMM-Embedding-2B \
         tencent/Hunyuan-4B-Instruct tencent/WeMM-Embedding-4B \
         tencent/ContextPilot-8B tencent/Hunyuan-7B-Instruct \
         tencent/ContextPilot-14B deepseek-ai/DeepSeek-R1-Distill-Qwen-32B \
         tencent/KaLM-Embedding-Gemma3-12B; do
  sha=$(curl -sS -m 40 "https://huggingface.co/api/models/$m" 2>/dev/null \
        | tr ',' '\n' | sed -n 's/.*"sha":"\([0-9a-f]\{40\}\)".*/\1/p' | head -1)
  printf '  %-42s %s\n' "$m" "${sha:-LOOKUP-FAILED}"
done
