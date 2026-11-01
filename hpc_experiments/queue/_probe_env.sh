#!/bin/bash
# Probe: tiny-node internet reachability evidence, HF cache inventory, LLM trainer CLI.
set -uo pipefail
HOME_DIR=/gpfs1/home/sychan552
CODE=$HOME_DIR/stage5_a2_durable/code

echo "=== tiny job 719797 stdout (login-node view) ==="
ls -l "$HOME_DIR"/slurm-*.out 2>/dev/null | tail -5
cat "$HOME_DIR"/slurm-719797.out 2>/dev/null

echo "=== HF cache hub dirs ==="
ls -1 "$HOME_DIR"/scratch/hf_cache/hub 2>/dev/null | head -30
echo "--- sizes (single du, not recursive storm) ---"
ls -1d "$HOME_DIR"/scratch/hf_cache/hub/models--* 2>/dev/null | head -30

echo "=== train_backbone_966 llm args ==="
grep -n 'add_argument' "$CODE/train_backbone_966.py" | grep -i 'llm\|encoder\|arm\|horizon\|seed\|export\|ckpt\|backbone\|profile\|contain' | head -40

echo "=== llm_encoder_backbone args ==="
grep -n 'add_argument' "$CODE/llm_encoder_backbone.py" 2>/dev/null | head -20

echo "=== venvs ==="
ls -1 /home/sychan552/.venvs 2>/dev/null
ls -l /home/sychan552/.venvs/mlflu_llm/bin/python 2>/dev/null

echo "=== verify markers ==="
ls -1 "$HOME_DIR"/stage5_a2_durable/author_runs/.miflu_verify/ 2>/dev/null | wc -l
