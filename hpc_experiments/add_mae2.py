import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_ieee.py'
c = open(p, 'r', encoding='utf-8').read()

# Find the reproduction results paragraph and add MAE
# Look for "1.4995" or "1.4355" which are in the reproduction section
for anchor in ['1.4995', '1.4355', '4-horizon mean', 'four-horizon mean']:
    idx = c.find(anchor)
    if idx > 0:
        print(f'Found anchor "{anchor}" at {idx}')
        # Find the end of the sentence
        period = c.find('. ', idx)
        if period > 0 and period - idx < 500:
            mae = ' MAE: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), L48 0.8381 vs 0.757 (+10.7%), L60 0.8596 vs 0.719 (+19.6%); mean 0.8043 vs 0.7452 (+7.9%).'
            c = c[:period] + mae + c[period:]
            print('MAE inserted')
            break

open(p, 'w', encoding='utf-8', newline='').write(c)
py_compile.compile(p, doraise=True)
print('compile OK')
print('0.7482 now in file:', '0.7482' in open(p, 'r', encoding='utf-8').read())
