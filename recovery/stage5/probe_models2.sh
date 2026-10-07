#!/bin/bash
echo "=== Qwen snapshot on scratch ==="
ls -la /scratch/sychan552/v3_cache/ 2>&1 | head
du -sh /scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B 2>&1
find /scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/snapshots -maxdepth 1 -mindepth 1 2>/dev/null
echo "--- files in snapshot ---"
ls -la /scratch/sychan552/v3_cache/models--Qwen--Qwen2.5-1.5B/snapshots/*/ 2>/dev/null | head -20
echo
echo "=== assets.py QWEN descriptor (revision) ==="
sed -n '28,70p' /scratch/sychan552/a2_stage5/scripts/innovation/assets.py
echo
echo "=== B-track measured wall time: look for run timing records ==="
for d in /scratch/sychan552/_v319b /scratch/sychan552/innovation_deploy_root_v3_clean14; do
  echo "--- $d"
  ls -1 "$d" 2>/dev/null | head -20
done
echo
echo "=== screening ledger with timings ==="
find /scratch/sychan552 -maxdepth 3 -name "*ledger*.jsonl" 2>/dev/null | head -5
find /scratch/sychan552 -maxdepth 4 -name "*.jsonl" -path "*v3*" 2>/dev/null | head -8
echo
echo "=== a per-run timing sample from the durable screening dir ==="
ls -1 /home/sychan552/innovation_durable/screening/primary__qwen_time_llm__L24__seed42__w1 2>/dev/null
cat /home/sychan552/innovation_durable/screening/primary__qwen_time_llm__L24__seed42__w1/*.json 2>/dev/null | head -60
