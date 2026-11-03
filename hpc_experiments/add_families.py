import sys, py_compile
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

p = '01_最终报告/_build2/dlv/text_internal.py'
c = open(p, 'r', encoding='utf-8').read()

# 1. Add model family overview + why chosen, BEFORE the benchmark results table
if 'model families' not in c and '模型家族' not in c:
    # Find the benchmark section header
    anchor = 'b.append(H1("7. The 16-arm benchmark"'
    idx = c.find(anchor)
    if idx > 0:
        # Find the bench_params table call after this
        bench_idx = c.find('b.append(T("bench_params"))', idx)
        if bench_idx > 0:
            # Insert family overview BEFORE bench_params
            family_text = '''    b.append(P(
        "We benchmark 28 models across 6 families, chosen to cover the full spectrum of modern forecasting: "
        "(1) **Linear** (NLinear) — the simplest baseline; (2) **Transformer** (PatchTST, iTransformer) — "
        "current state-of-the-art for long-term forecasting; (3) **Neural** (DNN, CNN, RNN, LSTM, GRU) — "
        "classic deep learning; (4) **Classical ML** (Gradient Boosting, Random Forest, Decision Tree, SVR, KNN) — "
        "non-neural baselines; (5) **LLM-based** (MIFlu, TimeCMA, Qwen-Time, CALF) — the paper's approach and "
        "its published competitors; (6) **Frozen LLM encoders** (11 arms: Qwen2.5, DeepSeek-R1, Tencent Hunyuan/"
        "ContextPilot) — testing whether pre-trained LLM representations transfer to influenza forecasting. "
        "This selection covers every major approach in the literature and directly answers which family a "
        "public-health team should deploy.",
        "我们对 6 个家族的 28 个模型进行了基准评估，覆盖现代预测的全部谱系：(1) **线性**（NLinear）——最简基线；"
        "(2) **Transformer**（PatchTST、iTransformer）——当前长期预测的最先进方法；(3) **神经网络**（DNN、CNN、RNN、"
        "LSTM、GRU）——经典深度学习；(4) **经典机器学习**（梯度提升、随机森林、决策树、SVR、KNN）——非神经基线；"
        "(5) **基于 LLM**（MIFlu、TimeCMA、Qwen-Time、CALF）——论文方法及其已发表的竞争者；(6) **冻结 LLM 编码器**"
        "（11 个：Qwen2.5、DeepSeek-R1、腾讯 Hunyuan/ContextPilot）——测试预训练 LLM 表征是否迁移到流感预测。"
        "此选择覆盖文献中的所有主要方法，直接回答公共卫生团队应部署哪个家族。"))
'''
            c = c[:bench_idx] + family_text + c[bench_idx:]
            print('Added model family overview')

# 2. Add ILITOTAL explanation in the benchmark section (before PTE/PIE discussion)
if 'ILITOTAL' not in c[c.find('7. The 16-arm'):c.find('8. Peak')]:
    # Find the peak skill section
    anchor2 = 'b.append(H1("8. Peak skill'
    idx2 = c.find(anchor2)
    if idx2 > 0:
        ilitotal = '''    b.append(P(
        "**Why PTE/PIE uses ILITOTAL (patient counts) instead of the 7-variable aggregate.** The 7-variable "
        "aggregate is a *loss*, not a time series — it cannot be de-normalised because the 7 channels span "
        "different scales (OT mean 493,629 vs %WEIGHTED ILI mean 1.74, a 283,650x difference). Peak timing "
        "and intensity require a single interpretable series in physical units, so PTE/PIE use ILITOTAL "
        "(total influenza-like illness visits) de-normalised to patient counts. The reproduction uses the "
        "7-variable aggregate because Table V defines it that way; the benchmark adds PTE/PIE on ILITOTAL "
        "because public-health deployment decisions need physically meaningful peak forecasts.",
        "**为什么 PTE/PIE 用 ILITOTAL（患者数）而非 7 变量聚合。** 7 变量聚合是*损失值*，不是时间序列——无法去归一化，"
        "因为 7 个通道的量级差异巨大（OT 均值 493,629 vs %加权 ILI 均值 1.74，相差 283,650 倍）。峰值时间和强度需要"
        "物理单位的单一可解释序列，因此 PTE/PIE 使用去归一化为患者数的 ILITOTAL（流感样病例就诊总数）。"
        "复现使用 7 变量聚合是因为 Table V 的定义如此；基准新增 ILITOTAL 的 PTE/PIE 是因为公共卫生部署决策需要"
        "物理上有意义的峰值预测。"))
'''
        c = c[:idx2] + ilitotal + c[idx2:]
        print('Added ILITOTAL explanation')

open(p, 'w', encoding='utf-8', newline='').write(c)

try:
    py_compile.compile(p, doraise=True)
    print('compile OK')
except Exception as e:
    print(f'FAIL: {str(e)[:250]}')
