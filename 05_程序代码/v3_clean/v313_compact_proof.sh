#!/bin/bash
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=110G
#SBATCH --time=02:00:00
#SBATCH --exclude=gpu-a100-05
#SBATCH --job-name=v313_compact
#SBATCH --output=/scratch/sychan552/_v313/logs/slurm_%j_v313_compact.out
#SBATCH --error=/scratch/sychan552/_v313/logs/slurm_%j_v313_compact.err

# Per-schema proof that the v3.13 compact checkpoint is reconstruction-complete
# and that the frozen backbone is NOT duplicated per row.
#
# READ-ONLY w.r.t. every deployment root and every existing artifact.
# calf/timecma use the v3.3 legacy checkpoints, which the D13 quarantine has
# MOVED (read-only access is still fine) — the same architectures are what the
# v3.13 Gate will exercise for real.
set -uo pipefail

module unload default 2>/dev/null || true
module load old_modules 2>/dev/null || true
export PATH=/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH
export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
export HF_DATASETS_CACHE=$HF_HOME
export TRANSFORMERS_CACHE=$HF_HOME
export PYTHONUNBUFFERED=1

BASE=/scratch/sychan552/_v313
R=/scratch/sychan552/innovation_deploy_root_v3_clean6
# the quarantine preserves the path RELATIVE TO the allowed root
# (/gpfs1/home/sychan552/innovation_durable), so legacy rows live under
# <quarantine>/screening/<dir>
Q=/gpfs1/scratch/sychan552/_d13_quarantine/screening
OUT=$BASE/compact_proof
TOOL=$BASE/compact_checkpoint.py
FAIL=0

cd "$R"
export PYTHONPATH="$R/scripts"
mkdir -p "$OUT"

echo "=== SCHEMA CONSTRUCTIBILITY (all primaries, ablations, controls) ==="
python -u "$TOOL" schema --run-dir "$R" --spec x --horizon 24 --out /dev/null \
  --report "$OUT/schema_report.json" 2>&1 | tail -30 || FAIL=1
echo "schema_stage_done fail=$FAIL"

prove() {  # prove <tag> <run_dir> <spec> <horizon>
  local tag="$1" rd="$2" spec="$3" h="$4"
  echo "=== PROOF $tag START ==="
  mkdir -p "$OUT/$tag"
  python -u "$TOOL" export-verify --run-dir "$rd" --spec "$spec" --horizon "$h" \
    --out "$OUT/$tag/compact.safetensors" --report "$OUT/$tag/report.json"
  local rc=$?
  echo "=== PROOF $tag END rc=$rc ==="
  [ $rc -eq 0 ] || FAIL=1
}

prove nlinear      "$R/results/v3_clean/runs/primary__nlinear__L24__seed42__w1"      primary__nlinear__L24__seed42__w1      24
prove dlinear      "$R/results/v3_clean/runs/primary__dlinear__L24__seed42__w1"      primary__dlinear__L24__seed42__w1      24
prove patchtst     "$R/results/v3_clean/runs/primary__patchtst__L24__seed42__w1"     primary__patchtst__L24__seed42__w1     24
prove itransformer "$R/results/v3_clean/runs/primary__itransformer__L24__seed42__w1" primary__itransformer__L24__seed42__w1 24
prove gpt2_miflu   "$R/results/v3_clean/runs/primary__gpt2_miflu__L24__seed42__w1"   primary__gpt2_miflu__L24__seed42__w1   24
prove qwen         "$R/results/v3_clean/runs/primary__qwen_time_llm__L24__seed42__w1" primary__qwen_time_llm__L24__seed42__w1 24
prove qwen_571472  "$R/results/v3_clean/runs/primary__qwen_time_llm__L24__seed46__w1" primary__qwen_time_llm__L24__seed46__w1 24
prove calf_legacy    "$Q/screening_calf_llm_L24_seed42"    primary__calf_llm__L24__seed42__w1     24
prove timecma_legacy "$Q/screening_timecma_llm_L24_seed42" primary__timecma_llm__L24__seed42__w1 24

echo "=== AGGREGATE ==="
python -u - "$OUT" <<'PY'
import glob, json, os, sys
out = sys.argv[1]
rows = []
for rp in sorted(glob.glob(os.path.join(out, "*", "report.json"))):
    try:
        d = json.load(open(rp, encoding="utf-8"))
    except Exception:
        continue
    if "source_bytes" not in d:
        continue
    r = d.get("restoration") or {}
    rows.append({"spec": d["spec_name"], "L": d["horizon"],
                 "src": d["source_bytes"], "compact": d["compact_bytes"],
                 "ratio": d["compression_ratio"],
                 "exact": d["reconstruction_exact"],
                 "frozen_excluded": d["frozen_backbone_excluded"],
                 "restoration_exact": r.get("restoration_exact"),
                 "unequal": r.get("n_keys_unequal")})
json.dump(rows, open(os.path.join(out, "aggregate.json"), "w",
                     encoding="utf-8"), indent=2)
print("TOTAL_PROOFS=%d" % len(rows))
for x in rows:
    print("%-14s L%-3d %12d -> %9d  x%-9.1f exact=%s frozen_excluded=%s "
          "restore_exact=%s unequal=%s" %
          (x["spec"], x["L"], x["src"], x["compact"], x["ratio"], x["exact"],
           x["frozen_excluded"], x["restoration_exact"], x["unequal"]))
PY

echo "PROOF_DONE fail=$FAIL"
exit $FAIL
