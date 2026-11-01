#!/bin/bash
# Import/logic smoke test that costs no GPU and no network: if any of these
# modules fails to import, every task tonight would fail in the same way.
set -uo pipefail
QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
CODE=$(dirname "$QDIR")
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$CODE" || exit 1

echo "=== import test (no GPU, no network touched) ==="
PYTHONPATH="$QDIR" "$PY" - <<'PY' 2>&1
import sys
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code")
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code/queue")
import queue_store, master_task, probe_hidden_state
print("imports OK:", queue_store.QUEUE)
print("queue counts:", queue_store.counts())
arms = master_task.arms()
print("arms in registry:", len(arms))
q = arms["Qwen/Qwen2.5-1.5B"]
print("qwen arm:", q["label"], q["venv"], q["encoder_batch_size"], q["revision"][:12])
print("llm_gate(no file):", master_task.llm_gate("/nonexistent", 24))
print("pinned_revision for tencent penguin:", master_task.pinned_revision(arms["tencent/Penguin-Encoder"]))
PY

echo
echo "=== unknown-kind dispatch (must be exit 3 = SKIPPED, never a crash) ==="
"$PY" -u "$QDIR/master_task.py" run --task-id p3_table8_ablations --kind unimplemented --require-a100 0
echo "exit=$?"

echo
echo "=== queue sanity: every row has 10 fields, states are legal, P0 count ==="
awk -F'\t' 'NR==1{next} NF!=10{bad++} END{print "rows_with_bad_field_count="bad+0}' "$QDIR/master_queue.tsv"
awk -F'\t' 'NR>1{print $7}' "$QDIR/master_queue.tsv" | sort | uniq -c
awk -F'\t' 'NR>1 && $6=="P0"{n++} END{print "P0 cells="n}' "$QDIR/master_queue.tsv"
awk -F'\t' 'NR>1 && $1 ~ /^miflu_/{print $1"\t"$10}' "$QDIR/master_queue.tsv" | head -3

echo
echo "=== chain status ==="
squeue -u sychan552 -o '%.8i %.10P %.14j %.2t %.11M %.21S' 2>&1
