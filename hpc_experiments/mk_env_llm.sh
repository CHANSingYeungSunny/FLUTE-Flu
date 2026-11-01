#!/bin/bash
# Create a SEPARATE conda env for Qwen3.8-27B-FP8 (model_type 'qwen3_5').
# mlflu_hpc (transformers 4.57.6) must stay untouched: 16 benchmark arms depend on it.
# Strategy: clone mlflu_hpc (fast, inherits torch) then upgrade transformers in the clone only.
set -x
date

# conda is a module on this cluster, not on PATH
if ! command -v conda >/dev/null 2>&1; then
    for f in /etc/profile.d/modules.sh /usr/share/Modules/init/bash; do
        [ -f "$f" ] && . "$f"
    done
    module load Conda/1.10.0
fi
command -v conda || { echo "FATAL: conda not found"; exit 1; }
conda --version

echo "=== envs before ==="
conda env list
echo "=== mlflu_hpc transformers (must be 4.57.6, do not touch) ==="
/home/sychan552/.conda/envs/mlflu_hpc/bin/python -c "import transformers; print('mlflu_hpc transformers', transformers.__version__)"

echo "=== cloning mlflu_hpc -> mlflu_llm ==="
conda create -y -n mlflu_llm --clone mlflu_hpc
RC=$?
echo "clone rc=$RC"
if [ $RC -ne 0 ]; then
    echo "CLONE FAILED"
    exit $RC
fi

echo "=== envs after ==="
conda env list
NEW=/home/sychan552/.conda/envs/mlflu_llm
ls -d "$NEW" || { echo "FATAL: $NEW missing"; exit 1; }
echo "=== clone transformers (should equal mlflu_hpc version) ==="
"$NEW/bin/python" -c "import torch, transformers, sys; print(sys.version); print('torch', torch.__version__); print('transformers', transformers.__version__)"
echo "=== CLONE_OK ==="
date
