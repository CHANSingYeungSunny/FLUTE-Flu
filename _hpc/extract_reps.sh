#!/bin/bash
set -u
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "############ L24 10-rep run: which log is it? ############"
for f in "$AR"/L24_s2021/training_miflu_log_*.txt; do
  n=$(grep -c "DONE: test_mse" "$f" 2>/dev/null || echo 0)
  echo "--- $(basename "$f")  reps_completed=$n"
  grep -hE "Config:|Profile |scaler|persisted|batch=|Text source|Author text embedding" "$f" | head -6
done
echo
echo "############ L24 10-rep run (196k log) per-rep values ############"
grep -h "DONE: test_mse" "$AR"/L24_s2021/training_miflu_log_20261031_195730.txt | sed 's/^\[[0-9:]*\] *//'
echo
echo "############ FINAL line per horizon (10-rep mean, 7-var) ############"
for L in 24 36 48 60; do
  echo -n "L=$L  "
  grep -h "FINAL: MSE_AllVars" "$AR"/L${L}_s2021/training_miflu_log_*.txt | tail -1 | sed 's/^\[[0-9:]*\] *//'
done
echo
echo "############ config of the L36/L48/L60 10-rep runs ############"
for L in 36 48 60; do
  echo "--- L=$L ---"
  grep -hE "Config:|author_repo|author_966|batch=|Text source" "$AR"/L${L}_s2021/training_miflu_log_*.txt | head -5
done
