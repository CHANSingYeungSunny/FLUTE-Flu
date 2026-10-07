# MIFlu 创新实验与评估计划 v2

## 1. 研究目标

在已完成 MIFlu 复现的基础上，分别替换文本编码器、预测骨干和融合模块，比较 Non-LLM、预训练语言编码器、LLM 和时间序列基础模型。所有模型采用相同数据切分、scaler、horizon、seed、训练预算和评估代码。

## 2. 候选模型

- Non-LLM：DLinear/NLinear、TimesNet、PatchTST、iTransformer、TimeMixer 或 ModernTCN。
- 文本编码器：none、TF-IDF+SVD、fastText、冻结 BERT/MiniLM、原始 GPT-2。
- 融合：concat+projection、FiLM/gating、cross-attention。
- LLM/TSFM：原始 MIFlu、Time-LLM 风格 reprogramming、CALF/TimeCMA 风格跨模态对齐，以及可本地运行的 Chronos、TimesFM、Moirai 等。
- 强制负对照：zero-text、shuffled-text，用于检验增益是否来自文本语义。

## 3. 实验阶段

1. 冻结原始 MIFlu 基线、数据和 10-seed 结果。
2. 先以无文本设置筛选预测骨干：L=24/60，seed=42/43/44。
3. validation 前三名扩展到 L={24,36,48,60} 和 seed=42..51。
4. 对前两名 Non-LLM 和原始 MIFlu 比较文本编码器及融合模块。
5. 对 validation 最强三项执行全部 horizon、10 seeds、共同日期窗口、pre-COVID/COVID 分段和资源分析。
6. 冻结冠军选择后，才进行一次性 test 汇总。

## 4. 两层标准，仅保留文献标准

### 第一层：训练停止

- 仅监控 validation MSE。
- patience=7，保存最低 validation MSE 的 checkpoint，并恢复该 checkpoint。
- PTE、PIE 和峰值验收结果不参与 epoch 级 early stopping，也不控制 checkpoint 保存。

### 第二层：训练完成后的准确性验收

- PTE = |预测峰值周 - 真实峰值周|。
- PIE = |预测峰值强度 - 真实峰值强度| / 真实峰值强度。
- 唯一峰值命中标准：PTE <= 1 周且 PIE <= 25%。
- 项目代码、配置、CSV、JSON、图表和论文只实现及报告上述文献标准。

## 5. 每次独立测试必须独立保存

唯一运行键：

```text
run_id = dataset__model__text_encoder__fusion__L{horizon}__seed{seed}__timestamp__gitsha
```

每个 run 单独保存：

```text
results/innovation/runs/{run_id}/
  config_resolved.yaml
  environment.txt
  git_commit.txt
  split_manifest.json
  scaler_metadata.json
  checkpoints/best_val_mse.pt
  checkpoints/checkpoint_manifest.json
  logs/train_history.csv
  predictions/validation_predictions.csv
  predictions/test_predictions.csv
  metrics/validation_metrics.json
  metrics/test_metrics.json
  metrics/peak_metrics_by_season.csv
  figures/loss_curve.png
  figures/forecast_continuous.png
  figures/peak_timing_intensity.png
  figures/residual_diagnostics.png
  run_status.json
```

强制规则：

- 每个 model × horizon × seed 的 checkpoint、预测、指标和图均独立，禁止覆盖。
- checkpoint manifest 记录 best epoch、validation MSE、SHA-256、恢复验证和产生它的完整配置。
- validation 与 test 产物分开。模型选择程序不得读取 test 路径或 test 字段。
- 每次运行独立计算 MSE、MAE、PTE、PIE 和文献峰值命中结果。
- 每个 horizon、seed 独立出图，再生成跨 seed 汇总图。汇总图不替代原始图和预测。
- 失败、中断、跳过也写入 run_status.json。
- 顶层 registry.csv 只追加，记录 run_id、状态、路径、checkpoint hash、时间和 commit。
- 论文中的每个数字必须能追溯到 run_id、预测 CSV 和 checkpoint hash。

## 6. 冠军选择

1. 每个 run 只接受最低 validation MSE checkpoint。
2. 每个 L 计算模型 validation MSE 相对 MIFlu baseline 的比值。
3. 四个 L 等权平均得到 primary score，越低越好。
4. 候选模型在 validation 上的文献峰值命中比例不得低于 MIFlu baseline。
5. primary score 差异小于 1% 时，依次使用 validation MAE、文献峰值命中比例、可训练参数和训练时间决胜。
6. 选择过程保存为 model_selection_audit.json。冠军冻结后，才允许 test 评估。
7. 报告 10 seeds 的均值、标准差、95% CI、配对检验、效应量和 Holm 校正。差异不显著时只称 observed best。

## 7. 防数据泄漏与公平性

- scaler 与 prompt statistics 只在 train 上拟合或计算。
- test 不参与 early stopping、调参、模型选择、进化或阈值制定。
- 所有模型使用相同 split、输入窗口、horizon、target、seed 集、聚合方式和搜索预算。
- 每个 horizon 独立评分，不跨 lead time 合并预测。
- 报告总参数、可训练参数、训练时间、GPU-hours、显存和推理延迟。
- pre-COVID/COVID 比较使用共同日期交集。

## 8. PMO 的 Oracle-budget AUC 是否可迁移

### 可以迁移的核心

PMO 的可迁移思想是：在统一昂贵评估预算下，比较优化流程多快找到高质量候选。对本项目，可把“一次候选模型训练并在 validation 上评估”定义为一次 evaluator call，同时记录累计 GPU-hours、训练 steps 和候选数。横轴为预算，纵轴为截至该预算找到的最佳 validation 表现，报告 AUC-Best-so-far 以及达到 MIFlu baseline 某一性能水平所需预算。

### 不能直接迁移的部分

- 疾病预测不是分子生成，Top-10 molecules 没有自然对应物。
- 反复查询固定 validation 会造成 adaptive overfitting，因此 validation 查询预算必须固定，并保留最终 test 一次性封存。
- evaluator-call AUC 评价的是模型发现或 AutoML 流程的效率，不是最终疾病预测准确率，不能替代 MSE、MAE、PTE、PIE。
- 不应把每个 epoch 或 test 评估称为 Oracle call。论文中建议使用 evaluator call 或 validation evaluation budget。

## 9. AlphaEvolve-inspired EvoForecast 扩展臂

可以加入，但必须与主架构比较分离：

1. LLM code editor 只能修改白名单模块，例如 forecasting backbone、fusion、forecast head 和训练配置。
2. 数据切分、scaler、指标、test gate、审计代码和产物规范锁定，不可演化。
3. Evaluation cascade：静态检查 -> 单元测试 -> 1-epoch smoke test -> 小预算 validation -> 完整 validation。
4. Program database 保存 parent、diff、完整代码、配置、分数、预算、失败原因和 hash。
5. Evaluator 只返回 validation MSE/MAE、PTE/PIE 文献验收、稳定性、参数量和 GPU-hours。
6. 预注册总预算，并与 random search 及 ASHA/Hyperband 或 Bayesian optimization 在相同 GPU-hours 下比较。
7. 最终候选仍需全部 horizon、10 seeds 复训，冻结后接受一次 test。
8. 若使用公开替代系统或自建实现，命名为 AlphaEvolve-inspired，不声称完整复现 AlphaEvolve。

## 10. 是否应纳入主论文

- **主论文必须包含**：独立 checkpoint/figure/result 保存、两层标准、完整架构消融、10-seed 统计和 test 隔离。
- **建议包含，作为次级实验**：预算曲线和 AUC-Best-so-far，用于证明模型搜索效率。
- **资源充分才纳入**：EvoForecast。它可能成为额外贡献，但会显著增加计算预算、适应性过拟合风险和论文复杂度。
- 当前检索未发现顶级论文已将 AlphaEvolve 直接用于流感或疾病预测并使用疾病预测 Oracle 闭环。因此最稳妥的表述是方法迁移探索，而不是已有范式复用。

## 11. 推荐顺序

1. 先完成 PatchTST/iTransformer/DLinear/TimesNet 等严格替换及独立产物保存。
2. 完成文本编码器、融合和负对照消融。
3. 完成 10 seeds、全部 horizon、统计检验和一次性 test。
4. 增加预算感知模型搜索效率曲线。
5. 最后以独立实验臂加入 EvoForecast，并与标准 AutoML 搜索做等预算比较。

## 12. 参考依据

- MIFlu, IEEE JBHI 2025, DOI: 10.1109/JBHI.2025.3561214.
- Kramer & Shaman, PLOS Computational Biology 2019, DOI: 10.1371/journal.pcbi.1006742.
- PatchTST, ICLR 2023.
- iTransformer, ICLR 2024 Spotlight.
- CALF, AAAI 2025.
- TimeCMA, AAAI 2025 Oral.
- Sample Efficiency Matters, NeurIPS 2022 Datasets and Benchmarks.
- AlphaEvolve, Google DeepMind technical report, 2025.
