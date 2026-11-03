import sys, re, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
c = open(p, 'r', encoding='utf-8').read()

print(f'Before: {len(c)} chars')

# ── Strategy: remove/condense verbose sections, keep results ──

# 1. REMOVE Section 4 (Data) — replace with 2-sentence summary
sec4_start = c.find('b.append(H1("4. Data"')
sec4_end = c.find('b.append(H1("5. Methodology"')
if sec4_start > 0 and sec4_end > 0:
    summary = '''    b.append(H1("4. Data", "4. 数据"))
    b.append(P(
        "CDC national influenza data: 966 weekly rows x 7 channels, bit-identical to the author's file. "
        "Split: 676/97/193 (70/10/20), time-ordered. Normalised with StandardScaler on train only.",
        "CDC 全国流感数据：966 周 x 7 通道，与作者文件逐字节相同。切分：676/97/193（70/10/20），按时间序。仅在训练段拟合 StandardScaler。"))
'''
    c = c[:sec4_start] + summary + c[sec4_end:]
    print('Section 4: condensed from 4084 to ~300 chars')

# 2. CONDENSE Section 5 (Methodology) — keep only key points
sec5_start = c.find('b.append(H1("5. Methodology"')
sec5_end = c.find('b.append(H1("6. Reproduction')
if sec5_start > 0 and sec5_end > 0:
    condensed = '''    b.append(H1("5. Methodology", "5. 方法"))
    b.append(P(
        "Two protocols, never mixed. (1) Reproduction: 10 seeds (2021-2030), validation-selected checkpoint, "
        "7-variable z-space MSE — for comparing with the paper's Table V. (2) Benchmark: 3 seeds (42/43/44), "
        "shared windows (W//16)*16 = 160/144/144/128 — for comparing 28 models. Two deliberate deviations "
        "[DEVIATION]: checkpoint selection (validation vs test = data leakage fix) and 7-variable metric "
        "(fixing test-loader bug). Eval windows: NOT a journal requirement — side effect of batch_size=16, drop_last=True.",
        "两套协议，从不混用。(1) 复现：10 种子（2021-2030），验证集选检查点，7 变量 z 空间 MSE——与论文 Table V 对比。"
        "(2) 基准：3 种子（42/43/44），共享窗口 (W//16)*16 = 160/144/144/128——28 模型互比。两处故意偏离 [DEVIATION]："
        "检查点选择（验证集 vs 测试集 = 修复数据泄漏）和 7 变量指标（修复 test-loader bug）。评测窗口：非期刊要求，"
        "是 batch_size=16, drop_last=True 的副作用。"))
    b.append(T("repro_params"))
'''
    c = c[:sec5_start] + condensed + c[sec5_end:]
    print('Section 5: condensed from 12000 to ~800 chars')

# 3. CONDENSE Section 10 (LLM encoders) — keep only conclusion
sec10_start = c.find('b.append(H1("10. Frozen LLM')
sec10_end = c.find('b.append(H1("16.')
if sec10_start > 0 and sec10_end > 0:
    condensed = '''    b.append(H1("10. Frozen LLM encoders", "10. 冻结 LLM 编码器"))
    b.append(P(
        "11 frozen LLM encoders (Qwen2.5, DeepSeek-R1, Tencent Hunyuan/ContextPilot) + shared linear head. "
        "Result: ALL perform poorly. Best Hunyuan-1.8B (MSE 4.7374), worst Qwen2.5-1.5B (5.2049) — all 3x worse "
        "than MIFlu (1.5574). None passes K&S. Conclusion: frozen LLM representations do NOT automatically "
        "improve influenza forecasting. This is the paper's most novel negative result.",
        "11 个冻结 LLM 编码器（Qwen2.5、DeepSeek-R1、腾讯 Hunyuan/ContextPilot）+ 共享线性头。结果：全部表现差。"
        "最佳 Hunyuan-1.8B（MSE 4.7374），最差 Qwen2.5-1.5B（5.2049）——均比 MIFlu（1.5574）差 3 倍。无一通过 K&S。"
        "结论：冻结 LLM 表征不会自动改善流感预测。这是论文最核心的负面发现。"))
'''
    c = c[:sec10_start] + condensed + c[sec10_end:]
    print('Section 10: condensed from 6663 to ~500 chars')

# 4. REMOVE Section 16 (How to reproduce) — not needed for supervisor
sec16_start = c.find('b.append(H1("16. How to reproduce')
sec16_end = c.find('b.append(H1("17. References')
if sec16_start > 0 and sec16_end > 0:
    c = c[:sec16_start] + c[sec16_end:]
    print('Section 16: removed (2107 chars)')

# 5. CONDENSE Section 17 (References) — keep only key refs
sec17_start = c.find('b.append(H1("17. References')
if sec17_start > 0:
    # Find return b
    ret = c.find('\n    return b', sec17_start)
    if ret > 0:
        condensed = '''    b.append(H1("17. References", "17. 参考文献"))
    b.append(BUL(
        ("Moon et al. MIFlu. IEEE JBHI 2025. DOI: 10.1109/JBHI.2025.3561214", "Moon et al. MIFlu. IEEE JBHI 2025."),
        ("Kramer & Shaman. PLoS Comput Biol 15(2):e1006742, 2019. DOI: 10.1371/journal.pcbi.1006742 [to verify]", "Kramer & Shaman. PLoS Comput Biol 2019."),
        ("Nie et al. PatchTST. ICLR 2023. arXiv:2211.14730", "Nie et al. PatchTST. ICLR 2023."),
        ("Liu et al. iTransformer. ICLR 2024.", "Liu et al. iTransformer. ICLR 2024.")))
    return b'''
        c = c[:sec17_start] + condensed + c[ret+14:]
        print('Section 17: condensed')

open(p, 'w', encoding='utf-8', newline='').write(c)
print(f'After: {len(c)} chars')

try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    print(f'FAIL: {str(e)[:250]}')
