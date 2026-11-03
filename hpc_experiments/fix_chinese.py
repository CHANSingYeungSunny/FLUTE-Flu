import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# The problem: I used \\u6d88 (literal backslash-u) instead of actual Chinese chars
# Fix: replace all literal \uXXXX sequences with actual Unicode characters

for p in ['01_最终报告/_build2/dlv/text_progress.py',
          '01_最终报告/_build2/dlv/text_ieee.py',
          '01_最终报告/_build2/dlv/text_internal.py']:
    c = open(p, 'r', encoding='utf-8').read()
    
    # Find literal \uXXXX sequences and replace with actual characters
    import re
    def replace_unicode_escapes(text):
        def replacer(m):
            code = m.group(1)
            try:
                return chr(int(code, 16))
            except:
                return m.group()
        # Match \uXXXX (literal backslash-u-hex)
        return re.sub(r'\\u([0-9a-fA-F]{4})', replacer, text)
    
    c_fixed = replace_unicode_escapes(c)
    
    if c_fixed != c:
        open(p, 'w', encoding='utf-8', newline='').write(c_fixed)
        print(f'{p.split("/")[-1]}: fixed Unicode escapes')
    else:
        print(f'{p.split("/")[-1]}: no literal \\u escapes found')
    
    py_compile.compile(p, doraise=True)

print('\nAll compile OK')
