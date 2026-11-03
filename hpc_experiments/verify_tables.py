import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document

d = Document(r'01_最终报告/report_internal_zh.docx')
print(f'Tables in doc: {len(d.tables)}')
for i, t in enumerate(d.tables):
    headers = [c.text[:20] for c in t.rows[0].cells]
    print(f'  Table {i}: {headers[:5]}')

txt = '\n'.join(p.text for p in d.paragraphs)
checks = ['复现设置', '原论文', '[DEVIATION]', 'Checkpoint', '验证集', '测试集', 'data leakage', 'repro_params']
for k in checks:
    found = k in txt
    print(f'  {k}: {"YES" if found else "NO"}')

# Also check for us-vs-essay table content
for t in d.tables:
    for row in t.rows:
        for cell in row.cells:
            if 'Checkpoint' in cell.text or '验证集' in cell.text:
                print(f'  FOUND us-vs-essay table row: {cell.text[:50]}')
                break
