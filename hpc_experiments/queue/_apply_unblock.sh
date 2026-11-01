#!/bin/bash
# _apply_unblock.sh -- deploy the local-snapshot resolver, then unblock ONLY the
# arms whose weights are verifiably on disk, flip their rows in place, verify.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1

echo "=== 0. deploy master_task_v2.py (local-snapshot resolver) ==="
sed -i 's/\r$//' master_task_v2.py
sed -i 's|^import queue_store |import queue_store_v2 as queue_store |' master_task_v2.py
sed -i 's|^import queue_store$|import queue_store_v2 as queue_store|' master_task_v2.py
"$PY" -m py_compile master_task_v2.py && echo "  task syntax OK"
grep -c 'def local_snapshot' master_task_v2.py | sed 's/^/  local_snapshot defined: /'

echo
echo "=== 1. histogram BEFORE ==="
awk -F'\t' 'NR>1{c[$6" "$8]++} END{for(k in c) printf "  %-34s %d\n", k, c[k]}' master_queue.tsv | sort
echo "  llm_cell TODO = $(awk -F'\t' 'NR>1 && $2=="llm_cell" && $8=="TODO"{n++}END{print n+0}' master_queue.tsv)"

echo
echo "=== 2. apply: pin revisions + flip only the verifiable arms ==="
cp -p master_queue.tsv "master_queue.tsv.bak_unblock_$(date +%H%M%S)"
cp -p arms_registry.json "arms_registry.json.bak_unblock_$(date +%H%M%S)"
"$PY" _unblock_verified.py --apply

echo
echo "=== 3. histogram AFTER ==="
awk -F'\t' 'NR>1{c[$6" "$8]++} END{for(k in c) printf "  %-34s %d\n", k, c[k]}' master_queue.tsv | sort
N=$(awk -F'\t' 'NR>1 && $2=="llm_cell" && $8=="TODO"{n++}END{print n+0}' master_queue.tsv)
echo "  llm_cell TODO = ${N}   (expected 12 P1 Qwen + 8 arms x 12 = 108)"
echo "  BLOCKED rows by model:"
awk -F'\t' 'NR>1 && $8=="BLOCKED_MISSING_WEIGHTS"{c[$3]++} END{for(k in c) printf "    %-44s %d\n", k, c[k]}' master_queue.tsv | sort

echo
echo "=== 4. registry: the 8 arms ==="
"$PY" - <<'PY'
import json
reg = json.load(open("arms_registry.json", encoding="utf-8"))
for a in reg["arms"]:
    print("  %-34s weights=%-13s revision=%s bs=%s params_b=%s"
          % (a["label"], a["weights"], (a["revision"] or "-")[:12],
             a["encoder_batch_size"], a["params_b"]))
PY

echo
echo "=== 5. can the code path execute an llm_cell? (measured, not claimed) ==="
"$PY" - <<'PY'
import os, sys, glob
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code/queue")
import master_task_v2 as M
print("  kind dispatch: main() -> llm_cell(task_id, model, L, seed, env)")
print("  env map:", M.ENVS)
for hf in ("tencent/Hunyuan-1.8B-Instruct", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
           "Qwen/Qwen2.5-1.5B"):
    arm = M.arms()[hf]
    bs, halved = M.batch_size_for(arm)
    rev = M.pinned_revision(arm)
    snap = M.local_snapshot(hf, rev)
    print("  %-44s env=%-4s bs=%-2s rev=%s" % (hf, arm["venv"], bs, (rev or "-")[:12]))
    print("       local_snapshot -> %s" % (snap or "NONE (would rely on HF_HUB_CACHE)"))
PY
