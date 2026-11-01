#!/bin/bash
#SBATCH --job-name=q38_cfgcheck
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=slurm-q38cfg-%j.out
#
# Step-3 verification: does the NEW env recognise model_type 'qwen3_5' offline?
# Runs on a CPU partition because compute nodes have no internet, so
# local_files_only (plus TRANSFORMERS_OFFLINE/HF_HUB_OFFLINE) is genuinely
# offline, and because AGENTS.md gotcha 12 forbids heavy imports on the login node.
set -uo pipefail
PY=/home/sychan552/.venvs/mlflu_llm/bin/python
export HF_HOME=/home/sychan552/scratch/hf_cache
export HF_HUB_CACHE=/home/sychan552/scratch/hf_cache
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export PYTHONUNBUFFERED=1

echo "host=$(hostname) job=${SLURM_JOB_ID:-none}"; date -Is
"${PY}" -V
"${PY}" -m pip show transformers 2>&1 | grep -E '^(Name|Version):'

"${PY}" - <<'PYEOF'
import transformers
print("transformers", transformers.__version__)
try:
    import torch
    print("torch", torch.__version__, "cuda_build", torch.version.cuda,
          "| torch_available_to_transformers:", transformers.utils.is_torch_available())
except Exception as e:
    print("torch import failed:", e)
from transformers import AutoConfig
c = AutoConfig.from_pretrained("Qwen/Qwen3.8-27B-FP8", local_files_only=True)
print("CONFIG OK model_type =", c.model_type)
print("CONFIG OK class      =", type(c).__name__)
tc = getattr(c, "text_config", None) or c
print("hidden_size       =", getattr(tc, "hidden_size", None))
print("num_hidden_layers =", getattr(tc, "num_hidden_layers", None))
print("num_attention_heads =", getattr(tc, "num_attention_heads", None))
print("vocab_size        =", getattr(tc, "vocab_size", None))
print("vision_config     =", "present" if getattr(c, "vision_config", None) else "absent")
try:
    from transformers.models.auto.modeling_auto import MODEL_MAPPING_NAMES
    print("qwen3_5 in AutoModelForCausalLM mapping:", "qwen3_5" in MODEL_MAPPING_NAMES)
except Exception as e:
    print("mapping introspection unavailable:", e)
print("CONFIG_VERIFY_OK")
PYEOF
echo "rc=$?"
