#!/bin/bash
# Poll the two MIFlu seed jobs. Safe to run repeatedly; read-only.
set -u
CD=/gpfs1/home/sychan552/stage5_a2_durable/code
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "=== now: $(date -Is) ==="
sacct -j 718929,718930 -o JobID,JobName%14,Partition,State,Elapsed,ExitCode 2>&1 | head -8
for j in 718929 718930; do
  f=$(ls -1 "${CD}"/slurm-miflu-seed*-${j}.out 2>/dev/null | head -1)
  echo
  echo "=== job ${j} -> ${f} ==="
  if [ -n "${f}" ]; then
    grep -E "ep [ 0-9]+/20|L=[0-9]+ DONE|predictions written|\[ok\] L=|\[FAIL\] L=|kept rep seed" "${f}" | tail -6
    echo "--- last 3 raw lines ---"
    tail -3 "${f}"
  fi
done
echo
echo "=== finished benchmark CSVs (seeds 42/43/44) ==="
ls -la "${AR}"/L*_s4[234]/predictions_miflu_L*_s*_paper_protocol.csv 2>/dev/null || echo "(none yet)"
