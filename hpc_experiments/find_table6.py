import os
R = '/gpfs1/home/sychan552/stage5_a2_durable'
print('=== SEARCHING FOR TABLE VI ARTIFACTS ===')
# Table VI is regional — L values are region IDs, not horizons
# Check different possible locations
for pattern_dir in ['regional', 'table6', 'region', 'hhs']:
    for root, dirs, files in os.walk(R):
        if pattern_dir in root.lower() and any(f.endswith('.npz') for f in files):
            print(f'  FOUND: {root} ({len(files)} files)')
            for f in sorted(files)[:5]:
                print(f'    {f}')
            break

print()
print('=== CHECKING RUNS WITH REGIONAL NAMING ===')
# Regional cells might use different model names like 'miflu_regional_L2_s42'
for d in sorted(os.listdir(os.path.join(R, 'expanded_runs'))):
    if 'regional' in d.lower() or 'region' in d.lower() or 'hhs' in d.lower():
        print(f'  {d}')

print()
print('=== TABLE VI DONE ROWS: ARTIFACT PATHS FROM MANIFEST ===')
import csv
q = os.path.join(R, 'code/queue', 'master_queue.tsv')
with open(q) as f:
    reader = csv.DictReader(f, delimiter='\t')
    for row in reader:
        if 'table6' in row.get('kind', '') and row.get('state', '') == 'DONE':
            note = row.get('note', '')
            model = row.get('model', '')
            L = row.get('L', '')
            seed = row.get('seed', '')
            print(f'  {model}_L{L}_s{seed}: {note[:100]}')

print()
print('=== WRITER JOBS: WHAT ARE THEY WRITING? ===')
for job_id in ['720001', '720019', '720052']:
    # Check logs
    logdir = os.path.join(R, 'code/queue', 'logs')
    if os.path.isdir(logdir):
        for f in sorted(os.listdir(logdir)):
            if job_id in f:
                fp = os.path.join(logdir, f)
                with open(fp) as lf:
                    lines = lf.readlines()
                    print(f'  {f}: last 3 lines:')
                    for l in lines[-3:]:
                        print(f'    {l.strip()[:120]}')
