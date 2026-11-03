import csv
q = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue/master_queue.tsv'
with open(q) as f:
    reader = csv.DictReader(f, delimiter='\t')
    all_rows = list(reader)

print(f'Total queue rows: {len(all_rows)}')

# Count by kind and state
by_kind = {}
for r in all_rows:
    kind = r.get('kind', '?')
    state = r.get('state', '?')
    key = f'{kind}:{state}'
    by_kind[key] = by_kind.get(key, 0) + 1

print('\n=== BY KIND:STATE ===')
for k, v in sorted(by_kind.items()):
    print(f'  {k}: {v}')

# Check for rolling origin / walk_forward / walkforward
print('\n=== ROLLING ORIGIN / WALK_FORWARD ROWS ===')
rolling = [r for r in all_rows if any(x in r.get('kind','').lower() + r.get('model','').lower() + r.get('note','').lower()
            for x in ['roll', 'walk', 'fold', 'origin', 'expanding'])]
if rolling:
    for r in rolling[:10]:
        print(f"  {r.get('task_id','?')}: kind={r.get('kind','')} model={r.get('model','')} state={r.get('state','')} note={r.get('note','')[:80]}")
else:
    print('  NONE FOUND — rolling origin NOT in queue!')

# Check TODO rows — what's left to run?
print('\n=== TODO ROWS (what scheduler should run next) ===')
todo = [r for r in all_rows if r.get('state') == 'TODO']
print(f'  Count: {len(todo)}')
todo_kinds = {}
for r in todo:
    kind = r.get('kind', '?')
    todo_kinds[kind] = todo_kinds.get(kind, 0) + 1
for k, v in sorted(todo_kinds.items(), key=lambda x: -x[1]):
    print(f'    {k}: {v}')

# Check SUPERSEDED rows
print('\n=== SUPERSEDED ROWS ===')
sup = [r for r in all_rows if r.get('state') == 'SUPERSEDED']
print(f'  Count: {len(sup)}')
sup_kinds = {}
for r in sup:
    kind = r.get('kind', '?')
    sup_kinds[kind] = sup_kinds.get(kind, 0) + 1
for k, v in sorted(sup_kinds.items(), key=lambda x: -x[1]):
    print(f'    {k}: {v}')

# Check for contamination / quarantine / delete references
print('\n=== CONTAMINATION / QUARANTINE REFERENCES IN NOTES ===')
contam = [r for r in all_rows if any(x in r.get('note','').lower() for x in ['contamin', 'quarantin', 'delete', 'corrupt', 'reject'])]
print(f'  Rows mentioning contamination/quarantine/delete: {len(contam)}')
for r in contam[:5]:
    print(f"    {r.get('task_id','?')}: {r.get('note','')[:100]}")

# Check if there are any rows that should exist but don't
print('\n=== EXPECTED TABLE VI REGIONS (HHS-10) ===')
t6_models = set()
for r in all_rows:
    if 'table6' in r.get('kind', ''):
        t6_models.add(r.get('model', ''))
print(f'  Table VI models/regions in queue: {sorted(t6_models)}')

# Driver status
print('\n=== DRIVER LANE STATUS ===')
import os
queue_dir = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue'
for f in ['CHAIN_DEAD', 'SUCCESSOR_SUBMITTED', 'QUEUE_OWNER', 'P0_LANE.job']:
    fp = os.path.join(queue_dir, f)
    if os.path.exists(fp):
        with open(fp) as fh:
            content = fh.read().strip()[:100]
        print(f'  {f}: {content}')
    else:
        print(f'  {f}: NOT FOUND')
