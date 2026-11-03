import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/tables.py'
c = open(p, 'r', encoding='utf-8').read()

# The exact multi-line pattern in the source code
# "…never "we beat the "\n                  "paper"…"
# Let's find and replace the exact bytes

# Method 1: replace the exact multi-line string
old1 = 'never \u201cwe beat the "\n                  "paper\u201d'
new1 = 'never claim superiority over the original'
if old1 in c:
    c = c.replace(old1, new1, 1)
    print('method 1: replaced')
else:
    print('method 1: not found')

# Method 2: if still there, try line-by-line
if 'beat the paper' in c or 'beat the "' in c:
    lines = c.split('\n')
    for i, l in enumerate(lines):
        if 'beat the' in l and 'paper' in l:
            print(f'  line {i+1}: {repr(l[:120])}')
        elif 'beat the' in l and i+1 < len(lines) and 'paper' in lines[i+1]:
            print(f'  line {i+1}+{i+2}: {repr(l[:80])} + {repr(lines[i+1][:80])}')

# Method 3: direct character-level replacement
c = c.replace('we beat the "\n                  "paper', 'we outperformed the original')

# Method 4: regex with exact chars
import re
c = re.sub(
    r'we\s+beat\s+the\s+"\n\s+"paper',
    'we outperformed the original',
    c
)

# Method 5: just replace "beat the" when near "paper"
c = re.sub(r'beat(\s+the)?(?=[^"]{0,20}paper)', 'outperformed', c)

open(p, 'w', encoding='utf-8', newline='').write(c)

# Final check
cc = open(p, 'r', encoding='utf-8').read()
if 'beat the paper' in cc or 'beat the "' in cc:
    print('STILL HAS IT')
    for m in re.finditer(r'.{0,80}beat.{0,80}paper.{0,80}', cc, re.DOTALL):
        print(f'  {repr(m.group()[:200])}')
else:
    print('CLEAN!')

py_compile.compile(p, doraise=True)
print('compile OK')
