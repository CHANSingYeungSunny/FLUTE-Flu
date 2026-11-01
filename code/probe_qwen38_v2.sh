#!/bin/bash -l
#SBATCH --job-name=qwen38_v2
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-q38v2-%j.out
#
# v2 load test for Qwen/Qwen3.8-27B-FP8.
#
# v1 (job 718448) failed in 34 s with
#   ValueError: The checkpoint you are trying to load has model type 'qwen3_5'
#   but Transformers does not recognize this architecture.
# because it ran in mlflu_hpc (transformers 4.57.6, Python 3.9). The checkpoint's
# config.json declares model_type=qwen3_5 and
# architectures=['Qwen3_5ForConditionalGeneration'] (a multimodal, 60+-layer,
# fp8-block-quantised model), which only exists from transformers 5.3.0 onwards.
#
# This job therefore runs in the NEW separate environment
#   /home/sychan552/.venvs/mlflu_llm   (Python 3.11.13 venv, torch 2.5.1
#   = same torch as mlflu_hpc, latest transformers 5.x)
# and NEVER touches mlflu_hpc.
#
# Reports: transformers version, AutoConfig output, param count, VRAM after
# load, one forward pass + peak VRAM. Fails loudly with the real traceback.
set -uo pipefail
PY=/home/sychan552/.venvs/mlflu_llm/bin/python
export HF_HOME=/home/sychan552/scratch/hf_cache
export HF_HUB_CACHE=/home/sychan552/scratch/hf_cache
export TRANSFORMERS_OFFLINE=1
export HF_HUB_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1

echo "=== job/env ==="
date -Is
echo "host=$(hostname)  job=${SLURM_JOB_ID:-none}"
timeout 20 nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader || echo NSMI_FAIL
"${PY}" -V
"${PY}" -m pip show transformers torch 2>&1 | grep -E '^(Name|Version):'

echo "=== cached snapshot on disk ==="
ls -d /home/sychan552/scratch/hf_cache/models--Qwen--Qwen3.8-27B-FP8/snapshots/* 2>/dev/null | head -2

# ---- 1. AutoConfig (the exact check requested) -----------------------------
echo "=== AutoConfig (offline) ==="
timeout 900 "${PY}" - <<'PYEOF'
import traceback
from transformers import AutoConfig
name = "Qwen/Qwen3.8-27B-FP8"
try:
    c = AutoConfig.from_pretrained(name, local_files_only=True)
    print("CONFIG OK model_type =", c.model_type)
    print("CONFIG OK class      =", type(c).__name__)
    # qwen3_5 is multimodal: text hyper-params live in `text_config`
    tc = getattr(c, "text_config", None) or c
    print("hidden_size      =", getattr(tc, "hidden_size", None))
    print("num_hidden_layers=", getattr(tc, "num_hidden_layers", None))
    print("vocab_size       =", getattr(tc, "vocab_size", None))
    print("vision_config    =", "present" if getattr(c, "vision_config", None) else "absent")
except Exception:
    traceback.print_exc()
    raise SystemExit(1)
PYEOF
cfg_rc=$?
echo "AutoConfig rc=$cfg_rc"
[ $cfg_rc -eq 0 ] || { echo "ABORT: qwen3_5 still not recognised"; exit $cfg_rc; }

# ---- 2. model load + forward ----------------------------------------------
echo "=== model load + forward ==="
timeout 3000 "${PY}" - <<'PYEOF'
import time, traceback
import torch
import transformers

name = "Qwen/Qwen3.8-27B-FP8"
print("transformers", transformers.__version__, "| torch", torch.__version__,
      "| cuda", torch.version.cuda, flush=True)
print("device", torch.cuda.get_device_name(0),
      "total %.1f GB" % (torch.cuda.get_device_properties(0).total_memory / 1e9), flush=True)

from transformers import AutoTokenizer

# qwen3_5 exposes a multimodal *ForConditionalGeneration class, so plain
# AutoModelForCausalLM may not resolve. Try the candidates in order of
# specificity and report which one worked - never silently switch dtype.
CANDIDATES = [
    ("Qwen3_5ForConditionalGeneration", lambda: getattr(transformers, "Qwen3_5ForConditionalGeneration")),
    ("AutoModelForImageTextToText",     lambda: transformers.AutoModelForImageTextToText),
    ("AutoModelForCausalLM",            lambda: transformers.AutoModelForCausalLM),
]

model = None
used = None


def _load(cls, label):
    """torch_dtype was renamed to dtype in transformers 5.x; support both names
    and report which one the installed version accepted."""
    kw = dict(local_files_only=True, low_cpu_mem_usage=True)
    for key in ("dtype", "torch_dtype"):
        try:
            m = cls.from_pretrained(name, **kw, **{key: "auto"})
            return m, key
        except TypeError as e:
            print(f"  [{label}] kwarg {key}= unsupported ({e}); trying next", flush=True)
    raise RuntimeError(f"{label}: neither dtype= nor torch_dtype= accepted")


for label, getter in CANDIDATES:
    try:
        cls = getter()
    except Exception as e:
        print(f"[skip] {label}: not available ({e})", flush=True)
        continue
    t0 = time.time()
    try:
        m, kw_used = _load(cls, label)
        model = m
        used = f"{label} (kwarg {kw_used}='auto')"
        print(f"[ok] loaded with {label} in {time.time()-t0:.0f}s", flush=True)
        break
    except Exception as e:
        print(f"[fail] {label}: {type(e).__name__}: {e}", flush=True)

if model is None:
    print("ABORT: no loader class could build this checkpoint")
    raise SystemExit(2)

tok = AutoTokenizer.from_pretrained(name, local_files_only=True)
print("tokenizer", type(tok).__name__, flush=True)

t0 = time.time()
model = model.cuda().eval()
print("to(cuda) %.1fs" % (time.time() - t0), flush=True)

n_all = sum(p.numel() for p in model.parameters())
print("PARAMS total      = %.4f B (%d)" % (n_all / 1e9, n_all), flush=True)
dt = {}
for p in model.parameters():
    dt[str(p.dtype)] = dt.get(str(p.dtype), 0) + p.numel()
for k, v in sorted(dt.items(), key=lambda x: -x[1]):
    print("  dtype %-16s %8.4f B" % (k, v / 1e9), flush=True)
print("VRAM after load   = %.2f GB allocated / %.2f GB reserved" % (
    torch.cuda.memory_allocated() / 1e9, torch.cuda.memory_reserved() / 1e9), flush=True)

ids = tok("Influenza-like illness weekly forecast for the next 4 weeks:",
          return_tensors="pt").to("cuda")
print("input_ids", tuple(ids["input_ids"].shape), flush=True)
torch.cuda.reset_peak_memory_stats()
t0 = time.time()
with torch.no_grad():
    out = model(**ids, output_hidden_states=True)
dt_fwd = time.time() - t0
peak = torch.cuda.max_memory_allocated() / 1e9
print("FORWARD OK logits=%s  %.3f s  peakVRAM %.2f GB" % (
    tuple(out.logits.shape), dt_fwd, peak), flush=True)

t0 = time.time()
with torch.no_grad():
    _ = model(**ids)
print("FORWARD warm     %.3f s  peakVRAM %.2f GB" % (
    time.time() - t0, torch.cuda.max_memory_allocated() / 1e9), flush=True)
print("LOADER USED      =", used, flush=True)
print("ALL_OK", flush=True)
PYEOF
echo "[qwen38_v2] DONE rc=$? $(date -Is)"
