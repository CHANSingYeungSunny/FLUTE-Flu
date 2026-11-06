#!/bin/bash
#SBATCH --job-name=t2_fm_env_finish
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/env_finish_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/env_finish_%j.err
# All heavy work (pip install, model load, offline pipeline) INSIDE sbatch.
set -u
BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm
LOGS=$BASE/logs
VENV=/home/sychan552/.venvs/mlflu_fm
MODELS=/gpfs1/scratch/sychan552/models
WORK=$BASE/extracted
mkdir -p "$LOGS" "$WORK"
echo "=== T2_ENV_FINISH START $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID ==="

echo "--- install missing deps ---"
timeout 900s "$VENV/bin/pip" install --disable-pip-version-check --no-input \
  "pandas>=2.0,<3" "scikit-learn>=1.2.2" "utilsforecast>=0.1.10" "wandb>=0.17.5" 2>&1 | tail -25
echo "PIP_MISSING_RC=$?"

echo "--- verify ALL imports (INSIDE sbatch) ---"
timeout 240s "$VENV/bin/python" - <<'PY' 2>&1
import sys, importlib, inspect
print("python", sys.version.split()[0], sys.executable)
for mod in ["torch","numpy","pandas","transformers","safetensors","einops",
            "sklearn","utilsforecast","wandb","chronos","timesfm"]:
    try:
        m = importlib.import_module(mod)
        print("IMPORT_OK", mod, getattr(m,"__version__","(n/a)"))
    except Exception as e:
        print("IMPORT_FAIL", mod, type(e).__name__, str(e)[:200])
try:
    import chronos
    from chronos import ChronosBoltPipeline, ChronosPipeline
    print("CHRONOS_OK", [x for x in ("ChronosBoltPipeline","ChronosPipeline","BaseChronosPipeline","Chronos2Pipeline") if hasattr(chronos,x)])
    print("ChronosBoltPipeline.from_pretrained SIG", inspect.signature(ChronosBoltPipeline.from_pretrained))
    print("ChronosBoltPipeline.predict SIG", inspect.signature(ChronosBoltPipeline.predict))
except Exception as e:
    print("CHRONOS_API_FAIL", type(e).__name__, str(e)[:300])
try:
    import timesfm
    print("TIMESFM_NAMES", [x for x in ("TimesFm","TimesFmHparams","TimesFmCheckpoint") if hasattr(timesfm,x)])
except Exception as e:
    print("TIMESFM_API_FAIL", type(e).__name__, str(e)[:300])
PY
echo "IMPORT_VERIFY_RC=$?"

echo "--- extract chronos_bolt_tiny tar INSIDE this compute-node job ---"
TAR=$MODELS/chronos_bolt_tiny.tar
echo "tar_sha256=$(timeout 120s sha256sum "$TAR" | cut -d' ' -f1)"
mkdir -p "$WORK/chronos_bolt_tiny"
timeout 300s tar -xf "$TAR" -C "$WORK/chronos_bolt_tiny" 2>&1
echo "TAR_EXTRACT_RC=$?"
echo "--- extracted files + sha256 ---"
find "$WORK/chronos_bolt_tiny" -type f -printf "%p %s\n" | sort | head -20
echo "model.safetensors sha256=$(timeout 120s sha256sum "$WORK/chronos_bolt_tiny/chronos_bolt_tiny/model.safetensors" 2>/dev/null | cut -d' ' -f1)"
echo "EXPECTED_LFS_OID=75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32"

echo "--- OFFLINE Chronos Bolt Tiny load test on CPU compute node ---"
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 timeout 300s "$VENV/bin/python" - <<'PY' 2>&1
import os, inspect
import torch
from chronos import ChronosBoltPipeline
p = "/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/extracted/chronos_bolt_tiny/chronos_bolt_tiny"
print("local_path_exists", os.path.isdir(p))
try:
    pipe = ChronosBoltPipeline.from_pretrained(p, local_files_only=True, device_map="cpu")
    print("OFFLINE_LOAD_OK", type(pipe).__name__, "device", getattr(pipe,"device",None))
    print("predict_sig", inspect.signature(pipe.predict))
    ctx = torch.zeros(104, dtype=torch.float32)
    out = pipe.predict(ctx, prediction_length=24)
    print("CPU_FORWARD_OK", tuple(out.shape), "finite", bool(torch.isfinite(out).all()))
except Exception as e:
    import traceback; traceback.print_exc()
    print("OFFLINE_LOAD_FAIL", type(e).__name__, str(e)[:400])
PY
echo "OFFLINE_LOAD_RC=$?"
echo "=== T2_ENV_FINISH END $(date -u +%FT%TZ) ==="
