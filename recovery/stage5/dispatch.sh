#!/bin/bash
# Stage 5 A2 dispatcher — one (model, horizon) job at a time (stingy: 1 run + 1 pending).
# Usage: bash recovery/stage5/dispatch.sh "miflu:24 miflu:36 ... notext:24 ... nlinear:36"
set -eo pipefail
cd /scratch/sychan552/a2_stage5
LED=results/stage5/logs/dispatch_log.txt
mkdir -p results/stage5/logs

for SPEC in "$@"; do
  M=${SPEC%%:*}
  L=${SPEC##*:}
  if [ "$M" = "nlinear" ] && [ "$L" = "24" ]; then
    echo "[dispatch] skip nlinear:24 (already COMPLETED in job 585525)" | tee -a "$LED"
    continue
  fi
  jid=$(sbatch --export=ALL,MODEL="$M",L="$L" recovery/stage5/run_task.sh | awk '{print $4}')
  echo "[dispatch] submitted MODEL=$M L=$L job=$jid at $(date -u +%FT%TZ)" | tee -a "$LED"
  while : ; do
    st=$(squeue -j "$jid" -h -o %T 2>/dev/null | head -1)
    [ -z "$st" ] && break
    sleep 20
  done
  el=$(sacct -j "$jid" -o Elapsed --noheader 2>/dev/null | head -1 | tr -d ' ')
  st2=$(sacct -j "$jid" -o State --noheader 2>/dev/null | head -1 | awk '{print $1}')
  echo "[dispatch] job=$jid MODEL=$M L=$L state=$st2 elapsed=$el" | tee -a "$LED"
done
echo "[dispatch] queue finished at $(date -u +%FT%TZ)" | tee -a "$LED"
