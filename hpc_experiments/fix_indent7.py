import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')

fixed = 0
for i, l in enumerate(lines):
    stripped = l.strip()
    if stripped.startswith('b.append(') and stripped:
        # Check if indent is exactly 4 spaces
        if l != '    ' + stripped:
            lines[i] = '    ' + stripped
            fixed += 1
            print(f'  fixed line {i+1}: had {len(l) - len(l.lstrip())} spaces')

open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
print(f'Fixed {fixed} lines')

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
            print(f'  {j+1}: {repr(ls[j][:120])}')
