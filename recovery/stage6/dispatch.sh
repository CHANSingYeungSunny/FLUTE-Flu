#!/bin/bash
# Stage 6 sequential dispatcher for the eight-model comparison.
# NOT RUN until an explicit additional compute authorization is granted.
#
#   bash recovery/stage6/dispatch.sh --run
#
# Order is deliberate: the five cheap backbones first so that a budget stop
# leaves a usable partial ranking, Qwen last because it alone is ~57% of the
# measured cost. Within each backbone, L=24..60.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1
LOG=results/stage6/logs/dispatch_log.txt
LOCK=results/stage6/logs/EXEC_LOCK
mkdir -p results/stage6/logs

if [ "${1:-}" != "--run" ]; then
  echo "dispatch.sh is armed but NOT running."
  echo "Planned order: dlinear, patchtst, itransformer, calf_llm, timecma_llm, qwen_time_llm"
  echo "x L in {24,36,48,60} = 24 jobs, 72 fits."
  echo "Authorized cap for this round (A0 + eight models): 2.3 GPU-h"
  echo "Submit with:  bash recovery/stage6/dispatch.sh --run"
  exit 0
fi

if [ -e "$LOCK" ] && ! grep -q "dispatcher_stage6" "$LOCK" 2>/dev/null; then
  echo "[s6] ABORT: lock $LOCK exists and is not owned by this script:" >&2
  cat "$LOCK" >&2; exit 9
fi
cat > "$LOCK" <<EOF
owner=dispatcher_stage6
pid=$$
host=$(hostname)
started_utc=$(date -u +%FT%TZ)
EOF

# ---- stop rule: refuse to start if the measured budget is already exhausted --
# The authorized cap for the whole 2026-09-26 round (A0 + eight models) is
# 2.3 GPU-h. A0 consumes part of it, so the dispatcher must count A0 jobs too,
# and must NOT charge unrelated jobs that happen to run under the same account.
# Only jobs whose name is in OUR_JOB_NAMES are charged to this authorization.
CAP_GPU_H=${CAP_GPU_H:-2.3}
OUR_JOB_NAMES="s6_task,s6_score,a0_gpu"
A0_CAP=${A0_CAP:-0.5}

_gpu_hours() {  # $1 = newline-separated "jobname|elapsed|alloctres" records
  /home/sychan552/.conda/envs/mlflu_hpc/bin/python -c '
import re, sys
tot = 0.0
for ln in sys.stdin:
    f = ln.rstrip("\n").split("|")
    if len(f) < 3: continue
    el, tres = f[1], f[2]
    d, _, t = el.partition("-") if "-" in el else ("0", "", el)
    p = (t.split(":") + ["0", "0", "0"])[:3]
    s = int(d)*86400 + int(p[0])*3600 + int(p[1])*60 + int(float(p[2]))
    m = re.search(r"gres/gpu[a-z0-9]*:(\d+)", tres) or re.search(r"gres/gpu=(\d+)", tres)
    tot += s * (int(m.group(1)) if m else 0)
print(f"{tot/3600:.4f}")'
}

_all_sacct() {
  sacct -u "$USER" -S 2026-09-26 -X --noheader \
        --format=JobID,JobName,State,Elapsed,AllocTRES%40,Submit -P 2>/dev/null
}

spent() {  # GPU-hours charged to THIS authorization so far
  _all_sacct | OURS="$OUR_JOB_NAMES" /home/sychan552/.conda/envs/mlflu_hpc/bin/python -c '
import os, sys
ours = set(os.environ["OURS"].split(","))
for ln in sys.stdin:
    f = ln.rstrip("\n").split("|")
    if len(f) < 6: continue
    if f[1] in ours:
        sys.stdout.write("|".join([f[1], f[3], f[4]]) + "\n")
' | _gpu_hours
}

spent_a0() {  # A0-only share, for the sub-budget report
  _all_sacct | /home/sychan552/.conda/envs/mlflu_hpc/bin/python -c '
import sys
for ln in sys.stdin:
    f = ln.rstrip("\n").split("|")
    if len(f) >= 6 and f[1] == "a0_gpu":
        sys.stdout.write("|".join([f[1], f[3], f[4]]) + "\n")
' | _gpu_hours
}

submit_one() {
  local BB="$1" L="$2" tries=0 out jid
  while : ; do
    tries=$((tries+1))
    out=$(sbatch --export=ALL,BACKBONE="$BB",L="$L" recovery/stage6/run_task.sh 2>&1)
    jid=$(printf '%s\n' "$out" | sed -n 's/.*Submitted batch job \([0-9][0-9]*\).*/\1/p' | head -1)
    if [ -n "$jid" ]; then printf '%s' "$jid"; return 0; fi
    if [ $((tries % 10)) -eq 1 ]; then
      echo "[s6] waiting to submit $BB L=$L (tries=$tries) at $(date -u +%FT%TZ)" >> "$LOG"
    fi
    if [ "$tries" -ge 360 ]; then printf ''; return 1; fi
    sleep 30
  done
}

wait_done() {
  local jid="$1" st
  while : ; do
    st=$(sacct -j "$jid" -X --noheader -o State 2>/dev/null | head -1 | awk '{print $1}')
    case "$st" in
      COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|BOOT_FAIL|DEADLINE|PREEMPTED)
        return 0 ;;
    esac
    sleep 15
  done
}

for BB in dlinear patchtst itransformer calf_llm timecma_llm qwen_time_llm; do
  for L in 24 36 48 60; do
    used=$(spent)
    over=$(/home/sychan552/.conda/envs/mlflu_hpc/bin/python -c "print(1 if $used >= $CAP_GPU_H else 0)")
    if [ "$over" = "1" ]; then
      echo "[s6] STOP RULE: charged $used GPU-h >= authorized cap $CAP_GPU_H; not submitting $BB L=$L" | tee -a "$LOG"
      echo "[s6] (A0 share so far: $(spent_a0) of its $A0_CAP sub-budget)" | tee -a "$LOG"
      echo "[s6] remaining matrix NOT run: see recovery/stage6/cost_and_matrix_zh.md" | tee -a "$LOG"
      rm -f "$LOCK"; exit 0
    fi
    jid=$(submit_one "$BB" "$L")
    if [ -z "$jid" ]; then
      echo "[s6] GAVE UP on $BB L=$L" | tee -a "$LOG"; continue
    fi
    echo "[s6] submitted $BB L=$L job=$jid charged=${used} at $(date -u +%FT%TZ)" | tee -a "$LOG"
    wait_done "$jid"
    st2=$(sacct -j "$jid" -X --noheader -o State 2>/dev/null | head -1 | awk '{print $1}')
    el=$(sacct -j "$jid" -X --noheader -o Elapsed 2>/dev/null | head -1 | tr -d ' ')
    echo "[s6] job=$jid $BB L=$L state=$st2 elapsed=$el charged=$(spent)" | tee -a "$LOG"
    case "$st2" in
      COMPLETED) ;;
      *) echo "[s6] WARNING: $BB L=$L ended $st2 — diagnose before any retry; "
                 "the same protocol must be reused (no seed/epoch/window changes)" | tee -a "$LOG" ;;
    esac
  done
done
echo "[s6] queue finished charged=$(spent) (A0 share $(spent_a0)) at $(date -u +%FT%TZ)" | tee -a "$LOG"
rm -f "$LOCK"
echo "[s6] lock released"
