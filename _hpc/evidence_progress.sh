#!/bin/bash
# Evidence that the MIFlu chain is progressing (not stuck), for the parent agent.
set -u
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
cd "${CODE}" || exit 1

echo "=== A. now ==="
date -Is

echo
echo "=== B. manifest / npz counts per horizon (controller's own glob) ==="
for L in 24 36 48 60; do
  echo "L=${L}: npz=$(ls ${OUT}/L${L}_all7/pred_miflu_L${L}_seed*.npz 2>/dev/null | wc -l) manifest=$(ls ${OUT}/L${L}_all7/manifest_miflu_L${L}_seed*.json 2>/dev/null | wc -l) results=$(ls ${OUT}/L${L}_all7/results_miflu_L${L}_seed*.csv 2>/dev/null | wc -l) widecsv=$(ls ${OUT}/L${L}_all7/predictions_miflu_L${L}_seed*.csv 2>/dev/null | wc -l)"
done
echo "TOTAL manifests: $(ls ${OUT}/L*_all7/manifest_miflu_*.json 2>/dev/null | wc -l)"
echo "verified markers: $(ls ${OUT}/.miflu_verify/*.json 2>/dev/null | wc -l)"
echo "verified marker names: $(ls ${OUT}/.miflu_verify/ 2>/dev/null | tr '\n' ' ')"

echo
echo "=== C. newest files anywhere under author_runs (last 12, with mtime) ==="
find "${OUT}" -maxdepth 2 -type f -newermt '-40 minutes' -printf '%TY-%Tm-%Td %TH:%TM:%TS %10s %p\n' 2>/dev/null | sort -r | head -12

echo
echo "=== D. ckpt_retrain (per-seed retrain dirs) ==="
ls -lt "${OUT}"/ckpt_retrain/*/ 2>/dev/null | head -20
echo "--- ckpt_retrain dir list ---"
ls -1 "${OUT}"/ckpt_retrain 2>/dev/null

echo
echo "=== E. per-cell training logs: newest line each (epoch progress) ==="
for d in "${OUT}"/_seedruns/L*/; do
  [ -d "${d}" ] || continue
  f=$(ls -t "${d}"controller_train.log 2>/dev/null | head -1)
  [ -n "${f}" ] || continue
  echo "--- $(basename "${d}")  (log mtime $(date -r "${f}" +%H:%M:%S)) ---"
  tail -n 2 "${f}" | sed 's/^/    /'
done

echo
echo "=== F. chain log tail 30 ==="
tail -n 30 "${CODE}/miflu_a100_chain.log" 2>/dev/null

echo
echo "=== G. queue + accounting for this user ==="
squeue -u sychan552 -o '%.8i %.12j %.8P %.9T %.10M %.25R'
echo "--- sacct 719222 / 719234 ---"
sacct -j 719222,719234 --format=JobID,JobName%14,State,ExitCode,Elapsed,Start,End,NodeList -P 2>/dev/null

echo
echo "=== H. has the watcher had to submit anything? ==="
grep -c "submitted generation" "${CODE}/miflu_a100_chain.log" 2>/dev/null || echo 0
grep -E "submitted generation|FAILED|HALT|REQUEUE" "${CODE}/miflu_a100_chain.log" 2>/dev/null | tail -5

echo
echo "=== I. exporter/controller files in use (naming) ==="
ls -l miflu_controller_v2.py miflu_a100_controller_v3.sh miflu_chain_driver.sh export_miflu_all7.py
echo "manifest naming template inside export_miflu_all7.py:"
grep -n "manifest_miflu_L{L}_seed{seed}.json" export_miflu_all7.py | head -3
