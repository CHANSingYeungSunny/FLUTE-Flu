import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# ═══ 1. Fix text_internal.py indentation ═══
p = '01_最终报告/_build2/dlv/text_internal.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')

for i, l in enumerate(lines):
    stripped = l.strip()
    if stripped.startswith('b.append(') and not l.startswith('    ') and stripped:
        lines[i] = '    ' + stripped

open(p, 'w', encoding='utf-8', newline='').write('\n'.join(lines))
try:
    py_compile.compile(p, doraise=True)
    print('text_internal.py: compile OK')
except Exception as e:
    print(f'text_internal.py: FAIL {str(e)[:200]}')

# ═══ 2. Expand text_progress.py to be COMPREHENSIVE (all semester progress) ═══
p2 = '01_最终报告/_build2/dlv/text_progress.py'
c2 = open(p2, 'r', encoding='utf-8').read()

# Check current size
print(f'\ntext_progress.py: {len(c2)} chars')

# The progress report should have ALL progress. Let me check what sections exist.
import re
for m in re.finditer(r'b\.append\(H([12])\("([^"]+)"', c2):
    print(f'  H{m.group(1)}: {m.group(2)[:60]}')
