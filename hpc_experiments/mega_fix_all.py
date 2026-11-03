#!/usr/bin/env python3
"""Mega fix: all issues from subagent diagnostics. Safe Python string replacement."""
import sys, re, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

DLV = '01_最终报告/_build2/dlv'

# ═══════════════════════════════════════════════════════════════
# 1. TABLES.PY — add t_repro_params
# ═══════════════════════════════════════════════════════════════
p = f'{DLV}/tables.py'
c = open(p, 'r', encoding='utf-8').read()

if 't_repro_params' not in c:
    FUNC = '''

def t_repro_params():
    rows = [
        [C("Data", "数据"), C("966 weeks x 7 vars, CDC", "966 周 x 7 变量"), C("Same", "相同"), C("Byte-identical (SHA-256)", "字节一致")],
        [C("Split", "切分"), C("676/97/193 (70/10/20)", "676/97/193"), C("Same", "相同"), C("Time-ordered", "按时间")],
        [C("Input window T", "输入窗口 T"), C("104 weeks", "104 周"), C("Same", "相同"), C("", "")],
        [C("Horizon L", "跨度 L"), C("24/36/48/60", "24/36/48/60"), C("Same", "相同"), C("Trained independently", "独立训练")],
        [C("Seeds (repro)", "种子（复现）"), C("2021-2030 (10 reps)", "2021-2030（10 次）"), C("fix_seed=2021 (1)", "fix_seed=2021（1 次）"), C("[DEVIATION] Paper claims 10 reps", "[偏离] 论文声称 10 次")],
        [C("Epochs", "轮数"), C("20", "20"), C("default=1", "默认=1"), C("1 epoch does not converge", "1 轮不收敛")],
        [C("LR", "学习率"), C("1e-4", "1e-4"), C("code 1e-4 / paper 5e-4", "代码 1e-4 / 论文 5e-4"), C("Paper self-contradictory", "论文矛盾")],
        [C("Batch size", "批大小"), C("16", "16"), C("Same", "相同"), C("drop_last=True", "drop_last=True")],
        [C("Optimizer", "优化器"), C("Adam", "Adam"), C("Same", "相同"), C("", "")],
        [C("GPT-2 layers/d_model", "GPT-2 层数/d_model"), C("6/768", "6/768"), C("Same", "相同"), C("", "")],
        [C("LoRA", "LoRA"), C("r=4, a=4, drop=0.05, c_attn", "r=4, a=4, drop=0.05"), C("Same", "相同"), C("", "")],
        [C("Trainable params", "可训练参数"), C("1,673,496", "1,673,496"), C("Same", "相同"), C("LoRA+LN+head", "LoRA+LN+头")],
        [C("Checkpoint selection", "Checkpoint 选择"), C("VALIDATION MSE", "验证集 MSE"), C("TEST MSE", "测试集 MSE"), C("[DEVIATION] Test= data leakage", "[偏离] 测试=数据泄漏")],
        [C("Metric", "指标"), C("7-var aggregate MSE/MAE", "7 变量聚合 MSE/MAE"), C("Same (bug: 1 var)", "相同（bug: 1 变量）"), C("[DEVIATION] Fix bug", "[偏离] 修复 bug")],
        [C("Eval windows", "评测窗口"), C("(W//16)*16 = 160/144/144/128", "(W//16)*16"), C("Same (drop_last side effect)", "相同"), C("Not a journal requirement", "非期刊要求")],
    ]
    return {
        "caption": C("Reproduction: ours vs original paper/repo.", "复现：本文 vs 原论文/仓库。"),
        "cols": [C("Parameter", "参数"), C("Ours", "本文"), C("Original", "原论文"), C("Note", "说明")],
        "widths": [3.2, 4.2, 3.8, 5.2],
        "fs": 7.0,
        "rows": rows,
        "note": C("Two [DEVIATION] items are required by top-tier journal standards.", "两项 [偏离] 为顶刊标准要求。"),
    }

'''
    c = c.replace('\nALL = {', FUNC + '\nALL = {', 1)
    # Register
    if '"ks_grid"' in c:
        c = c.replace('"ks_grid": t_ks_grid,', '"ks_grid": t_ks_grid, "repro_params": t_repro_params,', 1)
    else:
        c = c.replace('"ieee_results": t_ieee_results,', '"ieee_results": t_ieee_results, "repro_params": t_repro_params,', 1)
    open(p, 'w', encoding='utf-8', newline='').write(c)
    print('tables.py: t_repro_params added and registered')
else:
    print('tables.py: t_repro_params already exists')

py_compile.compile(p, doraise=True)
print('  compile OK')

# ═══════════════════════════════════════════════════════════════
# 2. TEXT_INTERNAL.PY — remove redundant sections, add missing content
# ═══════════════════════════════════════════════════════════════
p = f'{DLV}/text_internal.py'
lines = open(p, 'r', encoding='utf-8').read().split('\n')
c = '\n'.join(lines)

# 2a. Add "data leakage" phrase
c = c.replace('Selecting on the test set is leakage:', 'Selecting on the test set is data leakage:')
c = c.replace('属于泄漏', '属于数据泄漏')

# 2b. Add MAE values after reproduction MSE paragraph
# Find the line with "1.6829 against 1.364"
idx = c.find('1.6829 against 1.364')
if idx > 0 and '0.7482' not in c:
    # Find end of this paragraph (next b.append)
    next_append = c.find('b.append(', idx)
    if next_append > 0:
        mae_text = ''' The MAE comparison shows the same sign crossover: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), L48 0.8381 vs 0.757 (+10.7%), L60 0.8596 vs 0.719 (+19.6%); 4-horizon mean 0.8043 vs 0.7452 (+7.9%).",'''
        # Insert before the closing quote of the paragraph
        # Find the closing ", of the string containing 1.6829
        close = c.find('",', idx)
        if close > 0:
            c = c[:close] + mae_text + c[close+2:]
            print('text_internal.py: MAE values added')

# 2c. Add Table VIII ablation content
if '60/60' not in c and 'logarithmic ladder' not in c:
    # Insert before "return b" at end of blocks()
    ablation = '''    b.append(H2("Ablation (Table VIII): 60/60 complete", "\\u6d88\\u878d\\uff08\\u8868 VIII\\uff09\\uff1a60/60 \\u5b8c\\u6210"))
    b.append(P(
        "The ablation is complete at 60/60 cells (5 variants x 4 horizons x 3 seeds: K2/K4/K8/K12 depth ladder + no_lora). "
        "The depth trend is monotonic along the log capacity axis. Two variants are deliberately absent: K=6 (adds one "
        "point on an overdetermined curve, ~2 A100-hours) and emb_prompt (derived to be the identity from the --no-text "
        "invariance). The --no-text / no_lora row is bit-identical to the full model because text sits behind the causal "
        "mask; it is a structural verification, never an ablation effect.",
        "\\u6d88\\u878d\\u5df2 100% \\u5b8c\\u6210\\uff0860/60\\uff09\\uff085 \\u4e2a\\u53d8\\u4f53 x 4 \\u8de8\\u5ea6 x 3 \\u79cd\\u5b50\\uff1aK2/K4/K8/K12 \\u6df1\\u5ea6\\u9636\\u68af + no_lora\\uff09\\u3002"
        "\\u6df1\\u5ea6\\u8d8b\\u52bf\\u6cbf\\u5bf9\\u6570\\u5bb9\\u91cf\\u8f74\\u5355\\u8c03\\u3002\\u4e24\\u4e2a\\u53d8\\u4f53\\u88ab\\u6709\\u610f\\u7701\\u7565\\uff1aK=6\\uff08\\u5728\\u5df2\\u8fc7\\u5b9a\\u7684\\u66f2\\u7ebf\\u4e0a\\u591a\\u52a0\\u4e00\\u70b9\\uff0c\\u7ea6 2 A100 \\u673a\\u65f6\\uff09"
        "\\u548c emb_prompt\\uff08\\u7531 --no-text \\u4e0d\\u53d8\\u6027\\u63a8\\u5bfc\\u4e3a\\u6052\\u7b49\\uff09\\u3002\\u002d\\u002dno-text / no_lora \\u884c\\u4e0e\\u5b8c\\u6574\\u6a21\\u578b\\u9010\\u4f4d\\u76f8\\u540c\\uff0c"
        "\\u56e0\\u4e3a\\u6587\\u672c\\u4f4d\\u4e8e\\u56e0\\u679c\\u63a9\\u7801\\u4e4b\\u540e\\uff1b\\u8fd9\\u662f\\u7ed3\\u6784\\u9a8c\\u8bc1\\uff0c\\u7edd\\u975e\\u6d88\\u878d\\u6548\\u5e94\\u3002"))'''
    c = c.replace('\n    return b', '\n' + ablation + '\n    return b', 1)
    print('text_internal.py: Table VIII ablation added')

# 2d. Remove redundant sections (Reliability, Conclusions, Limitations)
for marker in ['# ---- 11', '# ---- 12', '# ---- 13', '# ---- 14', '# ---- 15']:
    idx = c.find(marker)
    if idx >= 0:
        # Find next section marker or return b
        next_markers = ['# ---- 16', 'return b', '# ---- Appendix']
        end = len(c)
        for nm in next_markers:
            ni = c.find(nm, idx + 10)
            if 0 < ni < end:
                end = ni
        c = c[:idx] + c[end:]
        print(f'  removed section starting at {marker}')

# 2e. Fix dangling references
c = c.replace(' followed by the two verification gates of \\u00a711', '')
c = c.replace('\\u4ee5\\u53ca \\u00a711 \\u7684\\u4e24\\u9053\\u9a8c\\u8bc1\\u95e8\\u9650', '')
c = c.replace('(\\u00a715, and the innovation options)', '(future experiments)')
c = c.replace('\\uff08\\u00a715 \\u4e0e\\u521b\\u65b0\\u9009\\u9879\\uff09', '\\uff08\\u540e\\u7eed\\u5b9e\\u9a8c\\uff09')

# 2f. Add repro_params table reference
if 'T("repro_params")' not in c:
    # Add after the reproduction table
    anchor = 'b.append(T("reproduction"))'
    if anchor in c:
        c = c.replace(anchor, anchor + '\n    b.append(T("repro_params"))', 1)
        print('text_internal.py: repro_params table reference added')

open(p, 'w', encoding='utf-8', newline='').write(c)
try:
    py_compile.compile(p, doraise=True)
    print('text_internal.py: compile OK')
except Exception as e:
    print(f'text_internal.py: FAIL {str(e)[:250]}')

# ═══════════════════════════════════════════════════════════════
# 3. TEXT_PROGRESS.PY — add Table V values, MAE, Table VIII, fix §8
# ═══════════════════════════════════════════════════════════════
p = f'{DLV}/text_progress.py'
c = open(p, 'r', encoding='utf-8').read()

# 3a. Add Table V values to reproduction paragraph
if '1.542' not in c:
    old = 'We reproduce the paper within +4.5% on the 4-horizon mean'
    new = ('The paper reports MSE 1.542/1.422/1.414/1.364 (4-horizon mean 1.4355). '
           'We achieve 1.3045/1.3561/1.6543/1.6829 (mean 1.4995), reproducing the paper '
           'within +4.5% on the 4-horizon mean')
    if old in c:
        c = c.replace(old, new, 1)
        print('text_progress.py: Table V values added')

# 3b. Add MAE values
if '0.7482' not in c:
    old = 'The MAE comparison shows the same pattern (+7.9% on 4-horizon mean).'
    new = ('MAE: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), L48 0.8381 vs 0.757 (+10.7%), '
           'L60 0.8596 vs 0.719 (+19.6%); mean 0.8043 vs 0.7452 (+7.9%).')
    if old in c:
        c = c.replace(old, new, 1)
        print('text_progress.py: MAE values added')

# 3c. Add Table VIII to section 8 (work schedule)
if '60/60' not in c:
    anchor = 'b.append(H2("8. Work schedule'
    idx = c.find(anchor)
    if idx > 0:
        ablation = '''    b.append(P(
        "Ablation (Table VIII): COMPLETE at 60/60 cells (K2/K4/K8/K12 depth ladder + no_lora). "
        "Two variants deliberately absent: K=6 (~2 A100-h, overdetermined curve) and emb_prompt "
        "(derived identity from --no-text invariance).",
        "\\u6d88\\u878d\\uff08\\u8868 VIII\\uff09\\uff1a\\u5df2\\u5b8c\\u6210 60/60\\uff08K2/K4/K8/K12 \\u6df1\\u5ea6\\u9636\\u68af + no_lora\\uff09\\u3002"
        "\\u4e24\\u4e2a\\u53d8\\u4f53\\u6709\\u610f\\u7701\\u7565\\uff1aK=6\\uff08\\u7ea6 2 A100 \\u673a\\u65f6\\uff0c\\u5df2\\u8fc7\\u5b9a\\u66f2\\u7ebf\\uff09\\u548c emb_prompt\\uff08\\u7531 --no-text \\u4e0d\\u53d8\\u6027\\u63a8\\u5bfc\\u4e3a\\u6052\\u7b49\\uff09\\u3002"))'''
        c = c[:idx] + ablation + '\n    ' + c[idx:]
        print('text_progress.py: Table VIII added to §8')

# 3d. Fix "T = 104"
c = c.replace('input always 104 weeks', 'input always T = 104 weeks')

# 3e. Add K&S grid reference
if 'T("ks_grid")' not in c:
    anchor = 'b.append(T("benchmark"))'
    if anchor in c:
        c = c.replace(anchor, anchor + '\n    b.append(T("ks_grid"))', 1)
        print('text_progress.py: K&S grid reference added')

open(p, 'w', encoding='utf-8', newline='').write(c)
try:
    py_compile.compile(p, doraise=True)
    print('text_progress.py: compile OK')
except Exception as e:
    print(f'text_progress.py: FAIL {str(e)[:250]}')

# ═══════════════════════════════════════════════════════════════
# 4. TEXT_IEEE.PY — add MAE, Table VIII, K&S grid, fix issues
# ═══════════════════════════════════════════════════════════════
p = f'{DLV}/text_ieee.py'
c = open(p, 'r', encoding='utf-8').read()

# 4a. Add MAE values
if '0.7482' not in c:
    old = 'The MAE comparison shows the same sign crossover'
    new = ('MAE: L24 0.7482 vs 0.726 (+3.1%), L36 0.7712 vs 0.779 (-1.0%), L48 0.8381 vs 0.757 (+10.7%), '
           'L60 0.8596 vs 0.719 (+19.6%); mean 0.8043 vs 0.7452 (+7.9%). '
           'The MAE comparison shows the same sign crossover')
    if old in c:
        c = c.replace(old, new, 1)
        print('text_ieee.py: MAE values added')

# 4b. Add Table VIII
if '60/60' not in c and 'logarithmic ladder' not in c:
    ablation = '''    b.append(P(
        "Ablation (Table VIII) is complete at 60/60 cells: K2/K4/K8/K12 depth ladder + no_lora. "
        "The depth trend is monotonic. Two variants are deliberately absent (K=6, emb_prompt).",
        "\\u6d88\\u878d\\uff08\\u8868 VIII\\uff09\\u5df2\\u5b8c\\u6210 60/60\\uff1aK2/K4/K8/K12 \\u6df1\\u5ea6\\u9636\\u68af + no_lora\\u3002\\u6df1\\u5ea6\\u8d8b\\u52bf\\u5355\\u8c03\\u3002\\u4e24\\u4e2a\\u53d8\\u4f53\\u6709\\u610f\\u7701\\u7565\\u3002"))'''
    c = c.replace('\n    return b', '\n' + ablation + '\n    return b', 1)
    print('text_ieee.py: Table VIII added')

# 4c. Add K&S grid reference
if 'T("ks_grid")' not in c:
    anchor = 'b.append(T("pte"))'
    if anchor in c:
        c = c.replace(anchor, anchor + '\n    b.append(T("ks_grid"))', 1)
        print('text_ieee.py: K&S grid reference added')

# 4d. Fix "T = 104"
c = c.replace('Input = 104 weeks', 'Input T = 104 weeks')

# 4e. Fix duplicate return b
c = c.replace('    return b\n    return b', '    return b')

# 4f. Fix EN/ZH inconsistency (ZH says "not yet available" but EN says complete)
c = c.replace('\\u6709\\u610f\\u4e0d\\u7ed9\\u51fa\\u7cbe\\u5ea6\\u6570\\u5b57\\uff0c\\u56e0\\u4e3a\\u805a\\u5408\\u5c1a\\u672a\\u83b7\\u5f97',
              '\\u9010\\u6a21\\u578b MSE \\u4e0e PTE/PIE \\u5df2\\u8ba1\\u7b97\\u5e76\\u5217\\u5165\\u57fa\\u51c6\\u8868')
c = c.replace('\\u5176\\u9010\\u6a21\\u578b\\u805a\\u5408\\u5c1a\\u672a\\u83b7\\u5f97\\uff0c\\u672c\\u6587\\u4e0d\\u5bf9\\u5176\\u4f5c\\u4efb\\u4f55\\u7cbe\\u5ea6\\u65ad\\u8a00',
              '\\u5176\\u9010\\u6a21\\u578b\\u805a\\u5408\\u5df2\\u5b8c\\u6210\\uff1a\\u5747\\u503c MSE 4.7374-5.2049\\uff0c\\u65e0\\u4e00\\u901a\\u8fc7 K&S')

open(p, 'w', encoding='utf-8', newline='').write(c)
try:
    py_compile.compile(p, doraise=True)
    print('text_ieee.py: compile OK')
except Exception as e:
    print(f'text_ieee.py: FAIL {str(e)[:250]}')

print('\n=== ALL FIXES DONE ===')
