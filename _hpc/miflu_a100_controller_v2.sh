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
# MIFlu 7-channel export -- resume to 40/40 cells (4 horizons x 10 reps, seeds 2021-2030).
#
# WHY THIS EXISTS (2026-11-01)
# ---------------------------
# Controller 719030 did NOT stop on its 3 h 05 m wall-clock guard and did NOT fail
# an sbatch: `sacct` shows `PREEMPTED`, exit code 0:15 (SIGTERM), 00:13:00 elapsed,
# with `slurmstepd-gpu-a100-04: error: *** JOB 719030 ... CANCELLED ... DUE TO
# PREEMPTION ***` at epoch 2/20 of L=36 seed 2025. `stingy` runs with
# `PreemptMode=CANCEL` and PriorityTier=1, so any higher-tier job (`special_cs`,
# `high`) that lands on gpu-a100-04 kills it outright -- Slurm does not requeue a
# CANCEL-preempted job, so nothing resumed and the export sat at 12/40.
# Two silent-corruption defects in that controller are fixed in
# `export_miflu_all7.find_ckpt` and re-checked per cell by the python driver:
#   * seed 2021 was picked from `ckpt_L{L}_s2021/best_miflu_L{L}.pth`, which is the
#     10-rep run's best-val rep (L24/36 -> seed 2024, L48 -> 2021, L60 -> 2025);
#   * the cell list omitted 36:2024 / 48:2021 / 60:2025 and included 60:2021,
#     which would have exported L60's seed-2025 weights as seed 2021.
#
# HOW IT SURVIVES PREEMPTION
# --------------------------
#   1. Before doing any work, the job submits its OWN SUCCESSOR with
#      `--dependency=afterany:$SLURM_JOB_ID` and checks that sbatch returned a
#      numeric job id AND that the scheduler can see it. The successor starts
#      whenever this job ends for ANY reason (preemption included) and its first
#      action is to recount the verified cells, so the chain stops by itself.
#   2. `RECORD`s: a cell is complete only when its four rule-11 artefacts exist,
#      the manifest's checkpoint sha256 matches, and the npz reproduces the
#      per-seed oracle to <= 1e-5 on the first (W//16)*16 test windows. Verified
#      cells are marked under author_runs/.miflu_verify/ so they are never redone
#      and never re-read.
#   3. A SIGTERM trap re-registers the successor if the pre-registration failed.
#   4. The wall budget (3 h 05 m inside the 4 h limit) stops claiming new cells.
#
# HARDWARE: A100 only (AGENTS.md rules 12-13). Asserted by API call, recorded in
# every manifest; a non-A100 would exit non-zero before any work.
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
WORKERS=${MIFLU_WORKERS:-3}
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

# ---- successor registration (verified, retried, loud on failure) ------------
REG=failed
register_successor() {
  if [ "${GEN}" -ge "${MAXGEN}" ]; then
    say "MAXGEN=${MAXGEN} reached - not requeueing"
    return 2
  fi
  local out sid try
  for try in 1 2 3; do
    out=$(sbatch --dependency="afterany:${SLURM_JOB_ID}" \
                 "${CODE}/miflu_a100_controller_v2.sh" $((GEN + 1)) 2>&1)
    sid=$(printf '%s\n' "${out}" | sed -n 's/^Submitted batch job \([0-9][0-9]*\).*/\1/p')
    if [ -n "${sid}" ]; then
      if scontrol show job "${sid}" >/dev/null 2>&1; then
        say "SUCCESSOR REGISTERED job_id=${sid} gen=$((GEN + 1)) dependency=afterany:${SLURM_JOB_ID}"
        REG=ok
        return 0
      fi
      say "sbatch returned job_id=${sid} but scontrol cannot see it - treating as FAILED"
    else
      say "sbatch FAILED (try ${try}): ${out}"
    fi
    sleep 10
  done
  say "SUCCESSOR REGISTRATION FAILED after 3 attempts - this generation cannot auto-resume"
  return 1
}

if [ "${NVER:-0}" -lt 40 ]; then
  register_successor || true
else
  say "all 40 cells already verified - no successor needed"
  REG=not-needed
fi

# ---- work loop --------------------------------------------------------------
trap 'say "SIGTERM/SIGINT received (preemption or wall-kill)"; if [ "${REG}" = "failed" ]; then register_successor || true; fi; exit 143' TERM INT

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
  say "work remains; the pending successor will continue"
  exit 0
fi
say "WORK REMAINS AND NO SUCCESSOR IS REGISTERED - failing loudly instead of dying silently"
exit 9
