import csv
q = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue/master_queue.tsv'
with open(q) as f:
    reader = csv.DictReader(f, delimiter='\t')
    t8 = {}
    t6 = {}
    other = {}
    t8_variants = {}
    t6_regions = {}
    for row in reader:
        kind = row.get('kind', '')
        state = row.get('state', '')
        model = row.get('model', '')
        L = row.get('L', '')
        if 'table8' in kind:
            t8[state] = t8.get(state, 0) + 1
            v = model.split('_')[-1] if '_' in model else model
            key = f"{model}"
            if state == 'DONE':
                t8_variants[key] = t8_variants.get(key, 0) + 1
        elif 'table6' in kind:
            t6[state] = t6.get(state, 0) + 1
            if state == 'DONE':
                key = f"{model}_L{L}"
                t6_regions[key] = t6_regions.get(key, 0) + 1
        else:
            other[state] = other.get(state, 0) + 1

print('=== TABLE8 (ablation) ===')
for k, v in sorted(t8.items()):
    print(f'  {k}: {v}')
print('  DONE variants:')
for k, v in sorted(t8_variants.items()):
    print(f'    {k}: {v} cells')

print('=== TABLE6 (regional) ===')
for k, v in sorted(t6.items()):
    print(f'  {k}: {v}')
print('  DONE regions:')
for k, v in sorted(t6_regions.items()):
    print(f'    {k}: {v} cells')

print('=== OTHER ===')
for k, v in sorted(other.items()):
    print(f'  {k}: {v}')

total = sum(t8.values()) + sum(t6.values()) + sum(other.values())
print(f'\nTotal rows: {total}')
