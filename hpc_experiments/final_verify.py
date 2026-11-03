import sys, os, shutil, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r"c:\Users\Asus\Desktop\FYP code\MLFlu"
ARCH = os.path.join(ROOT, "99_旧文件存档", "loose_files")

# Clean temp scripts
for f in os.listdir(ROOT):
    if f.startswith('_') and f.endswith('.py'):
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            shutil.move(p, os.path.join(ARCH, f))

# Verify deliverables
z = os.path.join(ROOT, "01_最终报告", "PROJECT_HANDOFF.zip")
sz = os.path.getsize(z)
print(f'ZIP: {sz//1024//1024} MB, Modified: {time.ctime(os.path.getmtime(z))}')

# Check key content
from docx import Document
for name in ['report_internal_zh', 'progress_report_zh', 'ieee_manuscript_zh']:
    d = Document(os.path.join(ROOT, '01_最终报告', f'{name}.docx'))
    txt = '\n'.join(p.text for p in d.paragraphs)
    tables = len(d.tables)
    checks = {
        '1.542': '论文值',
        '1.4995': '复现值',
        '0.7482': 'MAE',
        '60/60': 'Table VIII',
        'Kramer': 'K&S引用',
        'to verify': '核实标记',
        'Pareto': 'Pareto',
        'T = 104': '跨度定义',
        'DEVIATION': '偏离标注',
    }
    results = []
    for k, v in checks.items():
        ok = k in txt
        results.append(f'{v}:{"Y" if ok else "N"}')
    print(f'  {name}: {tables} tables | {" ".join(results)}')

print('\n=== FINAL DELIVERABLES ===')
for f in sorted(os.listdir(os.path.join(ROOT, '01_最终报告'))):
    if f.endswith(('.docx', '.pdf', '.zip', '.md')):
        sz = os.path.getsize(os.path.join(ROOT, '01_最终报告', f))
        print(f'  {f} ({sz:,} bytes)')
