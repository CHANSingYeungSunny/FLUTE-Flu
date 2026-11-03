import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')

# Show lines 90-100
for i in range(89, min(len(lines), 102)):
    print(f'{i+1}: {repr(lines[i])}')

# Fix line 95 (index 94) — should start with 4 spaces
print(f'\nLine 95 raw: {repr(lines[94])}')
lines[94] = '    ' + lines[94].strip()
print(f'Line 95 fixed: {repr(lines[94])}')

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
        for j in range(max(0, ln-3), min(len(lines), ln+3)):
            print(f'  {j+1}: {repr(lines[j][:120])}')
