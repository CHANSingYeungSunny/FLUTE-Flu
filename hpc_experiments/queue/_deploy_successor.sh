#!/bin/bash
# _deploy_successor.sh -- deploy and TEST the part-two successor logic, then
# submit the dedicated watcher. Does not touch 720083/720070/720052/720004.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }

echo "=== 0. de-CRLF + syntax ==="
for f in successor_lib.sh successor_lane.sh successor_watch.sh watchdog.sh master_controller_v2.sh; do
  sed -i 's/\r$//' "$f"; sed -i '1s/^\xEF\xBB\xBF//' "$f"
done
sed -i 's|/master_task\.py|/master_task_v2.py|g' master_controller_v2.sh
for f in successor_lib.sh successor_lane.sh successor_watch.sh watchdog.sh master_controller_v2.sh; do
  bash -n "$f" && echo "  OK   $f" || echo "  FAIL $f"
done

echo
echo "=== 1. record the designated P0 lane (720083) ==="
echo 720083 > P0_LANE.job
printf '  P0_LANE.job = %s (state=%s start=%s)\n' "$(cat P0_LANE.job)" "$(st 720083 JobState)" "$(st 720083 StartTime)"

echo
echo "=== 2. GATE DRY-RUN (must refuse right now, with a reason) ==="
rm -f SUCCESSOR_SUBMITTED
( . ./successor_lib.sh; why=$(successor_gate) && echo "  GATE=ready UNEXPECTED" || echo "  gate refuses as expected: ${why}" )

echo
echo "=== 3. GATE POSITIVE TEST on a sandbox: P0 already gone, stingy free ==="
SBX=$(mktemp -d "${Q}/succ_test.XXXXXX")
cp successor_lib.sh "$SBX/"
printf '999999\n' > "$SBX/P0_LANE.job"          # a job id that does not exist => not live
( export QDIR="$SBX"; export QUEUE_SUCCESSOR_MIN_RUNWAY=1
  . "${SBX}/successor_lib.sh"
  why=$(successor_gate)
  case "$why" in
    ready:*) echo "  sandbox gate: READY ($why)" ;;
    stingy-busy:*) echo "  sandbox gate: refused - stingy is busy ($why) [expected while a lane is queued]" ;;
    *) echo "  sandbox gate: refused ($why)" ;;
  esac )

echo
echo "=== 4. ONE-SHOT TEST: two concurrent fires must produce exactly one submit ==="
SBX2=$(mktemp -d "${Q}/succ_once.XXXXXX")
cp successor_lib.sh "$SBX2/"
printf '#!/bin/bash\necho %s\n' 888888 > "$SBX2/successor_lane.sh"   # not executable: fire is refused
chmod +x "$SBX2/successor_lane.sh"
( export QDIR="$SBX2"
  . "${SBX2}/successor_lib.sh"
  ( set -o noclobber; printf 'pid=%s\n' $$ > "${SUCC_SENTINEL}" ) 2>/dev/null && echo "  A created sentinel" || echo "  A lost"
  ( set -o noclobber; printf 'pid=%s\n' $$ > "${SUCC_SENTINEL}" ) 2>/dev/null && echo "  B created sentinel (BAD)" || echo "  B refused (one-shot holds)" )
rm -rf "$SBX" "$SBX2"

echo
echo "=== 5. submit the dedicated successor watcher (tiny, 12 h) ==="
W=$(sbatch --parsable --partition=tiny --cpus-per-task=2 --mem=2G --time=12:00:00 --requeue \
      --output="$Q/slurm-SW-%j.out" --export=ALL,QUEUE_SUCC_POLL=120 \
      "$Q/successor_watch.sh" 2>&1)
W=${W%%;*}
case "$W" in
  ''|*[!0-9]*) echo "  SUCCESSOR WATCHER SUBMIT FAILED: $W" ;;
  *) echo 720083 > P0_LANE.job
     printf '  successor watcher %s part=%s wall=%s start=%s state=%s\n' "$W" \
       "$(st "$W" Partition)" "$(st "$W" TimeLimit)" "$(st "$W" StartTime)" "$(st "$W" JobState)" ;;
esac

echo
echo "=== 6. successor.log after the watcher starts ==="
sleep 20
cat successor.log 2>/dev/null || echo "  (no log yet)"

echo
echo "=== 7. untouched jobs still intact ==="
for j in 720083 720070 720052 720004; do
  printf '  %-8s %-14s %-9s start=%-20s %s\n' "$j" "$(st "$j" JobName)" "$(st "$j" JobState)" \
    "$(st "$j" StartTime)" "$(st "$j" TimeLimit)"
done
echo
echo "=== 8. sentinel path / cutoff ==="
echo "  sentinel: ${Q}/SUCCESSOR_SUBMITTED"
echo "  log     : ${Q}/successor.log"
echo "  cutoff  : QUEUE_SUCCESSOR_CUTOFF=0700 (local, next occurrence), min runway 1800 s"
