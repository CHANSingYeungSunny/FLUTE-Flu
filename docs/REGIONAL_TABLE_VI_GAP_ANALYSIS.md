# Regional 任务 (论文 Table VI) 复现缺口清单

> 目标：完整复现 MIFlu 论文 Table VI（Regional ILI Forecasting, RMSE/PCC, 10 HHS regions, L∈{2,3,5,10,13,15,20}）。
> 本文只评估"还缺什么"，不写代码。状态基于 2026-08-17 仓库快照。

## 一、论文 Table VI 要求（权威口径，来自 MIFlu_paper.md）

- **数据**：US-Region（10 HHS regions，`num_ili` 绝对计数），199740–202018（week 40, 1997 – week 18, 2020）。
- **切分**：50:10:40（训练/验证/测试，按时间顺序），Paper §V-A / Table III。
- **任务设置**：N=10 变量，T=20 输入窗，L∈{2,3,5,10,13,15,20}，10 reps 取均值。
- **指标**：RMSE（Eq.5）+ PCC（Eq.6），均在 **de-normalized（反标准化物理单位）** 数据上计算。
- **超参**：K=4（GPT2 前 4 层），LoRA r=4，Lp=4，S=2，D=768，epochs=50（无早停），batch=32，lr=5e-4。
- **对比模型（8 个）**：MIFlu、**GPT4TS**、ReILIF(TV/S)、TFT、SAIFlu-Net、Cola-GNN、STNN、CNNRNN。
- **特殊规则**：L=1 不计；L>5 视为 long-term，L≤5 视为 short-term。

## 二、已具备（✅ 不需要再写）

| 组件 | 文件 | 状态 |
|---|---|---|
| Regional 数据下载 | `scripts/download_us_region.py` | ✅ 10 HHS, 1997–2020, num_ili |
| Regional 原始数据 | `data/raw/us_region_raw.csv` | ✅ 65.9KB 存在 |
| 数据校验 vs Table III | `scripts/verify_us_region.py` | ✅ 50:10:40 切分 + 统计对比 gold standard |
| MIFlu 全模型（Regional） | `scripts/train_regional_miflu.py` | ✅ T=20, N=10, L_list 7档, K=4, Lp=4, RMSE/PCC de-normalized |
| GPT4TS baseline（Regional） | `scripts/train_regional_baseline.py` | ✅ 同配置, htext=None |
| 模型骨架 | `scripts/miflu_model.py` | ✅ 已支持 N=10/T=20/Lp=4/K=4 |
| 文本嵌入器 | `scripts/textual_embedder.py` | ✅ full GPT2 |

## 三、缺口清单（❌ 需补充才能完整复现 Table VI）

### 缺口 1 — 6 个对比模型未实现（最关键）
Table VI 需要 8 列，目前只有 **MIFlu** 和 **GPT4TS** 两列。缺：
- ReILIF(TV/S) — 需外生时序数据（wind/temperature 或 population/pop-density）
- TFT（Temporal Fusion Transformer）
- SAIFlu-Net（LSTM + self-attention）
- Cola-GNN（GNN + RNN）
- STNN
- CNNRNN
> 论文明确："Results for the national and regional ILI forecasting models are taken from [9] and [14], respectively." 即部分对比结果应取自原论文 [9]=GPT4TS、[14]=ReILIF 等。**可行折中**：只复现 MIFlu + GPT4TS 两列（我们自己跑），其余 6 列引用原论文数值做对照（需显式标注"引用自 [14]"，非本仓库复现）。若要"完整复现全部 8 列"，则必须实现全部 6 个模型——工作量巨大，且 ReILIF 还需外生数据（缺口 2）。

### 缺口 2 — ReILIF 的外生数据缺失
ReILIF(TV) 用 time-varying 外生数据（wind/temperature），ReILIF(TV/S) 用 static 外生（population/density）。当前 `us_region_raw.csv` 只有 `num_ili`/`num_patients`/`num_providers`，**无外生变量**。要复现 ReILIF 需额外抓取/构造这些特征。

### 缺口 3 — Regional prompt 模板与 National 不一致（需核对）
`train_regional_miflu.py::build_regional_prompt` 现用"10 features ... ILI patient counts in 10 HHS regions"，且 min/max 从 `DATA_PATH` 重新读（与 `load_and_normalize` 的 train_mean/std 口径不同源）。
- 端口：论文 Table I 文本模板是否对 Regional 有专门模板？当前实现是"合理重构"，**未经论文原文逐字核对**。
- `train_min`/`train_max` 变量声明了但未被使用（dead code，line 53-54），实际用 `train_data[col].min()/max()` 重算——与 `load_and_normalize` 的 50% 切点一致（int(n*0.5)），但绕开了已算好的 `train_mean`/`train_std`，易引入口径漂移。

### 缺口 4 — Regional 没有 leakage audit / 切分边界校验脚本
National 有 `audit_channel_isolation.py` 等。Regional 的 50:10:40 切分在 `load_and_normalize` 内联实现，**无独立脚本验证** test target 起点 > val 终点、无跨窗口泄漏检查。需补一个 `audit_regional_split.py`（参考 National 审计）。

### 缺口 5 — Regional 没有独立 figure / 指标脚本
- National 有 `make_miflu_evaluation_figure.py` + `compute_miflu_indicators.py`。
- Regional 的 `train_regional_miflu.py` 只输出 CSV（`results_regional_miflu.csv`），**无可视化**（Figure 4 实际线 vs 预测线，L=2 / L=20）、**无 4 指标补充分析脚本**（Regional 论文未要求 4 指标，但复现报告通常需要）。
- 缺 `make_regional_evaluation_figure.py` 与对应 HPC 提交脚本。

### 缺口 6 — Regional HPC 提交脚本缺失
National 有 `submit_miflu_paper_protocol.sh` + `submit_miflu_array.sh`。Regional **无任何 SLURM 提交脚本**。Regional 7 档 × 10 reps × 50 epochs，单卡 A100 4h 可能不够（需评估时长或拆分档位）。需新建 `submit_regional_miflu.sh`（含 PATH-prepend conda、HF cache、stingy A100）。

### 缺口 7 — Regional 结果聚合 / 对照表脚本缺失
National 有聚合表生成。Regional 需把 MIFlu + GPT4TS（及可选的 6 引用列）汇总成 Table VI 格式（RMSE/PCC 两行或 RMSE 一列 + PCC 一列），并算相对增益（up to 26.2% vs GPT4TS, 43.0% vs ReILIF）。缺 `assemble_table_vi.py` 或等价物。

### 缺口 8 — Regional 没有 ablation（Table VIII 仅 National，但 Regional 可选）
论文 Table VIII ablation 用 National 数据集。Regional 无 ablation 要求，**非阻塞**。仅在想做 Regional 消融时补。

## 四、阻塞/风险（执行前须知）

1. **QOS 限制**：当前 HPC 单用户仅 1 pending job。Regional 7 档若串行提交，需链式 `--dependency=afterany`（参考 National L=36→48→60 方案），不能 array。
2. **时长**：Regional 50 epochs × 10 reps × 7 档，单卡可能超 4h。需先小测 L=2 单 rep 估算单档时长，再决定切分还是加 `--time`。
3. **数据 vintage 一致性**：`us_region_raw.csv` 是某次下载快照；ReILIF 等对比若引用原论文数值，需注明"非本仓库数据、非同 vintage"，否则 RMSE/PCC 不可直接比。

## 五、推荐的最小可行复现路径（不写代码，仅供参考）

- **方案 A（推荐，诚实且可行）**：复现 MIFlu + GPT4TS 两列（本仓库自跑），其余 6 列引用论文 [14]/[9] 原值并标注来源；产出 Table VI 对照表 + Figure 4（L=2, L=20）。缺口 = 缺口 3/4/5/6/7（约 5 个脚本）+ 数据校验。
- **方案 B（完整 8 列）**：额外实现 ReILIF/TFT/SAIFlu-Net/Cola-GNN/STNN/CNNRNN + 抓取外生数据。工作量极大，FYP 时间通常不允许，不推荐。

---
*生成于 2026-08-17，Step 4 (Task C) 交付物。未做任何代码修改。*
