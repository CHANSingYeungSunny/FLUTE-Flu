# Integrated revision 8 paragraph/table differences against returned v6

The old revision-4 comparison is archived under prior_revision4. This comparison uses the exact supplied six v6 DOCX baselines. Historical table preservation is asserted by build_current_documents.py; only declared operational cells change. Q01–Q25 headings are retained.

## ieee_manuscript_en.docx

```diff
--- returned v6
+++ integrated v8
@@ -2,7 +2,7 @@
 CHAN Sing Yeung
Final Year Project, Department of Electrical Engineering, City University of Hong Kong
 Single-column review draft oriented towards IEEE JBHI. Current submission rules and page limits remain unverified. This is an evaluation contribution and is not yet submission-ready.
 Abstract
-We audit an independent MIFlu reproduction and 28 forecasting implementations on a 966-row US national influenza series. The supplied reproduction table gives mean squared error (MSE) 1.4995 versus the published 1.4355, with lower MSE at two horizons and higher MSE at two. Under three benchmark seeds, MIFlu, PatchTST and NLinear achieve 1.5574, 1.6621 and 1.8716. A joint screen using literature-derived timing and intensity tolerances yields 4/16 passing aggregated cells for both NLinear and MIFlu and 0/16 for PatchTST. NLinear has lower mean peak-intensity error but higher mean timing error than MIFlu. Across 11 arms with parameter exports, the MSE–log-parameter fit has slope +0.1171 and R² 0.0223. An audit identifies an incorrect Holm routine in the supplied analysis: correcting 136 comparisons among 17 models yields no rejections, with NLinear–PatchTST p approximately 0.1172. This does not establish equivalence. Eleven frozen language encoders perform worse than a decision tree in the tested readout configuration. Ablation completion is owner-reported at 60/60 and is not aggregated. The findings are descriptive and limited to one split, retrospective peak detection and adapted implementations. We recommend reporting peak magnitude and timing alongside average error, then selecting on validation-defined costs and budgets before prospective deployment.
+We audit an independent MIFlu reproduction and 28 forecasting implementations on a 966-row US national influenza series. The supplied reproduction table gives mean squared error (MSE) 1.4995 versus the published 1.4355, with lower MSE at two horizons and higher MSE at two. Under three benchmark seeds, MIFlu, PatchTST and NLinear achieve 1.5574, 1.6621 and 1.8716. A joint screen using literature-derived timing and intensity tolerances yields 4/16 passing aggregated cells for both NLinear and MIFlu and 0/16 for PatchTST. NLinear has lower mean peak-intensity error but higher mean timing error than MIFlu. Across 11 arms with parameter exports, the MSE–log-parameter fit has slope +0.1171 and R² 0.0223. An audit identifies an incorrect Holm routine in the supplied analysis: correcting 136 comparisons among 17 models yields no rejections, with NLinear–PatchTST p approximately 0.1172. This does not establish equivalence. Eleven frozen language encoders perform worse than a decision tree in the tested readout configuration. The returned queue records ablation completion 60/60; per-variant aggregate analysis is pending. The findings are descriptive and limited to one split, retrospective peak detection and adapted implementations. We recommend reporting peak magnitude and timing alongside average error, then selecting on validation-defined costs and budgets before prospective deployment.
 I. Introduction
 Influenza forecasting supports preparedness, but lower average error does not ensure accurate peak magnitude or timing. We examine a supplied MIFlu reproduction [1] and a broader set of project implementations without treating the joint peak screen as clinical certification.
 Contributions. (1) An audited reproduction comparison with a +4.5% mean-MSE gap. (2) A shared-window ranking of 28 implementations. (3) A peak timing–magnitude comparison revealing 4/16, 4/16 and 0/16 aggregate-cell passes for the leading three arms. (4) A parameter and statistical audit identifying low explained variance (R² 0.0223) and a defective Holm adjustment. The prescriptive addition is a validation-defined decision rule, not a tested new forecasting method.
@@ -22,6 +22,7 @@
 D. Decision rule
 Decision rule for future validation: specify an MSE budget B, an allowable peak-failure rate q, and decision costs before inspecting a new test period. Among models meeting B and q on validation seasons, minimise expected decision cost, then parameter count as a tie-breaker. For an escalate/wait decision, use costs c_FP for unnecessary escalation and c_FN for a missed surge, with zero cost for correct actions. Escalate when a validated surge probability exceeds c_FP/(c_FP+c_FN). Costs, B and q have not been elicited or validated, so no model is certified for deployment. NLinear is a low-cost candidate for further peak-height validation; MIFlu remains the observed MSE leader.
 V. Experiments
+A ten-seed expansion (2021–2030) is underway. Returned artefacts cover 160/160 core cells, including DLinear controls outside the historical 28-arm roster. The national ledger contains 117/1120 complete cells at 4 November 23:35 HKT; the owner reports 141 at 5 November 00:15 HKT. These are execution counts rather than a completed new evaluation. All result tables in this manuscript retain the historical protocols.
 The roster comprises 13 conventional models, MIFlu and three other LLM-based implementations, and 11 frozen language encoders. Accuracy uses seven-variable standardised MSE/MAE. Peak errors use de-normalised ILITOTAL. Parameter analysis has 11 models, paired tests 17, and frozen-feature analysis 11; these denominators must not be conflated. We do not present these adapted implementations as verified exact replications of each cited comparator.
 VI. Results
 A. Reproduction
@@ -53,10 +54,11 @@
 F4 conclusion. The 11 tested frozen encoders score 4.7374–5.2049, or 3.04–3.34× MIFlu’s MSE. All exceed the decision tree’s 4.3198 and pass 0/16 cells. This is a negative result for this feature/readout configuration; prompting, fine-tuning and numerical foundation models remain untested.
 G. Ablation design
 TABLE VIII. Ablation design and snapshot status
-Owner-reported status at 3 November 2026: 60/60 additional cells, job 722968. Burgundy queue and per-cell manifests show 60/60 DONE; the per-variant aggregate trend has not been recomputed. The baseline 12 cells are not part of the additional 60. No trend is inferred.
-F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. It was inspected statically, not executed here. Other fusion paths and training randomness require separate checks.
+Returned Burgundy queue evidence dated 4 November 2026 records 60/60 additional ablation cells DONE. Per-variant seven-channel aggregation remains pending; this review did not independently rerun the ablation jobs. Historical job 722968 is reported CANCELLED, not active. The baseline 12 cells are not part of the additional 60. No trend is inferred.
+F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. The supplied JUnit and runtime log now record three no-text assertions passed with zero skips under fixed-weight CPU evaluation; they were not rerun in this review. Other fusion paths and training randomness require separate checks.
 VII. Threats to Validity
-One national series and one chronological split do not establish regional or prospective utility. Peak matching can use future observations to define events and is a retrospective evaluation tool. Synthetic date labels require a verified CDC calendar mapping before season-specific claims. Parameter exports omit MIFlu and encoders. The 60/60 ablation status is owner-reported, not a live cluster check. Modern numerical foundation baselines, regional results, rolling origins and validated uncertainty are missing.
+The new expansion still mixes stored scoring panels: cropped MIFlu metrics versus full-window metrics for other models. Complete seven-channel MIFlu exports are needed before harmonised comparison. PROTOCOL_LOCK.json remains unfrozen after submission; nothing is backdated or described as prospective confirmation. Supplied CPU no-text passes do not establish training-time causal effects. Queue-reported ablation completion does not establish a depth/LoRA effect.
+One national series and one chronological split do not establish regional or prospective utility. Peak matching can use future observations to define events and is a retrospective evaluation tool. Synthetic date labels require a verified CDC calendar mapping before season-specific claims. Parameter exports omit MIFlu and encoders. The supplied queue log records 60/60 ablation cells DONE, but no per-variant aggregate trend has been independently verified. Modern numerical foundation baselines, regional results, rolling origins and validated uncertainty are missing.
 Source p-values are retained but their complete raw paired inputs were not independently rescored. Corrected Holm values recover the enumeration grid and retain provenance to the rounded export. The reported source effect uses pooled model SD rather than paired-difference SD. A seed ensemble with an arbitrary variance floor is not a validated predictive distribution. No prospective utility, equivalence margin or calibrated surge probability has been established.
 VIII. Conclusion
 MIFlu leads the observed MSE ranking. NLinear offers lower peak-height error at low parameter count but has worse mean peak timing than MIFlu. The joint screen therefore exposes trade-offs rather than a universal winner. Corrected significance analysis supports no familywise rejection at the present resolution. Further regional, rolling-origin and foundation-model controls are needed before submission or deployment.
```

## ieee_manuscript_zh.docx

```diff
--- returned v6
+++ integrated v8
@@ -2,7 +2,7 @@
 CHAN Sing Yeung
香港城市大学电子工程学系毕业设计
 面向 IEEE JBHI 的单栏审阅草稿。当前投稿规则与页数限制仍待核实。贡献定位为实证评估，尚未达到投稿状态。
 摘要
-本文审计 MIFlu 的独立复现及美国全国流感 966 行序列上的 28 个预测实现。复现表平均 MSE 为 1.4995，原文为 1.4355，逐跨度两低两高。三种子基准中，MIFlu、PatchTST、NLinear 分别为 1.5574、1.6621、1.8716。采用文献容差的联合筛选下，NLinear 与 MIFlu 各通过 4/16 聚合单元，PatchTST 为 0/16。NLinear 峰高误差更低，但时间误差高于 MIFlu。11 个有参数导出的模型中，MSE 对对数参数的斜率为 +0.1171，R² 为 0.0223。源 Holm 程序存在错误；修正 17 模型的 136 配对后，没有拒绝，NLinear–PatchTST 的 p 约 0.1172，不能据此证明等价。11 个冻结语言编码器在所测读出配置中均差于决策树。消融仅有用户报告的 60/60 完成，尚未聚合。结论受单次划分、回顾性峰检测及适配实现限制。建议并列报告峰高、时间与平均误差，并在前瞻部署前依验证阶段确定的代价与预算选模。
+本文审计 MIFlu 的独立复现及美国全国流感 966 行序列上的 28 个预测实现。复现表平均 MSE 为 1.4995，原文为 1.4355，逐跨度两低两高。三种子基准中，MIFlu、PatchTST、NLinear 分别为 1.5574、1.6621、1.8716。采用文献容差的联合筛选下，NLinear 与 MIFlu 各通过 4/16 聚合单元，PatchTST 为 0/16。NLinear 峰高误差更低，但时间误差高于 MIFlu。11 个有参数导出的模型中，MSE 对对数参数的斜率为 +0.1171，R² 为 0.0223。源 Holm 程序存在错误；修正 17 模型的 136 配对后，没有拒绝，NLinear–PatchTST 的 p 约 0.1172，不能据此证明等价。11 个冻结语言编码器在所测读出配置中均差于决策树。回传队列记录消融 60/60 为 DONE，逐变体趋势尚未核实。结论受单次划分、回顾性峰检测及适配实现限制。建议并列报告峰高、时间与平均误差，并在前瞻部署前依验证阶段确定的代价与预算选模。
 I. 引言
 流感预测可支持准备工作，但较低平均误差不能保证峰高与时间准确。本文检查所附 MIFlu 复现 [1] 与更广的项目实现，并不把联合峰值筛选当作临床认证。
 贡献。 （1）审计平均 MSE 差为 +4.5% 的复现比较。（2）统一窗口下的 28 实现排名。（3）比较峰值时间与幅度，前三模型聚合单元通过数为 4/16、4/16、0/16。（4）参数及统计审计揭示较低解释度（R² 0.0223）与错误 Holm 校正。新增指导是验证阶段确定的决策规则，并非已测试的新预测方法。
@@ -22,6 +22,7 @@
 D. 决策规则
 后续验证的决策规则：在查看新测试期之前确定 MSE 预算 B、允许峰值失败率 q 与决策代价。在验证季同时满足 B 与 q 的模型中最小化期望决策代价，再以参数量打破平局。对升级响应 / 等待决策，误报代价为 c_FP，漏报代价为 c_FN，正确行动代价为零；仅当经过验证的高峰概率超过 c_FP/(c_FP+c_FN) 时升级。代价、B、q 尚未征询或验证，因此没有模型被认证可部署。NLinear 是低成本峰高验证候选，MIFlu 仍为观测 MSE 最优。
 V. 实验
+共同十种子（2021–2030）扩展正在进行。核心回传产物为 160/160，含不属于历史 28 模型名单的 DLinear 控制。全国账本在 11 月 4 日 23:35 HKT 有 117/1120 完成，用户在 11 月 5 日 00:15 HKT 报告 141。这些是执行计数，不是已完成的新评估；本稿所有科学表保留历史协议结果。
 模型名单包括 13 个传统模型、MIFlu 及另外三个基于 LLM 的实现、11 个冻结语言编码器。精度采用七变量标准化 MSE/MAE，峰值误差采用反标准化 ILITOTAL。参数分析为 11 模型，配对检验为 17，冻结特征分析为 11，分母不能混用。本文不将适配实现视为已核实的各参考方法精确复现。
 VI. 结果
 A. 复现
@@ -53,10 +54,11 @@
 F4 结论。 所测 11 个冻结编码器的 MSE 为 4.7374–5.2049，是 MIFlu 的 3.04–3.34 倍，全部高于决策树的 4.3198，且均通过 0/16 单元。这是该特征与读出配置的负面结果；提示、微调及数值时序基础模型仍未检验。
 G. 消融设计
 表 8. 消融设计与快照状态
-用户报告截至 2026 年 11 月 3 日：新增 60 单元中完成 27，作业 722968。Burgundy 队列与逐格 manifest 显示 60/60 已完成；逐变体聚合趋势尚未重算。参考 12 单元不计入新增 60 单元。不推断趋势。
-F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。本次仅静态检查，未执行。其他融合路径及训练随机性须分别验证。
+2026 年 11 月 4 日回传的 Burgundy 队列记录显示新增消融单元 60/60 为 DONE。逐变体七通道聚合仍待完成；本次未独立重跑消融作业。历史作业 722968 的回传状态为 CANCELLED，不是仍在运行。参考 12 单元不计入新增 60 单元。不推断趋势。
+F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。现有所附 JUnit 与运行日志记录三项固定权重 CPU no-text 断言通过、零跳过；本次审阅未重跑这些模型测试。其他融合路径及训练随机性须分别验证。
 VII. 有效性威胁
-单一全国序列与单次时序划分不能证明区域或前瞻效用。峰值匹配可使用未来观测定义事件，只能作为回顾性评测工具。合成日期标签必须与 CDC 日历核实映射后才能作逐季判断。参数导出缺少 MIFlu 与编码器。60/60 的消融状态来自用户报告，而非实时集群检查。现代数值基础模型、区域结果、滚动原点及经过验证的不确定性仍缺失。
+新扩展的所存评分面板尚不一致：MIFlu 为裁剪窗口，其他模型为全窗口。须补齐 MIFlu 七通道预测后才能共同评分。PROTOCOL_LOCK.json 在提交后仍未冻结，不能倒填时间或称作前瞻确认。所附 CPU no-text 通过不证明训练时因果作用；队列消融完成也不证明深度或 LoRA 收益。
+单一全国序列与单次时序划分不能证明区域或前瞻效用。峰值匹配可使用未来观测定义事件，只能作为回顾性评测工具。合成日期标签必须与 CDC 日历核实映射后才能作逐季判断。参数导出缺少 MIFlu 与编码器。所附队列日志记录消融 60/60 为 DONE，但尚未独立核实逐变体聚合趋势。现代数值基础模型、区域结果、滚动原点及经过验证的不确定性仍缺失。
 保留了源 p 值，但未从全部原始配对输入独立重评分。修正 Holm 值恢复枚举网格，并保留与四舍五入导出的来源关系。源效应量采用模型合并标准差，而非配对差标准差。带任意方差下限的种子集成不是已验证的预测分布。前瞻效用、等价界值及经校准的高峰概率均未确立。
 VIII. 结论
 MIFlu 在观测 MSE 排名中领先。NLinear 参数较少、峰高误差较低，但平均峰值时间差于 MIFlu。联合筛选揭示的是取舍，而非通用赢家。正确显著性分析在当前分辨率下没有检验族拒绝。投稿或部署前仍需区域、滚动原点与基础模型对照。
```

## progress_report_en.docx

```diff
--- returned v6
+++ integrated v8
@@ -19,7 +19,10 @@
 Design impact. All retained arms use the same cropped evaluation windows. Scaling is fitted on training data. The 7-variable average is dimensionless, while peak errors use ILITOTAL in patient counts. This allows transparent comparisons without pretending the joint screen certifies safe public-health use. Three benchmark seeds reflect compute limits; additional independent seasons are needed for uncertainty.
 
 6. Progress
-Progress against plan. The supplied exports contain the reproduction table and 28 × 4 × 3 benchmark cell means. The original suite is supplied under tests_archive/, but cannot be collected cleanly here. My audit now recomputes the CSV aggregates and has seven new CPU tests. The ablation remains owner-reported at 60/60 with no per-variant aggregation. Regional and rolling-origin evaluation are incomplete.
+Progress against plan. The supplied exports contain the reproduction table and 28 × 4 × 3 benchmark cell means. The original suite is supplied under tests_archive/, but cannot be collected cleanly here. My audit now recomputes the CSV aggregates and has seven new CPU tests. The returned queue reports 60/60 ablation cells DONE; per-variant aggregation remains pending. Regional and rolling-origin evaluation are incomplete.
+Execution update (5 November 2026 00:15 HKT). Core artefacts: 160/160 complete. The national 1120 matrix is in progress: packaged ledger 117 completed, later owner report 141. Supplied CPU no-text record: 3 passed, 0 skipped. Ablation queue: 60/60 DONE, aggregate trend pending. These execution records do not replace the historical results below.
+A common ten-seed result is not yet available. MIFlu stored metrics use cropped windows, while other supplied models use all valid windows; the complete seven-channel MIFlu prediction tensors were not attached. Scores must be harmonised before a common ranking. The submitted protocol still has frozen:false and no lock timestamp, so these comparisons remain retrospective/exploratory. The two data profiles have different byte hashes; the supplied aligned seven-channel comparison reports maximum numeric difference 0.0, which is not byte identity or independent verification of upstream provenance.
+At the 00:15 handoff the owner reports 13 empty decision_tree partial directories and two pending gpu_a100 lanes. Table VI (19 TODO) and walk-forward (170 TODO) have not started in the v2 successor chain, although earlier legacy DONE rows exist. One earlier summary lists 9 regional TODOs; execution-end status must reconcile the dates and skip counts. Storage is owner-reported at approximately 306/300 GB soft, with ten-day grace and 1024 GB hard; the source quota log uses KB units. These are dated reports, not current live readings.
 Table 3. MIFlu reproduction compared with the paper
 Source: ESSAY_VS_REPRODUCTION_TABLE_V.csv, lines 2–6. SD is recomputed from the code-transcribed ten-seed oracle; its raw run logs are not included. Positive differences mean higher error.
 The reproduction CSV reports mean MSE 1.4995 versus 1.4355, a 4.5% increase. MSE is lower at L24 and L36 and higher at L48 and L60. Mean MAE is 0.8043 versus 0.7452 (+7.9%), but its signs are one lower and three higher; MAE does not share the MSE 2–2 crossover. Protocol and missing upstream provenance limit claims of exact replication.
@@ -45,12 +48,12 @@
 11 retained encoders × 4 horizons × 3 seeds = 132 cells. The historical plan included two additional embedding-only arms, giving 156 planned cells; those 24 omitted cells are outside the 28-model roster. The result tests only this frozen-feature pipeline.
 F4 conclusion. The 11 tested frozen encoders score 4.7374–5.2049, or 3.04–3.34× MIFlu’s MSE. All exceed the decision tree’s 4.3198 and pass 0/16 cells. This is a negative result for this feature/readout configuration; prompting, fine-tuning and numerical foundation models remain untested.
 Table 9. Ablation design and snapshot status
-Owner-reported status at 3 November 2026: 60/60 additional cells, job 722968. Burgundy queue and per-cell manifests show 60/60 DONE; the per-variant aggregate trend has not been recomputed. The baseline 12 cells are not part of the additional 60. No trend is inferred.
-F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. It was inspected statically, not executed here. Other fusion paths and training randomness require separate checks.
+Returned Burgundy queue evidence dated 4 November 2026 records 60/60 additional ablation cells DONE. Per-variant seven-channel aggregation remains pending; this review did not independently rerun the ablation jobs. Historical job 722968 is reported CANCELLED, not active. The baseline 12 cells are not part of the additional 60. No trend is inferred.
+F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. The supplied JUnit and runtime log now record three no-text assertions passed with zero skips under fixed-weight CPU evaluation; they were not rerun in this review. Other fusion paths and training randomness require separate checks.
 Problems encountered. The source exported Holm column remains defective; the corrected corpus recomputes the proper adjustment. The roster arithmetic, MAE crossover, hardware coverage and missing tests also needed correction. Queue status cannot be certified from this offline snapshot. I will freeze the corrected reporting path and keep all original CSVs for comparison.
 7. Summary of objectives addressed and results achieved to date
 Table 10. Objectives addressed and estimated completion
-These are planning estimates supplied in the task, not measured research scores. 45% is 60/60. The other estimates are not independently measured.
+The ablation queue completion is 100% (60/60), while its per-variant analysis remains pending. Other project-completion percentages are owner planning estimates, not measured research scores. The old statement equating 45% with 60/60 was incorrect.
 8. Work schedule and expected results for the next one to two months
 Table 11. Work schedule and expected outputs
 Dates are targets. Queue availability, measured runtime and supervisor approval determine feasibility. No conference deadline is inferred from this schedule.
@@ -171,7 +174,7 @@
 28-arm benchmark export | Yes, arithmetic verified | 100%
 Peak and efficiency evaluation | Yes, interpretation corrected | 100%
 Frozen encoder axis | Yes, retained arms only | 100%
-Ablation | Partly, owner reports 60/60 | 45%
+Ablation | Queue DONE 60/60; analysis pending | 100% queue only
 Rolling origin | Code stage, not evaluated | 15%
 Manuscript | Draft; publication evidence incomplete | 70%
 Target date | Task | Expected output and fallback
```

## progress_report_zh.docx

```diff
--- returned v6
+++ integrated v8
@@ -19,7 +19,10 @@
 设计影响。 所有保留模型采用相同裁剪窗口，标准化仅在训练数据拟合。七变量均值无量纲，峰值误差则使用患者人数尺度的 ILITOTAL。这样能够透明比较，同时不把联合筛选误称为公共卫生安全认证。基准的三个种子反映算力限制，不确定性仍需更多独立季节。
 
 6. 进度
-对照计划的进度。 所附导出包含复现表和 28 × 4 × 3 基准单元聚合。原测试已包含在 tests_archive/，但本环境无法完整收集。本次审计重算 CSV 聚合，并新增七个 CPU 测试。消融仍为用户报告的 60/60，未逐变体聚合。区域与滚动原点评测尚未完成。
+对照计划的进度。 所附导出包含复现表和 28 × 4 × 3 基准单元聚合。原测试已包含在 tests_archive/，但本环境无法完整收集。本次审计重算 CSV 聚合，并新增七个 CPU 测试。回传队列记录消融 60/60 为 DONE，逐变体聚合仍待完成。区域与滚动原点评测尚未完成。
+执行更新（2026 年 11 月 5 日 00:15 HKT）：核心产物 160/160 完整；全国 1120 矩阵仍在进行，打包账本为 117 完成，稍后用户报告 141。所附 CPU no-text 记录为 3 通过、0 跳过；消融队列为 60/60 DONE，聚合趋势待完成。这些执行状态不替换下列历史科学结果。
+目前还没有完整共同十种子结果。MIFlu 的所存指标采用裁剪窗口，其他已附模型采用全部有效窗口；未附完整七通道 MIFlu 预测张量，须先统一评分再建立共同排名。已提交协议仍为 frozen:false、锁定时间为空，因此比较属于回顾性、探索性。两个数据 profile 的字节哈希不同；所附七通道对齐比较报告最大数值差为 0.0，这不等于字节身份或独立核实上游来源。
+00:15 交接时用户报告 13 个空 decision_tree 部分目录、两个 gpu_a100 通道待调度。Table VI（19 TODO）及滚动原点（170 TODO）在 v2 后继链尚未开始，但旧链已有 DONE 行。较早摘要另写区域 9 TODO，执行端须核对日期与跳过数。存储为用户报告约 306/300 GB 软配额、宽限十天、硬配额 1024 GB；原配额日志采用 KB。这些均是带日期报告，不是本次实时读取。
 表 3. MIFlu 复现与原文对照
 来源：ESSAY_VS_REPRODUCTION_TABLE_V.csv 第 2–6 行。标准差由代码中转录的十种子 oracle 重算；原始运行日志未随包提供。正差表示误差更高。
 复现 CSV 的平均 MSE 为 1.4995，对照 1.4355，增加 4.5%。L24、L36 更低，L48、L60 更高。平均 MAE 为 0.8043，对照 0.7452（+7.9%），但逐跨度为一低三高；MAE 没有 MSE 的二比二符号交叉。协议差异与上游来源缺失限制了精确复现的主张。
@@ -45,12 +48,12 @@
 11 个保留编码器 × 4 跨度 × 3 种子 = 132 单元。历史计划还包含两个仅嵌入模型，总计 156 单元；未纳入的 24 单元不属于 28 模型正式名单。此结果只评价该冻结特征流程。
 F4 结论。 所测 11 个冻结编码器的 MSE 为 4.7374–5.2049，是 MIFlu 的 3.04–3.34 倍，全部高于决策树的 4.3198，且均通过 0/16 单元。这是该特征与读出配置的负面结果；提示、微调及数值时序基础模型仍未检验。
 表 9. 消融设计与快照状态
-用户报告截至 2026 年 11 月 3 日：新增 60 单元中完成 27，作业 722968。Burgundy 队列与逐格 manifest 显示 60/60 已完成；逐变体聚合趋势尚未重算。参考 12 单元不计入新增 60 单元。不推断趋势。
-F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。本次仅静态检查，未执行。其他融合路径及训练随机性须分别验证。
+2026 年 11 月 4 日回传的 Burgundy 队列记录显示新增消融单元 60/60 为 DONE。逐变体七通道聚合仍待完成；本次未独立重跑消融作业。历史作业 722968 的回传状态为 CANCELLED，不是仍在运行。参考 12 单元不计入新增 60 单元。不推断趋势。
+F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。现有所附 JUnit 与运行日志记录三项固定权重 CPU no-text 断言通过、零跳过；本次审阅未重跑这些模型测试。其他融合路径及训练随机性须分别验证。
 遇到的问题。 源 CSV 导出的 Holm 列仍有误；修正语料已重新计算正确校正。模型名单算术、MAE 交叉、硬件覆盖与测试缺失也需修正。离线快照不能认证实时排队状态。我将冻结修正后的报告路径，并保留所有原 CSV 便于对照。
 7. 已处理目标与迄今成果总结
 表 10. 已处理目标与估计完成度
-这些是任务给定的项目进度估计，不是研究评分。45% 等于 60/60；其他比例未独立测量。
+消融队列完成度为 100%（60/60），逐变体分析仍待完成。其余项目完成比例属于用户规划估计，不是研究评分。旧文将 45% 等同于 60/60 的说法有误。
 8. 未来一至两月安排及预期成果
 表 11. 工作安排与预期产物
 日期为目标，能否执行取决于排队、实测运行时间与导师决定；此表不推断会议截止日。
@@ -171,7 +174,7 @@
 28 模型基准导出 | 是，算术已核实 | 100%
 峰值与效率评估 | 是，解释已修正 | 100%
 冻结编码器维度 | 是，仅保留模型 | 100%
-消融 | 部分，用户报告 60/60 | 45%
+消融 | 队列 DONE 60/60；分析待完成 | 队列完成 100%
 滚动原点 | 代码阶段，未评测 | 15%
 手稿 | 草稿，发表证据未齐 | 70%
 目标日期 | 任务 | 预期输出与替代方案
```

## report_internal_en.docx

```diff
--- returned v6
+++ integrated v8
@@ -16,7 +16,7 @@
 
 Reading purpose. This internal report supports supervision and explanation. Questions Q01–Q25 are placed beside the relevant evidence. Each answer connects named papers and reading locations to local evidence, explains the choice and gives a supervisor short answer. Accuracy and peak skill cover 28 arms; parameter exports cover 11, and paired tests 17.
 1 Data and provenance
-Run python scripts/verify_snapshot.py --raw-smoke and python -m pytest tests/test_snapshot_audit.py -q from the repository root. The audit re-derives headline aggregates, peak flags, correlations, regression, Holm adjustment and one raw prediction MSE. Seven newly added CPU audit tests passed; they are separate from the archived model suite. The corrected ZIP supplies tests_archive/. Collection fails under the historical layout and missing model dependencies. No archived-suite pass count or reliable collected total is claimed. Training, live HPC status and upstream code were not rerun. The original source CSVs are retained unchanged, with a separate corrected Holm export.
+Run python scripts/verify_snapshot.py --raw-smoke and python -m pytest tests/test_snapshot_audit.py -q from the repository root. The audit re-derives headline aggregates, peak flags, correlations, regression, Holm adjustment and one raw prediction MSE. Seven newly added CPU audit tests passed; they are separate from the archived model suite. The corrected ZIP supplies tests_archive/. Collection fails under the historical layout and missing model dependencies. No archived-suite pass count or reliable collected total is claimed. The return supplies GPU execution and scheduler records, including core artefact completion 160/160. This review did not rerun training, connect to live HPC or execute pinned upstream code. See the v7 addendum for dated national counts and remaining limits. The original source CSVs are retained unchanged, with a separate corrected Holm export.
 Table 1. Data and evaluation contract
 Identity compares the two supplied 966-row files after selecting their seven matching numeric columns. It does not re-establish byte identity with an independently downloaded upstream file. Dates in the author-format file are synthetic labels.
 Q01 Why use 676 training, 97 validation and 193 test rows?
@@ -198,23 +198,28 @@
 F4 conclusion. The 11 tested frozen encoders score 4.7374–5.2049, or 3.04–3.34× MIFlu’s MSE. All exceed the decision tree’s 4.3198 and pass 0/16 cells. This is a negative result for this feature/readout configuration; prompting, fine-tuning and numerical foundation models remain untested.
 Distribution mismatch, frozen capacity and the chosen readout are possible explanations. Their causal roles are not separated by these results. A linear readout does not guarantee that useful nonlinear features can be recovered.
 9 Ablation design and status
+Execution update at 5 November 2026 00:15 HKT
+The returned core Track B artefacts are complete for 160/160 cells: MIFlu, NLinear, PatchTST and DLinear, four forecast lengths and ten seeds (2021–2030). The national 28-arm expansion remains in progress. Its packaged ledger records 117 completed and 1003 queued at 4 November 23:35 HKT; a later supplied report records 139, and the owner reports 141/1120 at 5 November 00:15 HKT. These are different capture times, not conflicting estimates of one frozen snapshot. This review did not connect to Burgundy.
+The supplied JUnit and runtime log record three fixed-weight CPU no-text assertions passed with zero skips. This supports the inspected evaluation path, not equality of independently trained trajectories or text/LoRA gradient reachability. Whole-archive collection still fails. The supplied queue records 60/60 additional ablation cells DONE; their per-variant seven-channel aggregate trend remains unverified. Job 722968 is a historical cancelled job.
+A common ten-seed result is not yet available. MIFlu stored metrics use cropped windows, while other supplied models use all valid windows; the complete seven-channel MIFlu prediction tensors were not attached. Scores must be harmonised before a common ranking. The submitted protocol still has frozen:false and no lock timestamp, so these comparisons remain retrospective/exploratory. The two data profiles have different byte hashes; the supplied aligned seven-channel comparison reports maximum numeric difference 0.0, which is not byte identity or independent verification of upstream provenance.
+At the 00:15 handoff the owner reports 13 empty decision_tree partial directories and two pending gpu_a100 lanes. Table VI (19 TODO) and walk-forward (170 TODO) have not started in the v2 successor chain, although earlier legacy DONE rows exist. One earlier summary lists 9 regional TODOs; execution-end status must reconcile the dates and skip counts. Storage is owner-reported at approximately 306/300 GB soft, with ten-day grace and 1024 GB hard; the source quota log uses KB units. These are dated reports, not current live readings.
 Table 11. Ablation design and snapshot status
-Owner-reported status at 3 November 2026: 60/60 additional cells, job 722968. Burgundy queue and per-cell manifests show 60/60 DONE; the per-variant aggregate trend has not been recomputed. The baseline 12 cells are not part of the additional 60. No trend is inferred.
-F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. It was inspected statically, not executed here. Other fusion paths and training randomness require separate checks.
+Returned Burgundy queue evidence dated 4 November 2026 records 60/60 additional ablation cells DONE. Per-variant seven-channel aggregation remains pending; this review did not independently rerun the ablation jobs. Historical job 722968 is reported CANCELLED, not active. The baseline 12 cells are not part of the additional 60. No trend is inferred.
+F5 provisional conclusion. In miflu_model.py’s author_faithful path, text follows time tokens behind causal attention and the head reads the time tokens. Static inspection therefore predicts no text influence during deterministic evaluation. The supplied tests_archive/test_miflu_ablations.py explicitly asserts both text invariance and full/no-text equality with matched CPU initialisation. The supplied JUnit and runtime log now record three no-text assertions passed with zero skips under fixed-weight CPU evaluation; they were not rerun in this review. Other fusion paths and training randomness require separate checks.
 Q22 Why might no-text give identical outputs in the default path?
-Answer and local evidence. In the inspected author_faithful path, time tokens precede text tokens. Causal attention permits each position to read only its own or earlier positions, and the head reads the time-token positions. Those positions therefore cannot use later text in a deterministic evaluation forward pass. The supplied archive explicitly asserts text invariance and matched-initialisation full/no-text CPU equality, but those model tests were not executed here. Other fusion paths, dropout and independently trained trajectories require separate checks. The exact files and commands are in audit/NO_TEXT_VERIFICATION.md.
-Paper-based reasoning. The Transformer paper explains masking that prevents attention to subsequent positions [24, §3.1]. With the inspected ordering, time positions cannot acquire later text through these layers, and the head reads time positions. This is a structural argument about a fixed forward path, not certification of repository runtime or bitwise equality. The three archived assertions must control weights, inputs and evaluation randomness when comparing changed text and matched full/no-text outputs. They remain not executed. Independent training can consume randomness differently and requires its own test.
+Answer and local evidence. In the inspected author_faithful path, time tokens precede text tokens. Causal attention permits each position to read only its own or earlier positions, and the head reads the time-token positions. Those positions therefore cannot use later text in a deterministic evaluation forward pass. The supplied archive explicitly asserts text invariance and matched-initialisation full/no-text CPU equality, and the supplied JUnit now records those three fixed-weight CPU model assertions passed with zero skips; this review did not rerun them. Other fusion paths, dropout and independently trained trajectories require separate checks. The exact files and commands are in audit/NO_TEXT_VERIFICATION.md.
+Paper-based reasoning. The Transformer paper explains masking that prevents attention to subsequent positions [24, §3.1]. With the inspected ordering, time positions cannot acquire later text through these layers, and the head reads time positions. This is a structural argument about a fixed forward path, not certification of repository runtime or bitwise equality. The three archived assertions must control weights, inputs and evaluation randomness when comparing changed text and matched full/no-text outputs. The supplied JUnit now records three CPU assertions passed with zero skips; they were not rerun in this review. Independent training can consume randomness differently and requires its own test.
 Say to the supervisor. Causal masking supports the structural argument; controlled runtime tests must establish bitwise equality here [24].
 Reading locator. Vaswani et al. [24], §3.1 Decoder; local ForecastingLLM.forward and archived assertions.
 Evidence. miflu_model.py ForecastingLLM; tests_archive/test_miflu_ablations.py; audit/NO_TEXT_VERIFICATION.md
 Q23 What does 60/60 ablation completion allow us to say?
-Answer and local evidence. It is an owner-reported operational snapshot as of 3 November, not a live scheduler result or an aggregated model comparison. The additional design has five arms, each with four horizons and three seeds: 60 cells beyond the 12-cell reference. Without per-arm result exports, completion is not evidence of a depth trend or a benefit of LoRA. Do not infer a completed no-text ablation from the presence of its test assertions. We need run-level outputs, status and provenance before reporting scientific results.
+Answer and local evidence. It is queue-completion evidence in the returned 4 November records, not an aggregated model comparison or an independently rerun ablation study. The additional design has five arms, each with four horizons and three seeds: 60 cells beyond the 12-cell reference. Without per-arm result exports, completion is not evidence of a depth trend or a benefit of LoRA. Do not infer a completed no-text ablation from the presence of its test assertions. We need run-level outputs, status and provenance before reporting scientific results.
 Paper-based reasoning. Tan et al. remove or replace the LLM while retaining the surrounding trainable forecaster [13, §3.2]. This asks whether the backbone contributes beyond the wrapper. Our no-LoRA/depth variants address narrower adaptation/capacity questions; they do not automatically answer the same removal/replacement question or isolate text use. Partial completion is an operational status. Interpreting a scientific trend requires the reported variants’ scores, repeated-run variability and a matched protocol. The literature supplies an experimental question, not a result for our unfinished ladder.
 Say to the supervisor. The papers motivate removal/replacement controls; the incomplete ladder has not answered those causal questions [13].
 Reading locator. Tan et al. [13], §3.2 Proposed Ablations, w/o LLM / LLM2Attn / LLM2Trsf.
 Evidence. Owner snapshot; ablation design table; tests_archive/test_miflu_ablations.py
 10 Interpretation and publication plan
-One national series and one chronological split do not establish regional or prospective utility. Peak matching can use future observations to define events and is a retrospective evaluation tool. Synthetic date labels require a verified CDC calendar mapping before season-specific claims. Parameter exports omit MIFlu and encoders. The 60/60 ablation status is owner-reported, not a live cluster check. Modern numerical foundation baselines, regional results, rolling origins and validated uncertainty are missing.
+One national series and one chronological split do not establish regional or prospective utility. Peak matching can use future observations to define events and is a retrospective evaluation tool. Synthetic date labels require a verified CDC calendar mapping before season-specific claims. Parameter exports omit MIFlu and encoders. The supplied queue log records 60/60 ablation cells DONE, but no per-variant aggregate trend has been independently verified. Modern numerical foundation baselines, regional results, rolling origins and validated uncertainty are missing.
 Decision rule for future validation: specify an MSE budget B, an allowable peak-failure rate q, and decision costs before inspecting a new test period. Among models meeting B and q on validation seasons, minimise expected decision cost, then parameter count as a tie-breaker. For an escalate/wait decision, use costs c_FP for unnecessary escalation and c_FN for a missed surge, with zero cost for correct actions. Escalate when a validated surge probability exceeds c_FP/(c_FP+c_FN). Costs, B and q have not been elicited or validated, so no model is certified for deployment. NLinear is a low-cost candidate for further peak-height validation; MIFlu remains the observed MSE leader.
 Recommendation O1: retain the evaluation contribution and repair its evidence base before adding a new mechanism. The current draft is oriented towards IEEE JBHI because its subject is health forecasting, but it is not submission-ready. Rolling origins, regional validation, stronger baselines and independent code provenance matter more than another architecture before the school deadline.
 Q24 What is added beyond reproduction, and why keep O1?
@@ -224,11 +229,13 @@
 Reading locator. Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract.
 Evidence. audit/INNOVATION_DECISION.md; audit/LITERATURE_REVIEW.md; sources.json [1]
 11 Reproducibility and open checks
-Run python scripts/verify_snapshot.py --raw-smoke and python -m pytest tests/test_snapshot_audit.py -q from the repository root. The audit re-derives headline aggregates, peak flags, correlations, regression, Holm adjustment and one raw prediction MSE. Seven newly added CPU audit tests passed; they are separate from the archived model suite. The corrected ZIP supplies tests_archive/. Collection fails under the historical layout and missing model dependencies. No archived-suite pass count or reliable collected total is claimed. Training, live HPC status and upstream code were not rerun. The original source CSVs are retained unchanged, with a separate corrected Holm export.
+Independent review confirms both uploaded ZIP hashes, all manifest-listed file hashes, core 160/160 artefact completeness and national snapshot 117/1120. Recalculation matches 237 seven-channel NPZ cells and the ILITOTAL metrics of 40 MIFlu CSV cells at each recorded scoring panel. The as-received package validator flags one unlisted temporary prediction file; quarantining it in an extracted review copy yields PASS. Original uploads and the manifest were not rewritten. No full scientific validation follows from that integrity PASS.
+Pending work is to complete or account for every national cell, export all seven MIFlu channels, harmonise both scoring panels, aggregate peak/ablation results and use dependence-aware statistics. Regional/rolling-origin and numerical-foundation controls, real CDC calendar/vintage, full resource measurements and official-source method fidelity remain unresolved even after national completion. Existing tables remain the audited historical results.
+Run python scripts/verify_snapshot.py --raw-smoke and python -m pytest tests/test_snapshot_audit.py -q from the repository root. The audit re-derives headline aggregates, peak flags, correlations, regression, Holm adjustment and one raw prediction MSE. Seven newly added CPU audit tests passed; they are separate from the archived model suite. The corrected ZIP supplies tests_archive/. Collection fails under the historical layout and missing model dependencies. No archived-suite pass count or reliable collected total is claimed. The return supplies GPU execution and scheduler records, including core artefact completion 160/160. This review did not rerun training, connect to live HPC or execute pinned upstream code. See the v7 addendum for dated national counts and remaining limits. The original source CSVs are retained unchanged, with a separate corrected Holm export.
 Hardware provenance covers 204 rows, including the excluded DLinear and omitting MIFlu and all frozen encoders. It overlaps 192 retained cells. Complete per-cell hardware coverage is therefore not established. The original reproduce_all.py targets historical paths and is not the audited quickstart.
-Unverified items: pinned upstream checkpoint/loader protocol and learning rate; archived suite execution and no-text runtime test; ten-seed raw reproduction logs; model revisions/licences; live ablation and regional status; real CDC calendar mapping; current JBHI author limits/JCR record and next-cycle venue dates. Each requires its primary artefact, not a further prose assertion.
+Unverified items: pinned upstream checkpoint/loader protocol and learning rate; whole archived-suite execution beyond the three returned passing CPU no-text checks; ten-seed raw reproduction logs; model revisions/licences; ablation aggregate provenance and updated regional status; real CDC calendar mapping; current JBHI author limits/JCR record and next-cycle venue dates. Each requires its primary artefact, not a further prose assertion.
 Q25 What can a supervisor reproduce now, and what remains unexecuted?
-Answer and local evidence. The documented CPU commands reproduce CSV headline arithmetic, correct Holm and one raw prediction-cell MSE. Seven new CPU audit checks passed. The historical archive was supplied, but collection failed and its model assertions are not counted as passed. Full GPU training, all-run raw rescoring, live HPC, pinned upstream identity and no-text runtime remain unexecuted or unverified. Hardware provenance also lacks complete retained-cell coverage. A polished document does not close those gaps. Use the exact follow-up commands in audit/EXECUTION_STATUS.md and audit/NO_TEXT_VERIFICATION.md.
+Answer and local evidence. The documented CPU commands reproduce CSV headline arithmetic, correct Holm and one raw prediction-cell MSE. Seven new CPU audit checks passed. Whole-archive collection still failed. The supplied JUnit records three fixed-weight CPU no-text assertions passed with zero skips, while returned core artefacts satisfy 160/160 completeness checks. The national 1120 matrix remains in progress. Full common-panel scoring, pinned upstream identity and independent-training text effects remain unresolved; this review did not rerun GPU training or connect to live HPC. Hardware provenance also lacks complete retained-cell coverage. A polished document does not close those gaps. Use the exact follow-up commands in audit/EXECUTION_STATUS.md and audit/NO_TEXT_VERIFICATION.md.
 Paper-based reasoning. Kapoor and Narayanan ask for explicit reporting arguments rather than equating code availability with a valid result [22]. Here distinguish document rebuilding, CSV arithmetic, raw prediction rescoring and model retraining. A supervisor can begin with the CSV audit; the full bundle supports one raw-cell smoke check. Model text invariance needs the three named runtime assertions without skips in a pinned environment. The useful deliverable is a traceable evidence chain with exact commands and status. Passing one evidence level does not certify all the others.
 Say to the supervisor. I distinguish recomputed results from static inspection and give the command and status for each [22].
 Reading locator. Kapoor and Narayanan [22], model info sheets; EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md.
```

## report_internal_zh.docx

```diff
--- returned v6
+++ integrated v8
@@ -16,7 +16,7 @@
 
 阅读目的。 本内部报告用于导师交流及理解过程。Q01–Q25 放在相关证据旁：每题连接具名论文、阅读位置与本地证据，解释选择理由，并给出导师简答。精度与峰值覆盖 28 个模型，参数导出覆盖 11 个，配对检验覆盖 17 个。
 1 数据与来源
-在仓库根目录运行 python scripts/verify_snapshot.py --raw-smoke 及 python -m pytest tests/test_snapshot_audit.py -q。审计重算主要聚合值、峰值标记、相关系数、回归、Holm 校正和一个原始预测 MSE。七个新增 CPU 审计测试已通过，它们与归档模型测试分开。修正 ZIP 已提供 tests_archive/，但历史目录布局及模型依赖缺失导致收集失败。本次不主张归档测试通过数或可靠总数。本次未重跑训练、未查询实时 HPC，亦未运行上游代码。原 CSV 保持不变，Holm 修正另行导出。
+在仓库根目录运行 python scripts/verify_snapshot.py --raw-smoke 及 python -m pytest tests/test_snapshot_audit.py -q。审计重算主要聚合值、峰值标记、相关系数、回归、Holm 校正和一个原始预测 MSE。七个新增 CPU 审计测试已通过，它们与归档模型测试分开。修正 ZIP 已提供 tests_archive/，但历史目录布局及模型依赖缺失导致收集失败。本次不主张归档测试通过数或可靠总数。回传包现提供 GPU 执行和调度记录，包括核心单元产物完整性 160/160。本次审阅未重跑训练、连接实时 HPC 或执行固定版本上游代码；全国矩阵的分时计数及限制见 v7 增补。原 CSV 保持不变，Holm 修正另行导出。
 表 1. 数据与评测约定
 一致性是选择本包两个 966 行文件中相应七列后比较，不能重新证明与独立下载的作者文件逐字节相同。作者格式文件的日期为合成标签。
 Q01 为什么采用 676 行训练、97 行验证、193 行测试？
@@ -198,23 +198,28 @@
 F4 结论。 所测 11 个冻结编码器的 MSE 为 4.7374–5.2049，是 MIFlu 的 3.04–3.34 倍，全部高于决策树的 4.3198，且均通过 0/16 单元。这是该特征与读出配置的负面结果；提示、微调及数值时序基础模型仍未检验。
 分布差异、冻结容量和所选读出均可能影响结果，但本结果未分离其因果作用。线性读出不能保证提取可用的非线性特征。
 9 消融设计与状态
+截至 2026 年 11 月 5 日 00:15 HKT 的执行更新
+回传 Track B 核心产物满足 160/160 完整性检查：MIFlu、NLinear、PatchTST、DLinear，四个预测长度与十种子（2021–2030）。全国 28 模型扩展仍在进行。11 月 4 日 23:35 HKT 的打包账本为 117 完成、1003 排队；稍后所附报告为 139，用户在 11 月 5 日 00:15 HKT 报告 141/1120。这些对应不同采集时刻，不是同一冻结快照的矛盾估计。本次未连接 Burgundy 实时状态。
+所附 JUnit 及运行日志记录三项固定权重 CPU no-text 断言通过，零跳过。它支持已检查评估路径，不证明独立训练轨迹相等或文本、LoRA 梯度可达性。整个归档测试的收集仍失败。回传队列记录新增消融 60/60 为 DONE，但逐变体七通道聚合趋势仍未核实。作业 722968 是历史已取消作业。
+目前还没有完整共同十种子结果。MIFlu 的所存指标采用裁剪窗口，其他已附模型采用全部有效窗口；未附完整七通道 MIFlu 预测张量，须先统一评分再建立共同排名。已提交协议仍为 frozen:false、锁定时间为空，因此比较属于回顾性、探索性。两个数据 profile 的字节哈希不同；所附七通道对齐比较报告最大数值差为 0.0，这不等于字节身份或独立核实上游来源。
+00:15 交接时用户报告 13 个空 decision_tree 部分目录、两个 gpu_a100 通道待调度。Table VI（19 TODO）及滚动原点（170 TODO）在 v2 后继链尚未开始，但旧链已有 DONE 行。较早摘要另写区域 9 TODO，执行端须核对日期与跳过数。存储为用户报告约 306/300 GB 软配额、宽限十天、硬配额 1024 GB；原配额日志采用 KB。这些均是带日期报告，不是本次实时读取。
 表 11. 消融设计与快照状态
-用户报告截至 2026 年 11 月 3 日：新增 60 单元中完成 27，作业 722968。Burgundy 队列与逐格 manifest 显示 60/60 已完成；逐变体聚合趋势尚未重算。参考 12 单元不计入新增 60 单元。不推断趋势。
-F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。本次仅静态检查，未执行。其他融合路径及训练随机性须分别验证。
+2026 年 11 月 4 日回传的 Burgundy 队列记录显示新增消融单元 60/60 为 DONE。逐变体七通道聚合仍待完成；本次未独立重跑消融作业。历史作业 722968 的回传状态为 CANCELLED，不是仍在运行。参考 12 单元不计入新增 60 单元。不推断趋势。
+F5 暂定结论。 miflu_model.py 的 author_faithful 路径将文本置于时间词元之后，使用因果注意力，预测头只读取时间词元。静态检查因此推断确定性评估时文本不影响输出。所附 tests_archive/test_miflu_ablations.py 明确断言文本不变性，以及匹配 CPU 初始化时完整与无文本模型相同。现有所附 JUnit 与运行日志记录三项固定权重 CPU no-text 断言通过、零跳过；本次审阅未重跑这些模型测试。其他融合路径及训练随机性须分别验证。
 Q22 为什么默认路径下去掉文本可能得到完全相同的输出？
-直接回答与本地证据。 已检查的 author_faithful 路径把时间词元放在文本词元前。因果注意力只允许每个位置读取自身或更早位置，预测头又只读取时间词元位置。因此在确定性评估前向过程中，这些位置无法利用后面的文本。所附归档明确断言文本不变性，以及匹配初始化的完整/无文本 CPU 输出相同，但本次没有执行这些模型测试。其他融合路径、dropout 和独立训练轨迹仍需分别检查。精确文件与命令见 audit/NO_TEXT_VERIFICATION.md。
-文献依据与选择理由。 Transformer 原文说明遮罩如何阻止关注后续位置 [24，第 3.1 节]。按已检查顺序，时间位置不能通过这些层取得后方文本，预测头又只读时间位置。这是固定前向路径的结构论证，不是仓库运行或逐位相等认证。三项归档断言须控制权重、输入和评估随机性，再比较更换文本及匹配完整/无文本输出，当前仍未执行。独立训练可能不同地消耗随机数，须另测。
+直接回答与本地证据。 已检查的 author_faithful 路径把时间词元放在文本词元前。因果注意力只允许每个位置读取自身或更早位置，预测头又只读取时间词元位置。因此在确定性评估前向过程中，这些位置无法利用后面的文本。所附归档明确断言文本不变性，以及匹配初始化的完整/无文本 CPU 输出相同，所附 JUnit 现记录三项固定权重 CPU 模型断言通过、零跳过；本次审阅未重跑它们。其他融合路径、dropout 和独立训练轨迹仍需分别检查。精确文件与命令见 audit/NO_TEXT_VERIFICATION.md。
+文献依据与选择理由。 Transformer 原文说明遮罩如何阻止关注后续位置 [24，第 3.1 节]。按已检查顺序，时间位置不能通过这些层取得后方文本，预测头又只读时间位置。这是固定前向路径的结构论证，不是仓库运行或逐位相等认证。三项归档断言须控制权重、输入和评估随机性，再比较更换文本及匹配完整/无文本输出，所附 JUnit 现记录三项 CPU 断言通过且零跳过；本次未重跑模型测试。独立训练可能不同地消耗随机数，须另测。
 向导师简答。 因果遮罩支持结构论证，本地逐位相等须由受控运行测试建立 [24]。
 论文位置。 Vaswani et al. [24], §3.1 Decoder; local ForecastingLLM.forward and archived assertions.
 证据。 miflu_model.py ForecastingLLM; tests_archive/test_miflu_ablations.py; audit/NO_TEXT_VERIFICATION.md
 Q23 消融完成 60/60，究竟可以说什么？
-直接回答与本地证据。 这是截至 11 月 3 日用户报告的运行状态快照，不是实时调度器查询，也不是已聚合的模型比较。新增设计有五个变体，每个四跨度、三种子，合计 60 单元；参考模型另有 12 单元。没有逐变体结果导出，就不能从完成数量推断深度趋势或 LoRA 收益。存在 no-text 测试断言，也不代表已完成相应消融实验。报告科学结果前，需要逐运行输出、状态及来源。
+直接回答与本地证据。 这是 11 月 4 日回传记录中的队列完成证据，不是已聚合的模型比较，也不是本次独立重跑的消融研究。新增设计有五个变体，每个四跨度、三种子，合计 60 单元；参考模型另有 12 单元。没有逐变体结果导出，就不能从完成数量推断深度趋势或 LoRA 收益。存在 no-text 测试断言，也不代表已完成相应消融实验。报告科学结果前，需要逐运行输出、状态及来源。
 文献依据与选择理由。 Tan 等保留周边可训练预测器，移除或替换 LLM [13，第 3.2 节]，以检验骨干是否额外贡献信息。本地 no-LoRA/深度变体只回答较窄的适配/容量问题，不会自动回答同样的移除/替换问题，也不能分离文本使用。部分完成是操作状态；解释科学趋势需各报告变体分数、重复运行波动及匹配协议。文献提供实验问题，不提供本地未完成阶梯的结果。
 向导师简答。 文献支持移除/替换对照，未完成阶梯尚未回答这些因果问题 [13]。
 论文位置。 Tan et al. [13], §3.2 Proposed Ablations, w/o LLM / LLM2Attn / LLM2Trsf.
 证据。 Owner snapshot; ablation design table; tests_archive/test_miflu_ablations.py
 10 解释与发表计划
-单一全国序列与单次时序划分不能证明区域或前瞻效用。峰值匹配可使用未来观测定义事件，只能作为回顾性评测工具。合成日期标签必须与 CDC 日历核实映射后才能作逐季判断。参数导出缺少 MIFlu 与编码器。60/60 的消融状态来自用户报告，而非实时集群检查。现代数值基础模型、区域结果、滚动原点及经过验证的不确定性仍缺失。
+单一全国序列与单次时序划分不能证明区域或前瞻效用。峰值匹配可使用未来观测定义事件，只能作为回顾性评测工具。合成日期标签必须与 CDC 日历核实映射后才能作逐季判断。参数导出缺少 MIFlu 与编码器。所附队列日志记录消融 60/60 为 DONE，但尚未独立核实逐变体聚合趋势。现代数值基础模型、区域结果、滚动原点及经过验证的不确定性仍缺失。
 后续验证的决策规则：在查看新测试期之前确定 MSE 预算 B、允许峰值失败率 q 与决策代价。在验证季同时满足 B 与 q 的模型中最小化期望决策代价，再以参数量打破平局。对升级响应 / 等待决策，误报代价为 c_FP，漏报代价为 c_FN，正确行动代价为零；仅当经过验证的高峰概率超过 c_FP/(c_FP+c_FN) 时升级。代价、B、q 尚未征询或验证，因此没有模型被认证可部署。NLinear 是低成本峰高验证候选，MIFlu 仍为观测 MSE 最优。
 建议 O1：保留实证评估贡献，先补齐证据，再考虑新增机制。当前草稿面向 IEEE JBHI 的健康预测主题，但尚未达到投稿状态。在学校截止日前，滚动原点、区域验证、更强基线与独立代码来源比再加一个架构更重要。
 Q24 除了复现，本项目增加了什么，为什么默认仍选 O1？
@@ -224,11 +229,13 @@
 论文位置。 Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract.
 证据。 audit/INNOVATION_DECISION.md; audit/LITERATURE_REVIEW.md; sources.json [1]
 11 可复现性与待核实项
-在仓库根目录运行 python scripts/verify_snapshot.py --raw-smoke 及 python -m pytest tests/test_snapshot_audit.py -q。审计重算主要聚合值、峰值标记、相关系数、回归、Holm 校正和一个原始预测 MSE。七个新增 CPU 审计测试已通过，它们与归档模型测试分开。修正 ZIP 已提供 tests_archive/，但历史目录布局及模型依赖缺失导致收集失败。本次不主张归档测试通过数或可靠总数。本次未重跑训练、未查询实时 HPC，亦未运行上游代码。原 CSV 保持不变，Holm 修正另行导出。
+本次独立核查证实两个 ZIP 哈希、所有 manifest 列出的文件哈希、核心 160/160 产物完整性及全国快照 117/1120。对 237 个七通道 NPZ 单元及 40 个 MIFlu CSV 单元的 ILITOTAL 指标，按各自所存评分面板重算一致。原样 validator 因一个未列入清单的临时预测文件报 FAIL；在解压审阅副本隔离该文件后为 PASS。原上传及 manifest 未改写；完整性 PASS 不能替代科学验证。
+待完成的是逐项交代全国所有计划单元，补齐 MIFlu 七通道导出，统一两个评分面板，聚合峰值与消融，并使用处理依赖的统计。区域、滚动原点、数值时序基础模型控制、真实 CDC 日历与数据版本、完整资源测量及方法来源，即使全国完成后仍须核实。现有科学表保持经审计的历史结果。
+在仓库根目录运行 python scripts/verify_snapshot.py --raw-smoke 及 python -m pytest tests/test_snapshot_audit.py -q。审计重算主要聚合值、峰值标记、相关系数、回归、Holm 校正和一个原始预测 MSE。七个新增 CPU 审计测试已通过，它们与归档模型测试分开。修正 ZIP 已提供 tests_archive/，但历史目录布局及模型依赖缺失导致收集失败。本次不主张归档测试通过数或可靠总数。回传包现提供 GPU 执行和调度记录，包括核心单元产物完整性 160/160。本次审阅未重跑训练、连接实时 HPC 或执行固定版本上游代码；全国矩阵的分时计数及限制见 v7 增补。原 CSV 保持不变，Holm 修正另行导出。
 硬件来源表共 204 行，其中包括被排除的 DLinear，但没有 MIFlu 与冻结编码器；与正式名单重叠的是 192 单元。因此不能证明逐单元硬件来源已齐。原 reproduce_all.py 面向历史路径，并非此次核实的快速入口。
-待核实项：固定上游版本的检查点、加载器与学习率；归档测试执行与 no-text 运行测试；十种子原始复现日志；模型版本与许可；实时消融及区域状态；真实 CDC 日历映射；当前 JBHI 作者限制、JCR 记录及下一轮会议日期。每项都需原始证据，不能靠文字断言补足。
+待核实项：固定上游版本的检查点、加载器与学习率；三项已回传通过的 CPU no-text 检查以外的归档测试执行；十种子原始复现日志；模型版本与许可；消融聚合来源与更新的区域状态；真实 CDC 日历映射；当前 JBHI 作者限制、JCR 记录及下一轮会议日期。每项都需原始证据，不能靠文字断言补足。
 Q25 导师现在能复核什么，还有什么未执行？
-直接回答与本地证据。 文档中的 CPU 命令可以重算 CSV 主要聚合、正确 Holm 和一个原始预测单元的 MSE；七个新增 CPU 审计检查已通过。历史归档已经提供，但收集失败，不能把其中模型断言算作通过。完整 GPU 训练、全运行原始重评分、实时 HPC、固定上游身份和 no-text 运行测试仍未执行或未核实，硬件来源也未完整覆盖正式单元。文档排版完善不能补足这些证据。精确后续命令见 audit/EXECUTION_STATUS.md 与 audit/NO_TEXT_VERIFICATION.md。
+直接回答与本地证据。 文档中的 CPU 命令可以重算 CSV 主要聚合、正确 Holm 和一个原始预测单元的 MSE；七个新增 CPU 审计检查已通过。整个历史归档的收集仍失败。所附 JUnit 记录三项固定权重 CPU no-text 断言通过且零跳过，核心产物满足 160/160 完整性检查；全国 1120 矩阵仍在进行。完整共同面板评分及固定上游身份仍待核实，本次未重跑 GPU 训练或连接实时 HPC，硬件来源也未完整覆盖正式单元。文档排版完善不能补足这些证据。精确后续命令见 audit/EXECUTION_STATUS.md 与 audit/NO_TEXT_VERIFICATION.md。
 文献依据与选择理由。 Kapoor 与 Narayanan 要求明确报告论证，而非把代码可用等同于结果有效 [22]。这里应分开文档重建、CSV 算术、原始预测重评分与模型重训。导师可先运行 CSV 审计；完整包还支持一个原始单元 smoke 检查。模型文本不变性需在固定环境实际执行三项指定断言，且不能跳过。有用的交付是可追溯证据链、精确命令与状态，某一层通过不能认证其他所有层。
 向导师简答。 我区分重算结果与静态检查，并为每层提供命令和状态 [22]。
 论文位置。 Kapoor and Narayanan [22], model info sheets; EXECUTION_STATUS.md and NO_TEXT_VERIFICATION.md.
```

