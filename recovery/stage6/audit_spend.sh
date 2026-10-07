#!/bin/bash
# Tally the GPU cost of the whole Stage-6 round from sacct, and verify that
# every run the ledger claims to have started also finished cleanly.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1

echo "=== ledger: exit codes ==="
awk -F, 'NR>1{split($NF,a,"=");print a[1]}' results/stage6/logs/run_ledger.csv \
  | sort | uniq -c
echo "  rows = $(($(wc -l < results/stage6/logs/run_ledger.csv)-1))"

echo "=== checkpoints on disk ==="
find results/stage6/ckpt -name '*.pth' | wc -l

echo "=== GPU seconds, all s6_* and a0_gpu jobs, by state ==="
sacct -u "$USER" -S 2026-09-26 -X --noheader \
      --format=JobID,JobName,State,Elapsed,AllocTRES%60,Start,End -P 2>/dev/null \
| awk -F'|' '
    $1 !~ /\.|\+/ {
      jn=$2
      if (jn ~ /^s6_/ || jn ~ /^a0_gpu/) {
        g=0
        if (match($5, /gres\/gpu[a-z0-9]*=[0-9]+/)) {
          v=substr($5,RSTART,RLENGTH); sub(/.*=/,"",v); g=v+0
        }
        split($4,p,":"); s=(p[1]*3600+p[2]*60+p[3])
        key=$3; gpu_sec[key]+=s*g; cnt[key]++
        if (g>0 && $3=="COMPLETED") { ok+=s*g; okn++ }
      }
    }
    END {
      for (k in gpu_sec) printf "  %-12s jobs=%-4d %10.1f GPU-h\n", k, cnt[k], gpu_sec[k]/3600
      printf "  ---\n  COMPLETED with GPU: %d jobs, %.4f GPU-h\n", okn, ok/3600
    }'

echo "=== stage7 ledger if present ==="
[ -e results/stage7/GPU_LEDGER_stage7.tsv ] && cat results/stage7/GPU_LEDGER_stage7.tsv

echo "=== A0 GPU minimal: the two diagnostic runs ==="
sacct -u "$USER" -S 2026-09-26 -X --noheader \
      --format=JobID,JobName,State,Elapsed,AllocTRES%60 -P 2>/dev/null \
| awk -F'|' '$2=="a0_gpu" {print "  "$1"  "$3"  "$4"  "$5}'

echo "=== recompute verdict line ==="
grep -iE 'PASS|FAIL|max' results/stage6/logs/score_587385.out 2>/dev/null | tail -6
