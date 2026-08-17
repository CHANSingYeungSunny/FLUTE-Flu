#!/usr/bin/env bash
set -e
F=/home/sychan552/scratch/CHATTIME/Chattime/scripts/train_miflu.py
echo "--- grep rmse_ili / pcc_ili (should be EMPTY in CSV/table-write context) ---"
grep -n "rmse_ili\|pcc_ili" "$F" | head || true
echo "--- summary header (MSE/MAE only expected) ---"
grep -n "MSE / MAE\|/ MSE / MAE\|L / MSE" "$F" | head || true
echo "--- OT definition in train_miflu.py ---"
grep -n "num_patients\|OT =" "$F" | head || true
echo "--- verify_array script present ---"
ls -la /home/sychan552/scratch/CHATTIME/Chattime/submit_miflu_array.sh
