import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
c = open(p, 'r', encoding='utf-8').read()

# 1. Add Table VIII ablation content
if '60/60' not in c and 'logarithmic ladder' not in c:
    ablation = '''    b.append(H2("Ablation (Table VIII)", "消融（表 VIII）"))
    b.append(P(
        "Ablation complete at 60/60 cells (K2/K4/K8/K12 depth ladder + no_lora). Two variants deliberately "
        "absent: K=6 (~2 A100-h, overdetermined curve) and emb_prompt (derived identity from --no-text "
        "invariance). The no_lora row is bit-identical to the full model — structural verification, not "
        "an ablation effect.",
        "消融已 100% 完成（60/60）（K2/K4/K8/K12 深度阶梯 + no_lora）。两个变体有意省略：K=6（约 2 A100 机时，"
        "已过定曲线）和 emb_prompt（由 --no-text 不变性推导为恒等）。no_lora 行与完整模型逐位相同——结构验证，"
        "非消融效应。"))'''
    c = c.replace('\n    return b', '\n' + ablation + '\n    return b', 1)
    print('Added Table VIII ablation')

# 2. Add [to verify] and T=104 to definitions
if '[to verify]' not in c:
    # Find definitions section
    idx = c.find('Definitions and notation')
    if idx > 0:
        verify_text = '''    b.append(P(
        "**[to verify]** The K&S threshold (PTE <= 1 week AND PIE <= 25%) is attributed to Kramer & Shaman "
        "(2019), PLoS Comput Biol 15(2):e1006742, but the exact wording and page number must be verified "
        "against the original PDF before submission. Peak detection parameters (find_peaks, "
        "prominence=0.15*range, distance=15, +-8 week matching) are this study's own engineering choices.",
        "**[to verify]** K&S 阈值（PTE <= 1 周 且 PIE <= 25%）归因于 Kramer & Shaman (2019), "
        "PLoS Comput Biol 15(2):e1006742，但提交前必须对照原文核实确切措辞与页码。峰值检测参数"
        "（find_peaks, prominence=0.15*range, distance=15, ±8 周匹配）是本研究的工程选择。"))
'''
        # Insert before return b
        c = c.replace('\n    return b', '\n' + verify_text + '\n    return b', 1)
        print('Added [to verify] flag')

if 'T = 104' not in c:
    # Add to definitions
    idx = c.find('Definitions and notation')
    if idx > 0:
        horizon = '''    b.append(P(
        "**Horizon L**: future weeks predicted per forward pass. Input T = 104 weeks, output = L weeks. "
        "L=24 means predict 24 weeks ahead. Source: paper Table IV. **Step s**: which predicted week "
        "(step 0 = 1 week ahead). Source: analysis_expanded.py.",
        "**跨度 L**：一次前向预测的未来周数。输入 T = 104 周，输出 L 周。L=24 表示预测未来 24 周。"
        "来源：论文 Table IV。**步长 s**：第几个预测周（step 0 = 提前 1 周）。来源：analysis_expanded.py。"))
'''
        # Insert at beginning of definitions section
        defs_start = c.find('b.append(P(\n        "The following definitions')
        if defs_start > 0:
            c = c[:defs_start] + horizon + c[defs_start:]
            print('Added T = 104 definition')

open(p, 'w', encoding='utf-8', newline='').write(c)

try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    print(f'FAIL: {str(e)[:250]}')
