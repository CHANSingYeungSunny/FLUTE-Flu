# 变更日志 — 导师五大疑问回复报告更新（2026-09-02）

对应交付物：
1. `MIFlu_导师五大疑问_回复报告.docx`
2. `MIFlu_导师五大疑问_回复报告.md`
3. 本变更日志

两份报告由**同一份 Markdown 源**经 `scripts/md_to_docx.py` 生成，并用
`scripts/verify_report_parity.py` 验证一致性（**PARITY: OK**，314 个内容单元全部一致）。

---

## 一、代码文件改动

### 新增脚本（6 个）

| 文件 | 对应问题 | 作用 | GPU |
|---|---|---|---|
| `scripts/q1_step_sweep.py` | Q1 | step=0..3 平行聚合扫描，覆盖 L=24/36/48/60；产出表 + 图 | 否 |
| `scripts/q2_alignment_check.py` | Q2 | 打印测试集起止日期 + pre-COVID 正常年份对齐交叉验证图 | 否 |
| `scripts/q3_scaler_sanity_check.py` | Q3 | StandardScaler 往返可逆性 + 物理量值域 sanity check | 否 |
| `scripts/q4_recipe_comparison.py` | Q4 | 配方对比整合 + Welch t 检验显著性判断 | 否 |
| `scripts/md_to_docx.py` | 交付物 1 | Markdown → .docx 转换器（stdlib，含图片/超链接/表格） | 否 |
| `scripts/verify_report_parity.py` | 交付物 1/2 | 证明 .md 与 .docx 内容完全一致的校验器 | 否 |

### 修改文件（3 个）

| 文件 | 对应问题 | 改动内容 |
|---|---|---|
| `scripts/compute_miflu_indicators.py` | Q5 | 新增 PROVENANCE 注释块：区分 (a) 文献依据（PTE/PIE 定义 + Kramer & Shaman 2019 DOI）、(b) 本课题自定义阈值（0.75 / 2.0 周 / 20% / 0.60 / match_tol）、(c) 文献中不存在的双闸门机制 |
| `scripts/early_stopping.py` | Q5 | 新增 PROVENANCE 段落：把 `peak_hit_threshold=0.7` 与双闸门机制明确标注为本课题自定义工程决策（原写 "per the advisor"）；并显式披露 0.7（保存闸门）与 0.75（判定阈值）的差异 |
| `scripts/make_submission_figures.py` | Q3 | 在 `make_continuous()` 前新增注释，明确写出"图中两条曲线均使用 train[:717] 拟合的全局 StandardScaler 还原"，并说明这与模型内部 RevIN 的区别及为何不会混用 |

### 新增产物

| 路径 | 内容 |
|---|---|
| `results/ili/metrics/q1_step_sweep.csv` | L×step 的 MSE/MAE（z 空间 + 物理空间）+ 日期覆盖 |
| `results/ili/metrics/q2_alignment_check.csv` | 各 L 的 pre-COVID / COVID 段对齐指标（r、MAE、峰值周偏差） |
| `results/ili/metrics/q3_scaler_sanity_check.csv` | 各 split 的 ILITOTAL 描述统计 + 反变换后值域 |
| `results/ili/metrics/q4_recipe_comparison.csv` | 四配方 L=24 的 mean±std + Welch t 检验结果 |
| `results/ili/figures/fig_q1_step_sweep_L24_L60.png` | 新增图（Q1） |
| `results/ili/figures/fig_q2_alignment_precovid_vs_covid.png` | 新增图（Q2） |
| `results/ili/journal_evidence/recipe_summaries/` | 从 HPC 拉取的 4 份配方 summary.csv |

---

## 二、HPC 作业

**本次报告更新未提交新的 GPU 训练作业。** 按既定方案 A，Q4 不重跑种子——
`train_ablation.py` 每次运行的 10 个 rep 即种子 42–51，已有 n=10 的 mean±std。
Q1/Q2/Q3 全部为对已导出预测 CSV 的纯重聚合，**不需要 GPU**。

| 项 | 说明 |
|---|---|
| 数据来源 | HPC Burgundy `hpc_results/journal_evidence/`：`full_H{24,36,48,60}`、`full__adamw_cosine`、`full__huber_clip`、`full__earlystop`（各 10 rep） |
| 传输方式 | `scp` 拉至本地（预测 CSV 4 份 → `data/`；配方 summary 4 份 → `results/ili/journal_evidence/recipe_summaries/`） |
| 复用的既有作业 | 本轮次早前的 `520524`（stingy / gpu-a100-03，12.34s）生成了 Q2 嵌入的 L=24 连续预测图 |
| 队列状态 | 空闲，未占用资源 |

---

## 三、报告新增 / 修改内容（按问题）

| 问题 | 新增小节 | 核心内容 |
|---|---|---|
| **Q1** | 代码验证结果 | step=0..3 × L=24/36/48/60 的 MSE 表 + 图；L=24/36 误差随 lead time 递增（与 PMC11282251 一致）；**披露 L=60 窗口止于 2020-11-08、未覆盖崩塌期，故跨 L 比较不成立** |
| **Q2** | 代码验证结果 | 测试集 **2018-01-28 → 2021-12-26**（确认覆盖 COVID 期）；pre-COVID r=0.885–0.944、峰值偏差 1 周 → 索引/绘图正确；COVID 期 r=0.656–0.691、MAE 2–3× → 支持分布漂移而非索引错位 |
| **Q3** | 代码验证结果 | 全局 StandardScaler 标注已落地；往返误差 **3.64e-12**；ILITOTAL 值域确认"几千到几万量级"；**新发现 test max / train max = 1.65×（OOD，须外推）**；**披露 Table II 精确数值无法从 PDF 提取** |
| **Q4** | 代码验证结果 | 四配方 L=24 同口径表；**Welch t 检验 p = 0.5391 / 0.2572 / 0.0748，均不显著**；gap/seed std = 0.287；按【订正】改写为"baseline 最接近原论文数字"而非"全局最优" |
| **Q5** | 代码验证结果 | 三类内容（文献 / 自定义 / 文献中不存在）已在代码中分层标注；披露 0.7 与 0.75 两个阈值的差异 |

原有"结论 / 证据 / 【订正】 / 建议"四段式结构与 12 条参考文献**全部保留，未替换或删除**。

---

## 四、必须披露的限制（已写入报告）

1. **Table II 逐格比对未完成**：`MIFlu_paper.md` §V-A 明确记载 Table II 为扫描图片、数值不可机器提取。为避免编造论文数字，改用同一数据集的实测描述统计做等价交叉验证。
2. **Q4 结论不显著**：即使在 α=0.05 下不显著，这是本次实验的结论（差异在噪声内），而非证据不足；增加种子数不会使 0.1455 的差距变为显著。
3. **L=60 的对齐指标不可与其余 horizon 同等解读**：其评估窗口未覆盖真正的 ILI 崩塌期。
4. **Word/Markdown 工具链**：本机无 `pandoc`、`python-docx`、`npm docx`；`.docx` 由自建的 stdlib 转换器生成，已通过结构完整性与内容一致性校验。

---

## 五、复现命令

```powershell
# 1) 重新生成两份报告（单一 Markdown 源）
python scripts/build_report_docx.py      # 中文文件名经 argv 会乱码，故用写死路径的包装脚本

# 2) 验证两份报告内容完全一致 + 包结构完整
python scripts/verify_report_parity.py

# 3) 重新生成各问题的证据（均不需要 GPU）
python scripts/q1_step_sweep.py
python scripts/q2_alignment_check.py
python scripts/q3_scaler_sanity_check.py
python scripts/q4_recipe_comparison.py
python scripts/q6_text_attention_audit.py      # 需 HPC/GPU（或本地 CPU 亦可）
python scripts/q6_ablation_significance.py
```

---

## 六、Q6 补充（同日追加）—— MIFlu 多模态注意力核验

### 新增脚本

| 文件 | 作用 |
|---|---|
| `scripts/q6_text_attention_audit.py` | 在**原论文架构**上 hook GPT-2 因果自注意力，测量时序 query→文本 key 的注意力质量，并与**机会水平**比较 |
| `scripts/q6_ablation_significance.py` | 消融 Welch 显著性检验 + 文本贡献的 LN / 非-LN 拆解 |
| `scripts/submit_q6_attention_audit.sh` | HPC 提交脚本（stingy / A100 / 16G） |

### HPC 作业

| 作业 | 结果 |
|---|---|
| `521872` | ❌ OOM Killed —— Slurm 将内存重置为 **1024 MB**（不足加载 GPT-2 编码器 + checkpoint） |
| `521879` | ❌ 失败 —— `full/reps_1_to_10` 的 checkpoint 输出头为 `[420,768]` = 7×**60**，即保存的是 L 扫描最后一档 **L=60**，非 L=24 |
| `521890` | ✅ 成功（约 2 分钟） |

**未新增训练作业** —— 所有消融与配方实验此前均已完成 10 rep（种子 42–51）。

### 新增产物

- `results/ili/metrics/q6_text_attention_audit.csv`
- `results/ili/metrics/q6_ablation_significance.csv`

### 核心结论（已写入报告 Q6）

| 分论点 | 判定 |
|---|---|
| ① 文本完全未被使用 | ❌ 由**功能消融**否定：no_multi 移除文本 MSE +0.705（p=0.011）。**但**平均文本注意力仅 **0.526× 机会水平（低于随机）**，文本被稀疏定点使用；"38.6% 落在文本"不能读作"文本被大量使用" |
| ② 增益纯粹来自 LayerNorm 捷径 | ❌ 否定（LN 仅占 44.4%，p=0.154 不显著；移除 LN 后注意力几乎不变） |
| ③ 架构除 PE/LN/LoRA 外冻结 | ✅ 成立，但论文 Section IV **已公开披露** |
| ④ 论文"在说谎" | ❌ 不可判定（无作者代码，无法推断意图） |
| ⑤ 无法复现 | ⚠️ 部分成立（存在真实数值差距，但不可据此断言论文有误） |

### 产出物完整性盘点（供顶刊投稿证据链核对）

| 实验 | checkpoint | summary.csv |
|---|---|---|
| full（×4 horizon：full_H24/36/48/60） | ✅ 10/10（命名 `best_model_L{L}.pt`） | ✅ |
| gated_inject / no_lora / no_text_ln | ✅ 10/10 | ✅ |
| **no_multi** | ❌ 新格式无；HPC 仅存旧版 `checkpoint.pth` | ✅ |
| **no_lora_multi** | ❌ 新格式无；HPC 仅存旧版 `checkpoint.pth` | ✅ |
| **4 个配方**（adamw_cosine / huber_clip / earlystop） | ❌ 新格式无；HPC 仅存旧版 `checkpoint.pth` | ✅ |

缺口说明：经 HPC 核查，上述变体目录**确实存在且含 10 rep 的 `checkpoint.pth`**，但这是**旧版训练脚本**的产物（HPC_GUIDE §6 "代码漂移"问题），文件名/目录结构与当前 `train_ablation.py` 的 `checkpoints/best_model_*.pt` 不一致，且无法保证出自已修复 bug 的同一份代码。为顶刊可复现性，已决定用**当前代码重跑**这 5 个变体（各约 30 min GPU，见第七节），产出统一格式的新权重。

### 待处置项

- `scripts/plot_attention_proof.py` 中 "proves the original MIFlu gain was a LayerNorm statistical shortcut" 图注**建议删除或改写**（该"证明"依赖被混淆的对比与不可作为证据的统计量）。本次未改动该文件，待确认后处理。

### HPC 重跑执行记录（本轮）

- 缺口 5 个变体（no_multi / no_lora_multi / full__adamw_cosine / full__huber_clip / full__earlystop）在 HPC 用当前 `train_ablation.py` 重跑，产出统一格式 `best_model_*.pt`（位于 `horizon_L24/rep_XX/checkpoints/`）。
- **关键 bug 修复**：原 `train_L` 缺 `rep` 形参，保存 checkpoint 时 `NameError` 崩溃（仅跑完 rep 1）。已在本地 `scripts/train_ablation.py` 补 `rep=1` 形参并从 `main()` 传入，重新上传 HPC。
- **分区策略**：`gpu_a100` 全分区（节点 07–12）六个节点**全部**报 `CUDA-capable device(s) is/are busy or unavailable`（系统性故障，当日不可用）；`stingy`（gpu-a100-03~06）健康。
  - no_multi(521998)、no_lora_multi(522020) 经 stingy 完成（各 10 ckpt）。
  - huber_clip/earlystop 初投 gpu_a100(522022/522023) 均失败；最终合并为单 stingy 作业 **522036** 串行跑完 huber_clip + earlystop + adamw_cosine（~84 min）。
- **最终核验**：5 变体各 **10 个 checkpoint（共 50）** + 各 `summary.csv`（L=24，mse_all_mean：no_multi 3.052 / no_lora_multi 2.977 / huber_clip 2.606 / earlystop 2.599 / adamw_cosine 2.502）。本地已镜像 `summary.csv`+`metrics.csv` 至 `results/ili/journal_evidence/<variant>/reps_1_to_10/`；大模型权重（每变体 ~6.2GB，含冻结 GPT2 文本嵌入器）仍存 HPC 供投稿引用。

### 补充诊断指标精简：四项 → 两项（PTE / PIE），彻底移除 Peak Hit Rate 与 Direction（2026-09）

**决策**：图形与报告中只保留 **PTE（Peak Timing Error，峰值时间误差）** 与 **PIE（Peak Intensity Error，峰值强度误差）**；`peak_hit_rate`（峰值命中率）与 `directional_accuracy`（方向准确率）**彻底移除**——不再计算、不再判定、不出现在任何图形/表格中。

**关键正确性保障**：PTE/PIE **只在匹配峰值上定义**（`hit_rows = peak_df[status=="Hit"]`），故**保留** `peak_hit_count`（如 "2/3"）、`n_hit`、`n_missed` 作为**样本量限定语**，图中写作 `PTE = 1.5 wk (based on 2/3 matched peaks)`。该计数是限定语，**不是被报告的指标**。若连计数一并删除，PTE/PIE 会退化为无法判断样本量的裸数字，易被审稿人质疑。

**改动清单**：
- `scripts/compute_miflu_indicators.py`：删 `peak_hit_rate` 计算、`directional_accuracy` 计算（**保留** STL 趋势强度 beta/zeta）、两项 verdict、CLI `--thr_peak_hit_rate` / `--thr_directional_accuracy`；`verdicts()` 签名去掉已无用的 `trend` 形参；`[CONTEXT]` 输出改为只报匹配峰计数。
- `scripts/early_stopping.py`：**双闸门机制移除**，类 `PeakAwareEarlyStopping` → `EarlyStopping`（纯 val_loss + patience）；删 `peak_metrics()`、`degraded` 分支、`peak_hit_threshold`；`_self_check()` 重写为纯早停断言。
- `scripts/train_ablation.py`：同步 import / `train_L` 签名 / 传参 / 每 epoch 逻辑 / `metrics.csv` 列 / checkpoint_meta `selection` / CLI；`evaluate()` 不再返回仅供闸门使用的 `val_gt/val_pred`（改为 6 返回值，2 处调用点同步）。
- `scripts/make_miflu_evaluation_figure.py`、`scripts/make_submission_figures.py`：指标框只留 PTE / PIE 两行（带 matched-peaks 限定语），verdict 表与 `thr` 字典同步。
- `scripts/summarize_regional_table_vi.py`：表列改为 `PTE (wk)` / `PIE (%)` / `Matched peaks` / `Missed peaks`。
- `scripts/run_journal_experiments.py`、`scripts/submit_journal_job2.sh`：移除已删除的 `--peak-hit-threshold`（否则 argparse 直接崩溃）。
- 文档/报告同步：`docs/ILI_FOUR_INDICATORS.md`（四项→两项）、`docs/FIGURE_STYLE_GUIDE.md`、`docs/Tutor_QA_Draft_2026-08-17.md`（加口径变更警示）、`MIFlu_导师五大疑问_回复报告.md`（订正3 改为"已移除"、证据表 (b)/(c) 更新）、`导师五大疑问_零基础解答报告_最终版.md`（Q5 重写）、`Advisor_Questions_Resolution_Report.md`、`MIFlu_论文完整解析与答辩解答.md`、`MIFlu_paper_analysis_and_defense_EN.md`、`README.md`、`REPRODUCIBILITY.md`、`PROJECT_STATUS.md`、`hpc_results/journal_evidence/README.md`。
- 产物重生成：`miflu_L{24,36,48,60}_ili_peak_trend_summary.json`、`miflu_ili_*`、`miflu_verdict_table*.md`、4 个 horizon 的 `fig_miflu_eval_{continuous,diagnostics}_L*.png`、`National_Table_V_summary.{md,csv}`。

**验证**：`early_stopping.py` 自检 OK；`tests/test_timing_metric.py` 通过；3 个脚本 `py_compile` 通过；报告 `.md` → `.docx` 重生成，**PARITY: OK（504 单元）**。

**后续必做**：`full__earlystop` 使用过早停，双闸门移除后训练行为改变，已完成的旧结果**失效**，需在 HPC 重跑（stingy，约 28 分钟）。其余变体为固定 20 epoch，不受影响。

**已知限制（本次发现）**：`scripts/md_to_docx.py` 无法处理**块引用（`>`）内含行内代码反引号**的情况——该段会被静默丢弃，`verify_report_parity.py` 会报 FAIL。写法上需避免在 `>` 引用块中使用反引号。

**未改动（待定）**：`make_miflu_evaluation_figure.py` 诊断图的**左 panel「Rolling Directional Accuracy (13-wk)」**仍保留（已批准计划未包含移除它）。它与被删的 `directional_accuracy` 指标同源，若要求"图里只有 PTE/PIE"，需另行确认后删除该 panel。

---

## 七、Q6 表述修正（本轮追加）

用户质疑报告中"原版架构 38.6% 注意力落在文本上"可能被 ModalityAligner 污染（其记忆 text→time 占比 < 0.001）。核查结果：

1. **污染担忧不成立**：审计脚本 `q6_text_attention_audit.py` 的 `full_L24` 配置为 `gated_inject=False`、目录 `full_H24`，属**基础模型**，与 ModalityAligner 无关。用户记忆的 `<0.001` 对应 modality aligner 行 `observed_text_mass=0.00271`（恰好均匀，1.000×）。
2. **但 38.6% 被误读**：实测 `observed_text_mass=0.3858` vs 机会基线 `0.7347` → `mass_ratio_vs_chance=0.5256`（<1，低于随机因果基线）。文本占序列 55.6%，故"38.6% 落在文本"实为**低于随机**；文本是被**稀疏、定点**使用（仅峰值 34×）。故原"文本被大量使用"的措辞错误。
3. 文本"确实参与预测"的**硬证据**来自 `no_multi` 功能消融（ΔMSE +0.705, p=0.011），而非注意力质量。

报告 Q6 已据上述修正：① 依据改为功能消融；证据表改用原始数值（0.3858 / 0.7347 / 0.526×）并加注"低于随机"；判读 1 重写；**新增【订正4】**说明"多模态注意力是关键机制"未被注意力模式支持、真正高路由的 ModalityAligner（峰值 67×）不在原论文中（用户直觉部分成立）；建议 1 与验证表 #1 同步改写。

- `MIFlu_导师五大疑问_回复报告.docx` 由 `scripts/build_report_docx.py`（绕过中文文件名 argv 乱码）重新生成；`verify_report_parity.py` 复验 **PARITY: OK（504 个内容单元）**。
- 图注 `plot_attention_proof.py` 处置：仍待确认（见待处置项）。

---

## 八、Q1 图按 step 拆分（2026-09-07）

- 用户要求把问题一的 Q1 图按 **step size** 拆分为独立照片。原 `fig_q1_step_sweep_L24_L60.png`（2×3 拼图）**已移除**：`scripts/q1_step_sweep.py` 删除 `make_figure()` 与 `OUT_FIG`，仅保留 `make_per_step_figures()`；磁盘 PNG 已删除。
- 新增 4 张按 step 拆分的图：`fig_q1_step_sweep_L24_L60_step{0,1,2,3}.png`（每张含 L=24/36/48/60 四个 horizon 子图，仍各自独立、不跨 horizon 合并）。
- 报告 `MIFlu_导师五大疑问_回复报告.md` 问题一 章节：原单图引用替换为 4 张 step 拆分图引用；产物说明同步更新。
- 重新生成 `MIFlu_导师五大疑问_回复报告.docx`：`md_to_docx.py` 嵌入 8 图、`verify_report_parity.py` 复验 **PARITY: OK（504 单元，8 引用 == 8 嵌入）**。
- 注：本机 Windows 控制台为 cp950，脚本打印中文路径会 `UnicodeEncodeError`；运行报告管线需设 `PYTHONIOENCODING=utf-8`（转换本身在报错前已写盘，但校验会因打印异常中断）。
