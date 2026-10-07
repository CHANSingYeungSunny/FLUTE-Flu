#!/bin/bash
cd /scratch/sychan552/a2_stage5 || exit 1
J=${1:-585865}
echo "=== task_$J.out (head 40) ==="
head -40 results/stage5/logs/task_$J.out
echo "=== task_$J.out (tail 45) ==="
tail -45 results/stage5/logs/task_$J.out
echo "=== err ==="
tail -20 results/stage5/logs/task_$J.err
