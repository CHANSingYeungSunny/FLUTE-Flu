#!/bin/bash
# _probe_v2.sh -- one-shot inventory for the v2 queue: interpreters, analysis
# scripts, staged layout, current cluster state. Read-only.
set -uo pipefail
R=/gpfs1/home/sychan552/stage5_a2_durable
Q=$R/code/queue
A=$R/analysis
PY_HPC=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
PY_LLM=/home/sychan552/.venvs/mlflu_llm/bin/python

echo "=== interpreters ==="
for p in "$PY_HPC" "$PY_LLM"; do
  if [ -x "$p" ]; then
    printf '%-52s ' "$p"
    timeout 60 "$p" -c 'import sys;print("py",sys.version.split()[0],end=" ")' 2>&1 | tr -d '\n'
    timeout 90 "$p" -c 'import numpy,pandas;print("numpy",numpy.__version__,"pandas",pandas.__version__,end=" ")' 2>&1 | tr -d '\n'
    timeout 120 "$p" -c 'import torch;print("torch",torch.__version__,end=" ")' 2>&1 | tr -d '\n'
    timeout 120 "$p" -c 'import transformers;print("tr",transformers.__version__,end=" ")' 2>&1 | tr -d '\n'
    timeout 120 "$p" -c 'import matplotlib;print("mpl",matplotlib.__version__,end=" ")' 2>&1 | tr -d '\n'
    timeout 120 "$p" -c 'import scipy;print("scipy",scipy.__version__)' 2>&1 | tail -1
  else
    echo "MISSING $p"
  fi
done

echo
echo "=== analysis scripts required by F1-F5 ==="
for n in analysis_expanded analysis_postprocess seasonal_naive_baseline plot_bench plot_pareto \
         verify_bench_unchanged verify_miflu_oracle import_miflu_predictions eval_windows recipes; do
  printf '%-28s ' "$n"
  if [ -f "$A/scripts/$n.py" ]; then echo "OK $(wc -c < "$A/scripts/$n.py") bytes"; else echo MISSING; fi
done

echo
echo "=== staged analysis root ==="
ls -l "$A" | sed -n '1,10p'
echo "paper_tables csvs: $(ls -1 "$A"/paper_tables/*.csv 2>/dev/null | wc -l)"
echo "figures:           $(ls -1 "$A"/figures 2>/dev/null | wc -l)"
echo "cells:             $(ls -1 "$A"/hpc_results/expanded_runs/*/pred_*.npz 2>/dev/null | wc -l)"
echo "author all7 npz:   $(ls -1 "$A"/author_runs/L*_all7/*.npz 2>/dev/null | wc -l)"

echo
echo "=== does analysis_expanded run where cwd=\$A ? (dry import check) ==="
cd "$A" || exit 1
PYTHONPATH="$A/scripts" timeout 120 "$PY_HPC" -c 'import sys;sys.path.insert(0,"scripts");import analysis_expanded;print("analysis_expanded imports OK")' 2>&1 | tail -5

echo
echo "=== queue file shape ==="
head -1 "$Q/master_queue.tsv" | tr '\t' '\n' | nl
echo "rows: $(( $(wc -l < "$Q/master_queue.tsv") - 1 ))"

echo
echo "=== BENCH_MSE_BY_MODEL_L.csv head ==="
head -3 "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv"
echo "mtime: $(stat -c '%y' "$A/paper_tables/BENCH_MSE_BY_MODEL_L.csv")"

echo
echo "=== local-vs-cluster paper_tables identity (size compare on 3 files) ==="
for f in BENCH_MSE_BY_MODEL_L.csv BENCH_EFFICIENCY.post_evalwindow16.csv BENCH_KS_CHAMPION_DETAIL.csv; do
  printf '%-46s %s\n' "$f" "$(stat -c '%s %y' "$A/paper_tables/$f" 2>/dev/null)"
done
