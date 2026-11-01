#!/bin/bash
# Is the MIFlu chain livelocked? Measure generation turnover, epochs reached, checkpoint writes, gpu_a100 StartTime.
set -u
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
cd "${CODE}" || exit 1

echo "=== A. now / markers ==="
date -Is
echo "verified markers: $(ls ${OUT}/.miflu_verify/*.json 2>/dev/null | wc -l)"
echo "npz total: $(ls ${OUT}/L*_all7/pred_miflu_*.npz 2>/dev/null | wc -l)"

echo
echo "=== B. every miflu_a100 generation since 19:30 (state, elapsed, start, end, node) ==="
sacct -u sychan552 -S 2026-11-01T19:30:00 --format=JobID%12,JobName%14,State%12,ExitCode,Elapsed,Start,End,NodeList -P 2>/dev/null | grep -E "miflu_a100|miflu_chain"

echo
echo "=== C. queue right now ==="
squeue -u sychan552 -o '%.8i %.12j %.8P %.9T %.9M %.20R'

echo
echo "=== D. chain log: generation START lines + controller rc ==="
grep -E "START host|controller rc=|verified cells (before|after)|ALL 40|REQUEUE|SUCCESSOR|submitted generation" "${CODE}/miflu_a100_chain.log" | tail -40

echo
echo "=== E. what epoch did each in-flight/preempted retrain reach? ==="
for d in "${OUT}"/_seedruns/L*/; do
  [ -d "${d}" ] || continue
  f="${d}controller_train.log"
  [ -f "${f}" ] || continue
  echo "--- $(basename "${d}")  log_mtime=$(date -r "${f}" +%H:%M:%S)  lines=$(wc -l < "${f}") ---"
  grep -E "ep +[0-9]+/20" "${f}" | tail -2 | sed 's/^/    /'
  echo "    ckpt: $(ls -l ${OUT}/ckpt_retrain/$(basename "${d}")/ 2>/dev/null | tail -n +2 | awk '{print $5, $9}' | tr '\n' ' ')"
done

echo
echo "=== F. does train_miflu write a checkpoint before the last epoch? (source) ==="
grep -n "torch.save\|_rep_miflu\|best_miflu\|os.replace\|for ep in range\|saved_ckpts" train_miflu.py | head -30

echo
echo "=== G. gpu_a100 availability ==="
sinfo -p gpu_a100 -o '%.14N %.8t %.20G %.10C %.12m' 2>/dev/null | head -8
echo "--- partition ---"
scontrol show partition gpu_a100 2>/dev/null | tr ' ' '\n' | grep -Ei 'PreemptMode|PriorityTier|MaxTime|State|QoS|GraceTime|DefaultTime'
echo "--- would a job start now? (squeue --start for the partition, first 5) ---"
squeue -p gpu_a100 --start -o '%.10i %.10u %.12j %.9T %.20S %.20R' 2>/dev/null | head -6
