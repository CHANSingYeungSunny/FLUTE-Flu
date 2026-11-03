import csv
q = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue/master_queue.tsv'
with open(q) as f:
    reader = csv.DictReader(f, delimiter='\t')
    t6_rows = []
    for row in reader:
        if 'table6' in row.get('kind', ''):
            t6_rows.append(row)

print(f'=== TABLE VI: {len(t6_rows)} total rows ===')
print(f'Columns: {list(t6_rows[0].keys()) if t6_rows else "EMPTY"}')
print()

# Show ALL rows with state and note
print('=== ALL TABLE VI ROWS ===')
for r in t6_rows:
    tid = r.get('task_id', r.get('id', '?'))
    model = r.get('model', '?')
    L = r.get('L', '?')
    seed = r.get('seed', '?')
    state = r.get('state', '?')
    att = r.get('attempts', '?')
    note = r.get('note', '')[:80]
    print(f'  {model}_L{L}_s{seed}: state={state} att={att} note={note}')

print()
print('=== STATE COUNTS ===')
states = {}
for r in t6_rows:
    s = r.get('state', '?')
    states[s] = states.get(s, 0) + 1
for k, v in sorted(states.items()):
    print(f'  {k}: {v}')

print()
print('=== SKIPPED REASONS ===')
skip_notes = {}
for r in t6_rows:
    if r.get('state') == 'SKIPPED':
        note = r.get('note', 'NO NOTE')
        skip_notes[note] = skip_notes.get(note, 0) + 1
for note, count in sorted(skip_notes.items(), key=lambda x: -x[1]):
    print(f'  [{count}x] {note[:120]}')
