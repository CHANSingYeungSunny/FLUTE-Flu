#!/bin/bash
# _swap_719833.sh -- cancel the v1 stingy holder and put a working P0 lane in the
# 02:36 slot. Also price 720070 (the P1 lane) and drop it if it starts after the
# night, because P0 outranks P1 and a never-starting lane is only a QOS obstacle.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue
PY=/home/sychan552/.conda/envs/mlflu_hpc/bin/python
cd "$Q" || exit 1
st() { scontrol show job "$1" 2>/dev/null | tr ' ' '\n' | sed -n "s/^$2=//p"; }

echo "=== 0. deploy the priority-scope fix (P0 lane must own all 22 cells) ==="
sed -i 's/\r$//' master_controller_v2.sh
sed -i 's|/master_task\.py|/master_task_v2.py|g' master_controller_v2.sh
bash -n master_controller_v2.sh && echo "  controller syntax OK"
grep -c 'a priority-scoped lane owns' master_controller_v2.sh | sed 's/^/  priority-scope hook: /'

echo
echo "=== 1. 720070 (Qwen P1 lane) StartTime check ==="
T70=$(st 720070 StartTime)
S70=$(st 720070 JobState)
echo "  720070 state=$S70 start=$T70"
KEEP70=1
case "$T70" in
  Unknown|N/A|"") echo "  -> Unknown: Slurm has not priced it; it is not blocking a stingy slot, keeping it"
                 KEEP70=1 ;;
  2026-11-01*)   echo "  -> starts tonight: keeping it" ; KEEP70=1 ;;
  2026-11-02T0[0-8]*) echo "  -> starts before 09:00 tomorrow: keeping it" ; KEEP70=1 ;;
  *)             echo "  -> starts after tomorrow morning: CANCELLING it (P0 outranks P1 tonight)"
                 KEEP70=0 ;;
esac

echo
echo "=== 2. cancel 719833 (v1 code cannot parse the 11-column queue; holds 02:36 doing nothing) ==="
printf '  before: 719833 state=%s start=%s\n' "$(st 719833 JobState)" "$(st 719833 StartTime)"
scancel 719833 2>&1
sleep 6
printf '  after : 719833 state=%s\n' "$(st 719833 JobState)"

echo
echo "=== 3. submit the P0 lane to stingy IMMEDIATELY (4 h, 1 worker, -x gpu-a100-05) ==="
P=$(sbatch --parsable --partition=stingy --gres=gpu:a100:1 --cpus-per-task=8 --mem=48G \
      --time=04:00:00 --requeue --exclude=gpu-a100-05 \
      --output="$Q/slurm-P0-%j.out" \
      --export=ALL,QUEUE_STRIPE=0,QUEUE_PARTITION=stingy,QUEUE_WALL_SECONDS=14400,QUEUE_ONLY_PRIORITY=P0 \
      "$Q/master_controller_v2.sh" 2>&1)
P=${P%%;*}
case "$P" in
  ''|*[!0-9]*) echo "  P0 LANE SUBMIT FAILED: $P" ;;
  *) printf '%s\n' "$P" > runner_s0.job
     printf '  P0 lane %s part=%s wall=%s start=%s state=%s\n' "$P" \
       "$(st "$P" Partition)" "$(st "$P" TimeLimit)" "$(st "$P" StartTime)" "$(st "$P" JobState)" ;;
esac

if [ "$KEEP70" = "0" ]; then
  echo
  echo "=== 4. cancel 720070 (started after the night) ==="
  scancel 720070 2>&1; sleep 3
  printf '  720070 now=%s\n' "$(st 720070 JobState)"
  echo 720070 > runner_s1.job
fi

echo
echo "=== 5. jobs now ==="
squeue -u sychan552 -o '%.8i %.10P %.16j %.2t %.21S'
echo
echo "=== 6. state (scontrol, authoritative) ==="
for j in "$P" 720070 720052 720004 719833; do
  [ -n "$j" ] || continue
  printf '  %-8s %-14s %-10s start=%-20s %s\n' "$j" "$(st "$j" JobName)" "$(st "$j" JobState)" \
    "$(st "$j" StartTime)" "$(st "$j" TimeLimit)"
done
echo
echo "=== 7. markers ==="
ls -1 /gpfs1/home/sychan552/stage5_a2_durable/author_runs/.miflu_verify | wc -l
