import os
R = '/gpfs1/home/sychan552/stage5_a2_durable'
print('=== TABLE VI: ARTIFACTS FOR DONE CELLS ===')
for region in ['miflu_L2', 'miflu_L3', 'miflu_L5', 'miflu_L10', 'miflu_L13', 'miflu_L15', 'miflu_L20']:
    for seed in ['s42', 's43', 's44']:
        d = os.path.join(R, 'expanded_runs', f'{region}_{seed}')
        if os.path.isdir(d):
            files = os.listdir(d)
            npz = [f for f in files if f.endswith('.npz')]
            csvs = [f for f in files if f.endswith('.csv')]
            print(f'  {region}_{seed}: npz={len(npz)} csv={len(csvs)} files={len(files)}')
        else:
            print(f'  {region}_{seed}: NOT FOUND')

print()
print('=== RECENT NPZ FILES (last 24h) ===')
import time
now = time.time()
for d in sorted(os.listdir(os.path.join(R, 'expanded_runs'))):
    dp = os.path.join(R, 'expanded_runs', d)
    if not os.path.isdir(dp):
        continue
    for f in os.listdir(dp):
        if f.endswith('.npz'):
            fp = os.path.join(dp, f)
            age_hours = (now - os.path.getmtime(fp)) / 3600
            if age_hours < 24:
                print(f'  {d}/{f} ({age_hours:.1f}h ago)')

print()
print('=== RUNNING JOBS DETAILS ===')
import subprocess
r = subprocess.run(['sacct', '-X', '-S', '2026-11-03', '-u', 'sychan552',
                     '--format=JobID,JobName%25,State,Elapsed,Partition,WorkDir%80'],
                    capture_output=True, text=True)
for line in r.stdout.split('\n'):
    if 'RUNNING' in line or 'PENDING' in line:
        print(f'  {line.strip()[:150]}')
