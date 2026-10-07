#!/bin/bash
#SBATCH --job-name=r1b_pilot
#SBATCH --partition=stingy
#SBATCH --nodes=1
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/logs/r1b_pilot_%A_%a.out
#SBATCH --error=/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/logs/r1b_pilot_%A_%a.err
#
# ===========================================================================
# R1-B CORE NATIONAL-ILLNESS PAPER-REPRODUCTION PILOT
# AUTHORIZED: 0.30 GPU-hours, new and independent.
#             The sealed F1 0.35 and the older 0.05639 are NOT used.
# ===========================================================================
# Array index = horizon:  0 -> L=24, 1 -> L=36, 2 -> L=48, 3 -> L=60
# ONE element per submission (stingy MaxSubmit=1 / MaxJobsPU=1).
#
# PAPER CONFIGURATION (required): T=104, epochs=20, batch=16, lr=0.0005,
#   seven-channel target, functional text pathway, PEFT enabled, LoRA r=4,
#   c_attn modules, effective freezing, validation-based selection,
#   Test evaluated once, predictions+targets saved, independent scoring.
#
# DECLARED R1-B CONTRACT for the UNRECOVERED items (disclosed, not tunable):
#   pooling axes = mean over (origins x leads x 7 variables), z-space
#   optimizer    = Adam           (released default; the paper states none)
#   scheduler    = none           (the released default applies a hard-coded 0.9 decay)
#   selection    = best VALIDATION mse_all
#   seed identity = repetition index -> torch seed 1000+rep
#
# STORAGE: locked-checkpoint path only; atomic writes; preflight before each fit;
#   postflight after each fit; everything under $HOME; scratch never referenced.
#
# NAMESPACE: corrected results go to r1_v2_20261007/. The failed pilot wrote to
# r1/ (jobs 607969_0, 607984_1) and those outputs are INVALID - the dataset-origin
# formula produced short final Test targets. They are retained only as engineering
# evidence and must never be mistaken for corrected results.
# ===========================================================================
set -uo pipefail

PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
ROOT=/gpfs1/home/sychan552/official_repo_reproduction_20261006
R1=${ROOT}/r1_v2_20261007     # VERSIONED: jobs 607969/607984 wrote under r1/ and are INVALID
R1B=${ROOT}/r0_r5_cpu_stage_20261006/r1b
STORAGE=${ROOT}/r0_r5_cpu_stage_20261006/storage
COMPAT=${ROOT}/hpc_compat
A0=/scratch/sychan552/a0_replay                    # READ-ONLY
DATA_SHA=2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5

mkdir -p "${R1}"/{logs,ckpt,preds,manifests,scoring}
IDX=${SLURM_ARRAY_TASK_ID}
HOR=(24 36 48 60); L=${HOR[$IDX]}
TAG="r1b__L${L}__rep0"
OUTD="${R1}/preds/${TAG}"
mkdir -p "${OUTD}"

if [[ "$(hostname)" == hpclogin* ]]; then echo "[pilot] REFUSING login node"; exit 3; fi
echo "[pilot] job=${SLURM_JOB_ID}_${IDX} host=$(hostname) L=${L} start=$(date -u +%FT%TZ)"
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | sed 's/^/[pilot] gpu: /'

# ── gate 7/8: output is under $HOME, scratch never written ──────────────────
case "${OUTD}" in /gpfs1/home/*) ;; *) echo "[pilot] FATAL: output not under \$HOME"; exit 5;; esac

# ── storage PREFLIGHT ───────────────────────────────────────────────────────
export PYTHONPATH="${STORAGE}:${COMPAT}:${A0}:${R1B}"
export HF_HOME=/home/sychan552/.cache/huggingface
export TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1

$PY - <<PYEOF || { echo "[pilot] STORAGE PREFLIGHT REFUSED - not fitting"; exit 6; }
import sys, json
sys.path.insert(0, "${STORAGE}")
import storage_guard as SG
proj = SG.project_output_bytes(1, [${L}], trainer="locked")
# use the USER-QUOTA-aware preflight on the HPC (filesystem free space is not
# the binding constraint on GPFS)
r = SG.quota_preflight("${OUTD}", proj)
print("[pilot] preflight:", json.dumps(r, default=str))
print(f"[pilot] projected for this fit: {proj['projected_total_mib']} MiB "
      f"(checkpoint {proj['checkpoint_bytes_each']:,} B, locked path)")
sys.exit(0 if r["ok"] else 1)
PYEOF

# ── data identity ───────────────────────────────────────────────────────────
GOT=$(sha256sum "${A0}/dataset/illness/national_illness.csv" | cut -d' ' -f1)
[[ "${GOT}" != "${DATA_SHA}" ]] && { echo "[pilot] FATAL dataset sha ${GOT}"; exit 4; }

{
  echo "track=R1-B PAPER-REPRODUCTION PILOT (1 repetition)"
  echo "slurm_job=${SLURM_JOB_ID}_${IDX} horizon=${L} repetition=0"
  echo "dataset_sha256=${GOT}"
  echo "config: T=104 epochs=20 batch=16 lr=0.0005 PEFT=1 lora_r=4 c_attn freeze=1"
  echo "target: seven channels, z-space"
  echo "text pathway: functional (prefixed; patches read after the text) = B-2"
  echo "selection: best VALIDATION mse_all (B-5); Test evaluated once afterwards"
  echo "checkpoint: LOCKED path (trainable tensors + frozen-key sidecar), atomic write"
  echo "declared_unrecovered: pooling_axes optimizer scheduler selection_details seed_identity"
} | tee "${OUTD}/provenance.txt"

# ── the fit ─────────────────────────────────────────────────────────────────
cd "${A0}" || exit 2
$PY -u "${R1B}/r1b_train.py" \
    --code-root "${A0}" \
    --data "${A0}/dataset/illness/national_illness.csv" \
    --horizon "${L}" --repetition 0 --device cuda \
    --epochs 20 --lr 5e-4 --batch 16 --peft 1 \
    --out "${OUTD}" 2>&1 | tee "${OUTD}/train.log"
rc=${PIPESTATUS[0]}
echo "[pilot] fit rc=${rc} end=$(date -u +%FT%TZ)"

# ── storage POSTFLIGHT ──────────────────────────────────────────────────────
$PY - <<PYEOF || echo "[pilot] postflight reported residue"
import sys, json
sys.path.insert(0, "${STORAGE}")
import storage_guard as SG
print("[pilot] postflight:", json.dumps(SG.postflight("${OUTD}"), default=str))
PYEOF

# ── ledger: job id, elapsed, GPU count, GPU-hours ───────────────────────────
el=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
ng=$(sacct -j "${SLURM_JOB_ID}" -X --noheader -o AllocTRES%80 2>/dev/null \
     | grep -o 'gres/gpu:a100=[0-9]*' | head -1 | cut -d= -f2)
printf 'R1B_PILOT\t%s_%s\tL%s\t%s\tgpu=%s\trc=%s\n' \
  "${SLURM_JOB_ID}" "${IDX}" "${L}" "${el:-unknown}" "${ng:-0}" "${rc}" \
  >> "${R1}/manifests/GPU_LEDGER_R1B.tsv"
echo "[pilot] ledger row appended: elapsed=${el} gpu=${ng}"
ls -la "${OUTD}" | sed 's/^/[pilot] /'
exit ${rc}