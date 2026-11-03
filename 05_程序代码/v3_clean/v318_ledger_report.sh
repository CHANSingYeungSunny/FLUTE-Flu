#!/bin/bash
# READ-ONLY Wave-1 reconciliation. NOTE: the frozen order file must be scanned
# in its ORIGINAL positional order — sorting it silently reorders the matrix.
B=/scratch/sychan552/_v318d
R=/scratch/sychan552/innovation_deploy_root_v3_clean12
ORD="$B/formal_execution_order_wave1.txt"

echo "=== all wave1 ledgers on the filesystem ==="
find /scratch/sychan552 -maxdepth 6 -name 'wave1_ledger*' 2>/dev/null | head -20

echo
echo "=== this controller's ledger ==="
L="$B/wave1_ledger.jsonl"
echo "MY_ACCEPTED=$(grep -c '"event":"ACCEPTED"' "$L")"
echo "MY_SUBMITTED=$(grep -c '"event":"SUBMITTED"' "$L")"

echo
echo "=== cumulative accepted union across ALL ledgers + acceptance records ==="
: > /tmp/all_acc.txt
for f in $(find /scratch/sychan552 /gpfs1/scratch/sychan552 -maxdepth 6 \
             -name 'wave1_ledger*' -o -maxdepth 6 -name '*acceptance*.jsonl' 2>/dev/null); do
  grep -h '"event":"ACCEPTED"' "$f" 2>/dev/null | sed 's/.*"run_key":"//' \
    | cut -d'"' -f1 >> /tmp/all_acc.txt
  grep -h '"event": "ACCEPTED"' "$f" 2>/dev/null | sed 's/.*"run_key": "//' \
    | cut -d'"' -f1 >> /tmp/all_acc.txt
  # repair-acceptance records may carry a plain run_key field
  grep -h '"run_key"' "$f" 2>/dev/null | grep -h 'ACCEPTED' \
    | sed 's/.*"run_key": *"//' | cut -d'"' -f1 >> /tmp/all_acc.txt
done
grep -v '^$' /tmp/all_acc.txt | sort -u > /tmp/all_acc_u.txt
echo "CUMULATIVE_UNIQUE_ACCEPTED=$(wc -l < /tmp/all_acc_u.txt)"

echo
echo "=== durable row directories (independent cross-check) ==="
echo "DURABLE_ROWS=$(ls -1 /home/sychan552/innovation_durable/screening 2>/dev/null | grep -c '__w1$')"
echo "DURABLE_BASELINE_ROWS=$(ls -1 /home/sychan552/innovation_durable/screening 2>/dev/null | grep -c '^baseline__')"

echo
echo "=== scratch run dirs in the ACTIVE deployment root ==="
echo "SCRATCH_ROWS=$(ls -1d $R/results/v3_clean/runs/*__w1 2>/dev/null | wc -l)"

echo
echo "=== frozen order (positional, NOT sorted) ==="
sed '/^#/d;/^[[:space:]]*$/d' "$ORD" > /tmp/ord_pos.txt
echo "ORDER_TOTAL=$(wc -l < /tmp/ord_pos.txt)"

echo "--- accepted-per-position histogram ---"
awk 'NR==FNR{a[$0]=1;next}{s+=($0 in a)}END{print "ORDER_POSITIONS_ACCEPTED="s}' \
    /tmp/all_acc_u.txt /tmp/ord_pos.txt

echo "--- FIRST UNACCEPTED POSITION IN FROZEN ORDER ---"
awk 'NR==FNR{a[$0]=1;next}
     {if(!($0 in a)){print "POS="NR"  NEXT_KEY="$0; exit}}' \
    /tmp/all_acc_u.txt /tmp/ord_pos.txt

echo "--- last 6 positions of the order, with accepted flag ---"
awk 'NR==FNR{a[$0]=1;next}
     {n=NR; last[n]=$0}
     END{for(i=n-5;i<=n;i++) printf "POS=%d ACCEPTED=%s %s\n", i, \
         (last[i] in a ? "yes" : "NO"), last[i]}' /tmp/all_acc_u.txt /tmp/ord_pos.txt

echo
echo "=== arm composition of the frozen order (positional) ==="
cut -d_ -f1 /tmp/ord_pos.txt | sort | uniq -c

echo
echo "=== accepted NOT in frozen order (must be 0) ==="
sort /tmp/ord_pos.txt > /tmp/ord_sorted.txt
sort /tmp/all_acc_u.txt > /tmp/all_acc_s.txt
comm -23 /tmp/all_acc_s.txt /tmp/ord_sorted.txt | head -5
echo "COUNT=$(comm -23 /tmp/all_acc_s.txt /tmp/ord_sorted.txt | wc -l)"

echo
echo "=== controller / lock / queue ==="
echo "controller_procs=$(pgrep -cf 'wave1_controller_v31[0-9]')"
ls -d "$B"/.wave1_controller.lock 2>/dev/null || echo "NO_LOCK"
echo "active_jobs=$(squeue -u "$USER" -h -o %i 2>/dev/null | grep -c '^[0-9]')"
echo "test_eval_dirs=$(ls -1 $R/results/innovation/test_evaluations 2>/dev/null | wc -l)"

echo
echo "=== quota / usage ==="
mmlsquota 2>/dev/null | grep -Ev '^ *$' | head -6
du -sh /home/sychan552 2>/dev/null
du -sh /gpfs1/scratch/sychan552 2>/dev/null
