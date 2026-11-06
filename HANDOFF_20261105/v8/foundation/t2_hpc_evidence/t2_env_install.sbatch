#!/bin/bash
#SBATCH --job-name=t2_fm_env
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=4
#SBATCH --mem=12G
#SBATCH --time=00:35:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/env_install_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/env_install_%j.err
# All package installation and ALL imports of torch/chronos/timesfm happen
# INSIDE this compute-node job. Nothing heavy on the login node. (AGENTS.md RULE 1)
set -u
BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm
LOGS=$BASE/logs
VENV=/home/sychan552/.venvs/mlflu_fm
PY311=/home/sychan552/.venvs/mlflu_llm/bin/python
SRC_SITE=/home/sychan552/.venvs/mlflu_llm/lib/python3.11/site-packages
mkdir -p "$LOGS"
echo "=== T2_ENV_INSTALL START $(date -u +%FT%TZ) host=$(hostname) job=$SLURM_JOB_ID ==="

echo "--- base python ---"
"$PY311" -V 2>&1
echo "--- site-packages of mlflu_llm (reuse its Python-3.11 torch/transformers) ---"
"$PY311" -c "import site,sys; print(sys.version); [print(p) for p in site.getsitepackages()]" 2>&1
echo "--- key packages already in mlflu_llm (metadata only, NO torch import) ---"
"$PY311" - <<'PY' 2>&1
from importlib import metadata as m
for n in ["torch","transformers","numpy","pandas","safetensors","einops","accelerate",
          "jax","jaxlib","flax","huggingface-hub","scikit-learn","absl-py","einshape",
          "chronos-forecasting","timesfm","fire","PyYAML"]:
    try: print(f"{n}={m.version(n)}")
    except Exception as e: print(f"{n}=MISSING ({type(e).__name__})")
PY
echo "--- does mlflu_llm torch actually import on a COMPUTE node? ---"
timeout 60s "$PY311" -c "import torch; print('torch',torch.__version__,'cuda_available',torch.cuda.is_available())" 2>&1 | tail -3
echo "TORCH_IMPORT_RC=$?"

echo "--- create isolated venv (Python 3.11) ---"
if [ ! -x "$VENV/bin/python" ]; then
  "$PY311" -m venv "$VENV" 2>&1
  echo "VENV_CREATE_RC=$?"
else
  echo "VENV_ALREADY_EXISTS"
fi
"$VENV/bin/python" -V 2>&1
echo "--- reuse mlflu_llm site-packages via .pth (both are Python 3.11) ---"
SITE=$("$VENV/bin/python" -c "import site; print(site.getsitepackages()[0])")
echo "NEW_VENV_SITE=$SITE"
if [ -d "$SRC_SITE" ]; then
  echo "$SRC_SITE" > "$SITE/_mlflu_llm_reuse.pth"
  echo "PTH_WRITTEN=$SITE/_mlflu_llm_reuse.pth"
else
  echo "PTH_SKIPPED: $SRC_SITE not found"
fi

echo "--- pip install pinned, source-pinned packages (no deps first) ---"
timeout 600s "$VENV/bin/pip" install --disable-pip-version-check --no-input \
  --no-deps "chronos-forecasting==2.3.2" "timesfm==1.3.0" 2>&1
echo "PIP_NO_DEPS_RC=$?"

echo "--- install any small missing pure-python deps (no torch, no jax) ---"
timeout 600s "$VENV/bin/pip" install --disable-pip-version-check --no-input \
  "accelerate>=0.28" "einops" "safetensors" "fire" "PyYAML" "einshape" "absl-py" \
  "huggingface-hub" 2>&1 | tail -25
echo "PIP_SMALL_DEPS_RC=$?"

echo "--- verify imports (INSIDE sbatch) ---"
timeout 180s "$VENV/bin/python" - <<'PY' 2>&1
import sys, importlib
print("python", sys.version.split()[0], sys.executable)
for mod in ["torch","numpy","pandas","transformers","safetensors","einops","chronos","timesfm"]:
    try:
        m = importlib.import_module(mod)
        print("IMPORT_OK", mod, getattr(m,"__version__","(no __version__)"))
    except Exception as e:
        print("IMPORT_FAIL", mod, type(e).__name__, str(e)[:220])
try:
    from chronos import ChronosBoltPipeline, ChronosPipeline, BaseChronosPipeline
    print("CHRONOS_API_OK", "ChronosBoltPipeline", "ChronosPipeline", "BaseChronosPipeline")
except Exception as e:
    print("CHRONOS_API_FAIL", type(e).__name__, str(e)[:220])
try:
    import timesfm
    print("TIMESFM_API_NAMES", [x for x in ("TimesFm","TimesFmHparams","TimesFmCheckpoint") if hasattr(timesfm,x)])
except Exception as e:
    print("TIMESFM_API_FAIL", type(e).__name__, str(e)[:220])
PY
echo "IMPORT_VERIFY_RC=$?"

echo "--- installed versions in NEW venv ---"
"$VENV/bin/pip" list 2>/dev/null | grep -iE "chronos|timesfm|torch|transformers|numpy|pandas|safetensors|accelerate|einops|jax|flax|huggingface" | head -30
echo "=== T2_ENV_INSTALL END $(date -u +%FT%TZ) ==="
