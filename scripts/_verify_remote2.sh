#!/usr/bin/env bash
set -e
F=/home/sychan552/scratch/CHATTIME/Chattime/scripts/train_miflu.py
echo "--- summary/table header (the FINAL results table) ---"
grep -n "L / MSE\|MSE / MAE\|/ MAE\|mean ± std\|results_miflu_paper_protocol_table" "$F" | head || true
echo "--- columns written to results CSV (to_csv) ---"
grep -n "to_csv\|columns=\|L,rep\|mse_all\|mae_all\|rmse\|pcc" "$F" | head -30 || true
echo "--- any rmse column name in file? ---"
grep -n "rmse" "$F" | head || true
echo "--- table header literal near line 404 ---"
sed -n '399,418p' "$F"
