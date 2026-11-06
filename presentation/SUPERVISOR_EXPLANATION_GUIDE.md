# Supervisor explanation guide

This mirrors the Q01–Q25 material embedded beside the tables in both internal reports. Use the DOCX/PDF for the complete figures, tables and context.

## Q01  §1  Why use 676 training, 97 validation and 193 test rows?

为什么采用 676 行训练、97 行验证、193 行测试？

**Answer and local evidence / 直接回答与本地证据**

The supplied 966-row protocol reserves floor(966 × 0.7) = 676 rows for training and floor(966 × 0.2) = 193 for testing. The remaining 97 form validation. Training fits weights and scaling, validation chooses checkpoints, and the final test block estimates performance after that choice. Chronological order keeps later observations out of earlier training. This is the declared project protocol, not a universal journal requirement. The independently pinned upstream split is still unverified.

所附 966 行协议把 floor(966 × 0.7) = 676 行分给训练，floor(966 × 0.2) = 193 行分给测试，其余 97 行用于验证。训练段拟合权重和标准化参数，验证段选择检查点，最终测试段评价选择后的表现。按时间先后划分，可以避免用后来的观测训练较早的预测。这是本项目采用的协议，并非所有期刊统一要求；固定版本上游协议仍待独立核实。

**Paper-based reasoning / 文献依据与选择理由**

Tan et al. explicitly use 70/10/20 for Illness [13, §3.3], while iTransformer preserves chronological separation [5, App. A.1]. These provide a concrete forecasting precedent: retain enough training data, use validation for model selection, and reserve later observations for the final test. The exact 676/97/193 integers come from our 966 rows and rounding rule. The literature supports the design rationale; it does not prove that this ratio is optimal for every influenza season or that our upstream file identity is established.

Tan 等明确对 Illness 使用 70/10/20 [13，第 3.3 节]，iTransformer 则保持按时间分离 [5，附录 A.1]。这是具体的预测研究先例：保留较多训练数据，以验证集选模，再用较晚观测做最终测试。676/97/193 的精确整数来自本项目 966 行及取整规则。文献支持设计理由，但不证明该比例对所有流感季最优，也不能证明本地文件与上游身份一致。

**Supervisor short answer / 导师简答**

The split follows an Illness precedent in Tan et al.; chronological separation protects the final evaluation [13, 5].

这个划分有 Tan 等 Illness 实验的先例，时间分离用于保护最终评价 [13, 5]。

Reading locator / 论文位置: Tan et al. [13], §3.3 Datasets and Evaluation Metrics; iTransformer [5], Appendix A.1.

Project evidence / 本地证据: configs.py DATA_PROFILES[author_repo_966]; BENCH_MSE_BY_MODEL_L.csv; eval_windows.py

## Q02  §1  Why score 160 windows when 170 are available at L24?

L24 明明有 170 个窗口，为什么只评 160 个？

**Answer and local evidence / 直接回答与本地证据**

The local evaluation contract preserves complete batches of 16: (W//16)×16. Thus 170/158/146/134 available windows become 160/144/144/128 scored windows at L24/36/48/60. Using the same retained windows across models prevents a comparison of different test examples. Cropping can nevertheless change scores by removing a particular tail of time. It is a comparability choice inherited by this snapshot, not evidence that cropping is scientifically optimal. Full-window sensitivity remains necessary; a specific discarded-tail difficulty ratio was not independently reverified.

本地评测约定只保留完整的 16 个窗口一批，即 (W//16)×16。因此 L24/36/48/60 的 170/158/146/134 个可用窗口变成 160/144/144/128 个计分窗口。所有模型使用相同窗口，可避免拿不同测试样本比较。但裁剪会删去某一段时间尾部，仍可能改变分数。这是本快照为保持可比性采用的选择，不证明裁剪在科学上最优；仍需完整窗口敏感性分析。本次没有独立复核某个被删尾部的具体难度倍数。

**Paper-based reasoning / 文献依据与选择理由**

Tan et al. retain original data-loaders and training conditions during their reproduction checks [13, §3.1]. This supports disclosing exactly which examples are scored; it does not require cropping. Our complete-batch rule changes the scoring population. Giving every model the same retained windows removes a comparison unfairness, but deleting the tail can still alter the result. The necessary sensitivity analysis is to score every model on all available windows and compare rankings. A literature citation cannot establish our discarded-tail difficulty without its raw calculation.

Tan 等复核时保留原数据加载器与训练条件 [13，第 3.1 节]，说明必须交代哪些样本进入计分，却不表示论文要求裁剪。本地完整批量规则改变了计分样本。各模型采用相同保留窗口，可消除比较不公平，但删去尾部仍可能改变结果。必要的敏感性分析是让所有模型在完整窗口重评分，再比较排名。文献不能代替被删尾部难度的原始计算。

**Supervisor short answer / 导师简答**

Cropping preserves a shared scoring population; full-window rescoring tests its effect [13].

裁剪用于统一计分样本，完整窗口重评分用于检验裁剪影响 [13]。

Reading locator / 论文位置: Tan et al. [13], §3.1 Reproducibility Note; local eval_windows.py.

Project evidence / 本地证据: BENCH_MSE_BY_MODEL_L.csv; eval_windows.py; scripts/verify_snapshot.py --raw-smoke

## Q03  §1  Why fit scaling on training data only?

为什么标准化参数只能从训练段计算？

**Answer and local evidence / 直接回答与本地证据**

A mean or standard deviation fitted on the complete series would use information from the future test block. Train-only scaling keeps that information out of model preparation. Each channel is standardised separately. The local equality check compares seven matching numeric columns in the two supplied files and finds maximum absolute difference zero. That verifies numeric equality of these local copies, not byte identity with a newly downloaded author file.

如果用完整序列计算均值或标准差，就会把未来测试段的信息带入模型准备过程。只在训练段拟合，可避免这类信息泄漏。七个通道分别标准化。本次一致性检查比较所附两个文件的七个对应数值列，最大绝对差为零。这只能核实本地副本数值一致，不能代替重新下载作者文件后核实字节一致。

**Paper-based reasoning / 文献依据与选择理由**

Kapoor and Narayanan identify preprocessing across the training/test boundary as a leakage route [22, L1.2]. Here that means fitting channel means and standard deviations only on training, then reusing them. If future observations determine these constants, preparation has already adapted to the held-out distribution even without using test labels in gradient updates. This makes train-only scaling part of the experiment. The separate local file-equality check establishes matching inputs, not absence of every possible leakage route.

Kapoor 与 Narayanan 把跨越训练/测试边界的预处理列为泄漏路径 [22，L1.2]。用于这里，就是只在训练段拟合各通道均值和标准差，再原样复用。如果未来观测决定这些常数，预处理已适应留出分布，即使梯度更新没有使用测试标签。因此训练段标准化属于实验设计。本地文件相等检查则只证明输入一致，不能证明所有泄漏路径均不存在。

**Supervisor short answer / 导师简答**

Preprocessing is fitted on training only, following the leakage distinction in Kapoor and Narayanan [22].

依照 Kapoor 与 Narayanan 对泄漏的区分，预处理只在训练段拟合 [22]。

Reading locator / 论文位置: Kapoor and Narayanan [22], Results, leakage taxonomy L1 and L1.2.

Project evidence / 本地证据: 06_原始数据集/scaler_miflu_author966.json; scripts/verify_snapshot.py

## Q04  §2  Why ten reproduction seeds but three benchmark seeds?

为什么复现用十个种子，基准却用三个种子？

**Answer and local evidence / 直接回答与本地证据**

They answer different questions. The supplied reproduction uses seeds 2021–2030 to compare with the transcribed paper table. The broader benchmark uses 42/43/44 to compare implementations under one shared protocol. The retained matrix is 28 models × 4 horizons × 3 seeds = 336 cells. Ten seeds would require 1,120 cells. Three reflects the project compute budget; it does not prove adequate power, and additional seeds can improve uncertainty estimation. Neither a universal three-seed venue rule nor zero benefit from more seeds is established.

两者回答不同问题。所附复现以 2021–2030 十个种子对照转录的原文表格；更广的基准以 42/43/44 三个种子在统一协议下比较各实现。正式矩阵为 28 模型 × 4 跨度 × 3 种子 = 336 单元；十个种子则需要 1,120 单元。采用三个种子反映项目算力预算，不证明检验功效已经足够，更多种子也可能改善不确定性估计。本次没有证据支持所有场合均要求三个种子，或增加种子毫无收益。

**Paper-based reasoning / 文献依据与选择理由**

The original three-seed citation is incorrect. PatchTST uses fixed-seed main results plus a five-seed supervised robustness check [3, App. A.6.1]; iTransformer reports five-run standard deviations [5, App. A.2, Table 5]. Neither passage establishes three seeds as their shared convention. Our choice is a compute compromise. Bouthillier et al. distinguish repeated-run precision from broader benchmark variation [19]. Extra seeds can improve the former; extra seasons/origins address different uncertainty. Ten reproduction repetitions do not make the separate three-seed benchmark equally precise.

原来的三种子引用不正确。PatchTST 的主结果采用固定种子，另做五种子监督稳健性检查 [3，附录 A.6.1]；iTransformer 报告五次运行的标准差 [5，附录 A.2 表 5]。这些段落不能证明三种子是两文共同惯例。我们的选择属于算力折衷。Bouthillier 等区分重复运行精度和更广的基准变异 [19]：增加种子可改善前者，增加季节/原点处理另一类不确定性。十次复现不会让独立的三种子基准同样精确。

**Supervisor short answer / 导师简答**

Three seeds are our compute compromise. Both cited papers provide five-seed robustness evidence, motivating stronger checks [3, 5].

三种子是算力折衷；两篇所引论文实际提供五种子稳健性证据，提示仍需加强检查 [3, 5]。

Reading locator / 论文位置: PatchTST [3], Appendix A.6.1; iTransformer [5], Appendix A.2 and Table 5; Bouthillier et al. [19], Appendix C.3.

Project evidence / 本地证据: ESSAY_VS_REPRODUCTION_TABLE_V.csv; BENCH_MSE_BY_MODEL_L.csv; dlv/data.py ORACLE

## Q05  §2  Which implementation differences are established?

哪些实现差异已经核实，哪些仍只是待核实的说法？

**Answer and local evidence / 直接回答与本地证据**

The local code selects checkpoints on validation and scores all seven standardised channels. Supplied notes attribute test-selected checkpoints and a one-channel loader to upstream code, but no independently inspected pinned author checkout supports that attribution here. Notes also describe differences in learning-rate and epoch settings. Consequently we disclose the local procedure and unresolved reference settings rather than claiming that exactly two repairs explain every score difference. A fair causal comparison would hold data, seeds and all other settings fixed while changing one factor.

已检查的本地代码在验证段选择检查点，并对七个标准化通道计分。交接笔记把测试集选检查点和单通道加载问题归于上游代码，但本次没有独立检查到固定版本作者仓库来支持该归因。笔记还提到学习率和训练轮数设置差异。因此应披露本地流程与未核实的参考设置，不能声称只有两处修复就解释全部分数差异。若要确认因果，应固定数据、种子及其他设置，每次只改变一个因素。

**Paper-based reasoning / 文献依据与选择理由**

A checkpoint is a model-selection choice. Selecting it by test error uses the final evaluation to fit that choice, contrary to clean separation [22, L1]. This justifies our validation-selected checkpoint independently of whether a particular upstream bug can be proved. Scoring all seven declared channels is a separate metric-consistency issue. Neither principle proves Moon et al. committed the alleged defects or that exactly two changes caused our gap. Causal attribution needs matched runs changing checkpoint selection, loader or another factor one at a time.

检查点属于选模选择；按测试误差挑选，就是用最终评价拟合该选择，不符合干净分离 [22，L1]。不论上游缺陷是否能证实，这个原则都支持本地验证集选检查点。按声明的七通道计分则是另一项指标一致性问题。这些原则不能证明 Moon 等犯了所指缺陷，也不能证明差距仅由两项改变造成。因果归因需要配对运行，每次只改变检查点、加载器或另一项因素。

**Supervisor short answer / 导师简答**

Validation selection protects the held-out test; upstream defect attribution is a separate evidence question [22].

验证集选模保护留出测试；上游是否有缺陷，须另有证据 [22]。

Reading locator / 论文位置: Kapoor and Narayanan [22], taxonomy L1, clean separation through modelling and evaluation.

Project evidence / 本地证据: train_miflu.py; audit/REPO_AUDIT.md; audit/UNVERIFIED_ITEMS.md

## Q06  §2  Why use seven-variable MSE but ILITOTAL peak errors?

为什么 MSE 用七变量，而峰值误差只用 ILITOTAL？

**Answer and local evidence / 直接回答与本地证据**

Seven-variable MSE averages squared errors after each channel has been standardised, so it measures overall dimensionless forecast error. This average loss is not itself a patient-count time series and has no single inverse scaler. Peak timing and height require an actual series. We therefore compute them on ILITOTAL after its own training-fit inverse transform, with mean 9,439.84 and standard deviation 9,003.15 patients. A model can do well across seven channels while having worse ILITOTAL peaks. Different targets and loss functions help explain the different rankings.

七变量 MSE 先逐通道标准化，再平均平方误差，衡量整体无量纲预测误差。这个平均损失不是患者人数时间序列，也没有一个统一的反标准化器。峰值时间与高度则必须针对一条真实序列。因此本项目对 ILITOTAL 使用其训练段标准化参数反变换，均值为 9,439.84、标准差为 9,003.15 人。一个模型可以在七通道总体误差上较好，但在 ILITOTAL 峰值上较差。评价对象与损失函数不同，是排名变化的一个解释。

**Paper-based reasoning / 文献依据与选择理由**

Hyndman and Koehler explain why measurement scale matters [21, §2.1]; Kramer and Shaman define peaks on an observed disease series [2]. Our standardised aggregate divides each channel’s squared error in original units by its training variance. The result is a dimensionless loss, not a patient-count curve with one inverse scaler. For peaks, inverse-transform ILITOTAL predictions and observations first, then locate peaks. Taking a peak of the seven-channel loss would answer a different question. Literature motivates an interpretable endpoint; ILITOTAL is our explicit operational choice.

Hyndman 与 Koehler 解释尺度为何重要 [21，第 2.1 节]；Kramer 与 Shaman 在观测疾病序列上定义峰值 [2]。本项目标准化总体损失将各通道原单位平方误差除以训练方差，所得是无量纲损失，而非可用一组参数反变换的患者人数曲线。峰值评测应先反变换 ILITOTAL 预测和观测，再找峰；对七通道损失找峰会回答另一个问题。文献支持可解释端点，ILITOTAL 是明确的项目选择。

**Supervisor short answer / 导师简答**

Overall standardised error and an interpretable disease peak are different endpoints [21, 2].

标准化整体误差与可解释疾病峰值，是不同端点 [21, 2]。

Reading locator / 论文位置: Hyndman and Koehler [21], §2.1; Kramer and Shaman [2], Forecast accuracy and comparison.

Project evidence / 本地证据: BENCH_MSE_BY_MODEL_L.csv; BENCH_PTE_PIE_BY_STEP.csv; scaler_miflu_author966.json

## Q07  §3  Why is MIFlu 1.4995 here but 1.5574 in the benchmark?

为什么这里的 MIFlu 是 1.4995，基准表却是 1.5574？

**Answer and local evidence / 直接回答与本地证据**

The first is the four-horizon mean from the ten-seed reproduction table. The second is the four-horizon mean under the three benchmark seeds. They summarise separate run sets. Compare 1.4995 with the reported paper mean 1.4355 for reproduction, and compare 1.5574 with other models in the benchmark for model selection. Their difference is not a demonstrated improvement, degradation or transcription error between two otherwise identical experiments. Full run configuration and raw provenance are required to attribute it.

前者来自十种子复现表的四跨度均值，后者来自三个基准种子的四跨度均值，它们汇总的是不同运行集合。讨论复现时，应把 1.4995 与原文转录均值 1.4355 比较；讨论选模时，应把 1.5574 与同一基准中的其他模型比较。两数之差并不能证明在其他条件完全一致时模型进步、退步或抄错；归因还需要完整运行配置与原始来源。

**Paper-based reasoning / 文献依据与选择理由**

Bouthillier et al. show that benchmark estimates depend on the sampled learning pipeline [19]. A mean is therefore an estimate over specified runs, not an immutable property of a model name. Our two MIFlu estimates summarise separate seed sets and serve different comparisons. The gap could combine seed variability with configuration differences; it does not isolate one cause. Explain each table’s run definition first, then request matched run-level configurations if the cause of the difference matters.

Bouthillier 等说明基准估计取决于被抽样的学习流程 [19]。均值是指定运行集合的估计，不是模型名称自带的不变属性。两项 MIFlu 估计汇总不同种子集合，服务不同对照。差值可能同时包含种子波动与配置差异，不能分离某一原因。应先解释两表运行定义；若关心成因，再取回匹配的逐运行配置。

**Supervisor short answer / 导师简答**

They estimate separate run sets; the difference is not a controlled effect of one change [19].

两数估计不同运行集合，不能把差值视为一项改变的受控效果 [19]。

Reading locator / 论文位置: Bouthillier et al. [19], §§2–3, benchmark estimators and sources of variation.

Project evidence / 本地证据: ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6; BENCH_MSE_BY_MODEL_L.csv model=miflu

## Q08  §3  Why do MSE and MAE give different sign patterns?

为什么 MSE 与 MAE 的逐跨度方向不完全一致？

**Answer and local evidence / 直接回答与本地证据**

MSE squares errors and gives larger errors more weight. MAE averages absolute errors. Changing a few large errors can therefore alter MSE and MAE differently. Relative to the paper values, MSE is lower at L24/L36 and higher at L48/L60, whereas MAE is lower only at L36 and higher at the other three. The means are +4.5% MSE and +7.9% MAE. Calling both a two-versus-two crossover would misread the table.

MSE 对误差平方，因此更重视大误差；MAE 平均绝对误差。因此，少数大误差的变化可能对两者产生不同影响。相对原文转录值，MSE 在 L24/L36 较低、L48/L60 较高；MAE 只有 L36 较低，其他三个跨度较高。平均差为 MSE +4.5%、MAE +7.9%。不能把两者都说成两低两高。

**Paper-based reasoning / 文献依据与选择理由**

The paper distinguishes squared and absolute errors and their sensitivity to large residuals [21]. As an algebraic illustration, not an observed run, doubling a residual doubles its absolute contribution but quadruples its squared contribution. A changed residual distribution can thus move MSE and MAE differently. Our CSV determines the actual horizon signs; the literature explains why different signs are possible. Per-channel and per-window residuals, rather than this general principle alone, are needed to identify the actual errors behind the gap.

该文区分平方与绝对误差，以及两者对大残差的敏感性 [21]。作代数示例而非实测：残差翻倍，绝对贡献变两倍，平方贡献变四倍。因此残差分布改变时，MSE 与 MAE 可以不同向。CSV 确定实际逐跨度符号，文献解释为何可能不同。若要确定哪些误差造成差距，仍需逐通道、逐窗口残差，不能只靠一般原理。

**Supervisor short answer / 导师简答**

MSE weights large residuals more strongly than MAE, so the horizon signs must be read separately [21].

MSE 更重视大残差，逐跨度方向必须与 MAE 分开读取 [21]。

Reading locator / 论文位置: Hyndman and Koehler [21], §2.1, MSE/MAE and sensitivity to large residuals.

Project evidence / 本地证据: ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6

## Q09  §3  Do the seed oracle and plots prove a complete reproduction?

种子 oracle 和预测曲线能证明已完整复现吗？

**Answer and local evidence / 直接回答与本地证据**

The oracle is a code-transcribed record of ten seed scores. Its means and standard deviations can be checked arithmetically, but the corresponding raw ten-seed logs and predictions are not supplied for independent rescoring. The imported plots illustrate the benchmark series and are not independent traces of those ten reproduction runs. Checkpoint choice, seed variability and configuration differences are possible explanations for the horizon pattern, not isolated causal findings. The defensible result is a +4.5% mean-MSE gap under disclosed limits.

oracle 是代码中转录的十种子分数记录，可以核算均值和标准差，但没有提供对应十种子的原始日志与预测供独立重评分。沿用曲线展示基准序列，不是这些十种子复现运行的独立轨迹。检查点选择、种子波动和配置差异都可能解释逐跨度表现，但尚未分离其因果作用。可辩护的结果是在明确限制下，平均 MSE 差为 +4.5%。

**Paper-based reasoning / 文献依据与选择理由**

Repeated-run estimates and traceable evaluation address different weaknesses [19, 22]. The oracle checks the arithmetic of a transcribed record; saved predictions would check whether the pipeline produced it. The practical chain is run configuration → prediction → scoring code → cell → aggregate. A benchmark plot is another summary and cannot establish a ten-seed reproduction trajectory. Missing links limit the claim even when the mean is close. The imported panels remain useful illustrations if their true provenance is stated.

重复运行估计与可追溯评测处理不同缺口 [19, 22]。oracle 核对转录记录的算术，保存预测才可核对流程是否产生该记录。实际链条是运行配置 → 预测 → 计分代码 → 单元 → 聚合。基准图是另一种摘要，不能建立十种子复现轨迹。即使均值接近，链条缺项仍限制主张；只要说明真实来源，沿用曲线仍可作示例。

**Supervisor short answer / 导师简答**

The oracle establishes arithmetic; raw outputs establish provenance. Both evidence levels matter [19, 22].

oracle 建立算术证据，原始输出建立来源证据，两者都重要 [19, 22]。

Reading locator / 论文位置: Bouthillier et al. [19], variance analysis; Kapoor and Narayanan [22], model info sheets.

Project evidence / 本地证据: dlv/data.py ORACLE; ESSAY_VS_REPRODUCTION_TABLE_V.csv; figure_captions.json

## Q10  §4  What do the 28 models and different subsets mean?

28 个模型与不同分析子集各指什么？

**Answer and local evidence / 直接回答与本地证据**

The retained roster is 13 conventional + 4 LLM-based + 11 frozen encoders. Accuracy and peak analysis cover all 28. Parameter exports support 11 arms, while paired tests cover 17 non-encoder models including MIFlu. DLinear is excluded from the retained roster and paired table by project choice. Its appearance in historical provenance does not make it a retained arm. A sensitivity analysis including DLinear would strengthen baseline coverage; prior appearance in the source paper is not by itself a scientific reason to omit it.

正式名单为 13 个传统模型 + 4 个基于 LLM 的模型 + 11 个冻结编码器。精度和峰值分析覆盖全部 28 个；参数导出支持其中 11 个；配对检验覆盖包括 MIFlu 的 17 个非编码器模型。项目主动把 DLinear 排除于正式名单及配对表。它在历史硬件来源表中出现，不代表属于正式保留模型。补充含 DLinear 的敏感性分析可加强基线覆盖；它曾出现在原文，本身不足以构成科学排除理由。

**Paper-based reasoning / 文献依据与选择理由**

The families test different explanations: simple temporal mapping [4], patches and inverted variable tokens [3, 5], and explicit cross-modal alignment [7, 8]. This motivates diverse controls, not a claim that 28 is an optimal count. It also makes implementation fidelity important: a named adaptation may omit a paper’s decisive alignment or training component. DLinear is a relevant simple control in this literature. Its appearance in the source paper is not itself a scientific reason to omit it from a sensitivity analysis.

各家族检验不同解释：简单时间映射 [4]、patch 与反转变量词元 [3, 5]，以及明确的跨模态对齐 [7, 8]。这支持采用多样对照，不证明 28 是最优数量，也使实现忠实度很重要：同名适配可能省略原文关键对齐或训练组件。DLinear 是这条文献中的相关简单对照；它曾出现在原论文，本身不是在敏感性分析中省略它的科学理由。

**Supervisor short answer / 导师简答**

The papers motivate different controls; the exports determine which models each analysis actually covers [3–5, 7, 8].

论文支持选择不同对照；导出文件决定每项分析实际覆盖哪些模型 [3–5, 7, 8]。

Reading locator / 论文位置: Zeng et al. [4], §4; PatchTST [3], §3.1; iTransformer [5], §3; CALF [7] and TimeCMA [8], author abstracts.

Project evidence / 本地证据: BENCH_MSE_BY_MODEL_L.csv; BENCH_EFFICIENCY.csv; BENCH_PAIRED_TESTS.csv; BENCH_GPU_PROVENANCE.csv

## Q11  §4  Does the lowest MSE make MIFlu the deployment winner?

MIFlu 的 MSE 最低，是否就应直接选它部署？

**Answer and local evidence / 直接回答与本地证据**

MIFlu has the lowest observed benchmark MSE, 1.5574. That is a descriptive accuracy result under one national split. It does not measure the cost of missed peaks, false alarms, runtime, regional robustness or prospective benefit. The larger MSE spread also does not establish that hyperparameter tuning is unimportant, because tuning was not experimentally varied as an alternative factor. The later evaluation axes ask additional questions that the accuracy table alone cannot answer.

MIFlu 的观测基准 MSE 最低，为 1.5574。这是在单一全国划分下的描述性精度结果，没有直接测量漏峰、误报、运行时间、区域稳健性或前瞻效益。MSE 差距较大，也不能证明调参不重要，因为本实验没有把调参作为另一因素进行对照。后面的评价维度回答精度表单独无法回答的问题。

**Paper-based reasoning / 文献依据与选择理由**

Peak timing/intensity are disease-specific endpoints [2], while interval scoring evaluates predictive uncertainty [18]. A seven-channel point-error ranking supplies neither automatically. Separate observed accuracy, peak trade-offs and operational cost. NLinear’s lower height error does not erase its worse mean timing; MIFlu’s lowest MSE does not establish calibrated intervals or prospective benefit. This lets us defend an evidence-based selection process before claiming a public-health deployment winner.

峰值时间/强度是疾病领域端点 [2]，区间评分考查预测不确定性 [18]；七通道点误差排名不会自动提供这些证据。应分别看观测精度、峰值取舍与操作代价。NLinear 峰高误差低不能抹去平均时间误差更大；MIFlu 的 MSE 最低也不证明区间校准或前瞻效益。我们因此可先论证选模证据，再谈公共卫生部署赢家。

**Supervisor short answer / 导师简答**

MIFlu wins the observed point-error ranking; peak endpoints and uncertainty need their own evidence [2, 18].

MIFlu 赢的是观测点误差排名，峰值端点与不确定性须有各自证据 [2, 18]。

Reading locator / 论文位置: Kramer and Shaman [2], Forecast accuracy and comparison; Bracher et al. [18], §§3–4.

Project evidence / 本地证据: BENCH_MSE_BY_MODEL_L.csv; audit/GRADE_READINESS.md

## Q12  §5  Why do MIFlu and NLinear both pass 4/16?

为什么 MIFlu 和 NLinear 都通过 4/16，却仍有不同结论？

**Answer and local evidence / 直接回答与本地证据**

A pass requires mean PTE ≤ 1 week and mean PIE ≤ 25% in the same (L, step) cell. NLinear passes step 0 at all four horizons. MIFlu passes step 0 at L24/L36/L60 and step 1 at L48. Equal counts therefore hide different locations and error magnitudes. Across all 16 cells, NLinear has lower PIE, 9.477% versus 26.846%, while MIFlu has lower PTE, 1.128 versus 1.677 weeks. The result is a timing–height trade-off, not dominance by either model.

一次通过要求同一个（L，step）单元的平均 PTE ≤ 1 周且平均 PIE ≤ 25%。NLinear 在四个跨度的 step 0 均通过；MIFlu 在 L24/L36/L60 的 step 0，以及 L48 的 step 1 通过。因此，相同通过数会隐藏达标位置及误差大小的差异。跨全部 16 单元，NLinear 的 PIE 更低，为 9.477% 对 26.846%；MIFlu 的 PTE 更低，为 1.128 对 1.677 周。结论是时间与峰高之间存在取舍，任何一个都不是全面占优。

**Paper-based reasoning / 文献依据与选择理由**

The separate literature endpoints motivate inspecting timing and height before reducing them to a pass count [2]. Our equal four-pass counts hide different lead/horizon locations and distances from the thresholds. An application emphasising one-week-ahead height could favour a different trade-off from an application emphasising timing. That conditional interpretation comes from our table, not from a literature recommendation of NLinear. A binary pass is a coarse summary of continuous errors.

文献分开评价时间与强度，支持先看两项误差，再压缩为通过数 [2]。相同四次通过隐藏不同步长/跨度位置，以及距阈值多远的差别。优先重视提前一周峰高的应用，可能与重视时间的应用选择不同取舍。这是对本地表格的条件式解释，不是文献推荐 NLinear。二元通过标签只是连续误差的粗略摘要。

**Supervisor short answer / 导师简答**

Equal counts conceal different cells and a timing–height trade-off [2].

相同通过数隐藏不同位置与时间—峰高取舍 [2]。

Reading locator / 论文位置: Kramer and Shaman [2], Forecast accuracy and comparison, separate timing/intensity tolerances.

Project evidence / 本地证据: BENCH_PTE_PIE_BY_STEP.csv model in {miflu,nlinear}

## Q13  §5  Does 4/16 mean a 25% chance of a correct epidemic forecast?

4/16 是否表示预测流行季成功的概率为 25%？

**Answer and local evidence / 直接回答与本地证据**

No. The denominator is four horizons times four fixed forecast steps, not 16 independent seasons. Each cell already averages errors across the available runs/events. Applying thresholds after averaging can give a different answer from counting individual successful events. The separate timing and intensity tolerances are supported by Kramer–Shaman [2]; our conjunction on aggregated cells and detector settings are project choices. They are not a clinical acceptance test or a calibrated probability.

不是。分母是四个跨度乘四个固定预测步，不是 16 个独立流行季。每个单元本身已经聚合可用运行或事件的误差。先平均再应用阈值，与先判断每个事件成功再计数，可能得到不同结果。Kramer–Shaman [2] 支持分别采用时间和强度容差；把两者联合用于聚合单元，以及具体峰检测设置，属于本项目选择，不是临床接受检验或经校准的概率。

**Paper-based reasoning / 文献依据与选择理由**

Kramer and Shaman evaluate forecast-level peak accuracy by lead time [2]. Our sixteen configuration cells have a different denominator. Applying a threshold to an average is mathematically different from averaging event-level pass indicators. Thus 4/16 cannot be relabelled as season success probability. Bracher et al. discuss calibration of predictive distributions [18, §4.2]; small peak-height error does not establish it. Estimating event success requires retaining individual outcomes, defining the event denominator and accounting for dependence.

Kramer 与 Shaman 按提前时间评价逐预测峰值准确性 [2]，我们的十六个配置单元是另一种分母。对均值应用阈值，与对逐事件通过指示值取平均，在数学上不同，所以 4/16 不能改名为流行季成功概率。Bracher 等讨论预测分布校准 [18，第 4.2 节]，峰高误差小不等于已校准。估计事件成功率需保留逐事件结果、定义事件分母并处理依赖。

**Supervisor short answer / 导师简答**

Our denominator counts configurations after averaging, not successful seasons or calibrated probabilities [2, 18].

这里数的是平均后的配置，而非成功流行季或经校准概率 [2, 18]。

Reading locator / 论文位置: Kramer and Shaman [2], Forecast accuracy and comparison / Fig. 2; Bracher et al. [18], §4.2.

Project evidence / 本地证据: BENCH_PTE_PIE_BY_STEP.csv; Kramer–Shaman [2]; analysis peak detector settings

## Q14  §5  Why can peak rankings differ without proving decoupling?

为什么峰值排名会改变，却不能说已经证明脱钩？

**Answer and local evidence / 直接回答与本地证据**

The leading-three MSE order is MIFlu < PatchTST < NLinear; the PIE order is NLinear < MIFlu < PatchTST. Ordering is inverted at both ends, with different middle positions. Across all models, MSE–PIE correlation is positive (+0.736) and MSE–pass-count correlation negative (−0.429), both in the expected direction for generally better error. A local rank mismatch can coexist with those overall associations. We can claim that objectives change the ordering, not statistical independence or universal peak failure.

前三模型的 MSE 顺序为 MIFlu < PatchTST < NLinear，PIE 顺序为 NLinear < MIFlu < PatchTST。排序在两端倒置，中间位置也不同。跨全部模型，MSE–PIE 为正相关（+0.736），MSE–通过数为负相关（−0.429），都符合整体误差越低通常峰值表现越好的方向。局部排名不一致可以与整体相关同时存在。因此可主张评价目标改变排序，不能主张统计独立或所有模型都无法预测峰值。

**Paper-based reasoning / 文献依据与选择理由**

Zeng et al. describe NLinear’s last-value subtraction, linear map and addition back [4]. This gives a testable hypothesis about level handling, not a proven explanation for our peaks. The ranking mismatch itself follows a simpler distinction: MSE aggregates many points and seven channels, whereas PIE concentrates on detected ILITOTAL peak height [21 gives the error-measure context]. A model can improve many non-peak points yet worsen this endpoint. Controlled variants and peak/residual diagnostics are needed to attribute the observed trade-off to architecture.

Zeng 等说明 NLinear 先减最后一个值，经过线性映射，再加回该值 [4]。这提供水平处理的可检验假设，却非本地峰值成因的证明。排名差别有更直接的区别：MSE 聚合许多点和七通道，PIE 聚焦 ILITOTAL 检测峰高 [21 提供误差指标背景]。模型可能改善非峰点却使该端点较差。若要归因于架构，须有受控变体和峰值/残差诊断。

**Supervisor short answer / 导师简答**

The objectives aggregate different errors; NLinear’s level correction is a hypothesis to test [4, 21].

两种目标聚合不同误差，NLinear 水平校正是待检验的假设 [4, 21]。

Reading locator / 论文位置: Zeng et al. [4], §4 NLinear; Hyndman and Koehler [21], §2.1.

Project evidence / 本地证据: BENCH_MSE_BY_MODEL_L.csv joined to BENCH_PTE_PIE_BY_STEP.csv; audit/verified_facts.json

## Q15  §6  How should I explain the Pareto graph?

我该怎样向导师解释 Pareto 图？

**Answer and local evidence / 直接回答与本地证据**

The horizontal axis is parameter count and the vertical axis is MSE, so smaller values are preferred on both. A model is dominated within the measured subset if another has no more parameters and no higher MSE, with at least one strict improvement. The exported frontier contains NLinear and PatchTST: NLinear is smaller, while PatchTST has lower MSE. Neither dominates the other. This frontier covers only the 11 arms with parameter exports; MIFlu and the encoders are outside it, so a global frontier claim is unsupported.

横轴是参数量，纵轴是 MSE，两者均偏向越小越好。如果子集中另一个模型的参数不更多、MSE 不更高，且至少一项严格更好，前者就受到支配。导出的前沿包含 NLinear 和 PatchTST：NLinear 更小，PatchTST 的 MSE 更低，因此互不支配。这个前沿只覆盖有参数导出的 11 个模型，MIFlu 与冻结编码器不在其中，不能称为全部模型的全局前沿。

**Paper-based reasoning / 文献依据与选择理由**

iTransformer evaluates error alongside speed and memory [5, App. D], a precedent for considering performance with cost. Our cost axis is narrower: exported parameters. The two local frontier members follow from pairwise dominance in the eleven-model subset, not a paper’s recommendation of a universal winner. A Pareto graph removes dominated choices; the remaining choices still need a budget or acceptable-error preference. Missing MIFlu cost data prevents calling it the frontier of all 28 models.

iTransformer 同时评价误差、速度和内存 [5，附录 D]，是把表现与代价并列考虑的先例。我们的代价轴更窄，只用导出参数。两个前沿成员来自十一模型子集的两两支配关系，并非论文推荐的通用赢家。Pareto 图排除被支配选择；余下选择仍需预算或可接受误差偏好。MIFlu 代价缺失，使它不能称为全部 28 模型前沿。

**Supervisor short answer / 导师简答**

The frontier removes dominated choices within the measured subset; a decision preference still chooses among them [5].

前沿排除所测子集内的被支配选择，仍需决策偏好从中选模 [5]。

Reading locator / 论文位置: iTransformer [5], Appendix D Model Efficiency; local BENCH_EFFICIENCY.csv.

Project evidence / 本地证据: BENCH_EFFICIENCY.csv; fig_pareto_frontier.png

## Q16  §6  Does 211 times more parameters mean 211 times slower?

参数多 211 倍，是否就慢 211 倍？

**Answer and local evidence / 直接回答与本地证据**

No. 531,878 / 2,520 = 211.1 compares exported PatchTST and NLinear parameter counts. Their observed MSE reduction is (1.871583 − 1.662078) / 1.871583 ≈ 11.2%. Parameter storage, operations, hardware utilisation and batch size affect runtime differently. Latency, peak memory and energy require direct comparable measurements. We use the phrase parameter efficiency, and leave missing parameter counts missing rather than treating them as zero or describing MIFlu as non-parametric.

不是。531,878 / 2,520 = 211.1 比较的是导出的 PatchTST 与 NLinear 参数量。其观测 MSE 降幅为 (1.871583 − 1.662078) / 1.871583 ≈ 11.2%。参数存储、运算、硬件利用率及批量大小对运行时间有不同影响。延迟、峰值内存与能耗需要直接且可比的测量。因此使用“参数效率”这个表述；缺失参数继续记为缺失，不能当成零，更不能把 MIFlu 描述成无参数模型。

**Paper-based reasoning / 文献依据与选择理由**

iTransformer measures speed and memory under stated input/prediction lengths and the same batch size [5, App. D]. Our parameter export does not supply those measurements. Parameters affect storage; operations, token counts and hardware utilisation affect elapsed time differently. Consequently 211× parameters cannot imply 211× latency, memory or energy. A useful next efficiency table records hardware, precision, batch size and whether training or inference is timed. These fields cannot be invented from the parameter ratio.

iTransformer 在声明的输入/预测长度和统一批量下实测速度、内存 [5，附录 D]，我们的参数导出没有这些测量。参数影响存储，运算、词元数量与硬件利用率对耗时影响不同。因此参数多 211×，不能推出延迟、内存或能耗也多 211×。后续效率表应记录硬件、精度、批量，以及计时针对训练还是推理，不能用参数比猜这些字段。

**Supervisor short answer / 导师简答**

I report a parameter ratio. The literature shows the matched runtime measurements needed for a speed claim [5].

我报告的是参数比；文献展示了速度主张所需的匹配运行测量 [5]。

Reading locator / 论文位置: iTransformer [5], Appendix D, Fig. 10, matched speed/memory measurements.

Project evidence / 本地证据: BENCH_EFFICIENCY.csv; BENCH_MSE_BY_MODEL_L.csv model in {nlinear,patchtst}

## Q17  §6  What does R squared of 0.0223 actually mean?

R² = 0.0223 实际说明什么？

**Answer and local evidence / 直接回答与本地证据**

For the chosen fit of MSE against log10(parameter count) in 11 exported arms, parameter size alone accounts for little observed variation. This descriptive association does not isolate the effect of capacity: architectures, optimisation and training regimes also vary. A low R squared does not prove that capacity is irrelevant or that an observed accuracy gain is random noise. A causal capacity study would vary size within a controlled family and training protocol.

在有参数导出的 11 个模型中，以 MSE 对 log10(参数量) 拟合，参数规模单独解释的观测变化很少。这种描述性关联没有隔离容量作用，因为架构、优化与训练设置也同时不同。较低 R² 不能证明容量不重要，更不能证明观测精度增益只是随机噪声。若要研究容量因果作用，需要在受控模型家族及训练协议内改变规模。

**Paper-based reasoning / 文献依据与选择理由**

PatchTST varies layers and hidden dimension and specifically finds ILI sensitive to those settings [3, App. A.6.2]. This is relevant evidence against dismissing tuning on a small influenza series. Our cross-model R² mixes architecture, optimisation and size; it is not a controlled capacity effect. A stronger follow-up varies depth/width within one family under a fixed training protocol and repeats runs. The planned MIFlu depth ladder begins this question, but its unaggregated status provides no scientific trend yet.

PatchTST 改变层数和隐藏维度，并特别指出 ILI 对这些设置敏感 [3，附录 A.6.2]，这反对轻率否定小流感序列上的调参。我们的跨模型 R² 混合架构、优化和规模，不是受控容量作用。更强的后续是在一个家族内改变深度/宽度，固定训练协议并重复运行。MIFlu 深度阶梯开始提出这个问题，但未聚合状态不能提供科学趋势。

**Supervisor short answer / 导师简答**

Low cross-model R² does not dismiss tuning; PatchTST explicitly reports ILI sensitivity [3].

跨模型 R² 低不能否定调参；PatchTST 明确报告 ILI 敏感性 [3]。

Reading locator / 论文位置: PatchTST [3], Appendix A.6.2, Fig. 5, layers/width and ILI sensitivity.

Project evidence / 本地证据: BENCH_EFFICIENCY.csv; scripts/verify_snapshot.py linregress

## Q18  §7  Why does the paired table contain seemingly unrelated model pairs?

为什么配对检验表里会出现看起来不相关的模型对？

**Answer and local evidence / 直接回答与本地证据**

The report deliberately shows the NLinear–PatchTST frontier comparison first, followed by six rows with the smallest raw p-values. This combines the question of interest with examples of the wider test family. The frontier pair is 117th by ascending raw p in the exported table, so an automatic smallest-six display would omit it. The full family still contains all 136 comparisons; displayed-row selection never changes the Holm family or makes the selected pair significant.

报告有意把 NLinear–PatchTST 这对前沿比较放在第一行，再列原始 p 最小的六行，这样既展示核心问题，也展示更大检验族中的例子。该前沿对在导出表按原始 p 升序排列时位于第 117，因此自动只取最小六项会漏掉它。但完整检验族仍含全部 136 对；选择展示哪几行，不能改变 Holm 校正的检验族，更不能让选中比较变显著。

**Paper-based reasoning / 文献依据与选择理由**

Demšar motivates controlling the comparison family when inspecting particular differences [20]. Here the first row keeps the substantive frontier question visible; the next six show smaller raw-p contrasts. All 136 still enter the correction. Rank 117 refers to ascending raw p, not a model’s accuracy rank. Choosing display rows cannot change that family. Because the article’s main setting is multiple datasets, it also does not licence treating our overlapping horizons and shared test series as independent datasets.

Demšar 说明考查特定差异时须控制比较族 [20]。这里首行保留前沿核心问题，后六行展示原始 p 更小的对照，校正仍纳入全部 136 对。第 117 指原始 p 升序位置，不是模型精度排名。选择展示行不能改变检验族。该文主要讨论多数据集，也不许可把本地重叠跨度和共享测试序列当成独立数据集。

**Supervisor short answer / 导师简答**

The first row serves the research question; the full family still determines correction [20].

首行服务研究问题，校正仍由完整检验族决定 [20]。

Reading locator / 论文位置: Demšar [20], §3.2.2 Post-hoc tests; local raw-p rank.

Project evidence / 本地证据: BENCH_PAIRED_TESTS.csv model_a=nlinear/model_b=patchtst; audit/verified_facts.json pair_raw_rank

## Q19  §7  Why do 128 raw significant pairs become zero after Holm?

为什么未校正有 128 对显著，Holm 后却是零？

**Answer and local evidence / 直接回答与本地证据**

Testing many pairs increases the opportunity for false positives. Proper Holm sorts raw p-values and applies a forward cumulative maximum to the ordered multiplicity factors. The original exported column used the wrong direction and is quarantined. Recomputing all 136 gives 0/136 rejections, with minimum adjusted p about 0.0664 and NLinear–PatchTST 0.1172. With the documented two-sided exact n=12 resolution, the smallest possible raw p is 2/4096, already too large for Holm’s first 0.05/136 threshold. Dependence between horizon–seed cells is an additional concern.

同时检验很多模型对会增加误报机会。正确 Holm 先排列原始 p，再按递减多重比较因子计算并取前向累计最大值。原导出列方向错误，因此保留作来源记录但不使用。重算全部 136 对后为 0/136 个拒绝，最小校正 p 约 0.0664，NLinear–PatchTST 为 0.1172。在已记录的双侧精确 n=12 分辨率下，原始 p 最低为 2/4096，已高于 Holm 第一步的 0.05/136 阈值。跨度–种子单元之间的依赖还带来另一层限制。

**Paper-based reasoning / 文献依据与选择理由**

Demšar describes starting with the smallest p and stopping at the first failed Holm threshold [20]. Our first threshold is 0.05/136. The documented two-sided twelve-contribution sign-flip floor is 2/2^12; multiplying by 136 gives 0.06640625, so no pair can start the rejection sequence. This floor is local mathematical reasoning, not a result reported by Demšar for influenza. Holm permits dependence among valid p-values, but cannot repair invalid raw p-values from unjustified within-pair exchangeability. These are separate limitations.

Demšar 说明 Holm 从最小 p 开始，在首次未通过阈值处停止 [20]。本项目第一阈值为 0.05/136；按已记录的十二贡献双侧符号翻转下限 2/2^12，乘 136 得 0.06640625，所以无法启动拒绝序列。这是本地数学推导，不是 Demšar 报告的流感结果。Holm 可处理有效 p 值之间的依赖，却不能修复因配对内部交换性不合理而无效的原始 p；两者是不同限制。

**Supervisor short answer / 导师简答**

The exact-test floor exceeds Holm’s first threshold; that is a design-resolution limit [20].

精确检验下限超过 Holm 第一步阈值，这是设计分辨率限制 [20]。

Reading locator / 论文位置: Demšar [20], §3.2.2 Holm step-down; local exact-enumeration derivation.

Project evidence / 本地证据: BENCH_PAIRED_TESTS.csv p_raw; analysis_postprocess.py; audit/HOLM_RECOMPUTATION.csv

## Q20  §7  Does p = 0.1172 show that NLinear and PatchTST are equivalent?

p = 0.1172 是否说明 NLinear 与 PatchTST 等价？

**Answer and local evidence / 直接回答与本地证据**

No. PatchTST retains 11.2% lower observed mean MSE and lower error in 10/12 matched cells. Non-rejection means this familywise procedure does not establish a difference at the chosen threshold. It does not establish a small enough difference for practical equivalence. Equivalence needs a prespecified acceptable margin and a suitable uncertainty/test design. The table’s source effect also uses pooled model standard deviation rather than paired-difference standard deviation, so it is labelled as a source standardised effect.

不是。PatchTST 的观测平均 MSE 仍低 11.2%，且在 10/12 个配对单元中误差更低。未拒绝只表示该检验族校正流程没有在选定阈值下确立差异，不表示差异已小到可视为实际等价。等价判断需要预先规定可接受差异界值，并采用适合的不确定性与检验设计。表中源效应量还使用模型合并标准差，而非配对差标准差，因此只能标成源标准化效应。

**Paper-based reasoning / 文献依据与选择理由**

Lakens distinguishes a nonsignificant difference test from equivalence with prespecified meaningful bounds [25]. Thus p = 0.1172 does not answer whether NLinear’s observed extra error is acceptable for an application. Define that acceptable difference first, then use an uncertainty design respecting time/season dependence. Choosing a generous bound after seeing this table would not be convincing confirmation. Until then, observed error reduction, parameter ratio and inferential uncertainty should be reported together; the extra parameters cannot be dismissed as buying only noise.

Lakens 区分不显著差异检验与预先规定有意义界限的等价检验 [25]。因此 p = 0.1172 没回答 NLinear 额外观测误差是否可接受。应先定义可接受差异，再采用尊重时间/季节依赖的不确定性设计。看表后才挑宽松界限，不能构成有说服力的确认。在此之前应并列报告观测降幅、参数比和推断不确定性，不能说额外参数只换来噪声。

**Supervisor short answer / 导师简答**

Non-rejection is not equivalence; the observed trade-off and unresolved inference coexist [25].

未拒绝不等于等价，观测取舍与尚未解决的推断并存 [25]。

Reading locator / 论文位置: Lakens [25], Introduction and Testing for Equivalence.

Project evidence / 本地证据: BENCH_EFFICIENCY.csv; BENCH_PAIRED_TESTS.csv; audit/CLAIM_AUDIT.md C3

## Q21  §8  What can the frozen-encoder negative result explain?

冻结编码器的负面结果能解释到哪一步？

**Answer and local evidence / 直接回答与本地证据**

The tested pipeline freezes a language encoder and trains a linear readout. Its 11 encoder arms have MSE 4.7374–5.2049, all above decision tree 4.3198, with 0/16 joint passes each. This shows poor performance of these feature/readout configurations on this protocol. Distribution mismatch, frozen features and readout capacity are possible mechanisms, but the experiment does not separate them. Generation, prompting, fine-tuning and numerically pretrained time-series foundation models remain outside this test.

所测流程冻结语言编码器，再训练线性读出。11 个编码器的 MSE 为 4.7374–5.2049，均高于决策树的 4.3198，各自通过 0/16 联合单元。这说明这些特征与读出配置在当前协议中表现较差。分布不匹配、冻结特征和读出能力都可能解释结果，但实验没有分离其作用。生成、提示、微调及数值预训练时序基础模型均不属于这项测试。

**Paper-based reasoning / 文献依据与选择理由**

Time-LLM freezes its LLM but adds learned reprogramming and a prompt prefix [6]. Thus “frozen” alone does not define the same experiment as our feature/linear-readout pipeline. Chronos instead learns forecasting from numerical sequences [9]. These method differences justify keeping our negative finding narrow. To isolate a readout bottleneck, vary the readout/alignment while holding the encoder fixed; to isolate pretraining, compare matched pretrained and random backbones. Our eleven-arm result does not make those controlled separations.

Time-LLM 也冻结 LLM，却加入可学习重编程和提示前缀 [6]，所以“冻结”不等同于本项目特征/线性读出流程。Chronos 则从数值序列学习预测 [9]。这些方法差异支持缩小负面结论。要分离读出瓶颈，应固定编码器后改变读出/对齐；要分离预训练作用，应比较匹配的预训练和随机骨干。十一模型结果没有完成这些受控分离。

**Supervisor short answer / 导师简答**

The failure concerns our feature/readout pipeline; Time-LLM and Chronos test other mechanisms [6, 9].

失败限定本地特征/读出流程，Time-LLM 与 Chronos 检验其他机制 [6, 9]。

Reading locator / 论文位置: Time-LLM [6], author abstract; Chronos [9], §3.

Project evidence / 本地证据: BENCH_MSE_BY_MODEL_L.csv family=llm_encoder; BENCH_PTE_PIE_BY_STEP.csv

## Q22  §9  Why might no-text give identical outputs in the default path?

为什么默认路径下去掉文本可能得到完全相同的输出？

**Answer and local evidence / 直接回答与本地证据**

In the inspected author_faithful path, time tokens precede text tokens. Causal attention permits each position to read only its own or earlier positions, and the head reads the time-token positions. Those positions therefore cannot use later text in a deterministic evaluation forward pass. The supplied archive explicitly asserts text invariance and matched-initialisation full/no-text CPU equality, and the supplied JUnit now records those three fixed-weight CPU model assertions passed with zero skips; this review did not rerun them. Other fusion paths, dropout and independently trained trajectories require separate checks. The exact files and commands are in audit/NO_TEXT_VERIFICATION.md.

已检查的 author_faithful 路径把时间词元放在文本词元前。因果注意力只允许每个位置读取自身或更早位置，预测头又只读取时间词元位置。因此在确定性评估前向过程中，这些位置无法利用后面的文本。所附归档明确断言文本不变性，以及匹配初始化的完整/无文本 CPU 输出相同，所附 JUnit 现记录三项固定权重 CPU 模型断言通过、零跳过；本次审阅未重跑它们。其他融合路径、dropout 和独立训练轨迹仍需分别检查。精确文件与命令见 audit/NO_TEXT_VERIFICATION.md。

**Paper-based reasoning / 文献依据与选择理由**

The Transformer paper explains masking that prevents attention to subsequent positions [24, §3.1]. With the inspected ordering, time positions cannot acquire later text through these layers, and the head reads time positions. This is a structural argument about a fixed forward path, not certification of repository runtime or bitwise equality. The three archived assertions must control weights, inputs and evaluation randomness when comparing changed text and matched full/no-text outputs. The supplied JUnit now records three CPU assertions passed with zero skips; they were not rerun in this review. Independent training can consume randomness differently and requires its own test.

Transformer 原文说明遮罩如何阻止关注后续位置 [24，第 3.1 节]。按已检查顺序，时间位置不能通过这些层取得后方文本，预测头又只读时间位置。这是固定前向路径的结构论证，不是仓库运行或逐位相等认证。三项归档断言须控制权重、输入和评估随机性，再比较更换文本及匹配完整/无文本输出，所附 JUnit 现记录三项 CPU 断言通过且零跳过；本次未重跑模型测试。独立训练可能不同地消耗随机数，须另测。

**Supervisor short answer / 导师简答**

Causal masking supports the structural argument; controlled runtime tests must establish bitwise equality here [24].

因果遮罩支持结构论证，本地逐位相等须由受控运行测试建立 [24]。

Reading locator / 论文位置: Vaswani et al. [24], §3.1 Decoder; local ForecastingLLM.forward and archived assertions.

Project evidence / 本地证据: miflu_model.py ForecastingLLM; tests_archive/test_miflu_ablations.py; audit/NO_TEXT_VERIFICATION.md

## Q23  §9  What does 60/60 ablation completion allow us to say?

消融完成 60/60，究竟可以说什么？

**Answer and local evidence / 直接回答与本地证据**

It is queue-completion evidence in the returned 4 November records, not an aggregated model comparison or an independently rerun ablation study. The additional design has five arms, each with four horizons and three seeds: 60 cells beyond the 12-cell reference. Without per-arm result exports, completion is not evidence of a depth trend or a benefit of LoRA. Do not infer a completed no-text ablation from the presence of its test assertions. We need run-level outputs, status and provenance before reporting scientific results.

这是 11 月 4 日回传记录中的队列完成证据，不是已聚合的模型比较，也不是本次独立重跑的消融研究。新增设计有五个变体，每个四跨度、三种子，合计 60 单元；参考模型另有 12 单元。没有逐变体结果导出，就不能从完成数量推断深度趋势或 LoRA 收益。存在 no-text 测试断言，也不代表已完成相应消融实验。报告科学结果前，需要逐运行输出、状态及来源。

**Paper-based reasoning / 文献依据与选择理由**

Tan et al. remove or replace the LLM while retaining the surrounding trainable forecaster [13, §3.2]. This asks whether the backbone contributes beyond the wrapper. Our no-LoRA/depth variants address narrower adaptation/capacity questions; they do not automatically answer the same removal/replacement question or isolate text use. Partial completion is an operational status. Interpreting a scientific trend requires the reported variants’ scores, repeated-run variability and a matched protocol. The literature supplies an experimental question, not a result for our unfinished ladder.

Tan 等保留周边可训练预测器，移除或替换 LLM [13，第 3.2 节]，以检验骨干是否额外贡献信息。本地 no-LoRA/深度变体只回答较窄的适配/容量问题，不会自动回答同样的移除/替换问题，也不能分离文本使用。部分完成是操作状态；解释科学趋势需各报告变体分数、重复运行波动及匹配协议。文献提供实验问题，不提供本地未完成阶梯的结果。

**Supervisor short answer / 导师简答**

The papers motivate removal/replacement controls; the incomplete ladder has not answered those causal questions [13].

文献支持移除/替换对照，未完成阶梯尚未回答这些因果问题 [13]。

Reading locator / 论文位置: Tan et al. [13], §3.2 Proposed Ablations, w/o LLM / LLM2Attn / LLM2Trsf.

Project evidence / 本地证据: Owner snapshot; ablation design table; tests_archive/test_miflu_ablations.py

## Q24  §10  What is added beyond reproduction, and why keep O1?

除了复现，本项目增加了什么，为什么默认仍选 O1？

**Answer and local evidence / 直接回答与本地证据**

The study compares implementations across accuracy, peak skill, parameter efficiency and statistical evidence, with different declared subsets. We have not verified that the reference paper contains only the first two axes, so absence or first-ever claims are inappropriate. O1 develops this evaluation contribution through provenance repair, restored tests, rolling origins, regions and stronger controls. Optional O2 is validation-only peak-height recalibration: zero new GPU training if auditable validation/test predictions already exist. Such validation exports are not established here; CPU time and money are unmeasured, and a few working days is only a planning estimate.

本项目在明确不同子集的前提下，从精度、峰值技巧、参数效率和统计证据四个维度比较实现。本次没有核实参考论文是否只有前两项，因此不能断言原文缺失某项或声称首次发现。O1 通过补齐来源、恢复测试、滚动原点、区域和更强对照来发展实证贡献。可选 O2 是只在验证数据拟合的峰高再校准：若已有可审计的验证/测试预测，可不新增 GPU 训练。但本快照尚未确立这些验证导出；CPU 时间和费用未测量，几个工作日也仅为规划估计。

**Paper-based reasoning / 文献依据与选择理由**

Simple-linear and LLM-removal critiques predate this project [4, 13]; Qiu et al.’s preprint reports conditional gains in larger cross-dataset settings [14]. Our narrower contribution connects audited influenza accuracy, peak endpoints, a cost subset and corrected inference. O1 checks persistence across origins/regions; Tashman motivates rolling-origin evaluation [23]. O2 adds validation-fitted height adjustment only if suitable prediction exports exist. A new mechanism cannot replace those checks or establish a universal verdict about LLM forecasting.

简单线性及移除 LLM 的批评早已存在 [4, 13]，Qiu 等预印本又在更大跨数据集设置报告条件式收益 [14]。本地较窄贡献连接经审计流感精度、峰值端点、代价子集和正确推断。O1 检查跨原点/区域是否保持，Tashman 支持滚动原点评测 [23]。O2 仅在预测导出合适时加入验证集拟合峰高调整；新增机制不能替代检查，也不能确立对所有 LLM 的判决。

**Supervisor short answer / 导师简答**

O1 tests the influenza-specific findings; prior negative and conditional-positive evidence rule out a universal conclusion [4, 13, 14].

O1 检验流感特定发现；已有负面和条件式正面证据，不支持通用结论 [4, 13, 14]。

Reading locator / 论文位置: Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract.

Project evidence / 本地证据: audit/INNOVATION_DECISION.md; audit/LITERATURE_REVIEW.md; sources.json [1]

## Q25  §11  What can a supervisor reproduce now, and what remains unexecuted?

导师现在能复核什么，还有什么未执行？

**Answer and local evidence / 直接回答与本地证据**

The documented CPU commands reproduce CSV headline arithmetic, correct Holm and one raw prediction-cell MSE. Seven new CPU audit checks passed. Whole-archive collection still failed. The supplied JUnit records three fixed-weight CPU no-text assertions passed with zero skips, while returned core artefacts satisfy 160/160 completeness checks. The national 1120 matrix remains in progress. Full common-panel scoring, pinned upstream identity and independent-training text effects remain unresolved; this review did not rerun GPU training or connect to live HPC. Hardware provenance also lacks complete retained-cell coverage. A polished document does not close those gaps. Use the exact follow-up commands in audit/EXECUTION_STATUS.md and audit/NO_TEXT_VERIFICATION.md.

文档中的 CPU 命令可以重算 CSV 主要聚合、正确 Holm 和一个原始预测单元的 MSE；七个新增 CPU 审计检查已通过。整个历史归档的收集仍失败。所附 JUnit 记录三项固定权重 CPU no-text 断言通过且零跳过，核心产物满足 160/160 完整性检查；全国 1120 矩阵仍在进行。完整共同面板评分及固定上游身份仍待核实，本次未重跑 GPU 训练或连接实时 HPC，硬件来源也未完整覆盖正式单元。文档排版完善不能补足这些证据。精确后续命令见 audit/EXECUTION_STATUS.md 与 audit/NO_TEXT_VERIFICATION.md。

**Paper-based reasoning / 文献依据与选择理由**

Kapoor and Narayanan ask for explicit reporting arguments rather than equating code availability with a valid result [22]. Here distinguish document rebuilding, CSV arithmetic, raw prediction rescoring and model retraining. A supervisor can begin with the CSV audit; the full bundle supports one raw-cell smoke check. Model text invariance needs the three named runtime assertions without skips in a pinned environment. The useful deliverable is a traceable evidence chain with exact commands and status. Passing one evidence level does not certify all the others.

Kapoor 与 Narayanan 要求明确报告论证，而非把代码可用等同于结果有效 [22]。这里应分开文档重建、CSV 算术、原始预测重评分与模型重训。导师可先运行 CSV 审计；完整包还支持一个原始单元 smoke 检查。模型文本不变性需在固定环境实际执行三项指定断言，且不能跳过。有用的交付是可追溯证据链、精确命令与状态，某一层通过不能认证其他所有层。

**Supervisor short answer / 导师简答**

I distinguish recomputed results from static inspection and give the command and status for each [22].

我区分重算结果与静态检查，并为每层提供命令和状态 [22]。

Reading locator / 论文位置: Kapoor and Narayanan [22], model info sheets; EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md.

Project evidence / 本地证据: audit/EXECUTION_STATUS.md; audit/NO_TEXT_VERIFICATION.md; audit/REPO_AUDIT.md

## References

[1] Jaeuk Moon, Jonghwa Shim, Eunbeen Kim and Eenjun Hwang, “MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme,” IEEE JBHI 29(10), 7790-7801, 2025. https://doi.org/10.1109/JBHI.2025.3561214

[2] Sarah C. Kramer and Jeffrey Shaman, “Development and validation of influenza forecasting for 64 temperate and tropical countries,” PLOS Computational Biology 15(2), e1006742, 2019. https://doi.org/10.1371/journal.pcbi.1006742

[3] Yuqi Nie, Nam H. Nguyen, Phanwadee Sinthong and Jayant Kalagnanam, “A Time Series is Worth 64 Words: Long-term Forecasting with Transformers,” ICLR, 2023. https://arxiv.org/abs/2211.14730

[4] Ailing Zeng, Muxi Chen, Lei Zhang and Qiang Xu, “Are Transformers Effective for Time Series Forecasting?,” AAAI (preprint record opened), 2023. https://arxiv.org/abs/2205.13504

[5] Yong Liu et al., “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting,” ICLR (preprint record opened), 2024. https://arxiv.org/abs/2310.06625

[6] Ming Jin et al., “Time-LLM: Time Series Forecasting by Reprogramming Large Language Models,” ICLR, 2024. https://arxiv.org/abs/2310.01728

[7] Peiyuan Liu et al., “CALF: Aligning LLMs for Time Series Forecasting via Cross-modal Fine-Tuning,” arXiv:2403.07300, 2024. https://arxiv.org/abs/2403.07300

[8] Chenxi Liu et al., “TimeCMA: Towards LLM-Empowered Multivariate Time Series Forecasting via Cross-Modality Alignment,” AAAI, 2025. https://arxiv.org/abs/2406.01638

[9] Abdul Fatir Ansari et al., “Chronos: Learning the Language of Time Series,” Transactions on Machine Learning Research, 2024. https://arxiv.org/abs/2403.07815

[10] Abhimanyu Das, Weihao Kong, Rajat Sen and Yichen Zhou, “A decoder-only foundation model for time-series forecasting,” ICML, PMLR 235, 10148-10167, 2024. https://proceedings.mlr.press/v235/das24c.html

[11] Gerald Woo et al., “Unified Training of Universal Time Series Forecasting Transformers,” ICML, PMLR 235, 53140-53164, 2024. https://proceedings.mlr.press/v235/woo24a.html

[12] Kashif Rasul et al., “Lag-Llama: Towards Foundation Models for Probabilistic Time Series Forecasting,” arXiv:2310.08278, version 3, 2024. https://arxiv.org/abs/2310.08278

[13] Mingtian Tan, Mike A. Merrill, Vinayak Gupta, Tim Althoff and Thomas Hartvigsen, “Are Language Models Actually Useful for Time Series Forecasting?,” NeurIPS 37, 2024. https://arxiv.org/abs/2406.16964

[14] Xin Qiu et al., “Rethinking the Role of LLMs in Time Series Forecasting,” arXiv:2602.14744 v1, preprint, 2026. https://arxiv.org/abs/2602.14744

[15] Chen Xu and Yao Xie, “Conformal prediction interval for dynamic time-series,” ICML, PMLR 139, 11559-11569, 2021. https://proceedings.mlr.press/v139/xu21h.html

[16] Chen Xu and Yao Xie, “Sequential Predictive Conformal Inference for Time Series,” ICML, PMLR 202, 38707-38727, 2023. https://proceedings.mlr.press/v202/xu23r.html

[17] Isaac Gibbs and Emmanuel Candès, “Adaptive Conformal Inference Under Distribution Shift,” NeurIPS 34, 2021. https://arxiv.org/abs/2106.00170

[18] Johannes Bracher, Evan L. Ray, Tilmann Gneiting and Nicholas G. Reich, “Evaluating epidemic forecasts in an interval format,” PLOS Computational Biology 17(2), e1008618, 2021. https://doi.org/10.1371/journal.pcbi.1008618

[19] Xavier Bouthillier et al., “Accounting for Variance in Machine Learning Benchmarks,” Proceedings of Machine Learning and Systems 3, 2021. https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf

[20] Janez Demšar, “Statistical Comparisons of Classifiers over Multiple Data Sets,” Journal of Machine Learning Research 7, 1–30, 2006. https://jmlr.org/papers/volume7/demsar06a/demsar06a.pdf

[21] Rob J. Hyndman and Anne B. Koehler, “Another look at measures of forecast accuracy,” International Journal of Forecasting 22(4), 679–688, 2006. https://doi.org/10.1016/j.ijforecast.2006.03.001

[22] Sayash Kapoor and Arvind Narayanan, “Leakage and the reproducibility crisis in machine-learning-based science,” Patterns 4, article 100804, 2023. https://doi.org/10.1016/j.patter.2023.100804

[23] Leonard J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis and review,” International Journal of Forecasting 16(4), 437–450, 2000. https://doi.org/10.1016/S0169-2070(00)00065-0

[24] Ashish Vaswani et al., “Attention Is All You Need,” Advances in Neural Information Processing Systems 30, 2017. https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf

[25] Daniël Lakens, “Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses,” Social Psychological and Personality Science 8(4), 355–362, 2017. https://doi.org/10.1177/1948550617697177
