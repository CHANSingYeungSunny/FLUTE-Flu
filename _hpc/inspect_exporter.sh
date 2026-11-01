#!/bin/bash
# Inspect exporter CLI + L24 checkpoint dir + one manifest + npz shapes (login-node safe: cat/tail only).
set -u
CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
cd "${CODE}" || exit 1

echo "=== exporter argparse block ==="
grep -n "add_argument\|def main\|args\." export_miflu_all7.py 2>/dev/null | head -60

echo
echo "=== exporter: how cells are enumerated / skipped ==="
grep -n "skip\|exists\|all7\|for L\|cells\|horizons\|best_miflu\|_rep_" export_miflu_all7.py 2>/dev/null | head -60

echo
echo "=== L24 ckpt dir ==="
ls -la "${OUT}/ckpt_L24_s2021/" 2>/dev/null
echo
echo "=== L36/L48/L60 ckpt dirs ==="
for L in 36 48 60; do echo "--- L${L} ---"; ls -la "${OUT}/ckpt_L${L}_s2021/" 2>/dev/null | head -8; done

echo
echo "=== one L24 manifest ==="
cat "${OUT}/L24_all7/manifest_miflu_L24_seed2022.json" 2>/dev/null
echo
echo "=== one L36 manifest ==="
cat "${OUT}/L36_all7/manifest_miflu_L36_seed2023.json" 2>/dev/null
