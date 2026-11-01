#!/bin/bash -l
#SBATCH --job-name=miflu_ctrl
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-ctrl-%j.out
#
# Resumable controller — ONE queue slot for the whole remaining matrix.
#
# ORDER MATTERS: cheap benchmark cells first (seconds each), expensive MIFlu
# horizons last (~80 min each). The previous ordering would have spent the whole
# 4h wall on MIFlu and never reached the benchmark.
#
# Phase 1  benchmark, L in {24,36,48,60} x seeds {42,43,44}:
#          non-LLM : nlinear patchtst itransformer
#                    (NLinear is the linear representative. DLinear is NOT a
#                     competitor: the essay's Table V already benchmarks it, so
#                     re-running it adds no new baseline. Its numbers are kept
#                     as a replication reference only.)
#          LLM     : timecma_llm qwen_time_llm calf_llm
#          new NN  : dnn cnn rnn lstm gru
#          classical: decision_tree random_forest gradient_boosting svr knn
# Phase 2  MIFlu author protocol, L in {36,48,60}, 10 reps
#
# Resumable: every cell is skipped if its output exists. A wall-clock guard
# stops ~30 min before the limit; resubmitting this script continues.
set -uo pipefail          # NOT -e: one failed cell must not kill the sweep

module unload default
module load old_modules

CODE=/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/home/sychan552/stage5_a2_durable/author_runs
EXP=/home/sychan552/stage5_a2_durable/expanded_runs
mkdir -p "${OUT}" "${EXP}"
cd "${CODE}"

START=$(date +%s)
LIMIT=$((3 * 3600 + 20 * 60))     # 3h20m inside a 4h wall
remaining() { echo $(( LIMIT - ($(date +%s) - START) )); }

echo "[ctrl] host=$(hostname) start=$(date -Is)"

run_bb() {   # run_bb <backbone> <L> <seed>
  local m=$1 L=$2 s=$3 d="${EXP}/${1}_L${2}_s${3}"
  if [ -f "${d}/pred_${m}_L${L}_s${s}.npz" ]; then echo "[skip] ${m} L=${L} s=${s}"; return 0; fi
  [ "$(remaining)" -lt 900 ] && { echo "[budget] requeue"; sbatch "${CODE}/submit_controller.sh"; exit 0; }
  "${PY}" -u train_backbone_966.py --backbone "${m}" --horizon "${L}" --seed "${s}" \
    --profile author_966 --containment strict \
    --export-dir "${d}" --ckpt-dir "${d}/ckpt" || echo "[FAIL] ${m} L=${L} s=${s}"
}

run_cls() {  # run_cls <model> <L> <seed>
  local m=$1 L=$2 s=$3 d="${EXP}/${1}_L${2}_s${3}"
  if [ -f "${d}/pred_${m}_L${L}_s${s}.npz" ]; then echo "[skip] ${m} L=${L} s=${s}"; return 0; fi
  [ "$(remaining)" -lt 900 ] && { echo "[budget] requeue"; sbatch "${CODE}/submit_controller.sh"; exit 0; }
  "${PY}" -u train_classical_966.py --model "${m}" --horizon "${L}" --seed "${s}" \
    --profile author_966 --containment strict --export-dir "${d}" \
    || echo "[FAIL] ${m} L=${L} s=${s}"
}

# ─────────────── Phase 1: benchmark (cheap first) ────────────────────────────
for L in 24 36 48 60; do
  echo "=========== BENCHMARK L=${L} $(date +%H:%M) ==========="
  for m in nlinear patchtst itransformer timecma_llm qwen_time_llm calf_llm; do
    for s in 42 43 44; do run_bb "${m}" "${L}" "${s}"; done
  done
  for m in dnn cnn rnn lstm gru; do
    for s in 42 43 44; do run_bb "${m}" "${L}" "${s}"; done
  done
  for m in decision_tree random_forest gradient_boosting svr knn; do
    for s in 42 43 44; do run_cls "${m}" "${L}" "${s}"; done
  done
done

# ─────────────── Phase 2: MIFlu remaining horizons ───────────────────────────
for L in 36 48 60; do
  d="${OUT}/L${L}_s2021"
  if compgen -G "${d}/results_miflu_paper_protocol_*.csv" > /dev/null; then
    echo "[skip] MIFlu L=${L}"; continue
  fi
  [ "$(remaining)" -lt 5700 ] && { echo "[budget] requeue before MIFlu L=${L}"; sbatch "${CODE}/submit_controller.sh"; exit 0; }
  echo "=== MIFlu L=${L} (10 reps) $(date +%H:%M) ==="
  "${PY}" -u train_miflu.py \
    --profile author_repo_966 --horizon "${L}" --text-source author_file \
    --reps 10 --epochs 20 --batch 16 --learning-rate 0.0001 \
    --containment strict \
    --export-dir "${d}" --ckpt-dir "${OUT}/ckpt_L${L}_s2021" \
    || echo "[FAIL] MIFlu L=${L}"
done

echo "=========== SUMMARY ==========="
echo "benchmark npz: $(find ${EXP} -name 'pred_*.npz' 2>/dev/null | wc -l)"
echo "miflu results: $(ls ${OUT}/L*_s2021/results_miflu_paper_protocol_2*.csv 2>/dev/null | wc -l)"
echo "[ctrl] DONE $(date -Is)"
