#!/bin/bash
# Chain-submit remaining Stage 5 A2 tasks via --dependency=afterok (no login-node
# long-running process; the scheduler sequences everything).
set -eo pipefail
cd /scratch/sychan552/a2_stage5
LOG=results/stage5/logs/dispatch_log.txt
mkdir -p results/stage5/logs

prev="${CHAIN_FROM:-585581}"

for spec in miflu:48 miflu:60 notext:24 notext:36 notext:48 notext:60 nlinear:36 nlinear:48 nlinear:60 naive:0; do
  M="${spec%%:*}"
  L="${spec##*:}"
  jid=$(sbatch --dependency=afterok:"$prev" --export=ALL,MODEL="$M",L="$L" recovery/stage5/run_task.sh | awk '{print $4}')
  echo "[chain] submitted $M L=$L job=$jid dep=afterok:$prev at $(date -u +%FT%TZ)" | tee -a "$LOG"
  prev="$jid"
done
echo "[chain] last job=$prev at $(date -u +%FT%TZ)" | tee -a "$LOG"
