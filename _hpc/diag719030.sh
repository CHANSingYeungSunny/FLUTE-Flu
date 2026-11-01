#!/bin/bash
# Diagnostic for controller job 719030: find its log, show the tail, show sacct.
set -u
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
cd "${CODE}" || exit 1

echo "=== A. slurm logs mentioning 719030 ==="
ls -lat slurm-*719030* 2>/dev/null
ls -lat slurm-miflu-a100-*.out 2>/dev/null

echo
echo "=== B. controller script present? ==="
ls -la miflu_a100_controller.sh 2>/dev/null
md5sum miflu_a100_controller.sh 2>/dev/null

echo
echo "=== C. sacct 719030 ==="
sacct -j 719030 --format=JobID,JobName%24,Partition,State,ExitCode,Elapsed,Start,End,NodeList -P 2>/dev/null

echo
echo "=== D. sacct children / all jobs of user in window ==="
sacct -u sychan552 --starttime=2026-11-01T00:00:00 --format=JobID,JobName%24,Partition,State,ExitCode,Elapsed,Start,End,NodeList -P 2>/dev/null | tail -40

echo
echo "=== E. tail -30 of 719030 log ==="
f=$(ls -t slurm-*719030* 2>/dev/null | head -1)
echo "file=${f:-NONE}"
[ -n "${f}" ] && tail -n 30 "${f}"
