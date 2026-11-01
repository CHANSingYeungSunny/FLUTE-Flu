#!/bin/bash -l
#SBATCH --job-name=miflu_a100
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=04:00:00
#SBATCH --output=slurm-miflu-a100-%j.out
#SBATCH --requeue
#
# MIFlu 7-channel export -- resume to 40/40 cells (4 horizons x 10 reps, 2021-2030).
#
# WHY THIS EXISTS (2026-11-01)
# ---------------------------
# Controller 719030 did NOT stop on its 3 h 05 m wall-clock guard and did NOT fail
# an sbatch: `sacct` shows `PREEMPTED`, exit 0:15 (SIGTERM), 00:13:00 elapsed,
# `slurmstepd: *** JOB 719030 ... CANCELLED ... DUE TO PREEMPTION ***` at epoch
# 2/20 of L=36 seed 2025. `stingy` is `PreemptMode=CANCEL`, PriorityTier=1, so a
# higher-tier job (`special_cs`/`high`) landing on the node kills a stingy job
# outright and Slurm does not requeue it.
#
# At the same time, `partition-stingy` has MaxSubmitJobsPerUser=1 /
# MaxJobsPerUser=1, so a RUNNING stingy job **cannot** submit any successor:
# measured from job 719222 at 19:35:10-19:35:40 --
#   sbatch: error: QOSMaxSubmitJobPerUserLimit
#   sbatch: error: Batch job submission failed: Job violates accounting/QOS policy
# That is the structural reason a stingy job can never self-requeue by sbatch.
# The mechanisms used here are therefore:
#   * `scontrol requeue $SLURM_JOB_ID` when the wall budget is reached -- this
#     re-queues the SAME job id and creates no new submission, so the QOS limit
#     cannot reject it;
#   * an external CPU chain driver (`miflu_chain_driver.sh`, partition `tiny`,
#     a different QOS) that resubmits after a PREEMPTION, which nothing inside a
#     CANCEL-preempted job can survive;
#   * a verified single sbatch attempt at start-up, kept as evidence and as a
#     fallback if the account's QOS is ever relaxed.
#
# CORRECTNESS (both defects of 719030 are fixed and re-checked per cell)
# ---------------------------------------------------------------------
#   * `export_miflu_all7.find_ckpt` used to prefer
#     `ckpt_L{L}_s{seed}/best_miflu_L{L}.pth`, which for seed 2021 is the 10-rep
#     run's best-val rep (L24/36 -> 2024, L48 -> 2021, L60 -> 2025). Seed 2021
#     was therefore exported from seed-2024 weights (L24 failed its legacy
#     cross-check with dPRED=1.993; L36 seed 2021 was silently wrong on disk).
#   * the old CELLS list omitted 36:2024 / 48:2021 / 60:2025 and included
#     60:2021, which would have exported L60's seed-2025 weights as seed 2021.
# `miflu_controller_v2.py` enumerates all 4x10 cells and accepts a cell only
# when its npz reproduces the per-seed oracle to <= 1e-5 on the first
# (W//16)*16 test windows and its manifest carries the sha256 of the checkpoint
# the trust order picks. Verified cells are marked in author_runs/.miflu_verify/.
#
# HARDWARE: A100 only (rules 12-13), asserted by API call before any work.
set -uo pipefail
module unload default 2>/dev/null
module load old_modules 2>/dev/null

CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
ADMIN="${CODE}/miflu_a100_chain.log"
GEN=${1:-1}
MAXGEN=${MIFLU_MAXGEN:-12}
BUDGET=${MIFLU_BUDGET:-11100}      # 3 h 05 m inside the 4 h wall
WORKERS=${MIFLU_WORKERS:-1}
cd "${CODE}" || exit 1

say() { echo "[$(date '+%F %T')] gen=${GEN} job=${SLURM_JOB_ID:-?} $*" | tee -a "${ADMIN}"; }

say "START host=$(hostname) node=${SLURM_NODELIST:-?} part=${SLURM_JOB_PARTITION:-?} gen=${GEN}/${MAXGEN}"

if [ -f "${OUT}/.MIFLU_HALT" ]; then
  say "HALT marker present ($(cat "${OUT}/.MIFLU_HALT" 2>/dev/null)) - refusing to work"
  exit 7
fi

# ---- hardware assertion: A100 only -----------------------------------------
"${PY}" - <<'PYEOF'
import sys
import torch
if not torch.cuda.is_available():
    print("[a100] FATAL: no CUDA device"); sys.exit(3)
name = torch.cuda.get_device_name(0)
cap = torch.cuda.get_device_capability(0)
vram = torch.cuda.get_device_properties(0).total_memory / 2**30
print(f"[a100] MEASURED gpu={name} capability={cap} vram={vram:.1f}GiB")
if "A100" not in name:
    print(f"[a100] FATAL: expected an A100, got {name!r}; a non-A100 cell would "
          f"confound the benchmark (rules 12-13). Refusing to work.")
    sys.exit(4)
PYEOF
if [ $? -ne 0 ]; then say "HARDWARE ASSERTION FAILED - aborting"; exit 1; fi

NVER=$("${PY}" miflu_controller_v2.py --count 2>/dev/null | tail -1)
say "verified cells before this generation: ${NVER:-?}/40"

# ---- in-job successor attempt (kept as evidence; cannot succeed under QOS=1) --
REG=failed
if [ "${NVER:-0}" -lt 40 ]; then
  if [ "${GEN}" -ge "${MAXGEN}" ]; then
    say "MAXGEN=${MAXGEN} reached - not requeueing"
  else
    out=$(sbatch --dependency="afterany:${SLURM_JOB_ID}" \
                 "${CODE}/miflu_a100_controller_v3.sh" $((GEN + 1)) 2>&1)
    sid=$(printf '%s\n' "${out}" | sed -n 's/^Submitted batch job \([0-9][0-9]*\).*/\1/p')
    if [ -n "${sid}" ] && scontrol show job "${sid}" >/dev/null 2>&1; then
      say "SUCCESSOR REGISTERED job_id=${sid} dependency=afterany:${SLURM_JOB_ID}"
      REG=ok
    else
      say "in-job successor NOT registered: ${out:-no job id returned}"
    fi
  fi
else
  say "all 40 cells already verified - no successor needed"
  REG=not-needed
fi

# requeue our OWN job id: creates no new submission, so QOS=1 cannot reject it
try_requeue() {
  local before after rc
  before=$(scontrol show job "${SLURM_JOB_ID}" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p')
  scontrol requeue "${SLURM_JOB_ID}" >>"${ADMIN}" 2>&1
  rc=$?
  sleep 3
  after=$(scontrol show job "${SLURM_JOB_ID}" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p')
  if [ "${rc}" -eq 0 ] && [ "${after}" = "PENDING" ]; then
    say "SELF-REQUEUE ok: job ${SLURM_JOB_ID} state ${before:-?} -> PENDING"
    return 0
  fi
  say "SELF-REQUEUE FAILED rc=${rc}: state ${before:-?} -> ${after:-gone}"
  return 1
}

# ---- work loop --------------------------------------------------------------
trap 'say "SIGTERM/SIGINT received (preemption or wall-kill)"; try_requeue || true; exit 143' TERM INT

"${PY}" -u miflu_controller_v2.py \
  --workers "${WORKERS}" --budget-seconds "${BUDGET}" \
  --admin-log "${ADMIN}" --gen "${GEN}"
RC=$?
say "controller rc=${RC}"

NEND=$("${PY}" miflu_controller_v2.py --count 2>/dev/null | tail -1)
say "verified cells after this generation: ${NEND:-?}/40"

if [ "${NEND:-0}" -ge 40 ]; then
  say "ALL 40 CELLS VERIFIED - chain complete"
  exit 0
fi
if [ "${RC}" -eq 6 ]; then
  say "ORACLE HALT - refusing to accept the output; see ${OUT}/.MIFLU_HALT"
  exit 6
fi
if [ "${REG}" = "ok" ]; then
  say "work remains; the registered successor will continue"
  exit 0
fi
if [ "${RC}" -eq 2 ] || [ "${RC}" -eq 4 ]; then
  say "work remains (controller rc=${RC}) - self-requeueing the same job id"
  try_requeue && exit 0
fi
say "WORK REMAINS AND NO IN-JOB RESUME PATH - relying on the external chain driver; failing loudly"
exit 9
