import subprocess, csv, os, time

Q = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue/master_queue.tsv'

print('=== CURRENT RUNNING JOBS ===')
r = subprocess.run(['sacct', '-X', '-S', '2026-11-03', '-u', 'sychan552',
                     '--format=JobID,JobName%25,State,Elapsed,Partition'],
                    capture_output=True, text=True)
for line in r.stdout.split('\n'):
    if any(x in line for x in ['RUNNING', 'PENDING', '725643']):
        print(f'  {line.strip()[:120]}')

print('\n=== QUEUE STATE: TABLE VI ===')
with open(Q) as f:
    rows = list(csv.DictReader(f, delimiter='\t'))
t6_todo = [r for r in rows if 'table6' in r.get('kind','') and r.get('state') == 'TODO']
t6_done = [r for r in rows if 'table6' in r.get('kind','') and r.get('state') == 'DONE']
print(f'  TODO: {len(t6_todo)} rows')
print(f'  DONE: {len(t6_done)} rows')
if t6_todo:
    print(f'  First 3 TODO: {[r.get("model","")+"_s"+r.get("seed","") for r in t6_todo[:3]]}')

print('\n=== QUEUE STATE: ALL ===')
states = {}
for r in rows:
    s = r.get('state', '?')
    states[s] = states.get(s, 0) + 1
for k, v in sorted(states.items()):
    print(f'  {k}: {v}')

print('\n=== DRIVER FILE STATUS ===')
for f in ['CHAIN_DEAD', 'SUCCESSOR_SUBMITTED']:
    fp = os.path.join(os.path.dirname(Q), f)
    if os.path.exists(fp):
        with open(fp) as fh:
            content = fh.read().strip()
        age_min = (time.time() - os.path.getmtime(fp)) / 60
        print(f'  {f}: {content[:100]} ({age_min:.0f}min ago)')
    else:
        print(f'  {f}: NOT FOUND (good if CHAIN_DEAD)')

print('\n=== IS DRIVER ACTIVELY PROCESSING? ===')
# Check if any table6 cells are RUNNING
t6_running = [r for r in rows if 'table6' in r.get('kind','') and r.get('state') == 'RUNNING']
if t6_running:
    print(f'  YES: {len(t6_running)} Table VI cells RUNNING')
    for r in t6_running:
        print(f'    {r.get("model","")}_s{r.get("seed","")}: job={r.get("last_job","")}')
else:
    print('  NOT YET: No Table VI cells RUNNING (driver may be starting up)')
    # Check if any TODO rows have recent attempts
    recent = [r for r in t6_todo if r.get('attempts','0') != '0']
    if recent:
        print(f'  BUT: {len(recent)} rows have attempts > 0 (being processed)')
