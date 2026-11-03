import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')

# Show context around line 635-645
for i in range(632, min(len(lines), 648)):
    print(f'{i+1}: {repr(lines[i][:120])}')

# Fix line 637: add missing b.append(H2( prefix
if 'Definitions and notation' in lines[636] and not lines[636].strip().startswith('b.append('):
    lines[636] = '    b.append(H2("' + lines[636].strip()
    print('fixed line 637')

open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
py_compile.compile(p, doraise=True)
print('compile OK')
