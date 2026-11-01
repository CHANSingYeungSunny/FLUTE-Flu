#!/bin/bash -l
#SBATCH --job-name=miflu_expanded
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-expanded-%j.out
#
# Expanded non-LLM benchmark (2026-10-31).
#
# 10 new backbones x 4 horizons x 3 seeds = 120 cells:
#   torch  : dnn cnn rnn lstm gru              (train_backbone_966.py, A2 protocol)
#   sklearn: decision_tree random_forest gradient_boosting svr knn
#                                              (train_classical_966.py, A2 protocol imported verbatim)
#
# DLinear stays as the ONLY linear model; NLinear is deliberately excluded from
# the expanded set (it remains in the frozen Track-C archive).
#
# The cell loop is RESUMABLE: an existing pred_*.npz makes the cell skip, so a
# 4-hour wall-clock hit can be continued by simply resubmitting this script.
set -uo pipefail   # deliberately NOT -e: one bad cell must not kill the sweep

module unload default
module load old_modules

CODE=/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/home/sychan552/stage5_a2_durable/expanded_runs
mkdir -p "${OUT}"
cd "${CODE}"

HORIZONS="24 36 48 60"
SEEDS="42 43 44"
NN="dnn cnn rnn lstm gru"
CLS="decision_tree random_forest gradient_boosting svr knn"

echo "[expanded] host=$(hostname) date=$(date -Is)"

echo "=================== PREFLIGHT ==================="
"${PY}" -c "import sklearn, torch; print('sklearn', sklearn.__version__, '| torch', torch.__version__)"
for m in ${NN}; do
  "${PY}" train_backbone_966.py --self-check --backbone "${m}" 2>&1 | tail -3 \
    || echo "[preflight-FAIL] ${m}"
done

echo "=================== TORCH BACKBONES ==================="
for m in ${NN}; do
  for L in ${HORIZONS}; do
    for s in ${SEEDS}; do
      d="${OUT}/${m}_L${L}_s${s}"
      if [ -f "${d}/pred_${m}_L${L}_s${s}.npz" ]; then echo "[skip] ${m} L=${L} s=${s}"; continue; fi
      echo "=== ${m} L=${L} seed=${s} ==="
      "${PY}" -u train_backbone_966.py --backbone "${m}" --horizon "${L}" --seed "${s}" \
        --profile author_966 --containment strict \
        --export-dir "${d}" --ckpt-dir "${d}/ckpt" \
        || echo "[FAIL] ${m} L=${L} s=${s}"
    done
  done
done

echo "=================== CLASSICAL ML ==================="
for m in ${CLS}; do
  for L in ${HORIZONS}; do
    for s in ${SEEDS}; do
      d="${OUT}/${m}_L${L}_s${s}"
      if [ -f "${d}/pred_${m}_L${L}_s${s}.npz" ]; then echo "[skip] ${m} L=${L} s=${s}"; continue; fi
      echo "=== ${m} L=${L} seed=${s} ==="
      "${PY}" -u train_classical_966.py --model "${m}" --horizon "${L}" --seed "${s}" \
        --profile author_966 --containment strict --export-dir "${d}" \
        || echo "[FAIL] ${m} L=${L} s=${s}"
    done
  done
done

echo "=================== SUMMARY ==================="
find "${OUT}" -name "pred_*.npz" | wc -l
echo "[expanded] DONE date=$(date -Is)"
