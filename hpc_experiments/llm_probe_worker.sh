#!/bin/bash
# =============================================================================
# $R/llmprobe/run_probe.sh — CPU-only LLM readiness probe (NO measured cell).
#
# Two things, in this order, so the cheap one always lands:
#   1. measure_llm_forward.py on Qwen2.5-1.5B  -> real s/prompt + cell cost
#   2. train_backbone_966.py --probe-only on ONE cell of each qwen2 1.5B model
#      (8 train / 4 val windows) -> proves the adapter works on a REAL
#      checkpoint, not a mock.
#
# Everything lands under $P/_probe/ — never in hpc_results/expanded_runs/ and
# never in paper_tables/ (AGENTS.md rule 13(b); PARTITION POLICY: tiny/IO
# partitions produce no number that may enter a table).
# =============================================================================
#SBATCH --job-name=mlflu_llmprobe
#SBATCH --partition=tiny
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=8000M
#SBATCH --time=5-00:00:00
#SBATCH --output=/gpfs1/home/sychan552/stage5_a2_durable/llmprobe/logs/llmprobe-%j.out
#SBATCH --error=/gpfs1/home/sychan552/stage5_a2_durable/llmprobe/logs/llmprobe-%j.err
# NOTE: deliberately no GRES line (must stay placeable on a CPU partition).

set -uo pipefail
P=/gpfs1/home/sychan552/stage5_a2_durable/llmprobe
OUT=/home/sychan552/scratch/mlflu_weights
export HTTPS_PROXY="${HTTPS_PROXY:-http://proxy.cityu.edu.hk:8080}"
export HTTP_PROXY="${HTTP_PROXY:-http://proxy.cityu.edu.hk:8080}"
export HF_HOME=/home/sychan552/scratch/hf_cache
export HF_HUB_CACHE=/home/sychan552/scratch/hf_cache/hub
export TRANSFORMERS_CACHE="$HF_HUB_CACHE"
export PYTHONUNBUFFERED=1
export TOKENIZERS_PARALLELISM=false
mkdir -p "$P/logs" "$P/_probe" "$OUT"

say() { printf '[%s] %s\n' "$(date '+%F %T')" "$*"; }
say "=== llmprobe start job=${SLURM_JOB_ID:-LOCAL} node=${SLURM_NODELIST:-$(hostname)} partition=${SLURM_JOB_PARTITION:-none} ==="
# The `hpc` env is a CONDA env (transformers 4.57.6 + pandas); the `llm` env is
# a venv with transformers 5.x but NO pandas, so the runner cannot import there.
# qwen2/llama-family arms therefore run in mlflu_hpc (docs/LLM_ARMS.md §7.1).
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
if [ ! -x "$PY" ]; then
  say "FATAL: interpreter missing: $PY"
  exit 66
fi
say "python=$($PY -V 2>&1) $( $PY -c 'import transformers,torch;print("tr",transformers.__version__,"torch",torch.__version__)' 2>&1 | tail -1 )"
say "HF_HOME=$HF_HOME HF_HUB_CACHE=$HF_HUB_CACHE"

QSHA=8faed761d45a263340a0528343f099c05c9a4323   # Qwen/Qwen2.5-1.5B, pinned in innovation/assets.py

say "--- STEP 1: measured per-prompt encoder cost (Qwen2.5-1.5B) ---"
$PY "$P/scripts/measure_llm_forward.py" \
    --model-id Qwen/Qwen2.5-1.5B --revision "$QSHA" \
    --batch 8 --repeats 3 --measured-params-b 1.5 --gpu-factor 25 \
    --json-out "$OUT/measured_llm_forward_qwen25_1p5b.json" 2>&1 | tail -30
say "STEP1 rc=$?"

run_cell() {   # $1=slug  $2=model_id  $3=revision (may be empty)  $4=extra flags
  local slug=$1 model=$2 rev=$3 extra=${4:-}
  say "--- STEP 2: adapter probe cell $slug ($model) ---"
  local t0=$SECONDS
  # shellcheck disable=SC2086
  $PY "$P/scripts/train_backbone_966.py" \
      --backbone llm_encoder --horizon 24 --seed 42 \
      --profile author_966 --containment strict \
      --arm-label "probe_$slug" \
      --llm-model-id "$model" ${rev:+--llm-revision "$rev"} \
      --llm-allow-download --encoder-batch-size 8 \
      --max-train-windows 8 --max-val-windows 4 --epochs 1 --probe-only \
      --export-dir "$P/_probe/$slug" --ckpt-dir "$P/_probe/$slug/ckpt" \
      $extra 2>&1 | tail -25
  say "cell $slug rc=$? wall=$((SECONDS-t0))s"
  $PY - "$P/_probe/$slug" <<'PY'
import glob, json, os, sys
cell = sys.argv[1]
mans = glob.glob(os.path.join(cell, "manifest_*.json"))
if not mans:
    print("  [verify] NO MANIFEST"); raise SystemExit(0)
m = json.load(open(mans[0]))
print("  [verify] manifest:", os.path.basename(mans[0]))
print("  [verify] probe_only=%s artefact_is_a_result=%s" % (m.get("probe_only"), m.get("artefact_is_a_result")))
print("  [verify] model_id=%s revision=%s" % ((m.get("encoder") or {}).get("model_id"), (m.get("encoder") or {}).get("revision")))
print("  [verify] n_train=%s n_val=%s n_test=%s encoder_batch_size=%s" % (
    (m.get("config") or {}).get("n_train"), (m.get("config") or {}).get("n_val"),
    (m.get("config") or {}).get("n_test"), (m.get("config") or {}).get("encoder_batch_size")))
for nz in glob.glob(os.path.join(cell, "pred_*.npz")):
    import numpy as np
    d = np.load(nz, allow_pickle=True)
    print("  [verify] npz %s pred=%s target=%s keys=%d" % (
        os.path.basename(nz), d["pred"].shape, d["target"].shape, len(d.files)))
PY
}

run_cell qwen25_1p5b Qwen/Qwen2.5-1.5B "$QSHA" ""
run_cell ds_r1_qwen1p5b deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B "" "--llm-allow-unpinned"

say "--- probe artefacts (must all be under _probe/) ---"
find "$P/_probe" -maxdepth 3 -name 'manifest_*.json' -o -maxdepth 3 -name 'pred_*.npz' 2>/dev/null | sed 's/^/  /'
say "=== llmprobe done job=${SLURM_JOB_ID:-LOCAL} ==="
exit 0
