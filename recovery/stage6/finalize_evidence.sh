#!/bin/bash
# Freeze the two pieces of evidence the report cites but that were only ever
# printed to a terminal: the independent recomputation verdict, and the A0 GPU
# minimal diagnostic numbers.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
LOG=results/stage6/logs

export PYTHONPATH=/scratch/sychan552/a2_stage5/scripts
export MPLBACKEND=Agg
export ACTIVE_PROFILE=author_966

echo "=== 1. independent recomputation, captured to a durable log ==="
$PY -u recovery/stage6/recompute_eight.py --scoring results/stage6/scoring \
    > "$LOG/recompute_verify.out" 2> "$LOG/recompute_verify.err"
echo "  exit=$?"
tail -20 "$LOG/recompute_verify.out"
[ -s "$LOG/recompute_verify.err" ] && { echo "  --- stderr ---"; tail -5 "$LOG/recompute_verify.err"; }

echo
echo "=== 2. locate the A0 GPU minimal outputs ==="
find results -iname '*a0*' 2>/dev/null | head -20
echo "--- stage6 log dir, non-task files ---"
ls "$LOG" | grep -viE '^(task_|pipeline)' | head -20
echo "--- any file mentioning the A0 MODE numbers ---"
grep -rl '0.9685\|0.8581' results 2>/dev/null | head -10

echo
echo "=== 3. scoring job tail (what the job itself printed) ==="
tail -18 "$LOG/score_587385.out"
echo "--- score err ---"
tail -5 "$LOG/score_587385.err"
