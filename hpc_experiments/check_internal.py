import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
c = open(p, 'r', encoding='utf-8').read()

print(f'File size: {len(c)} chars')
print(f'Has repro_params: {"repro_params" in c}')

t_repro = 'T("reproduction")'
t_ks = 'T("ks_grid")'
print(f'Has {t_repro}: {t_repro in c}')
print(f'Has {t_ks}: {t_ks in c}')

# List all section headers
for m in re.finditer(r'b\.append\(H([12])\("([^"]+)"', c):
    level = 'H1' if m.group(1) == '1' else 'H2'
    print(f'  {level}: {m.group(2)[:80]}')

blocks = c.count('b.append(')
print(f'\nTotal b.append() calls: {blocks}')

redundant = ['Executive summary', 'Scope', 'Motivation', 'Reliability', 'Experiments still',
             'Limitations', 'Design decisions', 'Conclusion', 'Appendix A']
for r in redundant:
    if r in c:
        print(f'  REDUNDANT: {r}')
