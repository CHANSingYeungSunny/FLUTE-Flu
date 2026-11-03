import sys, os
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
from docx import Document

p = r'01_最终报告\report_internal_zh.docx'
d = Document(p)

# Check all text including tables
all_text = []
for para in d.paragraphs:
    all_text.append(para.text)
for t in d.tables:
    for row in t.rows:
        for cell in row.cells:
            all_text.append(cell.text)
full = '\n'.join(all_text)

checks = {
    '复现：本文 vs 原论文/仓库': '复现对比表标题',
    '基准协议：本文 vs 原论文': '基准对比表标题',
    '模型家族': '模型家族概述',
    '线性': 'Linear family',
    'Transformer': 'Transformer family',
    '冻结 LLM 编码器': 'Frozen LLM encoders',
    'ILITOTAL': 'ILITOTAL explanation',
    '283,650': 'scale difference',
    'PTE': 'PTE definition',
    'PIE': 'PIE definition',
    'Kramer': 'K&S citation',
    'to verify': 'verify flag',
    'DEVIATION': 'deviation marker',
    '1.542': 'paper MSE',
    '1.4995': 'our MSE',
    '0.7482': 'MAE',
    '60/60': 'Table VIII',
    'Pareto': 'Pareto',
    'T = 104': 'horizon def',
}

print(f'Tables: {len(d.tables)}')
for i, t in enumerate(d.tables):
    headers = [c.text[:15] for c in t.rows[0].cells]
    print(f'  Table {i}: {headers[:4]}')

print(f'\nContent checks:')
for k, v in checks.items():
    ok = k in full
    print(f'  {v:30s}: {"YES" if ok else "MISSING"}')

# Count repro_params occurrences
count = full.count('复现：本文 vs 原论文')
print(f'\n复现对比表出现次数: {count} (should be 1)')
