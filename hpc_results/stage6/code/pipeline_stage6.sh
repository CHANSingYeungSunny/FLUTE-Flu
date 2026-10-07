#!/bin/bash
# Stage 6 master pipeline: A0 MODE=1 -> eight-model fits -> lock + score + recompute.
# QOS on `stingy` allows only 1 running + 1 pending job, so every stage is strictly
# serial. Authorized cap for the whole round (A0 + eight models): 2.3 GPU-hours,
# counted over job names s6_task, s6_score, a0_gpu only.
set -uo pipefail
cd /scratch/sychan552/a2_stage5 || exit 1
LOG=results/stage6/logs/pipeline_log.txt
CAP_GPU_H=${CAP_GPU_H:-2.3}
mkdir -p results/stage6/logs
# NOTE: `say` must write to stderr, not stdout. `submit_retry` and friends are
# invoked through command substitution, `jid=$(submit_retry ...)`, and a `tee` to
# stdout would land the log text in $jid. A multi-line $jid then silently broke
# `sacct -j`/`scancel`, leaving `wait_done` polling a job that can never resolve.
say() { echo "[pipe $(date -u +%FT%TZ)] $*" | tee -a "$LOG" >&2; }

spent() {
  # Pure-awk GPU-hour accounting. A python call here deadlocked the pipeline:
  # the conda interpreter blocks during start-up on this login node.
  sacct -u "$USER" -S 2026-09-26 -X --noheader \
        --format=JobID,JobName,State,Elapsed,AllocTRES%40 -P 2>/dev/null \
  | awk -F'|' '
      function secs(e,   n,a,p,d,t) {
        n = split(e, a, "-"); d = (n > 1) ? a[1] + 0 : 0
        t = (n > 1) ? a[2] : e
        split(t, p, ":")
        return d*86400 + p[1]*3600 + p[2]*60 + p[3]
      }
      $2 == "s6_task" || $2 == "s6_score" || $2 == "a0_gpu" {
        s = secs($4); g = 0
        if (match($5, /gres\/gpu[a-z0-9]*=[0-9]+/)) {
          v = substr($5, RSTART, RLENGTH); sub(/.*=/, "", v); g = v + 0
        }
        tot += s * g
      }
      END { printf "%.4f\n", tot/3600 }'
}

wait_done() {
  local jid st
  jid=$(printf '%s' "$1" | tr -cd '0-9')
  if [ -z "$jid" ]; then say "wait_done: no numeric jid in '$1' - giving up"; return 1; fi
  while : ; do
    st=$(timeout 60 sacct -j "$jid" -X --noheader -o State 2>/dev/null | head -1 | awk '{print $1}')
    case "$st" in
      COMPLETED|FAILED|CANCELLED|TIMEOUT|OUT_OF_MEMORY|NODE_FAIL|BOOT_FAIL|DEADLINE|PREEMPTED) return 0 ;;
    esac
    sleep 15
  done
}

slot_free() {   # 0 when no job of mine is queued or running
  # Count only real job ids. `squeue -o "%t"` also writes the
  # "Last update in N seconds ago" banner to stdout, which made a state-based
  # grep always report "busy" and the pipeline never submitted anything.
  #
  # `grep -c` exits 1 when it counts zero lines, and this script runs under
  # `set -o pipefail`, so a bare `$(... | grep -c ...)` aborts the subshell and
  # leaves the caller with no value - i.e. permanently "busy". `|| true` keeps
  # the count while neutralising that exit status.
  local n
  n=$( { timeout 20 squeue -u "$USER" -h -o "%i" 2>/dev/null || true; } | grep -cE '^[0-9]+' || true)
  [ "${n:-0}" -eq 0 ]
}

submit_retry() {   # usage: submit_retry KEY=VALUE [KEY=VALUE ...] /path/to/script.sh
                   #
                   # The trailing script path MUST be kept out of the --export
                   # token. Joining everything with commas produced
                   #   --export=ALL,BACKBONE=dlinear,L=48,recovery/.../run_task.sh
                   # which leaves sbatch with no script argument at all: it then
                   # reads the script from stdin (redirected to /dev/null),
                   # fails instantly, and the loop below spins forever logging a
                   # misleading "waiting for a free slot".
                   #
                   # QoS `partition-stingy` is MaxSubmitJobsPerUser=1 /
                   # MaxJobsPerUser=1, so a taken submit slot makes sbatch block
                   # inside the controller instead of erroring. Hence the
                   # pre-check plus the timeout backstop.
  local tries=0 out jid exp script
  script="${!#}"                       # last arg = script path
  exp=$(IFS=,; echo "${*:1:$#-1}")     # everything before it = KEY=VALUE pairs
  while : ; do
    tries=$((tries+1))
    if slot_free; then
      out=$(timeout 120 sbatch --export=ALL,"$exp" "$script" 2>&1)
      jid=$(printf '%s\n' "$out" | sed -n 's/.*Submitted batch job \([0-9][0-9]*\).*/\1/p' | head -1)
      if [ -n "$jid" ]; then printf '%s' "$jid"; return 0; fi
      say "submit rejected (exp=$exp): $(printf '%s' "$out" | tr '\n' ' ')"
    else
      [ $((tries % 15)) -eq 1 ] && say "queue busy, waiting (try $tries)"
    fi
    [ $tries -ge 2160 ] && { say "gave up submitting exp=$exp"; printf ''; return 1; }
    sleep 15
  done
}

over_cap() {   # 1 when the round has reached the authorised cap
  awk -v u="$(spent)" -v c="$CAP_GPU_H" 'BEGIN{print (u>=c)?1:0}'
}

# A bad --export used to pass unnoticed: slurm would start the job with an empty
# $L and the ledger would quietly record a wrong run. Check the first line the
# job actually printed, but poll instead of sleeping a fixed 20 s because a
# freshly started job has not necessarily flushed its .out header yet.
verify_submission() {   # $1 = jid, $2 = expected "BACKBONE=$BB L=$L"
  local jid="$1" want="$2" hdr="" i
  for i in $(seq 1 20); do
    hdr=$(head -1 "results/stage6/logs/task_${jid}.out" 2>/dev/null)
    case "$hdr" in
      *"$want"*) return 0 ;;
      *"BACKBONE="*|*"L="*) [ -n "$hdr" ] && { say "BAD SUBMISSION: got '$hdr', want '$want'; killing $jid"
                                        scancel "$jid" 2>/dev/null; return 1; } ;;
    esac
    sleep 5
  done
  say "WARNING: job $jid printed no recognisable header within 100 s"
  return 0
}

# ── stage 1: A0 ────────────────────────────────────────────────────────────
# A0 is idempotent-by-evidence: only run a mode if its stdout log is missing.
# Jobs 587091 (MODE=0) and 587068 (MODE=1) already produced both logs.
a0_need() { [ ! -s "/scratch/sychan552/a0_runs/logs/$1_stdout.txt" ]; }

for MODE in 0 1; do
  TAG=$([ "$MODE" = "1" ] && echo multimodal1 || echo default)
  if ! a0_need "$TAG"; then
    say "stage 1: A0 MODE=$MODE already has evidence ($TAG) - skipping"
    continue
  fi
  if [ "$(over_cap)" = "1" ]; then
    say "STOP RULE: charged $(spent) >= cap $CAP_GPU_H; skipping A0 MODE=$MODE"
    continue
  fi
  say "stage 1: A0 MODE=$MODE (no evidence yet)"
  jid=$(submit_retry "MODE=$MODE" recovery/a0/a0_gpu_minimal.sh | tr -cd '0-9')
  if [ -n "$jid" ]; then
    say "A0 MODE=$MODE job=$jid submitted"
    wait_done "$jid"
    say "A0 MODE=$MODE job=$jid state=$(sacct -j "$jid" -X --noheader -o State | head -1 | awk '{print $1}') charged=$(spent)"
  else
    say "A0 MODE=$MODE submission gave up"
  fi
done

# ── stage 2: eight-model fits, cheap backbones first (dispatcher's own order) ──
have_pair() {   # all three seeds already present and COMPLETED in the ledger
  local n=0
  [ -d "results/stage6/ckpt/author_966/$1" ] || return 1
  for S in 42 43 44; do
    if grep -q "^S6-$(echo "$1" | tr a-z A-Z)-L$2-S$S,.*,exit=0$" \
              results/stage6/logs/run_ledger.csv 2>/dev/null; then
      n=$((n+1))
    fi
  done
  [ "$n" -eq 3 ]
}

for BB in dlinear patchtst itransformer calf_llm timecma_llm qwen_time_llm; do
  for L in 24 36 48 60; do
    if have_pair "$BB" "$L"; then
      say "stage 2: $BB L=$L already complete - skipping"
      continue
    fi
    if [ "$(over_cap)" = "1" ]; then
      say "STOP RULE: charged $(spent) >= cap $CAP_GPU_H; NOT submitting $BB L=$L"
      say "remaining matrix not run: $BB L=$L and any later pair"
      say "pipeline stopping early (budget), scored output will be partial"
      exit 0
    fi
    jid=$(submit_retry "BACKBONE=$BB" "L=$L" recovery/stage6/run_task.sh | tr -cd '0-9')
    [ -z "$jid" ] && { say "gave up submitting $BB L=$L"; continue; }
    say "submitted $BB L=$L job=$jid"
    verify_submission "$jid" "BACKBONE=$BB L=$L job=$jid"
    wait_done "$jid"
    st=$(sacct -j "$jid" -X --noheader -o State | head -1 | awk '{print $1}')
    el=$(sacct -j "$jid" -X --noheader -o Elapsed | head -1 | tr -d ' ')
    say "job=$jid $BB L=$L state=$st elapsed=$el charged=$(spent)"
    [ "$st" = "COMPLETED" ] || say "WARNING: $BB L=$L ended $st"
  done
done

# ── stage 3: lock 96 checkpoints, unified Test scoring, independent recompute ──
say "stage 3: lock + score + recompute (charged so far $(spent))"
if [ "$(over_cap)" = "1" ]; then
  say "STOP RULE: charged $(spent) >= cap; skipping scoring"
  exit 0
fi
jid=$(submit_retry "ALL" recovery/stage6/score_all.sh | tr -cd '0-9')
if [ -n "$jid" ]; then
  say "score job=$jid submitted"
  wait_done "$jid"
  say "score job=$jid state=$(sacct -j "$jid" -X --noheader -o State | head -1 | awk '{print $1}') charged=$(spent)"
else
  say "score submission gave up"
fi
say "pipeline finished charged=$(spent)"
