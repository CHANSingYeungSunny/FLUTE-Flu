# MIFlu 复现工作：导师五大疑问逐条回复

*基于顶刊/官方文献核实版（Evidence-Checked Version） — 2026年9月*

> 说明：本报告逐条回答导师提出的五个问题。每条回答均区分"有直接文献依据的结论"与"本课题自行设定的工程决策"，并对此前 AI 辅助工具（CodeBuddy）生成初稿中的过度归因之处做了订正标注（见各节【订正】方框）。所有引用文献均可通过文末参考文献列表核实。

> **2026-09-02 更新说明**：本次更新在保留原有"结论 / 证据 / 【订正】 / 建议"四段式结构的前提下，为每个问题追加了**「代码验证结果」**小节。新增内容均明确标注其来源层级：
> - **(a) 文献依据** — 附论文名 + DOI/链接；
> - **(b) 本次复现实验新增结果** — 由本次代码运行 / HPC 实验产生，注明脚本与产物路径；
> - **(c) 本课题自定义工程决策** — 明确标注"非文献标准，为本课题自定义"。
>
> 原有已核实的文献证据部分全部保留，未做替换或删除。

---

## 问题一：单时间步多预测值的融合机制（Aggregation Policy）

### 结论

- 代码中 `fixed_step, step=0`（恒定取"提前1周"预测，n_windows=1）的修复方向是正确的，解决了旧版 `mean_over_lead` 把不同提前期（lead time）预测混合平均、导致误差被人为平滑的问题。
- 但"选择单一 step=0"与 CDC FluSight 官方做法并不完全等同——官方做法不是"选一个代表性的 horizon"，而是把 0/1/2/3 周四个 horizon 全部保留、分别独立评分/独立报告，从不跨 horizon 合并。

### 证据

- **Flusion: Integrating multiple data sources for accurate influenza predictions**（arXiv 2407.19054 / ScienceDirect）：
  - 原文明确定义 FluSight 官方 horizon 集合为 0 周（nowcast）、1、2、3 周，每个 (reference date, horizon) 组合都被当作独立的 "model task" 打分，不做跨 horizon 融合。
  - 论文链接：https://www.sciencedirect.com/science/article/pii/S1755436524000719
- **Evaluation of FluSight influenza forecasting in the 2021–22 and 2022–23 seasons**（Nature Communications, 2024 / PMC11282251）：各队伍需分别提交 1–4 周 ahead 的独立预测，评分（WIS）按 horizon 单独计算，结论明确写道预测技巧"随 horizon 变长而下降"，说明各 horizon 从未被合并成一个数字。
  - https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11282251/
- **Expanding optimization ensemble model methods for forecasting seasonal influenza in the U.S.**（medRxiv 2025.11.24.25340597）：Target End Date = reference date + horizon × 7 天，每个 horizon 对应精确的目标日期、独立报告，官方 Ensemble 用同一 horizon 下不同团队预测的中位数合并，而不是跨 horizon 合并。
  - https://www.medrxiv.org/content/10.1101/2025.11.24.25340597.full.pdf
- MIFlu 论文自身 Table V（L=24/36/48/60，MSE/MAE 分列4列）与 Table VI（L=2/3/5/…/20，RMSE/PCC 分列7列）同样是"每个固定 horizon 单独一列"的报告方式，未做跨 horizon 平均——这与 fixed_step 的设计原则完全一致。

### 建议

- 当前 step=0 的修复已解决"错误地跨 horizon 平均"这一核心问题，可以作为主结果保留。
- 如果希望进一步与 FluSight 官方规范对齐，可补充生成 step=1, 2, 3（对应 2/3/4 周 ahead）的平行版本，作为附加证据展示在同一组图或附录表格中，而不是用来替换 step=0——这是"完善"而非"修正错误"，不属于必须项。

### 代码验证结果（本次复现实验新增结果）

> **来源标注：(b) 本次复现实验新增结果**
> 生成脚本：`scripts/q1_step_sweep.py`；产物：`results/ili/metrics/q1_step_sweep.csv`、`results/ili/figures/fig_q1_step_sweep_L24_L60_step{0,1,2,3}.png`（按 step 拆分的 4 张图；原 2×3 拼图已移除）
> 实现方式：**对已导出的预测 CSV 做纯重聚合，未重新训练、未重新推理，因此不需要 GPU**。导出的 CSV 已自带 `step` 列（0..L-1），改变聚合策略只是一次 pandas groupby。

已按建议补充 step=1, 2, 3 的平行聚合，并覆盖 **L=24/36/48/60 全部四个 horizon**（不只 L=24，以便与问题四的口径保持一致）。

**MSE（z 空间，Table V 口径，仅 test split）**

| L \ step | step=0（1周ahead） | step=1（2周） | step=2（3周） | step=3（4周） |
|---|---|---|---|---|
| 24 | 3.1173 | 3.5694 | 3.8022 | 4.5711 |
| 36 | 3.2153 | 3.3031 | 3.9146 | 4.2595 |
| 48 | 3.5514 | 3.3905 | 3.3819 | 3.5239 |
| 60 | 1.9811 | 2.0131 | 1.8886 | 1.9363 |

![Q1 step=0（1周ahead）聚合扫描](results/ili/figures/fig_q1_step_sweep_L24_L60_step0.png)
![Q1 step=1（2周ahead）聚合扫描](results/ili/figures/fig_q1_step_sweep_L24_L60_step1.png)
![Q1 step=2（3周ahead）聚合扫描](results/ili/figures/fig_q1_step_sweep_L24_L60_step2.png)
![Q1 step=3（4周ahead）聚合扫描](results/ili/figures/fig_q1_step_sweep_L24_L60_step3.png)

**需要诚实说明的两点：**

1. **L=24 与 L=36 的误差随 lead time 单调上升**（3.1173→4.5711；3.2153→4.2595），与 Nature Communications（PMC11282251）所述"预测技巧随 horizon 变长而下降"方向一致，可作为对上述文献证据的一次正面呼应。
2. **L=48 / L=60 呈现持平甚至略降**，且 L=60 的绝对误差（约 1.9–2.0）反而**低于** L=24（约 3.1–4.6）。这**不是**"长 horizon 更好"，而是评估窗口不同造成的混淆 —— 各 horizon 的 step=0 可评估窗口为：

   | L | 可评估周数 | 覆盖区间 |
   |---|---|---|
   | 24 | 182 | 2018-01-28 → **2021-07-18** |
   | 36 | 170 | 2018-01-28 → 2021-04-25 |
   | 48 | 158 | 2018-01-28 → 2021-01-31 |
   | 60 | 146 | 2018-01-28 → **2020-11-08** |

   L=60 的窗口在 2020-11-08 终止，**完全排除了 2021-02-07 那个 COVID 幻觉峰**（详见问题二）。因此**跨 L 直接比较这些数字是不恰当的**；真正有意义的是**同一 L 内部跨 step 的比较**。此点已在脚本产出的 CSV 中以 `date_start` / `date_end` 两列记录，保证可追溯。

---

## 问题二：真实曲线与预测曲线的视觉与逻辑对齐（COVID 期间"真值平、预测尖峰"）

### 结论

- 2020–2021 年美国 ILI 出现历史性骤降是真实、被大量流行病学文献证实的现象，不是画图 bug；但"曲线是否反转/数组是否错位"仍需要用与图无关的独立方法交叉验证，不能仅凭"看起来合理"就下结论。
- "frozen LLM 在分布漂移下依赖预训练季节性先验、产生幻觉式高估"这一解释方向与近期 LLM-based 时间序列预测研究的一般性发现一致，但该发现是一般规律，并非专门针对本数据集/本次实验证实的结论，报告中不应表述为"已被证实"。

### 证据 — NPI 导致 ILI 骤降属实

- **Washington State Influenza Summary 2020–2021 Season**：报告指出 2020–2021 流感季活动水平"历史性低"，直接归因于口罩佩戴、居家、洗手、停课等 COVID-19 防疫措施（NPI）。
  - https://doh.wa.gov/sites/default/files/2022-02/420-100-FluUpdateSeason2021.pdf
- **Decreased Seasonal Influenza Rates...**（JMIR Public Health and Surveillance, 2023）：基于众包监测系统的数据显示，ILI 检出率从基线季节（2016–2019）的 3.8% 降至 2020–2021 季节的 0.27%，降幅超过一个数量级。
  - https://doi.org/10.2196/40216
- **Influenza's Plummeting During the COVID-19 Pandemic**（PMC8808434）：中国、英国、美国监测系统显示 2020–2021 流感季活动较过去5年均值下降 92.4%–99.9%，并用口罩佩戴/人口流动模型定量估计了 NPI 的贡献。
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC8808434/
- **CDC FluView Summary**（ending April 3, 2021）：CDC 官方周报确认 2020–21 season 因疫情原因"暂停常规数据采集"，ILI 活动"远低于全国基线"，并提醒 ILI 数据在此期间应"极度谨慎解读"（因就医行为改变、症状重叠等原因）。
  - https://www.cdc.gov/flu/weekly/weeklyarchives2020-2021/

### 证据 — "预训练LLM在分布漂移下产生幻觉式预测"的一般性支持（谨慎引用）

- **Rethinking the Role of LLMs in Time Series Forecasting**（arXiv 2602.14744）：该研究发现，预训练 LLM 的先验知识在"数据分布发生较大偏移"或模型被用于"未见过的域外数据集"时，既可能提供有益的强先验，也说明模型行为在分布漂移期会更依赖预训练知识而非当前输入信号——这与你观察到的"模型按历史季节性规律硬造峰值"的现象方向一致。
  - https://arxiv.org/html/2602.14744v2

> **【订正】** 该文献是关于 LLM-for-time-series 的一般性规律总结，并非针对流感/COVID 场景的定向研究，不能用作"MIFlu 在 COVID 期间产生幻觉"这一具体现象的直接证据，只能作为"同类失效模式在文献中有迹可循"的背景支持。报告中应避免使用"已被证实的幻觉现象"这类强断言，改用"与文献中报告的 LLM 分布外先验依赖现象方向一致"等表述。

### 关于数组对齐的独立核查建议（不依赖文献，需要你自己在代码里验证）

- **交叉验证法**：单独挑选若干个非异常年份（如 2015–2019 正常流感季）画出同款连续预测图。若这些年份中红蓝两线吻合良好（无论幅度还是峰值周），说明整体 index 对齐、绘图逻辑没有问题，只有 COVID 年份出现异常，从而支持"分布漂移"而非"索引错位"的解释；反之如果连正常年份都对不上，则应优先排查 ground_truth 与 prediction 是否使用了不同的时间戳/索引来源。
- **确认数据集时间跨度**：National-Illness 数据集覆盖 2002–2021 年，按 70:10:20 切分训练/验证/测试集。若整个数据集约为 990 周（2002–2021），则测试集（末尾20%，约198周）在时间上大致落在 2017 年末至 2021 年，天然包含 2020–2021 COVID 异常期——建议在代码中直接 print 测试集起止日期加以确认，这是最直接、最省事的核实方式。
- **保留而非删除异常**：建议保留该异常并加注说明（如 CodeBuddy 报告中已做的红色标注框），而不是删除或平滑处理——这段"模型失效"的可视化证据恰恰真实反映了冻结式 LLM 在分布外场景下的局限性，是审稿人应该看到的诚实结果，也是论文"未来工作"部分可以正面讨论的内容。

### 代码验证结果（本次复现实验新增结果）

> **来源标注：(b) 本次复现实验新增结果**
> 生成脚本：`scripts/q2_alignment_check.py`；产物：`results/ili/metrics/q2_alignment_check.csv`、`results/ili/figures/fig_q2_alignment_precovid_vs_covid.png`
> 同样为纯重聚合，不需要 GPU。

**(1) 测试集日期核实 —— 直接回答"是否覆盖 COVID 2020–2021"**

脚本输出的原始测试集区间为：

```
[L=24] RAW TEST SPLIT : 2018-01-28 -> 2021-12-26  (rows=4368)
[L=36] RAW TEST SPLIT : 2018-01-28 -> 2021-12-26  (rows=6120)
[L=48] RAW TEST SPLIT : 2018-01-28 -> 2021-12-26  (rows=7584)
[L=60] RAW TEST SPLIT : 2018-01-28 -> 2021-12-26  (rows=8760)
```

**结论：测试集为 2018-01-28 至 2021-12-26，确认完全覆盖 2020–2021 COVID 异常期。** 报告中"测试集天然包含 COVID 期"的推断得到代码层面的直接确认。

**(2) 正常年份 vs COVID 期对齐交叉验证**

按 2020-01-01 为界切分（pre-COVID 段 = 2018–2019 两个正常流感季），对比两段的对齐质量：

| L | pre-COVID 皮尔逊 r | pre-COVID MAE（人） | COVID 期 r | COVID 期 MAE（人） | pre-COVID 峰值周偏差 |
|---|---|---|---|---|---|
| 24 | **+0.944** | 6,470 | +0.656 | 14,188 | 1 周 |
| 36 | **+0.925** | 5,067 | +0.691 | 16,904 | 1 周 |
| 48 | **+0.886** | 6,620 | +0.676 | 18,572 | 1 周 |
| 60 | +0.885 | 9,354 | +0.956* | 7,366 | 1 周 |

注：L=60 的 COVID 段仅 45 周、止于 2020-11-08，**未覆盖真正的 ILI 崩塌期**（与问题一的覆盖范围发现一致），故其高 r 不可与其余三行同等解读。

![Q2 对齐交叉验证：正常年份 vs COVID 期](results/ili/figures/fig_q2_alignment_precovid_vs_covid.png)

**判读：**

- 在**正常流感季（2018–2019）**，四个 horizon 的皮尔逊相关系数均达 **0.885–0.944**，且**峰值周定位偏差仅 1 周**。这直接满足报告建议中的判据："若这些年份中红蓝两线吻合良好（无论幅度还是峰值周），说明整体 index 对齐、绘图逻辑没有问题"。
- 进入 **COVID 期**，L=24/36/48 的相关系数降至 **0.656–0.691**，MAE 上升约 **2–3 倍**。
- 因此，代码层面的独立核查结果**支持"分布漂移"解释，而不支持"数组索引错位"解释**——若为索引错位，正常年份同样会失配，但实测正常年份吻合良好。
- 该结论属于**本次实验观测**，而非文献引用。它与"frozen LLM 在分布漂移下依赖预训练季节性先验"的解释方向一致，但如【订正】所述，仍不应表述为"已被证实的幻觉现象"。

**(3) 保留异常的处理**：已在 `make_submission_figures.make_continuous` 中保留 COVID 阴影与幻觉峰值标注（如 2021-02-07 pred=30,524 vs gt=14,108，约 2.2× 高估），未做删除或平滑，符合报告建议。

![MIFlu 连续预测（L=24，含 COVID 幻觉峰标注）](results/ili/figures/fig_miflu_eval_continuous_L24.png)

---

## 问题三：Y轴单位错误与 Z-score 反标准化问题

### 结论

- 在 MIFlu 论文的评估指标章节中，作者明确说明 Table V 报告的 MSE/MAE 是在"先用 StandardScaler 归一化"之后的 Z-score 空间中计算的，因此用同一套（训练集拟合的）StandardScaler 做 inverse_transform 来还原物理单位，方法论上与论文原文一致，是正确、可辩护的做法。
- 但需要注意论文中实际存在两套不同的"归一化"，容易混淆，建议在代码里明确区分并在方法说明中写清楚用的是哪一套。

### 论文原文依据

> "We first normalize each input variable to a normal distribution using StandardScaler. The mean square error (MSE) and mean absolute error (MAE) are then calculated using (3) and (4)." —— MIFlu 论文 Section V-B Evaluation Metrics

> "we impose reversible instance normalization [19] on each variable in Xinput by subtracting the mean Xinput from Xinput and dividing the result by the standard deviation of Xinput." —— MIFlu 论文 Section IV-B Time-Series Input Embedder

### 两套归一化的区别（需要在代码中确认用的是哪一套）

- **第一套（评估用，全局 StandardScaler）**：用于计算 Table V/VI 的 MSE/MAE 数值，通常在训练集上拟合一次全局的 mean/std，适用于"把 Z-space 的误差数字还原成物理单位"这个目的——你目前代码里 mean_=9368.3、scale_=8853.4、仅用 train[:717] 拟合、不使用测试集信息，这个做法是正确的，符合防止数据泄漏的基本原则。
- **第二套（模型内部用，RevIN 逐窗口归一化）**：模型每次接收一个长度为T的输入窗口时，会用该窗口自己的均值/标准差做归一化，且是"可逆"的（reversible），推理时模型内部会自动把输出逆变换回该窗口自己的尺度——这是训练时真正驱动模型学习的归一化方式，和整体训练集的全局统计量并不是同一件事。
- **对画图/物理量核对而言**：只要 ground truth 和 prediction 两条线自始至终使用同一套还原参数（都是全局 StandardScaler，或都是各自窗口的 RevIN 逆变换），结果都能正确对齐；最怕的情况是无意中把"全局 StandardScaler 还原的真值"和"RevIN 逐窗口还原的预测值"混在一起画同一张图，这样即使两者数值level接近，也可能存在系统性偏差。建议在代码里加一行注释明确写出"本图两条曲线均使用 train[:717] 拟合的全局 StandardScaler 还原"，避免歧义。

### 建议的独立核查方法（比"两条线形状一致"更有说服力）

- 直接用训练集内部的已知真实值做 sanity check：任选训练集中若干个样本，做 inverse_transform 后，与 MIFlu 论文 Table II 报告的 National-Illness 数据集描述性统计（各变量的 Min/Max）做比对，确认还原后的数值范围落在合理区间（例如 ILITOTAL 应为几千到几万量级），这是用论文自己公开的统计量做交叉验证，比"肉眼看两条线形状一致"更可信、更可复现。

### 代码验证结果（本次复现实验新增结果）

> **来源标注：(b) 本次复现实验新增结果**（含一处必须披露的限制，见下）
> 生成脚本：`scripts/q3_scaler_sanity_check.py`；产物：`results/ili/metrics/q3_scaler_sanity_check.csv`
> 代码改动：`scripts/make_submission_figures.py`（新增反标准化来源标注注释）

**(1) 已按建议在代码中明确标注所用的归一化**

已在 `scripts/make_submission_figures.py` 的 `make_continuous()` 前加入显式注释，明确写出：

- 图中**两条曲线（真值与预测）均使用同一套还原参数**——即在 `train[:717]` 上拟合的**全局 StandardScaler**（ILITOTAL mean = 9368.29，scale = 8853.43，持久化于 `data/scaler_miflu_national.json`）；
- 这**不是**模型内部的 RevIN 逐窗口归一化（RevIN 在模型内部、取 loss 之前即已被撤销）；
- 混用两套还原参数（例如用 RevIN 逆变换的预测值去对比全局 scaler 还原的真值）正是导师所警示的失效模式，而在此处**不可能发生**，因为两列均来自 `train_ablation.export_prediction_csv` 的同一次双轨导出。

**(2) 反标准化 sanity check 实测结果**

| 项目 | 数值 |
|---|---|
| 全局 StandardScaler（ILITOTAL） | mean = 9368.29，scale = 8853.43，train_end = 717 |
| 往返误差 max \|physical − inverse_z(physical)\| | **3.64e-12（OK，精确可逆）** |
| ILITOTAL 物理值域 — train | min 318，max 69,068，mean 9,368 |
| ILITOTAL 物理值域 — val | min 4,596，max 63,036 |
| ILITOTAL 物理值域 — test | min 5,497，max 113,921 |
| 测试集预测反变换后值域 | min 5,497，max 113,921 |

**"几千到几万量级"的定性判断得到确认**：测试集反变换后的 ILITOTAL 落在 5,497–113,921 区间，与论文对该变量量级的描述一致；且往返逆变换误差为 1e-12 量级，说明 inverse_transform 实现本身无系统性偏差。

**(3) 一项新发现（非 bug，须披露）**

测试集 ILITOTAL 的**最大值（113,921）是训练集最大值（69,068）的 1.65 倍**。这不是 scaler 错误，而是意味着**测试集包含训练期从未出现过的更高 ILI 峰值**（2019–20 重流感季），模型必须在其归一化范围之外**外推**。这一点本身即是 COVID 期失效的一个促成因素，建议在论文"局限性"部分提及。

**(4) ⚠️ 必须披露的限制：未能与论文 Table II 原始数据逐格比对**

报告建议与 MIFlu 论文 Table II 的 Min/Max 逐格比对。经核查，**该精确数值在本地代码库中不可用**：仓库内的论文副本 `MIFlu_paper.md`（§V-A）明确记载——

> "Exact numeric cell values are not machine-extractable from the source PDF table image; see Fig. 2(a) boxen plot below for the visual distribution of each of the seven variables."

即 Table II 在原始 PDF 中是**扫描表格图片**，无法机器提取。**为避免编造论文数字，本次未做逐格比对**，而是改用**同一份 National-Illness 原始数据集的实测描述统计**作为等价的独立交叉验证——二者描述的是同一批数据，若本地管线用错 scaler 或错轴，该检查足以暴露。若后续能取得 Table II 的精确数值，可再做逐格核对并补入。

![Q3 反标准化验证](results/ili/figures/fig_q3_inverse_transform_proof.png)

---

## 问题四：缺失的"训练配方"与超参数调优

### 结论

- 论文确实未披露完整训练细节，这是真实存在的复现缺口（reproducibility gap），不是无中生有的问题。
- 用网格搜索/系统性对比多组训练配方（optimizer、loss、scheduler、梯度裁剪等）来逼近论文报告的数字，是标准、合理的复现方法论，不需要额外论文来"批准"这种做法本身；但需要把"逼近论文数字"和"找到全局最优超参"这两件事说清楚，避免结论被过度解读。

### 论文原文中缺失细节的确认

> "We set the number of training epochs and the learning rate for MIFlu empirically because the hyperparameters vary depending on the base model." —— MIFlu 论文 Section V-C Experimental Details

> "We implement the proposed model using Python 3.9.18 with PyTorch 2.1.0 and a GeForce RTX 3090." —— 同上

论文全文未提及：Adam/AdamW 的具体 β₁/β₂/ε、weight decay 数值、是否使用学习率调度器（及其类型）、是否做梯度裁剪（及阈值）、随机种子、损失函数的精确形式（虽然从上下文可合理推断为 MSE，但未显式声明）。这些正是可能导致数字级（digit-level）差异的关键变量，你的 Q4 前提是成立的。

### 对系统性网格搜索方法的评价

- 四组配方（baseline Adam / AdamW+Cosine+WD / AdamW+Huber+梯度裁剪 / earlystop-only）覆盖了"优化器类型""权重衰减""学习率调度""损失函数鲁棒性""梯度裁剪"这几个最常见、最可能显著影响小样本时间序列微调效果的维度，是合理、有代表性的搜索空间设计。
- 固定 seed=42 并在四组配方间保持一致，是控制变量法的正确做法，能排除"纯随机波动导致的数字差异"这一混淆因素。

> **【订正】** 结论"baseline (Adam, lr=5e-4, 无weight decay, 无scheduler, MSE loss, 无梯度裁剪) 因为最接近原论文数字，所以是最优配方"这一表述需要更精确的措辞。"逼近原论文报告的数字"与"该配方本质上是全局最优超参数"是两个不同的主张：前者是本次复现研究的合理目标（用于对比、验证复现的可信度），后者需要更多证据（如在独立验证集上的稳健性、跨随机种子的方差分析）才能成立。建议将结论改写为："在本次复现实验中，baseline 配方在与原论文数字的逼近程度上表现最好，说明原作者很可能使用了与此接近的训练配方"，而不是笼统地宣称这就是"最优训练配方"。

### 建议的补充验证

- 若条件允许，建议对表现最好的 baseline 配方额外跑 3–5 个不同随机种子，报告 MSE/MAE 的均值±标准差，用来说明"3–5倍的差距主要来自超参数选择本身，而不是运气好压中了某个随机种子"，这样能进一步加固"baseline 配方最接近原论文"这一结论的说服力。

### 代码验证结果（本次复现实验新增结果）

> **来源标注：(b) 本次复现实验新增结果**
> 生成脚本：`scripts/q4_recipe_comparison.py`；产物：`results/ili/metrics/q4_recipe_comparison.csv`
> 输入来源（HPC Burgundy）：`full_H24/reps_1_to_10/summary.csv`、`full__adamw_cosine/...`、`full__huber_clip/...`、`full__earlystop/...`（已镜像至 `results/ili/journal_evidence/recipe_summaries/`）

**(1) 关于"额外跑 3–5 个随机种子"的处理决定**

经核查代码，`train_ablation.py` 中每次运行的种子为 `seed = args.seed + rep - 1`，即 **10 个 rep 本身就是种子 42–51**。因此**每一组配方已经有 10 个种子的均值±标准差**，无需再消耗 GPU 时间重复跑种子；本次直接汇总现有 n=10 结果并进行显著性检验。

**(2) 同一口径（L=24，n_reps=10）的配方对比**

| 配方 | MSE mean | MSE std | MAE mean | MAE std |
|---|---|---|---|---|
| **baseline（Adam, lr=5e-4）** | **2.5187** | 0.5073 | 1.0621 | 0.0543 |
| adamw_cosine（+WD, cosine） | 2.6642 | 0.5313 | 1.0670 | 0.0636 |
| huber_clip（Huber+clip） | 2.7505 | 0.3637 | 1.0711 | 0.0424 |
| earlystop（peak-aware） | 2.8799 | 0.3139 | 1.1018 | 0.0343 |

> 数据完整性说明：聚合目录 `full/reps_1_to_10/summary.csv` 只保留了最后写入的 L=60 一行，**不可用于配方对比**；正确数值取自各 per-horizon 目录（`full_H24` 等）。

**(3) 显著性检验（Welch t 检验，α = 0.05，对照 baseline）**

| 对比配方 | ΔMSE | t | df | p 值 | 判定 |
|---|---|---|---|---|---|
| adamw_cosine | +0.1455 | −0.626 | 18.0 | **0.5391** | 不显著 |
| huber_clip | +0.2318 | −1.174 | 16.3 | **0.2572** | 不显著 |
| earlystop | +0.3612 | −1.914 | 15.0 | **0.0748** | 不显著 |

![Q4 训练配方对比](results/ili/figures/fig_q4_training_recipe_comparison.png)

**(4) 按【订正】要求改写后的结论**

- **观测到的排序**：baseline < adamw_cosine < huber_clip < earlystop（MSE 由 2.5187 递增至 2.8799）。
- **但差距远小于种子噪声**：baseline 与次优配方（adamw_cosine）的差距仅 **0.1455**，而 baseline 自身的种子标准差达 **0.5073** —— **gap / seed std = 0.287**，即差距只有噪声的 28.7%。三组配对检验的 p 值分别为 **0.5391 / 0.2572 / 0.0748**，**在 α=0.05 下均不显著**。
- **因此可辩护的表述是**："在本次复现实验中，baseline 配方在与原论文数字的逼近程度上表现最好，说明原作者很可能使用了与此接近的训练配方"—— 而**不能**宣称 baseline 是全局最优超参数，也不能断言该排序在统计上稳健。
- 需要说明的是：即使增加种子数，标准差也不会显著缩小到使 0.1455 的差距变为显著；**"差异在噪声内"本身就是本次实验的结论**，而非证据不足。若审稿人要求更强的结论，正确的做法是扩大配方间的差异（例如更强的正则化/更大的学习率跨度），而不是增加重复次数。

---

## 问题五：定义"预测准确"的微调停止标准（Stopping Criteria）

### 最终推荐表述（采纳讨论后的修订版）

**(1) 指标定义（有直接文献依据）**：Peak Timing Error (PTE) = |预测峰值周 − 真实峰值周|（单位：周）；Peak Intensity Error (PIE) = |预测峰值强度 − 真实峰值强度| / 真实峰值强度（单位：百分比）。这两个指标及"PTE≤1周、PIE≤25%即判定为命中"的定义，直接引自 Kramer & Shaman (2019, PLOS Computational Biology, DOI: 10.1371/journal.pcbi.1006742)，并与 CDC "Predict the Influenza Season Challenge" 官方判定口径一致。

- 论文链接：https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1006742

**(2) 真正决定"何时停止训练"的机制（有直接文献依据）**：训练层面的停止标准仍是标准的 early stopping on validation loss（监控验证集 MSE/RMSE，patience 设为 5–10 个 epoch，不再改善即停止并回滚到最优权重），这与多篇 ILI/流行病预测顶刊/顶会论文的通用做法一致。

**(3) 两层标准如何配合**：训练过程用 early stopping 决定何时停止微调、产出模型；模型停止训练后，在验证集/测试集上计算 PTE / PIE，作为判断"该模型是否达到可发表精度"的验收标准，而不是作为触发停止训练本身的信号。这样处理既有明确文献依据支撑每个数字，也不会把两种不同性质的判据混为一谈。

### 对 CodeBuddy 原始版本的订正

> **【订正1】** CodeBuddy 报告将"Peak Hit Rate ≥ 0.75、Timing Error ≤ 1.0 周、Peak Intensity Error ≤ 20%"包装为依据"论文 Supplementary indicators"得出的"确切阈值"，这一归因不准确。经核实，MIFlu 原论文（IEEE JBHI, 2025）中不存在任何 Peak Hit Rate / Timing Error / Intensity Error 相关的 Supplementary indicators 或阈值定义，这三个数字并非来自 MIFlu 论文本身。（**2026-09 补充**：Peak Hit Rate 指标本身已在本次指标精简中**移除**，现仅保留 PTE / PIE 两项；本条订正作为历史记录保留。）

> **【订正2】** 其中 Peak Intensity Error ≤ 20% 这一具体数值与实际可查证的文献（Kramer & Shaman, 2019）报告的 25% 阈值不一致。如果确实希望保留 20% 这一更严格的数值，应在报告中明确标注为"在文献常见的 25% 基础上主动收紧的自定义工程门槛"，而不是暗示这也是文献标准，否则一旦被追问出处会难以自圆其说。

> **【订正3】**（已于 2026-09 落实：该机制已移除，不再需要为其标注出处）PeakAwareEarlyStopping 中的"双重闸门"机制（val_loss 下降 **且** peak_hit_rate > 0.75 同时满足才保存 checkpoint）虽有一定工程动机，但据检索没有任何顶刊论文使用完全相同的机制，且它依赖本课题自定义的 peak_hit_rate。**本次已将补充诊断指标精简为 PTE 与 PIE 两项，peak_hit_rate 被彻底移除，该双闸门机制随之删除**：PeakAwareEarlyStopping 已重写为纯 EarlyStopping（仅监控 val_loss + patience，见 scripts/early_stopping.py）。因此本条订正不再是"如何标注"的问题——该机制已不存在；full__earlystop 已按新口径重跑，早期"双闸门"结果不可与之比较。

### 建议的最终写法（可直接用于方法论章节）

- **训练停止**：验证集 MSE/RMSE 早停（patience 5–10 epoch，回滚至最优权重）——有明确文献依据。
- **准确性判定**：PTE ≤ 1 周、PIE ≤ 25%（如需更严格可主动收紧至 20%，但需注明为自定义收紧，而非文献标准）——判定方法有明确文献依据，具体数值的收紧程度是工程选择。
- **样本量限定语（必须同显）**：PTE / PIE 只在**匹配峰值**上有定义，报告中必须同时给出匹配峰值计数（如 `2/3`），否则读者无法判断该均值取自几个峰。该计数是**样本量说明**，不是被报告的指标——峰值命中"率"已随 `peak_hit_rate` 一并移除。

### 代码验证结果（本次代码改动）

> **来源标注：(c) 本课题自定义工程决策** 与 **(a) 文献依据** 的区分已在代码中落地
> 改动文件：`scripts/compute_miflu_indicators.py`（新增 PROVENANCE 注释块）、`scripts/early_stopping.py`（新增 PROVENANCE 段落）

**(1) 已在代码中建立三类内容的明确区分**

在 `scripts/compute_miflu_indicators.py` 中新增 PROVENANCE 注释块，将指标与阈值按来源分为三层：

| 层级 | 内容 | 标注 |
|---|---|---|
| **(a) 文献依据** | PTE / PIE 的**定义**；"PTE ≤ 1 周 且 PIE ≤ 25% 判定命中"的判定约定 | Kramer & Shaman, 2019, PLOS Comput Biol, **DOI: 10.1371/journal.pcbi.1006742**（与 CDC "Predict the Influenza Season Challenge" 同口径），链接已写入代码注释 |
| **(b) 本课题自定义** | PTE ≤ **2.0 周**（相对文献 1 周**放宽**）；PIE ≤ **20.0%**（相对文献 25% **收紧**）；±2 周的峰值匹配窗口 `match_tol` | 代码中明确标注"NON-LITERATURE, CUSTOM ENGINEERING CHOICES"，并注明若需改用文献口径应传 `--thr_mean_abs_delta_t 1.0 --thr_peak_mag_rel_err 25` 并显式说明 |
| **(c) 已移除（2026-09）** | `peak_hit_rate`（峰值命中率）、`directional_accuracy`（方向准确率），以及依赖前者的 `early_stopping.py` **双闸门**机制 | 三者已从计算、判定、图形、表格中彻底删除；早停现为纯 `val_loss + patience`。`full__earlystop` 已按新口径重跑，旧口径结果不可与之比较 |

**(2) 原先的一处阈值不一致问题已随机制移除而消失**

旧代码中存在两个不同的 peak-hit 阈值：`early_stopping.PeakAwareEarlyStopping` 以 **0.7** 控制 checkpoint **保存**，而 `compute_miflu_indicators` 以 **0.75** 控制报告中的"accurate"**判定**。随着 `peak_hit_rate` 指标与双闸门机制一并移除，这两个自定义阈值都已不复存在，口径不一致问题自然消除（`full__earlystop` 已按纯 val_loss 早停口径重跑）。

**(3) 与【订正】的对应关系**

上述分层落实了【订正1】【订正2】【订正3】的要求：20% 不再被暗示为"论文阈值"（已标注为自定义收紧）；0.75 与双闸门已**直接移除**而非仅作标注；PTE/PIE 的定义与 1 周 / 25% 的判定约定则明确挂到 Kramer & Shaman (2019) 的可核实 DOI 上。

---

## 问题六：MIFlu 的多模态注意力是否"名不副实"？（对一条流传结论的核验）

> **本节性质**：本节专门核验一条在本项目内部流传、并被硬编码进 `plot_attention_proof.py` 图注的结论。核验结论是：**该说法的"强形式"不成立**。以下逐条给出证据。

### 待核验的指控

一条结论曾在本项目内被表述为：

> "MIFlu 的多模态注意力是假的：text→time 的注意力占比极小，说明文本根本没参与分析；且 MIFlu 架构中除 PE、LayerNorm、LoRA 外几乎全部冻结；消融实验表明原论文用的是 LayerNorm 的间接效应，而非其声称的多模态注意力——因此论文在说谎，且无法复现。"

该结论目前被硬编码在 `scripts/plot_attention_proof.py` 的图注中：

> "This **proves** the original MIFlu gain was a LayerNorm statistical shortcut, not genuine text understanding."

### 结论（先说结论）

**该指控的"强形式"不成立，不应写入论文或答辩材料。** 逐条判定如下：

| 分论点 | 判定 | 依据 |
|---|---|---|
| ① 文本完全未被使用 | ❌ **被功能消融否定** | 依据**功能消融**而非注意力质量：彻底移除文本（no_multi）使 MSE 显著恶化 +0.705（p=0.011）。注意力质量显示平均文本注意力仅 **0.526× 机会水平（低于随机）**，文本是被**稀疏、定点**使用的 |
| ② 增益纯粹来自 LayerNorm 捷径 | ❌ **被数据否定** | LN 仅解释文本贡献的 44.4%，且不显著（p=0.154）；移除 LN 后文本注意力几乎不变 |
| ③ 架构除 PE/LN/LoRA 外全部冻结 | ✅ **成立，但论文已公开披露** | MIFlu 论文 Section IV 原文明确写出，非隐藏信息（见下） |
| ④ 论文"在说谎" | ❌ **不可判定** | 我们没有作者代码，无法推断主观意图；且③属公开披露，与"隐瞒"相矛盾 |
| ⑤ 无法复现 | ⚠️ **部分成立，但表述需修正** | 确实存在显著的数值复现差距（我们的 L=24 MSE 2.519 vs 论文 1.542），但差异同样可能源于**我方实现**与作者实现的差别，不能据此断言论文有误 |

### 证据 — 注意力实测（原论文架构）

> **来源标注：(b) 本次复现实验新增结果**
> 脚本 `scripts/q6_text_attention_audit.py`；HPC 作业 `521890`（stingy / A100）；产物 `results/ili/metrics/q6_text_attention_audit.csv`

**方法**：原版 MIFlu 没有独立的 cross-attention 模块，文本以**前缀**拼接（`hfuse = [htext || htime]`，`miflu_model.py:376`），时序 patch **通过 GPT-2 因果自注意力**访问文本。因此本次直接 hook GPT-2 的自注意力，测量"时序 query 分配给文本 key 的注意力质量"，并与**机会水平**比较（因果掩码下，位置 q 可见 q+1 个 key，其中 n_text 个是文本，故机会水平 = n_text/(q+1)）。

| 变体 | 文本注意力质量 | 机会水平 | **相对机会** | 峰值注意力 | **峰值/机会** |
|---|---|---|---|---|---|
| **full_L24（原论文架构）** | 0.3858 | 0.7347 | **0.526× (<1，低于随机)** | 0.0679 | **34.1×** |
| no_text_ln（去掉文本 LN） | 0.3963 | 0.7347 | 0.548× | 0.0632 | 31.7× |
| no_lora | 0.5554 | 0.7347 | 0.762× | 0.1199 | 60.2× |
| gated_inject（本课题自定义） | 0.00271 | 0.00271 | **1.000× (恰好均匀)** | 0.1819 | 67.1× |

> 注：**相对机会 = 实测文本注意力质量 ÷ 因果掩码机会基线**（= n_text/(q+1) 的平均）。full 系列均 <1，说明平均文本注意力**低于随机因果基线**（文本占序列 55.6%、机会基线 73.5%）；**38.6% 仅是绝对占比，不能读作"文本被大量使用"**。gated_inject 的均值恰好=均匀(1.000×)，其文本路由同样只集中在峰值(67×)。 |

**判读（三点，均很重要）：**

1. **原版架构的平均文本注意力低于随机，文本被稀疏、定点使用。** 时序 query 分配给文本 token 的注意力质量均值为 **0.386**，但因果掩码下的机会基线为 **0.735**（文本占序列 55.6%、且位于序列开头始终可见），故**相对机会仅 0.526×——平均而言模型对文本的注意力反而低于随机因果注意力**。唯一高于机会的信号是**峰值 34×**，即个别时间 query 对个别文本 token 的定点关注。因此"38.6% 落在文本上"**不能读作'文本被大量使用'**；文本"确实参与预测"的硬证据来自下方功能消融（no_multi），而非注意力质量。
2. **"相对机会 0.526×"不等于"忽略文本"。** 文本占序列长度 369/663 ≈ 55.6%，因位于序列开头（因果掩码下始终可见）其机会水平高达 73.5%；模型实际给 38.6%，即**相对其数量占比下调了权重，但仍投入超过三分之一的注意力预算**。若真的"完全不用"，该值应趋近 0 而非 0.39。
3. **去掉文本 LayerNorm 后，文本注意力几乎不变（0.526× → 0.548×，相对变化约 4%）。** 这是对"LN 捷径"机制的**直接反证**：若文本的影响真的经由 LN 的统计重标定实现，移除 LN 应当显著改变文本的被注意程度，但实测几乎无变化。

### 证据 — 消融显著性检验（决定性）

> **来源标注：(b) 本次复现实验新增结果**
> 脚本 `scripts/q6_ablation_significance.py`；产物 `results/ili/metrics/q6_ablation_significance.csv`
> 数据来自 HPC 各变体的 10 rep（种子 42–51）汇总。

| 变体 | 移除的内容 | ΔMSE | p 值 | 判定 |
|---|---|---|---|---|
| **no_multi** | **文本输入编码器整体移除** | **+0.7049** | **0.0108** | **显著** |
| no_text_ln | 仅移除文本 LayerNorm | +0.3129 | 0.1543 | 不显著 |
| no_lora | 仅移除 LoRA | +0.1613 | 0.4282 | 不显著 |
| no_lora_multi | LoRA + 文本均移除（等价 GPT4TS） | +0.5808 | 0.0105 | 显著 |
| gated_inject | ModalityAligner + 解冻 2 层（本课题自定义） | +0.5200 | 0.0107 | 显著 |

**文本贡献拆解（MSE 单位）：**

| 项 | 数值 | 占比 |
|---|---|---|
| 移除全部文本（no_multi） | +0.7049 | 100% |
| 其中：可归因于文本 LayerNorm（no_text_ln） | +0.3129 | **44.4%** |
| **残差：不经过 LN 的文本贡献** | **+0.3920** | **55.6%** |

**结论**：彻底移除文本会造成**统计显著**的性能损失（p=0.011）；而仅移除文本 LN 的损失**不显著**（p=0.154）。**超过一半（55.6%）的文本贡献并不经过 LayerNorm**。因此"增益纯粹是 LN 统计捷径"这一机制解释**不成立**。

### 证据 — 架构事实与复现差距

**(a) 架构确实高度冻结 —— 但论文已公开披露。**

MIFlu 论文 Section IV 原文（`MIFlu_paper.md` 第 214 行附近）：

> "Following standard technique [9], [21], only PE and layer-normalization layers are typically fine-tuned. [...] **LoRA is applied only to the multi-head attention layer**, letting the pre-trained LLM learn new relationships in h_fuse without compromising inference speed."

即"除 PE / LayerNorm / LoRA 外基本冻结"是论文**主动写明**的设计选择，属于公开披露信息。将其作为"隐瞒"或"造假"的证据，与原文直接矛盾。

**(b) 复现差距确实存在（这是真实、可写入论文的发现）。**

| 指标 | 论文报告值 | 本次复现值 | 比值 |
|---|---|---|---|
| L=24 MSE（Table V） | 1.542 | 2.5187 | 1.63× |
| L=24 MAE（Table V） | 0.726 | 1.0621 | 1.46× |
| 四 horizon 平均 MSE（Table VIII） | 1.436 | 3.1700 | 2.21× |
| 四 horizon 平均 MAE（Table VIII） | 0.745 | 1.1587 | 1.56× |

论文来源：Moon J, Shim J, Kim E, Hwang E. MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme. *IEEE J. Biomed. Health Inform.*, vol.29, no.10, pp.7790–7801, Oct. 2025. DOI: 10.1109/JBHI.2025.3561214.

> **⚠️ 必须谨慎表述的一点**：存在数值差距**不等于**论文有误。我们**没有作者的实现代码**，无法排除差距源于我方实现与作者在提示词模板、数据版本、划分细节、评估口径（例如跨 7 个变量平均 vs 仅 ILITOTAL）等方面的差异。可辩护的表述是"本次独立复现未能复现论文报告的量级"，而**不能**表述为"论文数据不实"。

### 【订正】关于项目内部流传的这条结论

> **【订正1】** 支撑"文本未被使用"的两个统计量均不可作为证据：
> - `extract_attention.py` 的 `mean_text_attention == uniform`：对 cross-attention 而言，softmax 仅在文本 key 上归一化，故均值恒等于 1/n_text，**是数学恒等式，零信息量**。
> - `plot_attention_proof.py` 将 `full` 的文本注意力**画成 0**：仅因 `full` 没有可 hook 的 cross-attention 模块。**"没有可测量的模块"是测量手段的局限，不是"文本未被使用"的证据**；原版本就通过 GPT-2 因果自注意力实现跨模态交互。

> **【订正2】** `gated_inject` 与 `full` 的对比**存在混淆变量**。`gated_inject` 相对 `full` 改动了**两处**：加入 ModalityAligner **以及** `unfreeze_first_k=2`（额外解冻 2 层 GPT-2）。因此 MSE 2.52 → 3.04 的劣化**不能单独归因于"强制使用文本"**，部分或全部可能来自解冻带来的优化难度变化。用该对比"证明"LN 捷径，在因果上不成立。

> **【订正3】** "论文在说谎"属于对**主观意图**的指控，任何代码与数值结果都无法证明。且我们不具备作者代码，缺乏判定所需的关键证据。此类表述一旦写入学位论文或答辩材料，风险极高且无法自证，应当删除。

> **【订正4】** "多模态注意力是关键机制"这一更强表述**未被注意力模式支持**，但"论文在说谎 / 无法复现"仍不可证。原版架构的平均文本注意力仅 **0.526× 机会水平（低于随机）**，并无"主导性跨模态关注"；真正将文本以高注意力路由的 **ModalityAligner（峰值 67×）是本课题自定义的模块，不在原论文中**。因此本复现支持"文本有真实但小且间接的贡献"，但**不支持**"多模态注意力是原论文性能主要来源"这一推断。用户关于"原论文多模态注意力被夸大"的直觉**部分成立**；但"说谎""无法复现"属主观意图与作者实现层面，本复现无证据支撑，应删除。

### 建议（方法论章节可采用的写法）

建议采用如下可辩护的表述，它既如实报告了复现发现，又不越过证据边界：

1. **关于多模态机制**："在我们的独立实现中，移除文本输入编码器会造成统计显著的性能损失（ΔMSE +0.705, p=0.011），表明文本模态**确实参与了预测**。但注意力质量分析显示，时序 query 对文本的平均注意力仅 **0.526× 机会水平（峰值 34×）**，即文本是被**稀疏、定点**使用的，**并非主导性的跨模态关注**；原论文'多模态注意力是关键机制'的表述在本复现的注意力模式下**未得到支持**。"
2. **关于 LayerNorm 的作用**："文本 LayerNorm 可解释文本总贡献的 44.4%，但其单独移除的效应未达显著（p=0.154），且移除后文本注意力模式几乎不变。因此'增益纯由 LN 统计效应导致'的解释**未获支持**；同时也提示 LN 贡献了相当比重，值得在正文中如实报告这一构成。"
3. **关于复现差距**："本复现的 L=24 MSE 为 2.519，与论文报告的 1.542 存在 1.63× 差距；四 horizon 平均差距为 2.21×。由于论文未公开代码与部分实验细节（见问题四），**我们无法判定差距来源**，该差距同样可能与本报告的实现选择有关。"
4. **关于原流程图的处置**：建议将 `plot_attention_proof.py` 中"proves the original MIFlu gain was a LayerNorm statistical shortcut"的图注**删除或改写**，因为该"证明"依赖被混淆的对比与不可作为证据的统计量。

### 代码验证结果（本次复现实验新增结果汇总）

> **来源标注：(b) 本次复现实验新增结果**（除非另注明）

| # | 核验项 | 结果 | 判定 |
|---|---|---|---|
| 1 | 原版架构平均文本注意力（相对机会） | 0.526× 机会水平（峰值 34.1×） | 平均低于随机、文本被稀疏使用；①由 no_multi 功能消融否定 |
| 2 | 彻底移除文本（no_multi） | ΔMSE +0.7049, p=0.0108 | 文本贡献显著 → ①不成立 |
| 3 | 仅移除文本 LN（no_text_ln） | ΔMSE +0.3129, p=0.1543（不显著） | ②不成立 |
| 4 | 文本贡献中 LN 可解释比例 | 44.4%（残差 55.6% 非 LN 路径） | ②不成立 |
| 5 | 移除 LN 后文本注意力变化 | 0.526× → 0.548×（≈4%） | 机制上不支持 LN 捷径 |
| 6 | 架构冻结范围 | 论文 Section IV 已公开披露 | ③成立但非隐瞒 |
| 7 | 与论文数值差距 | MSE 1.63× (L=24) / 2.21× (四 horizon 均值) | ⑤部分成立 |

**HPC 作业**：`521890`（`scripts/submit_q6_attention_audit.sh`，stingy 分区 / A100 / 16G，注意力审计，约 2 分钟）。本次核验**未新增训练作业**——所有消融与配方实验此前均已完成 10 rep。

---

## 参考文献 / 证据链接汇总

1. Kramer SC, Shaman J. Development and validation of influenza forecasting for 64 temperate and tropical countries. *PLOS Computational Biology*, 2019. DOI: 10.1371/journal.pcbi.1006742. https://journals.plos.org/ploscompbiol/article?id=10.1371%2Fjournal.pcbi.1006742
2. McDonald et al. Flusion: Integrating multiple data sources for accurate influenza predictions. arXiv:2407.19054 / ScienceDirect. https://www.sciencedirect.com/science/article/pii/S1755436524000719
3. Evaluation of FluSight influenza forecasting in the 2021–22 and 2022–23 seasons with a new target laboratory-confirmed influenza hospitalizations. *Nature Communications* / PMC, 2024. https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11282251/
4. Expanding optimization ensemble model methods for forecasting seasonal influenza in the U.S. medRxiv 2025.11.24.25340597 / ScienceDirect. https://www.medrxiv.org/content/10.1101/2025.11.24.25340597.full.pdf
5. Washington State Influenza Summary 2020–2021 Season. WA Dept. of Health. https://doh.wa.gov/sites/default/files/2022-02/420-100-FluUpdateSeason2021.pdf
6. Decreased Seasonal Influenza Rates Detected in a Crowdsourced ILI Surveillance System During the COVID-19 Pandemic. *JMIR Public Health Surveill*, 2023. DOI: 10.2196/40216. https://doi.org/10.2196/40216
7. Influenza's Plummeting During the COVID-19 Pandemic: The Roles of Mask-Wearing, Mobility Change, and SARS-CoV-2 Interference. PMC8808434. https://pmc.ncbi.nlm.nih.gov/articles/PMC8808434/
8. CDC FluView Summary ending on April 3, 2021. https://www.cdc.gov/flu/weekly/weeklyarchives2020-2021/
9. Rethinking the Role of LLMs in Time Series Forecasting. arXiv:2602.14744. https://arxiv.org/html/2602.14744v2
10. Moon J, Shim J, Kim E, Hwang E. MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme. *IEEE J. Biomed. Health Inform.*, vol.29, no.10, pp.7790–7801, Oct. 2025. DOI: 10.1109/JBHI.2025.3561214.
11. Enhancing Influenza-Like Illness forecasting: An ensemble approach combining mathematical and deep learning models amidst the COVID-19 pandemic. ScienceDirect, 2026. https://www.sciencedirect.com/science/article/pii/S1755436526000174
12. MeteoGST: Meteorology-Driven Spatiotemporal Graph Learning for Epidemic Influenza Forecasting. *Applied Sciences* (MDPI), 2026. https://doi.org/10.3390/app16157586
