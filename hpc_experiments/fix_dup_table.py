import sys, re, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
c = open(p, 'r', encoding='utf-8').read()

# 1. Find all repro_params references
for m in re.finditer(r'b\.append\(T\("repro_params"\)\)', c):
    print(f'Found repro_params at char {m.start()}')
    # Show context
    start = max(0, m.start()-100)
    end = min(len(c), m.end()+100)
    print(f'  Context: {repr(c[start:end][:200])}')

# 2. Keep only ONE repro_params (the first one, in methodology section)
# Remove the second occurrence
first = c.find('b.append(T("repro_params"))')
second = c.find('b.append(T("repro_params"))', first + 10)
if second > 0:
    # Remove the second occurrence
    end_line = c.find('\n', second)
    c = c[:second] + c[end_line+1:]
    print(f'Removed second repro_params at char {second}')

# 3. Add benchmark comparison table reference
# First check if bench_params table exists in tables.py
tables_c = open('01_最终报告/_build2/dlv/tables.py', 'r', encoding='utf-8').read()
if 't_bench_params' not in tables_c:
    print('Need to add t_bench_params to tables.py')
    
    # Add benchmark params table
    FUNC = '''

def t_bench_params():
    rows = [
        [C("Seeds", "种子"), C("42/43/44 (3 seeds)", "42/43/44（3 种子）"), C("N/A (no benchmark)", "无（无基准）"), C("PatchTST/iTransformer convention", "PatchTST/iTransformer 惯例")],
        [C("Eval windows", "评测窗口"), C("(W//16)*16 = 160/144/144/128", "(W//16)*16"), C("Same (drop_last)", "相同"), C("Shared across all 28 models", "28 模型共享")],
        [C("Metric", "指标"), C("7-var z-space MSE/MAE", "7 变量 z 空间 MSE/MAE"), C("Same", "相同"), C("Comparable with Table V", "与 Table V 可比")],
        [C("Peak metric", "峰值指标"), C("PTE/PIE on ILITOTAL", "ILITOTAL 的 PTE/PIE"), C("N/A", "无"), C("For deployment decisions", "用于部署决策")],
        [C("Models", "模型"), C("28 (16 conventional + MIFlu + 3 LLM + 11 encoders)", "28（16 常规 + MIFlu + 3 LLM + 11 编码器）"), C("1 (MIFlu only)", "1（仅 MIFlu）"), C("Comprehensive benchmark", "全面基准")],
        [C("Checkpoint selection", "检查点选择"), C("Validation MSE", "验证集 MSE"), C("N/A", "无"), C("Same fix as reproduction", "与复现相同的修复")],
        [C("Hardware", "硬件"), C("A100-SXM4-80GB", "A100-SXM4-80GB"), C("Not disclosed", "未披露"), C("Provenance recorded", "记录来源")],
    ]
    return {
        "caption": C("Benchmark protocol: ours vs the original (which has no benchmark).",
                     "基准协议：本文 vs 原论文（原论文无基准）。"),
        "cols": [C("Parameter", "参数"), C("Ours (benchmark)", "本文（基准）"), C("Original", "原论文"), C("Note", "说明")],
        "widths": [3.2, 4.2, 3.8, 5.2],
        "fs": 7.0,
        "rows": rows,
        "note": C("The original paper has no benchmark — this is our contribution.", "原论文无基准——这是我们的贡献。"),
    }

'''
    tables_c = tables_c.replace('\nALL = {', FUNC + '\nALL = {', 1)
    tables_c = tables_c.replace('"repro_params": t_repro_params,', '"repro_params": t_repro_params, "bench_params": t_bench_params,', 1)
    open('01_最终报告/_build2/dlv/tables.py', 'w', encoding='utf-8', newline='').write(tables_c)
    py_compile.compile('01_最终报告/_build2/dlv/tables.py', doraise=True)
    print('tables.py: t_bench_params added')

# 4. Add bench_params table to the benchmark section
if 'T("bench_params")' not in c:
    # Find the benchmark section
    anchor = 'b.append(H1("7. The 16-arm benchmark"'
    idx = c.find(anchor)
    if idx > 0:
        # Find the first T("benchmark") after this
        bench_table = c.find('b.append(T("benchmark"))', idx)
        if bench_table > 0:
            # Add bench_params BEFORE the benchmark results table
            block = '    b.append(T("bench_params"))\n'
            c = c[:bench_table] + block + c[bench_table:]
            print('Added bench_params table to benchmark section')

open(p, 'w', encoding='utf-8', newline='').write(c)
try:
    py_compile.compile(p, doraise=True)
    print('text_internal.py: compile OK')
except Exception as e:
    print(f'FAIL: {str(e)[:250]}')
