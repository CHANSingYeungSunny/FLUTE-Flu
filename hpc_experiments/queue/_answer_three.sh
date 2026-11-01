#!/bin/bash
# _answer_three.sh -- the three questions, answered from the code on the cluster.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "$Q" || exit 1

echo "=== Q1a. the llm_cell branch (master_task_v2.py) ==="
grep -n 'a.kind == "llm_cell"\|^def llm_cell\|a.kind == "miflu_cell"\|a.kind in KIND_TO_ID' master_task_v2.py
echo
echo "=== Q1b. which column selects the interpreter ==="
grep -n 'env_py()\|py=\$(env_py\|--env "\${envr}"\|ENVS = \|venv = env_name' master_controller_v2.sh master_task_v2.py | head -12
echo
echo "=== Q1c. --encoder-batch-size source (registry + OOM override) ==="
grep -n 'def batch_size_for\|--encoder-batch-size' master_task_v2.py | head -6
echo "  measured values for the two sizes asked about:"
/home/sychan552/.conda/envs/mlflu_hpc/bin/python - <<'PY'
import sys
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code/queue")
import master_task_v2 as M
A = M.arms()
for hf in ("tencent/Hunyuan-1.8B-Instruct", "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"):
    arm = A[hf]
    bs, halved = M.batch_size_for(arm)
    print("    %-44s registry bs=%s -> effective --encoder-batch-size %s (halved_from=%s)"
          % (hf, arm["encoder_batch_size"], bs, halved or "-"))
PY

echo
echo "=== Q2. does the controller re-read the queue every cycle? ==="
echo "  pick_next / scan_pending / global_count each open master_queue.tsv afresh:"
grep -n 'done < "\${QUEUE}"\|awk -F' master_controller_v2.sh | head -8
echo "  (no in-memory cache of row STATES: only STRIPE_OF and CLAIM_BUSY are memoised)"
grep -n 'declare -A STRIPE_OF\|declare -A CLAIM_BUSY\|STRIPE_OF\[.*\]=\|CLAIM_BUSY\[' master_controller_v2.sh | head -6

echo
echo "=== Q3. successor lane scope ==="
grep -n 'QUEUE_ONLY_PRIORITY\|QUEUE_SMOKE_ABORT\|QUEUE_TASK_TIMEOUT\|exec bash' successor_lane.sh
echo "  is_mine() priority-scope rule:"
sed -n '/A priority-scoped lane owns EVERY cell/,/return 0; fi/p' master_controller_v2.sh
echo
echo "=== live queue right now ==="
awk -F'\t' 'NR>1{c[$6" "$8]++} END{for(k in c) printf "  %-34s %d\n", k, c[k]}' master_queue.tsv | sort
echo "  llm_cell TODO = $(awk -F'\t' 'NR>1 && $2=="llm_cell" && $8=="TODO"{n++}END{print n+0}' master_queue.tsv)"
echo "  successor watcher state: $(scontrol show job 720107 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p')"
echo "  successor.log tail:"; tail -3 successor.log 2>/dev/null | sed 's/^/    /'
