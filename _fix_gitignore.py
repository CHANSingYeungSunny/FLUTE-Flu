import sys, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '.gitignore'
c = open(p, 'r', encoding='utf-8', errors='replace').read()

# 1. Fix mojibake lines at the bottom (replace the corrupted block)
lines = c.split('\n')
fixed_lines = []
for line in lines:
    if '?蝏??' in line or '_build/' in line or '.dsh-office-' in line or '_build2/verify/' in line:
        # Skip corrupted lines, we'll re-add corrected versions
        continue
    fixed_lines.append(line)

c = '\n'.join(fixed_lines).rstrip() + '\n'

# 2. Append correct rules
c += '''
# --- Corrected document-build paths (mojibake fix 2026-11-03) ---
01_最终报告/_build/
01_最终报告/.dsh-office-*/
01_最终报告/_build2/verify/

# --- Large artefacts NOT for git (GitHub 100MB/file limit) ---
# built packages (deliver as files, not via git)
*.zip
# raw prediction arrays + their large CSV twins (keep npz locally, too big for git)
03_预测数据_证据/expanded_runs/**/predictions_*.csv
03_预测数据_证据/*.tgz
03_预测数据_证据/**/*.tgz
# archive folder entirely excluded
99_旧文件存档/
# memory/runtime caches
__pycache__/
*.pyc
'''

open(p, 'w', encoding='utf-8', newline='').write(c)
print('gitignore fixed and extended')
print(f'Total lines: {len(c.split(chr(10)))}')
