#!/bin/bash
set -u
AR=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
echo "=== md5 checkpoints (L24 two copies) ==="
md5sum "$AR"/ckpt_L24_s2021/best_miflu_L24.pth "$AR"/ckpt_L24_s2021_pred/best_miflu_L24.pth \
       "$AR"/ckpt_L36_s2021/best_miflu_L36.pth "$AR"/ckpt_L48_s2021/best_miflu_L48.pth \
       "$AR"/ckpt_L60_s2021/best_miflu_L60.pth
echo "=== md5 prediction CSVs ==="
md5sum "$AR"/L24_s2021_pred/predictions_miflu_L24_paper_protocol.csv \
       "$AR"/L36_s2021/predictions_miflu_L36_paper_protocol.csv \
       "$AR"/L48_s2021/predictions_miflu_L48_paper_protocol.csv \
       "$AR"/L60_s2021/predictions_miflu_L60_paper_protocol.csv
echo "=== textual_embedder imports ==="
grep -nE "^(import|from)" /gpfs1/home/sychan552/stage5_a2_durable/code/textual_embedder.py | head -20
echo "=== MIFlu.__init__ signature ==="
grep -n -A22 "class MIFlu" /gpfs1/home/sychan552/stage5_a2_durable/code/miflu_model.py | head -40
echo "=== attach_calendar signature ==="
grep -n -A12 "def attach_calendar" /gpfs1/home/sychan552/stage5_a2_durable/code/cdc_calendar.py
echo "=== text emb files ==="
ls -la /gpfs1/home/sychan552/stage5_a2_durable/code/assets/text_emb/
echo "=== queues ==="
squeue -u sychan552 -o "%.10i %.9P %.20j %.8T %.10M" 2>&1 | head
echo "=== partitions tiny/batch ==="
sinfo -o "%.14P %.6a %.10l %.6D %.6t" 2>&1 | grep -E "tiny|batch|PARTITION"
