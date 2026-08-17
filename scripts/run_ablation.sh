#!/bin/bash
# run_ablation.sh — Table VIII Ablation Batch Runner
# Run on A100: bash run_ablation.sh

export HF_ENDPOINT=https://hf-mirror.com

VARIANTS=("no_dataset" "no_task" "no_vardesc" "no_lora" "no_multi" "no_lora_multi")

echo "============================================"
echo "  Table VIII Ablation — Batch Run"
echo "  $(date)"
echo "  Variants: ${VARIANTS[@]}"
echo "============================================"

for v in "${VARIANTS[@]}"; do
    echo ""
    echo ">>> Running: $v"
    echo ">>> $(date)"
    python train_ablation.py --variant $v
    echo "<<< Done: $v"
    echo "<<< $(date)"
done

echo ""
echo "============================================"
echo "  All ablations complete!"
echo "  $(date)"
echo ""
echo "  Results:"
for v in "${VARIANTS[@]}"; do
    echo "    data/results_ablation_${v}.csv"
    echo "    data/training_ablation_${v}_log.txt"
done
echo "============================================"
