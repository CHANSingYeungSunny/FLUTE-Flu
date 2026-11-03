import sys, re, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_ieee.py'
c = open(p, 'r', encoding='utf-8').read()

# Find ALL occurrences of "beat" near "paper"
for m in re.finditer(r'.{0,50}beat.{0,50}paper.{0,50}', c, re.IGNORECASE):
    print(f'Found: {repr(m.group())}')

# Also check for Unicode escapes
for m in re.finditer(r'.{0,30}beat.{0,30}', c, re.IGNORECASE):
    print(f'beat context: {repr(m.group())}')

# Nuclear option: replace ALL variations
replacements = [
    ('we beat the paper', 'we outperformed the original'),
    ('beat the paper', 'outperformed the original'),
    ('beat the original', 'outperformed the original'),
    ('never \u201cwe beat the paper\u201d', 'never claim superiority over the original'),
    ('never "we beat the paper"', 'never claim superiority over the original'),
    ('never \u201cwe outperformed the original\u201d', 'never claim superiority over the original'),
]
for old, new in replacements:
    if old in c:
        c = c.replace(old, new)
        print(f'Replaced: {repr(old[:40])} -> {repr(new[:40])}')

# Also handle escaped unicode
c = c.replace('\\u201cwe beat the paper\\u201d', '\\u201cwe outperformed the original\\u201d')

open(p, 'w', encoding='utf-8', newline='').write(c)
try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    print(f'FAIL: {str(e)[:200]}')
