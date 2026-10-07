#!/bin/bash
# ============================================================================
# hpc_env_check.sh — HPC environment FACTS for the innovation pilot.
# Prints facts ONLY. It does NOT verify the source, does NOT unlock pilot
# submission, and never submits anything.
# Run from the deployment root:   bash hpc_scripts/hpc_env_check.sh
# ============================================================================
set -u
ROOT="${INNOVATION_DEPLOYMENT_ROOT:-$(pwd)}"
echo "== host =="; hostname; date -u '+%Y-%m-%dT%H:%M:%SZ'; echo "pwd=$(pwd)"; echo "deployment_root=${ROOT}"
echo "== slurm =="; echo "SLURM_JOB_ID=${SLURM_JOB_ID:-none}"; sinfo -V 2>/dev/null || echo "sinfo: unavailable"
echo "== python/lib stack =="
python - <<'PY'
import platform
print("python", platform.python_version())
for m in ("torch", "transformers", "numpy", "pandas", "scipy", "sklearn", "statsmodels", "matplotlib"):
    try:
        mod = __import__(m); print(m, getattr(mod, "__version__", "?"))
    except Exception as e:
        print(m, "UNAVAILABLE", type(e).__name__)
try:
    import torch
    print("cuda_available", torch.cuda.is_available())
    print("cuda_device_count", torch.cuda.device_count())
    if torch.cuda.is_available():
        print("cuda_device_name", torch.cuda.get_device_name(0))
        print("cudnn_version", torch.backends.cudnn.version())
        print("cudnn_deterministic", torch.backends.cudnn.deterministic)
except Exception as e:
    print("torch probe failed", type(e).__name__, e)
PY
echo "== gpu =="; nvidia-smi 2>/dev/null || echo "nvidia-smi: unavailable"
echo "== offline GPT-2 load probe (must NOT download) =="
python - <<'PY'
import os
os.environ.setdefault("HF_HUB_OFFLINE", "1"); os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
try:
    from transformers import GPT2Model, GPT2Tokenizer
    GPT2Tokenizer.from_pretrained("gpt2"); GPT2Model.from_pretrained("gpt2")
    print("gpt2_offline_load=OK")
except Exception as e:
    print("gpt2_offline_load=FAILED", type(e).__name__, e)
PY
echo "== pilot script syntax (bash -n) =="
for f in hpc_scripts/pilot_*.sh hpc_scripts/innovation_worker.sh; do
  [ -f "$f" ] && { bash -n "$f" && echo "ok $f" || echo "FAIL $f"; }
done
echo "== deployment-root verification (informational; authoritative check is the pilot startup step) =="
python scripts/innovation/verify_source_snapshot.py \
  --deployment-root "${ROOT}" \
  --manifest results/innovation/source_snapshot_manifest.json || echo "DEPLOYMENT_ROOT_VERIFY=FAILED"
echo "== done =="
