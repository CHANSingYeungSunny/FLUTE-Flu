#!/bin/bash
# miflu_seed_driver.sh -- one author-faithful MIFlu fit per (L, seed) with a
# per-window prediction export. Run inside an sbatch allocation.
#
# WHY THIS EXISTS
# ---------------
# The benchmark row for MIFlu must use the SAME seeds as the other 16 arms
# (42/43/44), not the reproduction protocol's seeds (2021..2030). No usable
# seed-42/43/44 checkpoint existed (the only `_s42` checkpoints came from a
# cancelled prompt-mode run), so each cell has to be fit once.
#
# PROTOCOL (identical to submit_export.sh, which produced the validated
# `L24_s2021_pred` export, except for --seed):
#   profile author_repo_966 | author text embedding file | T=104 | Lp=24 | S=2
#   K=6 | lora_r=4 | use_text_ln=False | batch 16 | lr 1e-4 | 20 epochs
#   containment strict (A2) | validation-selected best epoch
#
# `--reps 1` is deliberate: the single rep's validation-best-epoch checkpoint is
# the exported one, which is exactly how the 16 benchmark arms pick
# `best_<arm>_L{L}_seed{S}.pth` per seed. `--reps 3` would export only the
# best-val rep of the three and silently lose two seeds.
#
# Runtime seeding parity: train_miflu.train_L() calls set_seed(seed + L), the
# SAME convention as train_backbone_966.train_one(). So `--seed 42` here and
# `--seed 42` in the arms draw from the identical RNG stream.
#
# Resume: a (L, seed) whose final CSV already exists is skipped.
set -uo pipefail
module unload default
module load old_modules

CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
BUDGET=${MH_BUDGET:-11400}          # wall-clock seconds this job may consume
cd "${CODE}"

START=$(date +%s)
elapsed() { echo $(( $(date +%s) - START )); }

echo "[driver] host=$(hostname) start=$(date -Is)"
echo "[driver] jobs: $*"
echo "[driver] budget=${BUDGET}s"

# ---- preflight: author-faithful trainable parameter count (non-fatal) -------
echo "[preflight] building MIFlu(N=1,T=104,L=24,Lp=24,S=2,K=6,lora_r=4,use_text_ln=False)"
"${PY}" - <<'PYEOF'
import sys
sys.path.insert(0, "/gpfs1/home/sychan552/stage5_a2_durable/code")
import miflu_model as m
mod = m.MIFlu(N=1, T=104, L=24, Lp=24, S=2, K=6, lora_r=4, device="cpu",
              use_text_ln=False, flatten_head=True)
tr = sum(p.numel() for p in mod.parameters() if p.requires_grad)
print("[preflight] trainable params =", tr, flush=True)
print("[preflight] expected         = 1673496", flush=True)
print("[preflight] MATCH" if tr == 1673496 else "[preflight] MISMATCH", flush=True)
PYEOF
if [ $? -ne 0 ]; then echo "[preflight] WARN: could not build model on CPU; continuing"; fi

# ---- per-(L, seed) fit + export --------------------------------------------
for pair in "$@"; do
  L=${pair%%:*}
  S=${pair##*:}
  d="${OUT}/L${L}_s${S}"
  final="${d}/predictions_miflu_L${L}_s${S}_paper_protocol.csv"

  if [ -f "${final}" ]; then
    echo "[skip] L=${L} s=${S} -> $(basename "${final}") already exists"
    continue
  fi
  if [ "$(elapsed)" -gt "${BUDGET}" ]; then
    echo "[budget] out of wall clock before L=${L} s=${S}; rerun to resume"
    break
  fi

  mkdir -p "${d}"
  echo "================================================================"
  echo "=== MIFlu L=${L} seed=${S}  start $(date +%H:%M:%S)  elapsed=$(elapsed)s"
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
    --export-dir "${d}" \
    --ckpt-dir   "${OUT}/ckpt_L${L}_s${S}"
  rc=$?

  src="${d}/predictions_miflu_L${L}_paper_protocol.csv"
  if [ ${rc} -eq 0 ] && [ -f "${src}" ]; then
    mv "${src}" "${final}"
    rows=$(( $(wc -l < "${final}") - 1 ))
    echo "[ok] L=${L} s=${S}: ${rows} rows -> ${final}"
  else
    echo "[FAIL] L=${L} s=${S}: rc=${rc}, export present=$([ -f "${src}" ] && echo yes || echo no)"
  fi

  echo "[rec] checkpoint selection:"
  grep -h "\[CKPT\]" "${d}"/training_miflu_log_*.txt 2>/dev/null | tail -1
  echo "[rec] test metrics:"
  grep -h "DONE: test_mse" "${d}"/training_miflu_log_*.txt 2>/dev/null | tail -1
  echo "=== MIFlu L=${L} seed=${S}  end $(date +%H:%M:%S)  elapsed=$(elapsed)s"
done

echo "[driver] DONE $(date -Is) elapsed=$(elapsed)s"
echo "[driver] CSVs present:"
ls -1 "${OUT}"/L*_s4[234]/predictions_miflu_L*_s*_paper_protocol.csv 2>/dev/null
