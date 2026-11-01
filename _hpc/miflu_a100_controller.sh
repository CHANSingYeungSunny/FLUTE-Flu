#!/bin/bash -l
#SBATCH --job-name=miflu_a100
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-miflu-a100-%j.out
#
# MIFlu reproduction repetitions (10 reps, seeds 2021-2030) for L=36/48/60.
# ONE controller that self-requeues inside the 4 h wall (stingy allows 1 running
# + 1 pending per user), so 27 runs complete over ~2 wall slots.
#
# HARDWARE: A100 only. AGENTS.md HARD RULE 12 -- a V100 cell is invalid for the
# comparison and must never be silently mixed in. The GPU is asserted by API call
# before any training, and the measured device is recorded in each manifest.
#
# HARD RULE 11: each cell's full artefact set (7-channel npz + wide CSV +
# per-variable results CSV + manifest with checkpoint sha256) is written by THIS
# job immediately after the fit.
#
# ORACLE: every rep is compared against the per-rep test_mse_all recorded by the
# ORIGINAL 10-rep run that produced AGENTS.md 1.1. A mismatch means the cell is
# not the same experiment -> the job stops and reports instead of accepting it.
set -uo pipefail
module unload default
module load old_modules

CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
cd "${CODE}"

START=$(date +%s)
elapsed() { echo $(( $(date +%s) - START )); }
BUDGET=11100          # 3h05m inside the 4h wall

# ---- oracle: per-rep test_mse_all recorded by the original 10-rep runs -------
oracle() {
  case "$1" in
    36:2021) echo 1.314358 ;; 36:2022) echo 1.306645 ;; 36:2023) echo 1.269466 ;;
    36:2024) echo 1.154099 ;; 36:2025) echo 1.767328 ;; 36:2026) echo 1.312511 ;;
    36:2027) echo 1.400796 ;; 36:2028) echo 1.302717 ;; 36:2029) echo 1.404061 ;;
    36:2030) echo 1.328807 ;;
    48:2021) echo 1.482299 ;; 48:2022) echo 1.711215 ;; 48:2023) echo 1.663857 ;;
    48:2024) echo 1.879495 ;; 48:2025) echo 1.723161 ;; 48:2026) echo 1.620327 ;;
    48:2027) echo 1.628296 ;; 48:2028) echo 1.588157 ;; 48:2029) echo 1.570881 ;;
    48:2030) echo 1.675020 ;;
    60:2021) echo 1.599641 ;; 60:2022) echo 1.664878 ;; 60:2023) echo 1.821282 ;;
    60:2024) echo 1.915250 ;; 60:2025) echo 1.410785 ;; 60:2026) echo 1.984315 ;;
    60:2027) echo 1.614602 ;; 60:2028) echo 1.401814 ;; 60:2029) echo 1.520661 ;;
    60:2030) echo 1.895393 ;;
    *) echo "" ;;
  esac
}

CELLS="36:2021 36:2022 36:2023 36:2025 36:2026 36:2027 36:2028 36:2029 36:2030
       48:2022 48:2023 48:2024 48:2025 48:2026 48:2027 48:2028 48:2029 48:2030
       60:2021 60:2022 60:2023 60:2024 60:2026 60:2027 60:2028 60:2029 60:2030"

echo "[a100] host=$(hostname) job=${SLURM_JOB_ID:-?} node=${SLURM_JOB_NODELIST:-?} start=$(date -Is)"

# ---- hardware assertion: A100 only -----------------------------------------
"${PY}" - <<'PYEOF'
import sys, torch
if not torch.cuda.is_available():
    print("[a100] FATAL: no CUDA device"); sys.exit(3)
name = torch.cuda.get_device_name(0)
cap = torch.cuda.get_device_capability(0)
vram = torch.cuda.get_device_properties(0).total_memory / 2**30
print(f"[a100] MEASURED gpu={name} capability={cap} vram={vram:.1f}GiB")
if "A100" not in name:
    print(f"[a100] FATAL: expected an A100, got {name!r}. A non-A100 cell would "
          f"confound the benchmark (HARD RULE 12). Refusing to train.")
    sys.exit(4)
PYEOF
if [ $? -ne 0 ]; then echo "[a100] hardware assertion failed - aborting"; exit 1; fi

# ---- L=24: no training needed, export the 10 saved checkpoints on GPU -------
# (a forward pass on GPU keeps the hardware provenance uniform with the trained
# cells; a CPU-forward number would have to be labelled CPU per HARD RULE 12)
echo "[a100] L=24 export pass on GPU $(date +%H:%M:%S)"
"${PY}" -u export_miflu_all7.py --all --horizons 24 --device cuda \
  || echo "[FAIL] L=24 export pass"

# ---- per-cell loop ----------------------------------------------------------
for pair in ${CELLS}; do
  L=${pair%%:*}; S=${pair##*:}
  ckpt="${OUT}/ckpt_L${L}_s${S}/best_miflu_L${L}.pth"
  art="${OUT}/L${L}_all7"
  run="${OUT}/_seedruns/L${L}_s${S}"

  # a cell is complete only if checkpoint AND all four rule-11 artefacts exist
  if [ -f "${ckpt}" ] && [ -f "${art}/pred_miflu_L${L}_seed${S}.npz" ] \
     && [ -f "${art}/predictions_miflu_L${L}_seed${S}.csv" ] \
     && [ -f "${art}/results_miflu_L${L}_seed${S}.csv" ] \
     && [ -f "${art}/manifest_miflu_L${L}_seed${S}.json" ]; then
    echo "[skip] L=${L} s=${S}: complete"
    continue
  fi

  if [ "$(elapsed)" -gt "${BUDGET}" ]; then
    echo "[budget] requeueing at $(elapsed)s before L=${L} s=${S}"
    sbatch "${CODE}/miflu_a100_controller.sh"
    exit 0
  fi

  mkdir -p "${run}" "${art}"
  echo "================================================================"
  echo "=== L=${L} seed=${S} start $(date +%H:%M:%S) elapsed=$(elapsed)s"
  echo "================================================================"

  if [ ! -f "${ckpt}" ]; then
    "${PY}" -u train_miflu.py \
      --profile author_repo_966 --horizon "${L}" --text-source author_file \
      --reps 1 --seed "${S}" --epochs 20 --batch 16 --learning-rate 0.0001 \
      --containment strict \
      --export-dir "${run}" --ckpt-dir "${OUT}/ckpt_L${L}_s${S}"
  else
    echo "[reuse] checkpoint present, reusing it"
  fi

  if [ ! -f "${ckpt}" ]; then echo "[FAIL] L=${L} s=${S}: no checkpoint"; continue; fi

  # ---- oracle check against the original 10-rep run ----------------------
  GOT=$(grep -h "DONE: test_mse" "${run}"/training_miflu_log_*.txt 2>/dev/null | tail -1 | sed -E 's/.*test_mse=([0-9.]+).*/\1/')
  EXP=$(oracle "${pair}")
  echo "[oracle] L=${L} s=${S} got=${GOT:-n/a} expected=${EXP:-n/a}"
  if [ -n "${GOT}" ] && [ -n "${EXP}" ]; then
    "${PY}" - "${GOT}" "${EXP}" <<'PYEOF'
import sys
g, e = float(sys.argv[1]), float(sys.argv[2])
d = abs(g - e)
print(f"[oracle] |diff|={d:.3e}")
sys.exit(0 if d <= 1e-5 else 5)
PYEOF
    if [ $? -ne 0 ]; then
      echo "[ORACLE MISMATCH] L=${L} s=${S}: got ${GOT} expected ${EXP}. This cell is NOT the same experiment - stopping."
      exit 6
    fi
  fi

  # ---- rule 11: all-7 artefacts in the same job --------------------------
  "${PY}" -u export_miflu_all7.py --cells "${L}:${S}" --device cuda --force \
    || echo "[FAIL] L=${L} s=${S}: all-7 export failed"
  for f in "pred_miflu_L${L}_seed${S}.npz" "predictions_miflu_L${L}_seed${S}.csv" \
           "results_miflu_L${L}_seed${S}.csv" "manifest_miflu_L${L}_seed${S}.json"; do
    [ -f "${art}/${f}" ] || echo "  [artifact MISSING] ${f}"
  done
  echo "=== L=${L} seed=${S} end $(date +%H:%M:%S) elapsed=$(elapsed)s"
done

echo "[a100] DONE $(date -Is) elapsed=$(elapsed)s"
for L in 24 36 48 60; do
  n=$(ls "${OUT}"/L${L}_all7/pred_miflu_L${L}_seed20*.npz 2>/dev/null | wc -l)
  echo "  L=${L}: ${n}/10 cells with 7-channel npz"
done
