import sys, re, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
c = open(p, 'r', encoding='utf-8').read()

# 1. Ensure repro_params table is rendered after reproduction table
if 'T("repro_params")' in c:
    # Check if it's actually after T("reproduction")
    idx_repro = c.find('T("reproduction")')
    idx_params = c.find('T("repro_params")')
    if idx_params > 0 and idx_repro > 0 and idx_params < idx_repro:
        print('repro_params is BEFORE reproduction — reordering')
        # Move it after
        line_params = c.rfind('b.append(', 0, idx_params)
        end_params = c.find('\n', idx_params)
        params_block = c[line_params:end_params]
        c = c[:line_params] + c[end_params:]
        # Insert after reproduction
        idx_repro2 = c.find('T("reproduction")')
        end_repro = c.find('\n', idx_repro2)
        c = c[:end_repro] + '\n' + params_block + c[end_repro:]
    else:
        print(f'repro_params at {idx_params}, reproduction at {idx_repro} — order OK')
else:
    # Add it
    anchor = 'b.append(T("reproduction"))'
    if anchor in c:
        c = c.replace(anchor, anchor + '\n    b.append(T("repro_params"))', 1)
        print('repro_params table reference added')

# 2. Remove Appendix A content (the figure list, keep definitions)
# Find "# ---- Appendix A" or "Appendix A" comment block
idx = c.find('Appendix A')
if idx > 0:
    # Find the start of the block
    block_start = c.rfind('# ----', 0, idx)
    if block_start < 0:
        block_start = c.rfind('b.append(PB)', 0, idx)
    # Find where definitions start (keep those)
    defs_start = c.find('Definitions and notation', idx)
    if defs_start > 0:
        # Remove from block_start to defs_start
        c = c[:block_start] + c[defs_start:]
        print(f'Removed Appendix A content (lines {block_start}-{defs_start})')

# 3. Remove verbose sections if they exist
for marker in ['# ---- 11', '# ---- 12', '# ---- 13', '# ---- 14', '# ---- 15']:
    idx = c.find(marker)
    if idx >= 0:
        # Find next section
        next_h1 = c.find('b.append(H1("', idx + 10)
        next_return = c.find('\n    return b', idx)
        end = min(x for x in [next_h1, next_return] if x > 0)
        if end > 0:
            c = c[:idx] + c[end:]
            print(f'Removed section at {marker}')

# 4. Add us-vs-essay comparison paragraph BEFORE the repro_params table
if 'repro_params' in c and 'us vs' not in c.lower()[:5000]:
    # Find repro_params table call
    idx = c.find('b.append(T("repro_params"))')
    if idx > 0:
        para = '''    b.append(P(
        "The table below compares our reproduction settings against the original paper/repository "
        "side by side. Two deliberate deviations are marked [DEVIATION]: checkpoint selection "
        "(validation vs test) and the 7-variable metric (fixing the test-loader bug).",
        "下表逐项对比我们的复现设置与原论文/仓库。两处故意偏离标记为 [DEVIATION]：检查点选择"
        "（验证集 vs 测试集）和 7 变量指标（修复 test-loader bug）。"))
'''
        c = c[:idx] + para + c[idx:]
        print('Added us-vs-essay intro paragraph')

open(p, 'w', encoding='utf-8', newline='').write(c)
py_compile.compile(p, doraise=True)
print('compile OK')
