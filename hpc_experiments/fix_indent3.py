import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')

# Show context around line 293
for i in range(max(0, 288), min(len(lines), 300)):
    print(f'{i+1}: {repr(lines[i][:120])}')

# Fix: ensure all b.append lines have proper 4-space indent
for i, l in enumerate(lines):
    stripped = l.strip()
    if stripped.startswith('b.append(') and not l.startswith('    '):
        lines[i] = '    ' + stripped
        print(f'fixed indent line {i+1}')

open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
py_compile.compile(p, doraise=True)
print('compile OK')
