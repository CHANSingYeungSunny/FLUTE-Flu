squeue -u sychan552 -o '%i|%P|%j|%T|%M|%R'
echo "=== 719534 ==="
scontrol show job 719534 | tr ' ' '\n' | grep -E '^(Partition|Command|WorkDir|JobName|TimeLimit|SubmitTime|StartTime)='
echo "=== 719538 ==="
scontrol show job 719538 | tr ' ' '\n' | grep -E '^(Partition|Command|WorkDir|JobName|TimeLimit|StartTime|Reason|BatchFlag|Requeue|Command)='
echo "=== nodes stingy ==="
sinfo -p stingy -h -o '%N|%t|%G|%C'
echo "=== nodes gpu_a100 ==="
sinfo -p gpu_a100 -h -o '%N|%t|%G|%C'
