import sys, os, shutil, time
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

ROOT = r"c:\Users\Asus\Desktop\FYP code\MLFlu"
ARCH = os.path.join(ROOT, "99_旧文件存档", "loose_files")
os.makedirs(ARCH, exist_ok=True)

# Clean up temp scripts
for f in os.listdir(ROOT):
    if f.startswith('_') and f.endswith('.py'):
        p = os.path.join(ROOT, f)
        if os.path.isfile(p):
            shutil.move(p, os.path.join(ARCH, f))
            print(f'  archived: {f}')

# Check zip
z = os.path.join(ROOT, "01_最终报告", "PROJECT_HANDOFF.zip")
sz = os.path.getsize(z)
print(f'\nZIP: {sz//1024//1024} MB, Modified: {time.ctime(os.path.getmtime(z))}')

# Verify key content in docs
from docx import Document
for name in ['report_internal_en', 'progress_report_en', 'ieee_manuscript_en']:
    d = Document(os.path.join(ROOT, '01_最终报告', f'{name}.docx'))
    txt = '\n'.join(p.text for p in d.paragraphs)
    checks = {
        '1.542': 'paper L24',
        '1.4995': 'our mean',
        '0.7482': 'MAE L24',
        '60/60': 'Table VIII',
        'Kramer': 'K&S citation',
        'to verify': 'K&S flag',
        'Pareto': 'Pareto',
        'T = 104': 'horizon def',
    }
    results = []
    for k, v in checks.items():
        ok = k in txt
        results.append(f'{v}:{"Y" if ok else "N"}')
    print(f'  {name}: {" ".join(results)}')

print('\n=== DONE ===')
