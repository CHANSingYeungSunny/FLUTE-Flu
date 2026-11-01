#!/bin/bash
set -u
J=${1:-719191}
echo "=== squeue -j ${J} ==="
squeue -j "${J}" -o '%.8i %.14j %.8P %.8T %.10M %.20R' 2>&1
echo "=== sacct -j ${J} ==="
sacct -j "${J}" --format=JobID,JobName%22,Partition,State,ExitCode,Elapsed,Start,End,NodeList -P 2>/dev/null
echo "=== tail log ==="
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
f=$(ls -t "${CODE}"/slurm-nlinear-a100-${J}.out 2>/dev/null | head -1)
echo "log=${f:-NONE}"
[ -n "${f}" ] && tail -n 25 "${f}"
