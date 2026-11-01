#!/bin/bash
set -uo pipefail
cd /gpfs1/home/sychan552/stage5_a2_durable/code/queue || exit 1
echo 720070 > runner_s1.job
echo 719833 > runner_s0.job
echo 720052 > runner_sw.job
echo 720004 > watchdog.job
echo 719858 > runner_scpu.job
for f in runner_s0.job runner_s1.job runner_sw.job runner_scpu.job watchdog.job runner_s1.qwen.job; do
  printf '%-20s %s\n' "$f" "$(tr '\n' ' ' < "$f" 2>/dev/null)"
done
