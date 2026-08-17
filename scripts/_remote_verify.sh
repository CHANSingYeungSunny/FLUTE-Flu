#!/bin/bash
F=/home/sychan552/scratch/CHATTIME/Chattime/scripts/train_miflu.py
echo "=== rmse_ili / pcc_ili occurrences (should be only in compute/evaluate, NOT in CSV row/agg/table) ==="
grep -n "rmse_ili\|pcc_ili" "$F"
echo "=== header line (should print only L/MSE/MAE) ==="
grep -n "MSE.*MAE\|'L':>4s" "$F"
echo "=== done ==="
