#!/bin/bash
# Submit a stingy job one array element at a time, waiting for each to reach a
# terminal state. REQUIRED because partition-stingy sets MaxSubmit=1 and
# MaxJobsPU=1; a multi-element --array is rejected outright.
#
# Usage:  bash run_one_at_a_time.sh <sbatch-file> <first-index> <last-index>
# This wrapper does NOT submit anything by itself - it is the tool you would
# use once a submission is authorised.
set -euo pipefail
SB=${1:?sbatch file}
FROM=${2:?first index}
TO=${3:?last index}
for i in $(seq "$FROM" "$TO"); do
  echo "[seq] submitting index ${i}"
  jid=$(sbatch --parsable --array="${i}-${i}" "$SB")
  echo "[seq] job ${jid} for index ${i}; waiting"
  while true; do
    st=$(sacct -j "${jid}" -X --noheader -o State 2>/dev/null | head -1 | tr -d ' ')
    case "$st" in
      COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY) echo "[seq] ${jid} -> ${st}"; break;;
      "") sleep 15;;
      *) sleep 20;;
    esac
  done
done
echo "[seq] all indices done"
