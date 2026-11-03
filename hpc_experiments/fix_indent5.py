import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')

# Show context around line 95
for i in range(90, min(len(lines), 105)):
    print(f'{i+1}: {repr(lines[i][:120])}')

# Fix all indentation issues
for i, l in enumerate(lines):
    stripped = l.strip()
    if stripped.startswith('b.append(') and not l.startswith('    ') and l.strip():
        lines[i] = '    ' + stripped
        print(f'fixed indent line {i+1}')
    elif stripped.startswith('def ') and not l.startswith('def ') and l.strip():
        # def at wrong indent
        lines[i] = stripped
        print(f'fixed def indent line {i+1}')

open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    print(f'FAIL: {str(e)[:250]}')
