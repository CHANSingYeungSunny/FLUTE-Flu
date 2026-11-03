import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_progress.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')

# Show context around line 265
for i in range(max(0, 260), min(len(lines), 275)):
    print(f'{i+1}: {repr(lines[i][:120])}')

# Fix: the ablation block was inserted without proper indentation
# Find the broken block and fix
for i, l in enumerate(lines):
    if l.strip().startswith('b.append(P(') and 'Ablation (Table VIII)' in lines[i+1] if i+1 < len(lines) else False:
        # This line needs proper indentation
        lines[i] = '    ' + l.strip()
        print(f'fixed line {i+1}')

# Also check for any bare b.append lines
for i, l in enumerate(lines):
    stripped = l.strip()
    if stripped.startswith('b.append(') and not l.startswith('    '):
        lines[i] = '    ' + stripped
        print(f'fixed indent line {i+1}')

open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines))

try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    err = str(e)
    print(f'FAIL: {err[:250]}')
    import re
    m = re.search(r'line (\d+)', err)
    if m:
        ln = int(m.group(1))
        ls = '\n'.join(lines).split('\n')
        for j in range(max(0, ln-3), min(len(ls), ln+3)):
            print(f'  {j+1}: {ls[j][:120]}')
