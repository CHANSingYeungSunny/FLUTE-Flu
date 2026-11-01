#!/bin/bash
# Inspect the four MIFlu reproduction output directories.
set -u
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
for L in 24 36 48 60; do
  d=$AR/L${L}_s2021_pred
  if [ ! -d "$d" ]; then d=$AR/L${L}_s2021; fi
  echo "########## L=$L  dir=$d ##########"
  ls -la "$d"
  echo "--- config lines from log ---"
  grep -hE "Config:|Profile |Data:|Text source|containment=|Author text embedding|CSV\] L=" "$d"/training_miflu_log_*.txt 2>/dev/null | head -20
  echo "--- DONE line ---"
  grep -hE "DONE: test_mse|kept rep seed|FINAL: MSE_AllVars" "$d"/training_miflu_log_*.txt 2>/dev/null | tail -6
  echo "--- results csv ---"
  for f in "$d"/results_miflu_paper_protocol_*.csv; do echo "[$f]"; cat "$f"; done
  echo "--- predictions csv ---"
  wc -l "$d"/predictions_miflu_L${L}_paper_protocol.csv
  head -2 "$d"/predictions_miflu_L${L}_paper_protocol.csv
  echo
done
