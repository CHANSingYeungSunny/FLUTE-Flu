import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_ieee.py'
c = open(p, 'r', encoding='utf-8').read()

# Replace "we beat the paper" with neutral phrasing that passes the check
c = c.replace('never \\u201cwe beat the paper\\u201d', 'never claim superiority over the original')
c = c.replace('never "we beat the paper"', 'never claim superiority over the original')
c = c.replace('\\u7edd\\u4e0d\\u8bf4\\u201c\\u6211\\u4eec\\u6253\\u8d25\\u4e86\\u8bba\\u6587\\u201d', '\\u7edd\\u4e0d\\u5ba3\\u79f0\\u4f18\\u4e8e\\u539f\\u8bba\\u6587')
c = c.replace('never \\u201cwe beat the paper\\u201d', 'never claim superiority over the original')

# Also fix the specific sentence pattern
c = c.replace('never \\u201cwe beat the paper\\u201d.', 'never claim superiority over the original.')

open(p, 'w', encoding='utf-8', newline='').write(c)
try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    print(f'FAIL: {str(e)[:200]}')

# Also check text_internal.py for same issue
p2 = '01_最终报告/_build2/dlv/text_internal.py'
c2 = open(p2, 'r', encoding='utf-8').read()
if 'we beat the paper' in c2 or '\\u6211\\u4eec\\u6253\\u8d25\\u4e86\\u8bba\\u6587' in c2:
    c2 = c2.replace('never \\u201cwe beat the paper\\u201d', 'never claim superiority over the original')
    c2 = c2.replace('never "we beat the paper"', 'never claim superiority over the original')
    c2 = c2.replace('\\u7edd\\u4e0d\\u8bf4\\u201c\\u6211\\u4eec\\u6253\\u8d25\\u4e86\\u8bba\\u6587\\u201d', '\\u7edd\\u4e0d\\u5ba3\\u79f0\\u4f18\\u4e8e\\u539f\\u8bba\\u6587')
    open(p2, 'w', encoding='utf-8', newline='').write(c2)
    print('text_internal.py: fixed')
else:
    print('text_internal.py: no issue')

# Also check text_progress.py
p3 = '01_最终报告/_build2/dlv/text_progress.py'
c3 = open(p3, 'r', encoding='utf-8').read()
if 'we beat the paper' in c3 or '\\u6211\\u4eec\\u6253\\u8d25\\u4e86\\u8bba\\u6587' in c3:
    c3 = c3.replace('never \\u201cwe beat the paper\\u201d', 'never claim superiority over the original')
    c3 = c3.replace('never "we beat the paper"', 'never claim superiority over the original')
    c3 = c3.replace('\\u7edd\\u4e0d\\u8bf4\\u201c\\u6211\\u4eec\\u6253\\u8d25\\u4e86\\u8bba\\u6587\\u201d', '\\u7edd\\u4e0d\\u5ba3\\u79f0\\u4f18\\u4e8e\\u539f\\u8bba\\u6587')
    open(p3, 'w', encoding='utf-8', newline='').write(c3)
    print('text_progress.py: fixed')
else:
    print('text_progress.py: no issue')
