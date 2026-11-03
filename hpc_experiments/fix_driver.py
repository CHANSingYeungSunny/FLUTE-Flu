import os
qdir = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue'

# Read CHAIN_DEAD to understand the guard
with open(os.path.join(qdir, 'CHAIN_DEAD')) as f:
    chain_dead = f.read().strip()
print(f'CHAIN_DEAD: {chain_dead}')

# Read SUCCESSOR_SUBMITTED
with open(os.path.join(qdir, 'SUCCESSOR_SUBMITTED')) as f:
    successor = f.read().strip()
print(f'SUCCESSOR_SUBMITTED: {successor}')

# Check if persistent_driver.sh has the PATCH
driver_sh = os.path.join(qdir, 'persistent_driver.sh')
if os.path.exists(driver_sh):
    with open(driver_sh) as f:
        content = f.read()
    has_patch = content.count('PATCH 2026-11-02')
    has_lk = content.count('lk_acquire')
    print(f'\npersistent_driver.sh: PATCH count={has_patch}, lk_acquire count={has_lk}')
    # Check wall-clock guard logic
    for i, line in enumerate(content.split('\n')):
        if 'wall' in line.lower() and ('guard' in line.lower() or 'clock' in line.lower()):
            print(f'  L{i+1}: {line.strip()[:120]}')
        if 'CHAIN_DEAD' in line:
            print(f'  L{i+1}: {line.strip()[:120]}')
else:
    print('persistent_driver.sh NOT FOUND')

# Check if there's a successor submission script
for f in ['_deploy_successor.sh', '_apply_unblock.sh']:
    fp = os.path.join(qdir, f)
    if os.path.exists(fp):
        with open(fp) as fh:
            first_lines = fh.readlines()[:5]
        print(f'\n{f}:')
        for l in first_lines:
            print(f'  {l.strip()[:120]}')

# Check what the wall-clock guard limit is
print('\n=== WALL-CLOCK GUARD CONFIG ===')
for f in ['master_controller_v2.sh', 'master_controller.sh']:
    fp = os.path.join(qdir, f)
    if os.path.exists(fp):
        with open(fp) as fh:
            for i, line in enumerate(fh):
                if 'wall' in line.lower() and ('limit' in line.lower() or 'guard' in line.lower() or 'max' in line.lower()):
                    print(f'  {f} L{i+1}: {line.strip()[:120]}')
