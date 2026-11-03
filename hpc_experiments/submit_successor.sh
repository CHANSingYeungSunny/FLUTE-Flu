#!/bin/bash
# Submit a successor driver to continue processing the remaining 543 TODO rows.
# The previous driver chain died due to wall-clock guard at 2026-11-03 02:23:50.
set -uo pipefail
Q=/gpfs1/home/sychan552/stage5_a2_durable/code/queue

echo "=== BEFORE ==="
echo "CHAIN_DEAD: $(cat $Q/CHAIN_DEAD 2>/dev/null)"
echo "SUCCESSOR: $(cat $Q/SUCCESSOR_SUBMITTED 2>/dev/null)"
echo "TODO count:"
python3 -c "
import csv
with open('$Q/master_queue.tsv') as f:
    rows = list(csv.DictReader(f, delimiter='\t'))
todo = sum(1 for r in rows if r.get('state') == 'TODO')
run = sum(1 for r in rows if r.get('state') == 'RUNNING')
print(f'  TODO={todo} RUNNING={run}')
"

# Clear CHAIN_DEAD so the new driver can start
echo ""
echo "=== CLEARING CHAIN_DEAD ==="
mv $Q/CHAIN_DEAD $Q/CHAIN_DEAD.bak.$(date +%s)
echo "CLEARED"

# Submit successor driver
echo ""
echo "=== SUBMITTING SUCCESSOR DRIVER ==="
cd $Q
# Check the submit script
if [ -f persistent_driver.sh ]; then
    sbatch persistent_driver.sh
    echo "Submitted persistent_driver.sh"
else
    echo "ERROR: persistent_driver.sh not found"
    ls -la $Q/persistent_driver* 2>/dev/null
fi

# Record successor
echo "$(date '+%Y-%m-%d %H:%M:%S') pid=$$ successor=manual_resubmit" > $Q/SUCCESSOR_SUBMITTED
echo "Recorded in SUCCESSOR_SUBMITTED"

echo ""
echo "=== AFTER ==="
echo "CHAIN_DEAD: $(cat $Q/CHAIN_DEAD 2>/dev/null || echo 'CLEARED')"
echo "SUCCESSOR: $(cat $Q/SUCCESSOR_SUBMITTED 2>/dev/null)"

# Check running jobs
echo ""
echo "=== RUNNING JOBS ==="
sacct -X -S 2026-11-03 -u sychan552 --format=JobID,JobName%25,State,Elapsed,Partition 2>/dev/null | grep -i 'run\|pend' | head -10
