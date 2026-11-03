import csv, os
q = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue/master_queue.tsv'
with open(q) as f:
    rows = list(csv.DictReader(f, delimiter='\t'))

# 1. Table VI: show ALL rows with seeds and states
print('=== TABLE VI: ALL ROWS (sorted by seed) ===')
t6 = [r for r in rows if 'table6' in r.get('kind', '')]
t6.sort(key=lambda r: (r.get('seed', ''), r.get('L', '')))
for r in t6:
    seed = r.get('seed', '?')
    state = r.get('state', '?')
    L = r.get('L', '?')
    model = r.get('model', '?')
    att = r.get('attempts', '?')
    note = r.get('note', '')[:60]
    print(f'  {model}_L{L}_s{seed}: state={state} att={att} note={note}')

# 2. Count by seed group
print('\n=== TABLE VI: SEED GROUPS ===')
seed_groups = {}
for r in t6:
    seed = r.get('seed', '?')
    state = r.get('state', '?')
    key = f'seed={seed}'
    if key not in seed_groups:
        seed_groups[key] = {}
    seed_groups[key][state] = seed_groups[key].get(state, 0) + 1
for k in sorted(seed_groups.keys()):
    print(f'  {k}: {seed_groups[k]}')

# 3. Table IX rows
print('\n=== TABLE IX ROWS ===')
t9 = [r for r in rows if 'table_ix' in r.get('kind', '').lower() or 'table9' in r.get('kind', '').lower()]
for r in t9:
    print(f"  {r.get('task_id','?')}: kind={r.get('kind','')} model={r.get('model','')} state={r.get('state','')} note={r.get('note','')[:80]}")
if not t9:
    print('  NONE FOUND')

# 4. Check wf_miflu_cell (rolling origin) priority vs table6
print('\n=== PRIORITY COMPARISON ===')
print('  Table VI rows:')
for r in t6[:5]:
    print(f"    pri={r.get('priority','?')} state={r.get('state','?')} {r.get('model','')}_L{r.get('L','')}_s{r.get('seed','')}")
print('  Rolling origin (wf) rows (first 5 TODO):')
wf_todo = [r for r in rows if r.get('state') == 'TODO' and 'wf' in r.get('kind', '')][:5]
for r in wf_todo:
    print(f"    pri={r.get('priority','?')} kind={r.get('kind','')} {r.get('model','')}_L{r.get('L','')}_s{r.get('seed','')}")
