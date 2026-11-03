#!/usr/bin/env python3
"""Fix Table VI: un-skip reproduction-protocol rows, add missing seeds, boost priority."""
import csv, os, sys

Q = '/gpfs1/home/sychan552/stage5_a2_durable/code/queue/master_queue.tsv'
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open(Q) as f:
    reader = csv.DictReader(f, delimiter='\t')
    fieldnames = reader.fieldnames
    rows = list(reader)

print(f'Before: {len(rows)} rows')

# 1. Un-skip Table VI rows with seeds 2024-2030 (reproduction protocol)
unskipped = 0
for r in rows:
    if 'table6' in r.get('kind', '') and r.get('state') == 'SKIPPED':
        seed = r.get('seed', '')
        if seed.isdigit() and 2024 <= int(seed) <= 2030:
            r['state'] = 'TODO'
            r['attempts'] = '0'
            r['note'] = f"Table VI regional (HHS-10, region=all, T=20 K=4, 50 ep, bs=32), rep=1, protocol 10 seeds 2021-2030 -- UN-SKIPPED 2026-11-03: regional reproduction uses reproduction protocol, NOT benchmark 3-seed"
            r['priority'] = 'P3'  # Higher than rolling origin (P5)
            unskipped += 1
print(f'Un-skipped: {unskipped} rows (seeds 2024-2030)')

# 2. Add missing seeds 2021-2023 for Table VI
regions = ['miflu_L2', 'miflu_L3', 'miflu_L5', 'miflu_L10', 'miflu_L13', 'miflu_L15', 'miflu_L20']
existing = set()
for r in rows:
    if 'table6' in r.get('kind', ''):
        existing.add(f"{r.get('model','')}_s{r.get('seed','')}")

added = 0
for seed in ['2021', '2022', '2023']:
    for region in regions:
        key = f'{region}_s{seed}'
        if key not in existing:
            rows.append({
                'task_id': f'table6_{region}_s{seed}',
                'kind': 'table6_cell',
                'model': region,
                'L': region.split('_L')[1] if '_L' in region else '?',
                'seed': seed,
                'priority': 'P3',
                'env': 'stingy',
                'state': 'TODO',
                'attempts': '0',
                'last_job': '-',
                'note': f'Table VI regional (HHS-10, region=all, T=20 K=4, 50 ep, bs=32), rep=1, protocol 10 seeds 2021-2030 -- ADDED 2026-11-03: missing reproduction seed',
            })
            added += 1
print(f'Added: {added} rows (seeds 2021-2023)')

# 3. Boost priority of Table VI rows above rolling origin
boosted = 0
for r in rows:
    if 'table6' in r.get('kind', '') and r.get('state') == 'TODO':
        r['priority'] = 'P3'  # P3 > P5 (rolling origin)
        boosted += 1
print(f'Priority boosted to P3: {boosted} rows')

# 4. Lower rolling origin priority to P5 (below Table VI)
lowered = 0
for r in rows:
    if 'wf' in r.get('kind', '') and r.get('state') == 'TODO':
        r['priority'] = 'P5'
        lowered += 1
print(f'Rolling origin priority set to P5: {lowered} rows')

# 5. Mark Table IX as TODO (needs regeneration from correct Table VI data)
for r in rows:
    if 'table_ix' in r.get('kind', '').lower():
        r['state'] = 'TODO'
        r['note'] = 'Table IX regional training time -- REGENERATE from Table VI 10-seed results (2026-11-03)'
        print(f'Table IX marked TODO for regeneration')

# Write back
with open(Q, 'w', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter='\t')
    writer.writeheader()
    writer.writerows(rows)

print(f'\nAfter: {len(rows)} rows')
print(f'  Un-skipped: {unskipped}')
print(f'  Added: {added}')
print(f'  Priority boosted: {boosted}')

# Verify
print('\n=== TABLE VI STATE AFTER FIX ===')
t6 = [r for r in rows if 'table6' in r.get('kind', '')]
states = {}
seeds_by_state = {}
for r in t6:
    s = r.get('state', '?')
    states[s] = states.get(s, 0) + 1
    seed = r.get('seed', '?')
    if s not in seeds_by_state:
        seeds_by_state[s] = set()
    seeds_by_state[s].add(seed)
for k, v in sorted(states.items()):
    print(f'  {k}: {v} rows, seeds={sorted(seeds_by_state[k])}')

print('\n=== TABLE IX STATE ===')
for r in rows:
    if 'table_ix' in r.get('kind', '').lower():
        print(f"  {r.get('task_id','?')}: state={r.get('state','')} note={r.get('note','')[:80]}")
