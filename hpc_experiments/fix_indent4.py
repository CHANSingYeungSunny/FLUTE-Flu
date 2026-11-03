import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')

# Fix line 293 (index 292): should be 4-space indent
lines[292] = '    b.append(P('
# Fix line 299 (index 298): should be 4-space indent
lines[298] = '    b.append(T("repro_params"))'

open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
py_compile.compile(p, doraise=True)
print('compile OK')
