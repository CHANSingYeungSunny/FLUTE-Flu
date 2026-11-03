import sys, os, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

for root, dirs, files in os.walk('01_最终报告/_build2'):
    for f in files:
        if f.endswith('.py') or f.endswith('.json'):
            fp = os.path.join(root, f)
            c = open(fp, 'r', encoding='utf-8', errors='replace').read()
            if 'beat the paper' in c or 'beat the ' in c and 'paper' in c:
                for m in re.finditer(r'.{0,60}beat.{0,60}paper.{0,60}', c, re.IGNORECASE | re.DOTALL):
                    print(f'{fp}: {repr(m.group()[:150])}')

# Also check dlv/data.py
print('\n=== checking data.py ===')
c = open('01_最终报告/_build2/dlv/data.py', 'r', encoding='utf-8').read()
if 'beat' in c:
    for m in re.finditer(r'.{0,60}beat.{0,60}', c, re.IGNORECASE):
        print(f'  {repr(m.group()[:120])}')
