#!/bin/bash
# The qwen3_5 GPU load test needs an A100 (fp8 needs sm_89+; the V100s cannot do it).
# A100 partitions: `stingy` (fast, but QOS = 1 submitted + 1 running per user) and
# `gpu_a100` (booked until 2026-11-02 19:29, so useless today).
#
# On 2026-11-01 18:07 a sibling job (`miflu_seedA`, job 718929, 4 h wall limit)
# took the single `stingy` slot. This watcher waits for that slot and submits
# `probe_qwen38_v2.sh` as soon as it is free, so no manual polling is needed.
#
# It only runs `sacct` + `sleep` - no heavy I/O, no python imports - so it cannot
# trigger the login-node D-state problem recorded in AGENTS.md §4 gotcha 12.
LOG=/gpfs1/home/sychan552/stage5_a2_durable/code/submit_when_free.log
cd /gpfs1/home/sychan552/stage5_a2_durable/code || exit 1
echo "watcher start $(date -Is)" >> "$LOG"

for i in $(seq 1 300); do
    busy=$(sacct -n -u sychan552 --starttime=now-8hours -X -o Partition,State 2>/dev/null \
           | awk '$1=="stingy" && ($2 ~ /RUNNING|PENDING|CONFIGURING|COMPLETING/)' | wc -l)
    if [ "$busy" -eq 0 ]; then
        out=$(sbatch --parsable probe_qwen38_v2.sh 2>&1)
        rc=$?
        echo "attempt $i at $(date -Is): busy=0 sbatch rc=$rc -> $out" >> "$LOG"
        if [ $rc -eq 0 ]; then
            echo "SUBMITTED $out" >> "$LOG"
            exit 0
        fi
    else
        if [ $((i % 10)) -eq 1 ]; then
            echo "attempt $i at $(date -Is): stingy busy ($busy job(s)) - waiting" >> "$LOG"
        fi
    fi
    sleep 45
done
echo "watcher gave up $(date -Is)" >> "$LOG"
exit 1
