#!/bin/bash
#SBATCH --job-name=diag_peft
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=16G
#SBATCH --time=00:20:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/diag_peft_%j.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/logs/diag_peft_%j.err
#
# CPU-only diagnosis (ZERO GPU-hours). Question: can the AUTHOR's LoRA branch
# (GPT4TS_lora.py line 86, get_peft_model with target_modules=['c_attn'])
# execute on the current mlflu_hpc stack, and if not, what is the minimal fix?
set -uo pipefail
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
HOME_ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
A0=/scratch/sychan552/a0_replay
COMPAT=${HOME_ROOT}/hpc_compat
if [[ "$(hostname)" == hpclogin* ]]; then echo "REFUSING login node"; exit 3; fi
export PYTHONPATH="${COMPAT}:${A0}:${PYTHONPATH:-}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

$PY - <<'PYEOF'
import torch, peft, transformers
print("torch", torch.__version__, "| transformers", transformers.__version__, "| peft", peft.__version__)
from transformers.models.gpt2.modeling_gpt2 import GPT2Model
m = GPT2Model.from_pretrained('gpt2')
m.h = m.h[:6]

# what type IS c_attn on this stack?
att = m.h[0].attn
print("type(c_attn) =", type(att.c_attn).__mro__[:3])
print("module names containing attn:", [n for n,_ in m.named_modules() if 'c_attn' in n][:4])

from peft import LoraConfig, get_peft_model

def try_cfg(label, **kw):
    try:
        cfg = LoraConfig(r=4, lora_alpha=4, lora_dropout=0.05, bias="none",
                         task_type="FEATURE_EXTRACTION", **kw)
        pm = get_peft_model(GPT2Model.from_pretrained('gpt2'), cfg)
        tr = sum(p.numel() for p in pm.parameters() if p.requires_grad)
        print(f"  OK      {label:<48} trainable={tr}")
        return True
    except Exception as e:
        print(f"  FAIL    {label:<48} {type(e).__name__}: {str(e)[:110]}")
        return False

print("\n--- candidate target_modules spellings (author's is the first) ---")
try_cfg("target_modules=['c_attn']  (AUTHOR CODE)", target_modules=["c_attn"])
try_cfg("target_modules='c_attn'    (string->regex)", target_modules="c_attn")
try_cfg("target_modules=['attn.c_attn']", target_modules=["attn.c_attn"])
try_cfg("target_modules=['h.0.attn.c_attn']", target_modules=["h.0.attn.c_attn"])
try_cfg("target_modules=r'^.*c_attn$' (regex str)", target_modules=r"^.*c_attn$")
try_cfg("target_modules=['c_attn'] + layers_to_transform", target_modules=["c_attn"], layers_to_transform=[0,1,2,3,4,5])
try_cfg("baseline: target_modules=['c_proj']", target_modules=["c_proj"])
PYEOF
echo "exit=$?"
