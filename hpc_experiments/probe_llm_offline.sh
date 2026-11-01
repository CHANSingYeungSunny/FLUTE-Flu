#!/bin/bash -l
#SBATCH --job-name=llm_offline
#SBATCH --partition=gpu_v100s
#SBATCH --gres=gpu:v100s:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=48G
#SBATCH --time=01:00:00
#SBATCH --output=slurm-offline-%j.out
#
# Second half of the LLM feasibility check. The weights are already in the shared
# cache (downloaded on the LOGIN node, because compute nodes have no internet).
# This job therefore runs OFFLINE and answers:
#   2. do they load with TRANSFORMERS_OFFLINE=1 ?
#   3. hidden size / layers / params / dtype
#   4. one forward: shape, latency, peak VRAM (at our sequence length)
set -uo pipefail
module unload default
module load old_modules
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
export HF_HOME=/home/sychan552/scratch/hf_cache
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader

"${PY}" - <<'PYEOF'
import os, time, torch
from transformers import AutoConfig, AutoModel, AutoTokenizer
for name in ["Qwen/Qwen2.5-1.5B", "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B"]:
    print("\n===", name, "===", flush=True)
    try:
        cfg = AutoConfig.from_pretrained(name)
        tok = AutoTokenizer.from_pretrained(name)
        m = AutoModel.from_pretrained(name, torch_dtype=torch.float16).cuda().eval()
        n = sum(p.numel() for p in m.parameters())
        print("type=%s hidden=%s layers=%s heads=%s" % (
            cfg.model_type, getattr(cfg, "hidden_size", None),
            getattr(cfg, "num_hidden_layers", None), getattr(cfg, "num_attention_heads", None)))
        print("params=%.3fB  fp16=%.2f GB" % (n/1e9, n*2/1e9))
        ids = tok("Influenza-like illness weekly forecast.", return_tensors="pt").to("cuda")
        print("tokens:", tuple(ids["input_ids"].shape))
        torch.cuda.reset_peak_memory_stats()
        t0 = time.time()
        with torch.no_grad():
            out = m(**ids)
        print("forward OK %s | %.3fs | peakVRAM %.2f GB" % (
            tuple(out.last_hidden_state.shape), time.time()-t0,
            torch.cuda.max_memory_allocated()/1e9))
        del m; torch.cuda.empty_cache()
    except Exception as e:
        print("FAILED", type(e).__name__, str(e)[:300], flush=True)
print("\nPROBE DONE", flush=True)
PYEOF
echo "[offline] done $(date -Is)"
