import sys, re
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
c = open(p, 'r', encoding='utf-8').read()

print(f'Total chars: {len(c)}')

# Count chars per section
sections = []
for m in re.finditer(r'b\.append\(H([12])\("([^"]+)"', c):
    sections.append((m.start(), 'H'+m.group(1), m.group(2)[:60]))

for i, (pos, level, title) in enumerate(sections):
    end = sections[i+1][0] if i+1 < len(sections) else len(c)
    chars = end - pos
    print(f'  {level} {title:60s} {chars:6d} chars')

# Count paragraph blocks
paras = c.count('b.append(P(')
tables = c.count('b.append(T(')
figs = c.count('b.append(FIG(')
print(f'\nParagraphs: {paras}, Tables: {tables}, Figures: {figs}')
