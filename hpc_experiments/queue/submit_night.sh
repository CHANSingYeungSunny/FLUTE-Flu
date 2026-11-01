#!/bin/bash
# submit_night.sh (queue v2) -- replace the whole chain with the hardened one.
#
# WHY EVERY OLD JOB MUST DIE (measured, not cosmetic)
# ---------------------------------------------------
# `sbatch` SPOOLS THE SCRIPT AT SUBMISSION. Every job already queued carries the
# OLD code: a v1 controller parses the v2 11-column queue with a 10-column reader
# and misreads it SILENTLY (state lands in the wrong field -> zero TODO -> it
# exits thinking the night is over). The running watchdog 719844 has exactly that
# bug against the 11-column file. So: cancel first, submit second, and never
# assume a queued job is running the code on disk.
#
# WHAT IS SUBMITTED
# -----------------
#   A  gpu_a100  12h  stripe 1   primary engine (A100, rule 13)
#   B  stingy    12h  stripe 0   second lane, disjoint stripe, preemptible
#   C  tiny      5d   CPU only   downloads + revision pin + hidden-state smoke
#   D  tiny      5d              watcher: restarts a lane only if it VANISHES
#
# WALL CLOCKS ARE A SCHEDULING LEVER, NOT A TARGET
# -----------------------------------------------
# Measured 2026-11-01 on this cluster: gpu_a100 with 5d -> StartTime
# 2026-11-02T22:05, with 12h -> 2026-11-02T02:50. A LONGER wall can start LATER,
# so "the partition maximum" is the wrong default when the night is the deadline.
# stingy's MaxTime is UNLIMITED (scontrol show partition stingy), and stingy is
# PreemptMode=CANCEL, so its real limit is preemption, not the wall; the
# controller self-requeues at the wall guard either way.
#
# USAGE  (on the cluster)
#   bash submit_night.sh                 # cancel old chain, submit A B C D
#   bash submit_night.sh --dry-run       # print what would be submitted
#   OLD_JOBS="1 2 3" bash submit_night.sh
set -uo pipefail

QDIR=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
cd "${QDIR}" || exit 1
CTRL=${QDIR}/master_controller.sh
CPUW=${QDIR}/cpu_worker.sh
WD=${QDIR}/watchdog.sh

#: the old chain (v1 code) plus the v1 watchdog that misreads the 11-column queue
OLD_JOBS=${OLD_JOBS:-"719833 719835 719836 719837 719844"}
#: nodes that must never be used tonight (dead CUDA context, DOWN+DRAIN)
EXCLUDE=${EXCLUDE:-gpu-a100-05,gpu-a100-09}
WALL_A=${WALL_A:-12:00:00};      SECS_A=${SECS_A:-43200}
WALL_B=${WALL_B:-12:00:00};      SECS_B=${SECS_B:-43200}
WALL_C=${WALL_C:-5-00:00:00};    SECS_C=${SECS_C:-432000}
WALL_D=${WALL_D:-5-00:00:00};    SECS_D=${SECS_D:-432000}
DRY=0
[ "${1:-}" = "--dry-run" ] && DRY=1

state_of() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^JobState=//p'; }
start_of() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^StartTime=//p'; }
wall_of()  { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^TimeLimit=//p'; }
part_of()  { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n 's/^Partition=//p'; }
show()     { printf '  job %-8s %s\n' "$1" "$(scontrol show job "$1" 2>/dev/null | tr ' ' '\n' \
               | grep -E '^(JobName|JobState|Partition|TimeLimit|StartTime|Reason|ExcNodeList|ReqTRES)=' | tr '\n' ' ')"; }

echo "=== 1. cancel the superseded chain (v1 code, spooled at submission) ==="
echo "  cancel: ${OLD_JOBS}"
if [ "${DRY}" = "0" ]; then
  scancel ${OLD_JOBS} 2>&1
  sleep 6
  for j in ${OLD_JOBS}; do
    st=$(state_of "$j")
    printf '  %-8s now=%-10s %s\n' "$j" "${st:-gone}" \
      "$(if [ "${st}" = "RUNNING" ] || [ "${st}" = "PENDING" ]; then echo 'STILL ALIVE - will retry cancel'; fi)"
    case "${st}" in RUNNING|PENDING|CONFIGURING) scancel "$j" 2>&1; sleep 2 ;; esac
  done
fi
echo

# archive the old runner map so a stale id cannot be resurrected by the watchdog
STAMP=$(date '+%Y%m%dT%H%M%S')
for f in runner_s0.job runner_s1.job runner_scpu.job; do
  [ -f "${f}" ] && cp -p "${f}" "${f}.v1.${STAMP}.bak"
done
: > runner_s0.job
: > runner_s1.job
: > runner_scpu.job
rm -f runner_s0.done runner_s1.done runner_scpu.done runner_s*.halted COMPLETE CHAIN_DEAD
rm -f runner_s0.idle runner_s1.idle runner_scpu.idle
#: a fresh chain owns a fresh exclusion file (the dead nodes are in EXCLUDE anyway)
: > exclude_nodes.txt

submit() {   # echo the job id, or "" on failure
  local out id
  out=$(sbatch --parsable "$@" 2>&1)
  id=${out%%;*}
  case "${id}" in
    ''|*[!0-9]*) echo "" ; return 1 ;;
  esac
  if scontrol show job "${id}" > /dev/null 2>&1; then echo "${id}"; return 0; fi
  echo ""; return 1
}

echo "=== 2. submit the four lanes ==="
if [ "${DRY}" = "0" ]; then
  A=$(submit --partition=gpu_a100 --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
        --time="${WALL_A}" --requeue --exclude="${EXCLUDE}" \
        --output="${QDIR}/slurm-A-%j.out" \
        --export="ALL,QUEUE_STRIPE=1,QUEUE_PARTITION=gpu_a100,QUEUE_WALL_SECONDS=${SECS_A}" \
        "${CTRL}") || true
  echo "  A(stripe1 gpu_a100 ${WALL_A}) = ${A:-SUBMIT FAILED}"

  B=$(submit --partition=stingy --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
        --time="${WALL_B}" --requeue --exclude=gpu-a100-05 \
        --output="${QDIR}/slurm-B-%j.out" \
        --export="ALL,QUEUE_STRIPE=0,QUEUE_PARTITION=stingy,QUEUE_WALL_SECONDS=${SECS_B}" \
        "${CTRL}") || true
  echo "  B(stripe0 stingy   ${WALL_B}) = ${B:-SUBMIT FAILED}"

  C=$(submit --partition=tiny --cpus-per-task=8 --mem=8G \
        --time="${WALL_C}" --requeue \
        --output="${QDIR}/slurm-C-%j.out" "${CPUW}") || true
  echo "  C(cpu tiny         ${WALL_C}) = ${C:-SUBMIT FAILED}"

  D=$(submit --partition=tiny --cpus-per-task=2 --mem=2G \
        --time="${WALL_D}" --requeue \
        --output="${QDIR}/slurm-D-%j.out" \
        --export="ALL,QUEUE_WD_MAX_SUBMITS=30,QUEUE_WD_MAX_SECONDS=432000" \
        "${WD}") || true
  echo "  D(watchdog tiny    ${WALL_D}) = ${D:-SUBMIT FAILED}"

  [ -n "${A}" ] && printf '%s\n' "${A}" > runner_s1.job
  [ -n "${B}" ] && printf '%s\n' "${B}" > runner_s0.job
  [ -n "${C}" ] && printf '%s\n' "${C}" > runner_scpu.job
  [ -n "${D}" ] && printf '%s\n' "${D}" > watchdog.job
else
  echo "  (dry-run: nothing submitted)"
fi
echo

echo "=== 3. record: partition / wall / StartTime / state ==="
for pair in "A:${A:-}" "B:${B:-}" "C:${C:-}" "D:${D:-}"; do
  name=${pair%%:*}; id=${pair#*:}
  [ -n "${id}" ] || { printf '  %-2s NOT SUBMITTED\n' "${name}"; continue; }
  printf '  %-2s id=%-8s part=%-9s wall=%-11s start=%-20s state=%s\n' \
    "${name}" "${id}" "$(part_of "${id}")" "$(wall_of "${id}")" \
    "$(start_of "${id}")" "$(state_of "${id}")"
done
echo

echo "=== 4. stripe split (cksum(task_id) % 2; F1-F5 are lane-agnostic) ==="
for pri in P0 P1 P2 P3 P4; do
  n0=0; n1=0; nf=0
  while IFS=$'\t' read -r tid kind model L seed p envr st att lj note; do
    [ "${tid}" = "task_id" ] && continue
    [ "${p}" = "${pri}" ] || continue
    case " f1_import_miflu f2_miflu_oracle f3_analysis_chain f4_verify f5_llm_import finalise " in
      *" ${kind} "*) nf=$((nf+1)); continue ;;
    esac
    s=$(printf '%s' "${tid}" | cksum | awk '{print $1 % 2}')
    if [ "${s}" = "0" ]; then n0=$((n0+1)); else n1=$((n1+1)); fi
  done < master_queue.tsv
  printf '  %-3s stripe0(stingy)=%-4s stripe1(gpu_a100)=%-4s any-lane(finalise)=%s\n' \
         "${pri}" "${n0}" "${n1}" "${nf}"
done
echo
echo "=== 5. F1-F5 rows (finalisation) ==="
awk -F'\t' 'NR>1 && $6=="P4" {printf "  %-24s kind=%-20s env=%-4s state=%s\n", $1,$2,$7,$8}' master_queue.tsv
echo
echo "=== 6. queue state summary ==="
awk -F'\t' 'NR>1{c[$6" "$8]++} END{for(k in c) printf "  %-26s %d\n", k, c[k]}' master_queue.tsv | sort
echo
echo "=== 7. live jobs (user-scoped; scontrol/sacct is authoritative here) ==="
squeue -u sychan552 -o '  %.8i %.10P %.14j %.2t %.11M %.21S %.12r' 2>&1
echo
echo "=== 8. next step ==="
echo "  tail -f ${QDIR}/queue_events.log"
echo "  bash ${CTRL} --dry-run    # stripe partition assertions on the live queue"
