import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_ieee.py'
c = open(p, 'r', encoding='utf-8').read()

if '0.7482' not in c:
    # Find the reproduction paragraph and add MAE
    old = 'The MAE comparison shows the same sign crossover'
    new = ('MAE: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), L48 0.8381 vs 0.757 (+10.7%), '
           'L60 0.8596 vs 0.719 (+19.6%); mean 0.8043 vs 0.7452 (+7.9%). '
           'The MAE comparison shows the same sign crossover')
    if old in c:
        c = c.replace(old, new, 1)
        print('MAE added to text_ieee.py')
    else:
        # Try different anchor
        old2 = 'reproduced within 4.5 % on the 4-horizon mean'
        idx = c.find(old2)
        if idx > 0:
            # Find end of this sentence
            period = c.find('. ', idx + len(old2))
            if period > 0:
                mae = ' MAE: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), L48 0.8381 vs 0.757 (+10.7%), L60 0.8596 vs 0.719 (+19.6%); mean 0.8043 vs 0.7452 (+7.9%).'
                c = c[:period] + mae + c[period:]
                print('MAE added (alternative anchor)')
else:
    print('MAE already present')

open(p, 'w', encoding='utf-8', newline='').write(c)
py_compile.compile(p, doraise=True)
print('compile OK')
