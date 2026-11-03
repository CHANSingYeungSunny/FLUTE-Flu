import os
Q = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue'

print('=== 1. DISPATCH LOGIC: How does scheduler pick rows? ===')
for ctrl in ['master_controller_v2.sh', 'master_controller.sh']:
    fp = os.path.join(Q, ctrl)
    if not os.path.exists(fp):
        continue
    with open(fp) as f:
        lines = f.readlines()
    print(f'\n--- {ctrl} ({len(lines)} lines) ---')
    for i, line in enumerate(lines):
        # Find dispatch/priority logic
        if any(x in line.lower() for x in ['priority', 'pri', 'order by', 'sort', 'pick_next', 'dispatch']):
            if 'echo' not in line and '#' not in line[:3]:
                print(f'  L{i+1}: {line.strip()[:120]}')

print('\n=== 2. WALL-CLOCK GUARD: What triggers it? ===')
for ctrl in ['master_controller_v2.sh', 'master_controller.sh']:
    fp = os.path.join(Q, ctrl)
    if not os.path.exists(fp):
        continue
    with open(fp) as f:
        lines = f.readlines()
    print(f'\n--- {ctrl} ---')
    for i, line in enumerate(lines):
        if 'wall' in line.lower() and ('guard' in line.lower() or 'clock' in line.lower() or 'limit' in line.lower()):
            print(f'  L{i+1}: {line.strip()[:120]}')

print('\n=== 3. TABLE IX: Auto-generation after Table VI? ===')
# Check if there's a post-processing step
for f in ['master_controller_v2.sh', 'master_controller.sh', 'persistent_driver.sh']:
    fp = os.path.join(Q, f)
    if not os.path.exists(fp):
        continue
    with open(fp) as fh:
        content = fh.read()
    if 'table_ix' in content.lower() or 'build_table' in content.lower():
        print(f'  {f}: mentions table_ix/build_table')
        for i, line in enumerate(content.split('\n')):
            if 'table_ix' in line.lower() or 'build_table' in line.lower():
                print(f'    L{i+1}: {line.strip()[:120]}')
    else:
        print(f'  {f}: NO table_ix reference')

print('\n=== 4. CHAIN_DEAD: What causes it? ===')
for ctrl in ['master_controller_v2.sh', 'master_controller.sh']:
    fp = os.path.join(Q, ctrl)
    if not os.path.exists(fp):
        continue
    with open(fp) as f:
        lines = f.readlines()
    print(f'\n--- {ctrl} ---')
    for i, line in enumerate(lines):
        if 'chain_dead' in line.lower() or 'CHAIN_DEAD' in line:
            print(f'  L{i+1}: {line.strip()[:120]}')

print('\n=== 5. CONTINUE_CHAIN: What makes chain continue? ===')
for ctrl in ['master_controller_v2.sh', 'master_controller.sh']:
    fp = os.path.join(Q, ctrl)
    if not os.path.exists(fp):
        continue
    with open(fp) as f:
        lines = f.readlines()
    for i, line in enumerate(lines):
        if 'continue_chain' in line and ('def' in line or 'function' in line):
            print(f'\n--- {ctrl} L{i+1} ---')
            for j in range(i, min(i+30, len(lines))):
                print(f'  L{j+1}: {lines[j].strip()[:120]}')
            break

print('\n=== 6. CURRENT DRIVER STATUS ===')
for f in ['CHAIN_DEAD', 'SUCCESSOR_SUBMITTED', 'P0_LANE.job']:
    fp = os.path.join(Q, f)
    if os.path.exists(fp):
        with open(fp) as fh:
            print(f'  {f}: {fh.read().strip()[:120]}')
