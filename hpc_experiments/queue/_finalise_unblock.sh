#!/bin/bash
# _finalise_unblock.sh -- make the registry consistent with what is runnable, and
# print the exact composition of the TODO LLM cells for the report.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1

echo "=== 1. registry: penguin/youtu are UNUSABLE whatever their byte count ==="
"$PY" - <<'PY'
import json, os
p = "arms_registry.json"
reg = json.load(open(p, encoding="utf-8"))
UNSUP = {"tencent/Penguin-Encoder": "trust_remote_code / no per-layer hidden states (download verified 0.82 GB, adapter unsupported)",
         "tencent/Youtu-HiChunk": "no per-layer hidden states (download verified 7.60 GB, adapter unsupported)"}
n = 0
for a in reg["arms"]:
    if a["hf_id"] in UNSUP:
        a["weights"] = "unsupported"
        a["note"] = "UNSUPPORTED for this benchmark: %s -- 12 cells stay BLOCKED, never retried" % UNSUP[a["hf_id"]]
        n += 1
tmp = p + ".tmp"
json.dump(reg, open(tmp, "w", encoding="utf-8"), indent=2, sort_keys=True)
open(tmp, "a", encoding="utf-8").write("\n")
os.replace(tmp, p)
print("  %d arm(s) marked unsupported" % n)
for a in reg["arms"]:
    print("  %-34s weights=%-13s revision=%s bs=%-2s params_b=%s"
          % (a["label"], a["weights"], (a["revision"] or "-")[:12],
             a["encoder_batch_size"], a["params_b"]))
PY

echo
echo "=== 2. exact composition of the TODO llm_cell rows ==="
awk -F'\t' 'NR>1 && $2=="llm_cell" && $8=="TODO"{c[$3]++} END{for(k in c) printf "  %-44s %3d cells\n", k, c[k]}' master_queue.tsv | sort
echo "  ---- totals ----"
echo "  llm_cell TODO                 = $(awk -F'\t' 'NR>1 && $2=="llm_cell" && $8=="TODO"{n++}END{print n+0}' master_queue.tsv)"
echo "  llm_cell BLOCKED (never run)  = $(awk -F'\t' 'NR>1 && $2=="llm_cell" && $8=="BLOCKED_MISSING_WEIGHTS"{n++}END{print n+0}' master_queue.tsv)"
echo "  P1 (Qwen2.5-1.5B) TODO        = $(awk -F'\t' 'NR>1 && $6=="P1" && $8=="TODO"{n++}END{print n+0}' master_queue.tsv)"
echo "  P0 TODO / DONE                = $(awk -F'\t' 'NR>1 && $6=="P0" && $8=="TODO"{n++}END{print n+0}' master_queue.tsv) / $(awk -F'\t' 'NR>1 && $6=="P0" && $8=="DONE"{n++}END{print n+0}' master_queue.tsv)"
echo
echo "  every TODO llm_cell has a pinned revision and a local snapshot?"
"$PY" - <<'PY'
import sys
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code/queue")
import master_task_v2 as M
A = M.arms()
rows, miss_rev, miss_snap = set(), set(), set()
for line in open("master_queue.tsv", encoding="utf-8").read().splitlines()[1:]:
    f = line.split("\t")
    if len(f) < 11 or f[1] != "llm_cell" or f[7] != "TODO":
        continue
    m = f[2]
    rows.add(m)
    arm = A.get(m)
    rev = M.pinned_revision(arm) if arm else None
    if not rev:
        miss_rev.add(m)
    if not M.local_snapshot(m, rev):
        miss_snap.add(m)
print("  arms with TODO cells: %d" % len(rows))
print("  missing a pinned revision: %s" % (sorted(miss_rev) or "none"))
print("  missing a verified local snapshot: %s" % (sorted(miss_snap) or "none"))
PY
