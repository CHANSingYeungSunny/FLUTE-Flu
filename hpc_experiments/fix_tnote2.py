import sys, re, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/tables.py'
c = open(p, 'r', encoding='utf-8').read()

# Find ALL occurrences of "beat" near "paper" and show context
for m in re.finditer(r'.{0,60}beat.{0,60}paper.{0,60}', c, re.IGNORECASE | re.DOTALL):
    print(f'Found: {repr(m.group()[:150])}')

# Nuclear: replace any "beat.*paper" pattern
# First, handle the multi-line case
c = re.sub(
    r'never\s+[“"\u201c]we\s+beat\s+the\s+[”"\u201d\n\s+[”"\u201d]paper[”"\u201d]',
    'never claim superiority over the original',
    c
)

# Then handle single-line cases
c = c.replace('we beat the paper', 'we outperformed the original')
c = c.replace('beat the paper', 'outperformed the original')
c = c.replace('never \u201cwe outperformed the original\u201d', 'never claim superiority over the original')
c = c.replace('never "we outperformed the original"', 'never claim superiority over the original')

open(p, 'w', encoding='utf-8', newline='').write(c)

# Verify
cc = open(p, 'r', encoding='utf-8').read()
if 'beat the paper' in cc:
    print('STILL HAS IT — showing remaining:')
    for m in re.finditer(r'.{0,60}beat.{0,60}paper.{0,60}', cc, re.IGNORECASE | re.DOTALL):
        print(f'  {repr(m.group()[:150])}')
else:
    print('CLEAN: no more beat-the-paper')

py_compile.compile(p, doraise=True)
print('compile OK')
