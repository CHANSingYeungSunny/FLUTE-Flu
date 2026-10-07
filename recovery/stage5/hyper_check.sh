#!/bin/bash
cd /scratch/sychan552/a2_stage5/results/stage5 || exit 1
echo "=== miflu log header (L24 S42) ==="
sed -n '1,25p' author_966/miflu/training_miflu_log_20260925_223912.txt
echo
echo "=== nlinear metrics.csv (already shown) / any log ==="
ls -1 author_966/nlinear
echo
echo "=== scheduler / early-stopping evidence in miflu logs ==="
grep -h -i -E "scheduler|early|patience|lr=" author_966/miflu/training_miflu_log_20260925_223912.txt | head -20
echo
echo "=== ablation training log header ==="
sed -n '1,30p' author_966/notext/training_ablation.log
echo
echo "=== early_stopping.py scheduler presence (code actually executed) ==="
grep -n -i -E "scheduler|ReduceLROnPlateau|Cosine|OneCycle" /scratch/sychan552/a2_stage5/scripts/train_miflu.py | head
grep -n -i -E "scheduler|ReduceLROnPlateau" /scratch/sychan552/a2_stage5/scripts/train_nlinear_966.py | head
