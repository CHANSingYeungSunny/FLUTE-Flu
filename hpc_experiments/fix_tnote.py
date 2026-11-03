import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/tables.py'
c = open(p, 'r', encoding='utf-8').read()

# Fix "we beat the paper" -> neutral phrasing
c = c.replace('never \u201cwe beat the paper\u201d', 'never claim superiority over the original')
c = c.replace('never "we beat the paper"', 'never claim superiority over the original')
c = c.replace('never \u201cwe beat the "\n                  "paper\u201d', 'never claim superiority over the original')

# Fix the specific multi-line string
old = '— never “we beat the "\n                  "paper”. The aggregate MAE for L48/L60 is not in the pulled artefact set (only the per-repetition "\n                  "prediction CSVs survive locally), so the 4-horizon MAE mean 0.7597 covers L24/L36 only and is marked "\n                  "partial.'
new = '— never claim superiority over the original. MAE: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), "\n                  "L48 0.8381 vs 0.757 (+10.7%), L60 0.8596 vs 0.719 (+19.6%); mean 0.8043 vs 0.7452 (+7.9%).'
if old in c:
    c = c.replace(old, new, 1)
    print('tables.py: reproduction note fixed (beat + MAE)')
else:
    # Try simpler replacement
    c = c.replace('never \u201cwe beat the "\n                  "paper\u201d', 'never claim superiority over the original')
    print('tables.py: simpler replacement applied')

# Also fix text_internal.py
p2 = '01_最终报告/_build2/dlv/text_internal.py'
c2 = open(p2, 'r', encoding='utf-8').read()
c2 = c2.replace('It is not \u201cwe beat the paper\u201d', 'It is not a claim of superiority over the original')
c2 = c2.replace('It is not "we beat the paper"', 'It is not a claim of superiority over the original')
c2 = c2.replace('\u8fd9\u4e0d\u662f\u201c\u6211\u4eec\u8d85\u8fc7\u4e86\u8bba\u6587\u201d', '\u8fd9\u4e0d\u662f\u201c\u6211\u4eec\u4f18\u4e8e\u539f\u8bba\u6587\u201d')
open(p2, 'w', encoding='utf-8', newline='').write(c2)
print('text_internal.py: fixed')

# Verify no more "beat the paper"
for f in [p, p2]:
    cc = open(f, 'r', encoding='utf-8').read()
    if 'beat the paper' in cc or 'beat the "\n                  "paper' in cc:
        print(f'WARNING: still has beat-the-paper in {f}')
    else:
        print(f'OK: {f.split("/")[-1]} clean')

for f in [p, p2]:
    py_compile.compile(f, doraise=True)
print('All compile OK')
