#!/bin/bash
# Pre-flight for the Stage 6 unified scoring job, then submit it.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python

echo "=== syntax ==="
bash -n recovery/stage6/score_all.sh && echo "  score_all.sh OK"
bash -n recovery/stage6/prepare_lock.sh && echo "  prepare_lock.sh OK"
$PY -m py_compile recovery/stage6/recompute_eight.py && echo "  recompute_eight.py OK"

echo "=== lock template ==="
$PY -c "import json;d=json.load(open('recovery/stage6/lock_templates.json'));print('  models:',len(d['templates']),sorted(d['templates']))"

echo "=== checkpoint coverage under the stage6 roots ==="
CK=results/stage6/ckpt/author_966
tot=0
for m in miflu notext nlinear dlinear patchtst itransformer qwen_time_llm calf_llm timecma_llm; do
  n=$(find "$CK/$m" -maxdepth 1 -name '*.pth' 2>/dev/null | wc -l)
  tot=$((tot+n))
  printf '  %-16s %2d/12%s\n' "$m" "$n" "$([ "$n" -eq 12 ] || echo '   <-- SHORT')"
done
echo "  total = $tot/108"

echo "=== validation evidence present? ==="
for m in miflu notext nlinear dlinear patchtst itransformer qwen_time_llm calf_llm timecma_llm; do
  f=results/stage6/author_966/$m/metrics.csv
  if [ "$m" = "miflu" ]; then
    n=$(find results/stage6/author_966/miflu -name 'training_miflu_log_*.txt' 2>/dev/null | wc -l)
    echo "  miflu: $n training logs"
  else
    [ -e "$f" ] && echo "  $m: metrics.csv OK" || echo "  $m: MISSING metrics.csv"
  fi
done

echo "=== GPU charged so far this round ==="
sacct -u "$USER" -S 2026-09-26 -X --noheader \
      --format=JobID,JobName,State,Elapsed,AllocTRES%40 -P 2>/dev/null \
| awk -F'|' '
    $2=="s6_task" || $2=="s6_score" || $2=="a0_gpu" {
      s=$4; g=0
      if (match($5, /gres\/gpu[a-z0-9]*=[0-9]+/)) {
        v=substr($5,RSTART,RLENGTH); sub(/.*=/,"",v); g=v+0
      }
      split(s,p,":"); tot+=(p[1]*3600+p[2]*60+p[3])*g
    }
    END { printf "  %.4f GPU-h of 2.3 cap (%.1f%%)\n", tot/3600, 100*tot/3600/2.3 }'

echo "=== queue ==="
squeue -u "$USER" -o '  %i %T %M %j' 2>/dev/null
