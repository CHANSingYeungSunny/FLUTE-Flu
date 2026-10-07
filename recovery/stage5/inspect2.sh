#!/bin/bash
cd /scratch/sychan552/a2_stage5 || exit 1
R=results/stage5

echo "=== NOTEXT metrics.csv ==="
cat $R/author_966/notext/metrics.csv
echo
echo "=== NOTEXT horizon dirs (full) ==="
find $R/author_966/notext -type f | sort
echo
echo "=== NLINEAR metrics.csv ==="
cat $R/author_966/nlinear/metrics.csv
echo
echo "=== NAIVE metrics.csv ==="
cat $R/author_966/naive/metrics.csv
echo
echo "=== MIFLU: one results csv (head) ==="
head -5 $R/author_966/miflu/results_miflu_paper_protocol_20260925_223912.csv
echo
echo "=== MIFLU: one table csv ==="
cat $R/author_966/miflu/results_miflu_paper_protocol_table_20260925_223912.csv
echo
echo "=== MIFLU training log 223912 (L24 S42) ==="
cat $R/author_966/miflu/training_miflu_log_20260925_223912.txt
echo
echo "=== script hashes ==="
cd /scratch/sychan552/a2_stage5
sha256sum scripts/train_miflu.py scripts/train_ablation.py scripts/train_nlinear_966.py scripts/train_naive_966.py scripts/score_test_stage5.py scripts/configs.py 2>&1
md5sum scripts/train_miflu.py scripts/train_ablation.py scripts/train_nlinear_966.py scripts/train_naive_966.py scripts/configs.py 2>&1
echo
echo "=== scoring script head ==="
sed -n '1,60p' scripts/score_test_stage5.py
