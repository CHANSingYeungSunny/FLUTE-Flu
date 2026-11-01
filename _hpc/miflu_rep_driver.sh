#!/bin/bash
# miflu_rep_driver.sh -- fit the MISSING repetitions of the MIFlu reproduction
# protocol (10 reps, seeds 2021-2030) for one horizon, one process per seed.
#
# WHY per-seed processes instead of one `--reps 10` job
# -----------------------------------------------------
# `train_miflu.main()` renames the best-validation rep's checkpoint to
# `best_miflu_L{L}.pth` and then DELETES every other `_rep_*.pth`. A single
# `--reps 10` run therefore keeps only ONE per-rep checkpoint, which is useless
# for per-rep prediction export. One `--reps 1 --seed S` process per seed keeps
# one validation-selected checkpoint per seed and writes that seed's own CSV.
#
# This is NOT a different experiment: `train_L()` calls `set_seed(seed + L)` on
# entry, so rep S of `--reps 10 --seed 2021` and a standalone `--reps 1 --seed S`
# draw the identical RNG stream and produce the identical weights. Verified
# empirically for L=24 seed=2021: standalone 1-rep test_mse_all = 1.240157,
# identical to rep 1 of the 10-rep run recorded in
# `L24_s2021/training_miflu_log_20261031_195730.txt`.
#
# Resume: a (L, seed) whose `ckpt_L{L}_s{S}/best_miflu_L{L}.pth` exists is skipped.
set -uo pipefail
module unload default
module load old_modules

CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
BUDGET=${MH_BUDGET:-11400}
cd "${CODE}"

START=$(date +%s)
elapsed() { echo $(( $(date +%s) - START )); }

echo "[reps] host=$(hostname) start=$(date -Is) budget=${BUDGET}s"
echo "[reps] cells: $*"

for pair in "$@"; do
  L=${pair%%:*}
  S=${pair##*:}
  ckpt="${OUT}/ckpt_L${L}_s${S}/best_miflu_L${L}.pth"
  run="${OUT}/_seedruns/L${L}_s${S}"

  if [ -f "${ckpt}" ]; then
    echo "[skip] L=${L} seed=${S}: checkpoint already present"
    continue
  fi
  if [ "$(elapsed)" -gt "${BUDGET}" ]; then
    echo "[budget] out of wall clock before L=${L} seed=${S}; rerun to resume"
    break
  fi

  mkdir -p "${run}"
  echo "================================================================"
  echo "=== L=${L} seed=${S}  start $(date +%H:%M:%S)  elapsed=$(elapsed)s"
  echo "================================================================"
  "${PY}" -u train_miflu.py \
    --profile author_repo_966 \
    --horizon "${L}" \
    --text-source author_file \
    --reps 1 \
    --seed "${S}" \
    --epochs 20 \
    --batch 16 \
    --learning-rate 0.0001 \
    --containment strict \
    --export-dir "${run}" \
    --ckpt-dir   "${OUT}/ckpt_L${L}_s${S}"
  rc=$?

  if [ ${rc} -eq 0 ] && [ -f "${ckpt}" ]; then
    echo "[ok] L=${L} seed=${S}: checkpoint written"
    # HARD RULE 11: the full artefact set (7-channel npz + wide CSV + per-variable
    # results CSV + manifest) must be produced by THIS job, not a later pass.
    DEV=cpu
    "${PY}" -c 'import torch,sys; sys.exit(0 if torch.cuda.is_available() else 1)' 2>/dev/null && DEV=cuda
    echo "[rule11] exporting all-7 artifacts on ${DEV} ..."
    "${PY}" -u export_miflu_all7.py --cells "${L}:${S}" --device "${DEV}" --force \
      || echo "[FAIL] L=${L} seed=${S}: all-7 export failed (checkpoint is kept; rerun the export)"
    for f in "pred_miflu_L${L}_seed${S}.npz" "predictions_miflu_L${L}_seed${S}.csv" \
             "results_miflu_L${L}_seed${S}.csv" "manifest_miflu_L${L}_seed${S}.json"; do
      [ -f "${OUT}/L${L}_all7/${f}" ] && echo "  [artifact ok] ${f}" || echo "  [artifact MISSING] ${f}"
    done
  else
    echo "[FAIL] L=${L} seed=${S}: rc=${rc} ckpt_present=$([ -f "${ckpt}" ] && echo yes || echo no)"
  fi
  echo "[rec] $(grep -h 'DONE: test_mse' "${run}"/training_miflu_log_*.txt 2>/dev/null | tail -1 | sed 's/^\[[0-9:]*\] *//')"
  echo "=== L=${L} seed=${S}  end $(date +%H:%M:%S)  elapsed=$(elapsed)s"
done

echo "[reps] DONE $(date -Is) elapsed=$(elapsed)s"
echo "[reps] per-seed checkpoints present:"
for L in 24 36 48 60; do
  n=$(ls "${OUT}"/ckpt_L${L}_s20*/best_miflu_L${L}.pth 2>/dev/null | wc -l)
  echo "  L=${L}: ${n}/10"
done
