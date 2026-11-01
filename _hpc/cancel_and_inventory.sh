#!/bin/bash
# Confirm cancellation + inventory the 10-rep (seeds 2021..2030) checkpoints.
set -u
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "=== now $(date -Is) ==="
echo "=== scancel 718929 718964 ==="
scancel 718929 718964 2>&1
sleep 6
echo "=== states ==="
sacct -j 718929,718930,718964 -o JobID,JobName%14,State,Elapsed 2>&1 | head -14
echo
echo "=== squeue (must be empty of miflu_seed jobs) ==="
squeue -u sychan552 -h -o "%i %j %T" 2>&1 | head -10
echo
echo "=== L24 s2021 per-rep checkpoints ==="
ls -la --time-style=+%H:%M "$AR"/ckpt_L24_s2021/ | sort -k6
echo
echo "=== kept-rep-seed per horizon (which seed became best_miflu_*) ==="
for L in 24 36 48 60; do
  echo "--- L=$L ---"
  grep -h "kept rep seed" "$AR"/L${L}_s2021/training_miflu_log_*.txt 2>/dev/null
done
echo
echo "=== per-rep test_mse_all recorded by the original 10-rep runs ==="
for L in 24 36 48 60; do
  echo "--- L=$L ---"
  grep -h "DONE: test_mse" "$AR"/L${L}_s2021/training_miflu_log_*.txt 2>/dev/null | sed 's/.*test_mse=//'
done
echo
echo "=== all checkpoint dirs now ==="
ls -d "$AR"/ckpt_* 2>/dev/null
