#!/bin/bash -l
#SBATCH --job-name=miflu_chain2
#SBATCH --partition=tiny
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=12:00:00
#SBATCH --output=slurm-miflu-chain2-%j.out
#
# External chain driver v2 for the MIFlu export.
#
# WHY v2 (measured 2026-11-01, 20:11-20:46):
#   * `stingy` generations 719222/719354/719377/719393/719399 were all PREEMPTED,
#     at elapsed 36:55 / 04:33 / 01:01 / 01:30 / 17:39. With 3 workers an epoch
#     takes ~80 s, so a 20-epoch retrain needs ~27 min and can never finish
#     inside those windows (719399's workers died at epoch 13/20).
#   * `train_miflu.py` keeps `best_state` in RAM and calls `torch.save` only
#     AFTER the epoch loop (lines 370-385 vs 399/429), so a killed retrain loses
#     everything - there is no mid-cell resume to exploit.
#   * With ONE worker an epoch takes ~24 s, so a cell takes ~8 min and DOES fit.
#   * `gpu_a100` was probed (job 719459, node gpu-a100-07): measured
#     `NVIDIA A100-SXM4-80GB`, cap (8,0), 79.2 GiB - the SAME hardware as the 204
#     benchmark cells - and a job starts in ~40 s. It also allows 4 submissions,
#     so the controller's in-job successor registration finally works there.
# So: submit `miflu_a100_controller_v3.sh` (1 worker) on `gpu_a100`, 10 h wall.
set -uo pipefail
module unload default 2>/dev/null
module load old_modules 2>/dev/null

CODE=/gpfs1/home/sychan552/stage5_a2_durable/code
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
OUT=/gpfs1/home/sychan552/stage5_a2_durable/author_runs
ADMIN="${CODE}/miflu_a100_chain.log"
MAX_SUBMITS=${MIFLU_MAX_SUBMITS:-14}
MAX_SECONDS=${MIFLU_MAX_SECONDS:-42000}
PART=${MIFLU_PART:-gpu_a100}
WALL=${MIFLU_WALL:-10:00:00}
cd "${CODE}" || exit 1

say() { echo "[$(date '+%F %T')] chain2 job=${SLURM_JOB_ID:-?} $*" | tee -a "${ADMIN}"; }
say "CHAIN DRIVER v2 START host=$(hostname) partition=${PART} wall=${WALL} max_submits=${MAX_SUBMITS}"

n=0
t0=$(date +%s)
while :; do
  now=$(date +%s)
  if [ $((now - t0)) -gt "${MAX_SECONDS}" ]; then say "chain time cap reached"; exit 0; fi
  if [ -f "${OUT}/.MIFLU_HALT" ]; then say "HALT marker present - stopping chain"; exit 0; fi

  nver=$("${PY}" miflu_controller_v2.py --count 2>/dev/null | tail -1)
  if [ "${nver:-0}" -ge 40 ]; then
    say "ALL 40 CELLS VERIFIED - chain complete (${nver}/40)"
    exit 0
  fi

  q=$(squeue -u "${USER}" -h -o '%j %T' 2>/dev/null | awk '$1=="miflu_a100"{print $1" "$2}')
  if [ -n "${q}" ]; then
    say "waiting: miflu_a100 ${q} (verified ${nver}/40)"
    sleep 60
    continue
  fi

  if [ "${n}" -ge "${MAX_SUBMITS}" ]; then
    say "MAX_SUBMITS=${MAX_SUBMITS} reached with ${nver}/40 verified - stopping"
    exit 0
  fi

  out=$(sbatch --partition="${PART}" --time="${WALL}" --export=ALL,MIFLU_WORKERS=1 \
               --chdir="${CODE}" "${CODE}/miflu_a100_controller_v3.sh" 2>&1)
  n=$((n + 1))
  sid=$(printf '%s\n' "${out}" | sed -n 's/^Submitted batch job \([0-9][0-9]*\).*/\1/p')
  if [ -n "${sid}" ]; then
    say "submitted generation #${n}: job_id=${sid} partition=${PART} wall=${WALL} (verified ${nver}/40)"
  else
    say "submission #${n} FAILED: ${out}"
    sleep 120
  fi
  sleep 45
done
