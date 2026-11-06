# Ten assessor questions and concise answers

English answers are for live follow-up. Chinese lines are preparation aids. Internal-report Q01–Q25 supply the longer explanations and evidence locators.

## 1. Is this just a reproduction, or are the four axes novel?

The contribution is a specific influenza protocol audit and a broader four-axis evaluation. Earlier work already examines simple baselines and LLM-removal controls. We have not verified that the original MIFlu paper contains only the first two axes, and we do not claim first-ever novelty.

**Paper basis and connection.** Simple-linear and LLM-removal critiques predate this project [4, 13]; Qiu et al.’s preprint reports conditional gains in larger cross-dataset settings [14]. Our narrower contribution connects audited influenza accuracy, peak endpoints, a cost subset and corrected inference. O1 checks persistence across origins/regions; Tashman motivates rolling-origin evaluation [23]. O2 adds validation-fitted height adjustment only if suitable prediction exports exist. A new mechanism cannot replace those checks or establish a universal verdict about LLM forecasting.

**Read:** Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract.

中文提示：重点是更全面、可审计的再评估，不能把增加图表数量等同方法创新。 详细说明：内部报告 Q24。

## 2. Why ten seeds for reproduction and three for the benchmark?

They are separate protocols: the supplied reproduction table uses ten repetitions and the broader benchmark three. Three keeps the historical retained matrix at 336 cells and reflects its compute budget. A new common ten-seed expansion is underway, with completion and scoring limitations stated separately.

**Paper basis and connection.** The original three-seed citation is incorrect. PatchTST uses fixed-seed main results plus a five-seed supervised robustness check [3, App. A.6.1]; iTransformer reports five-run standard deviations [5, App. A.2, Table 5]. Neither passage establishes three seeds as their shared convention. Our choice is a compute compromise. Bouthillier et al. distinguish repeated-run precision from broader benchmark variation [19]. Extra seeds can improve the former; extra seasons/origins address different uncertainty. Ten reproduction repetitions do not make the separate three-seed benchmark equally precise.

**Read:** PatchTST [3], Appendix A.6.1; iTransformer [5], Appendix A.2 and Table 5; Bouthillier et al. [19], Appendix C.3.

中文提示：三种子属于旧基准；新的共同十种子矩阵仍在进行。 详细说明：内部报告 Q04。

## 3. Why does MIFlu have both 1.4995 and 1.5574?

The first is the ten-seed reproduction mean, compared with the paper table. The second is the three-seed benchmark mean, compared with other implementations. They aggregate different run sets, so their difference cannot be attributed to a single controlled change.

**Paper basis and connection.** Bouthillier et al. show that benchmark estimates depend on the sampled learning pipeline [19]. A mean is therefore an estimate over specified runs, not an immutable property of a model name. Our two MIFlu estimates summarise separate seed sets and serve different comparisons. The gap could combine seed variability with configuration differences; it does not isolate one cause. Explain each table’s run definition first, then request matched run-level configurations if the cause of the difference matters.

**Read:** Bouthillier et al. [19], §§2–3, benchmark estimators and sources of variation.

中文提示：先指出两张表回答不同问题，再解释种子集合。 详细说明：内部报告 Q07。

## 4. MIFlu also passes 4/16. What is the finding?

Both pass four aggregated cells, but at different horizon/lead positions. NLinear has lower mean peak-height error while MIFlu has lower mean timing error and MSE. This is a trade-off, and the denominator is not 16 independent seasons.

**Paper basis and connection.** The separate literature endpoints motivate inspecting timing and height before reducing them to a pass count [2]. Our equal four-pass counts hide different lead/horizon locations and distances from the thresholds. An application emphasising one-week-ahead height could favour a different trade-off from an application emphasising timing. That conditional interpretation comes from our table, not from a literature recommendation of NLinear. A binary pass is a coarse summary of continuous errors.

**Read:** Kramer and Shaman [2], Forecast accuracy and comparison, separate timing/intensity tolerances.

中文提示：不要把 NLinear 说成全面优于 MIFlu。 详细说明：内部报告 Q12–Q13。

## 5. Does the changed peak ranking demonstrate decoupling?

The leading-three MSE and PIE orders differ, with ordering inverted at both ends. Overall MSE–PIE correlation is +0.736 and MSE–pass-count correlation −0.429, both in expected accuracy directions. This supports a local objective mismatch, not statistical independence.

**Paper basis and connection.** Zeng et al. describe NLinear’s last-value subtraction, linear map and addition back [4]. This gives a testable hypothesis about level handling, not a proven explanation for our peaks. The ranking mismatch itself follows a simpler distinction: MSE aggregates many points and seven channels, whereas PIE concentrates on detected ILITOTAL peak height [21 gives the error-measure context]. A model can improve many non-peak points yet worsen this endpoint. Controlled variants and peak/residual diagnostics are needed to attribute the observed trade-off to architecture.

**Read:** Zeng et al. [4], §4 NLinear; Hyndman and Koehler [21], §2.1.

中文提示：局部顺序变化与整体相关可以同时存在。 详细说明：内部报告 Q14。

## 6. Why is MIFlu absent from the Pareto graph?

The efficiency export has parameter counts for 11 arms, excluding MIFlu and the encoders. The graph therefore shows that subset’s frontier. The 211× ratio is parameter count, not a measured runtime or energy ratio.

**Paper basis and connection.** iTransformer evaluates error alongside speed and memory [5, App. D], a precedent for considering performance with cost. Our cost axis is narrower: exported parameters. The two local frontier members follow from pairwise dominance in the eleven-model subset, not a paper’s recommendation of a universal winner. A Pareto graph removes dominated choices; the remaining choices still need a budget or acceptable-error preference. Missing MIFlu cost data prevents calling it the frontier of all 28 models.

**Read:** iTransformer [5], Appendix D Model Efficiency; local BENCH_EFFICIENCY.csv.

中文提示：缺失参数不是零，也不能把 MIFlu 说成无参数。 详细说明：内部报告 Q15–Q17。

## 7. Does p≈0.1172 mean NLinear and PatchTST are equivalent?

No. PatchTST retains 11.2% lower observed MSE and wins 10/12 matched cells. Proper Holm rejects 0/136 pairs at this exact-test resolution. Equivalence would require a prespecified acceptable margin and an appropriate design.

**Paper basis and connection.** Lakens distinguishes a nonsignificant difference test from equivalence with prespecified meaningful bounds [25]. Thus p = 0.1172 does not answer whether NLinear’s observed extra error is acceptable for an application. Define that acceptable difference first, then use an uncertainty design respecting time/season dependence. Choosing a generous bound after seeing this table would not be convincing confirmation. Until then, observed error reduction, parameter ratio and inferential uncertainty should be reported together; the extra parameters cannot be dismissed as buying only noise.

**Read:** Lakens [25], Introduction and Testing for Equivalence.

中文提示：未拒绝不等于等价，更不能直接说增益是噪声。 详细说明：内部报告 Q18–Q20。

## 8. Do frozen encoders prove LLM forecasting is ineffective?

The result concerns frozen language features with a trained linear readout. It does not cover generation, prompting, fine-tuning or numerical time-series foundation models. Possible causes are not separated by this comparison.

**Paper basis and connection.** Time-LLM freezes its LLM but adds learned reprogramming and a prompt prefix [6]. Thus “frozen” alone does not define the same experiment as our feature/linear-readout pipeline. Chronos instead learns forecasting from numerical sequences [9]. These method differences justify keeping our negative finding narrow. To isolate a readout bottleneck, vary the readout/alignment while holding the encoder fixed; to isolate pretraining, compare matched pretrained and random backbones. Our eleven-arm result does not make those controlled separations.

**Read:** Time-LLM [6], author abstract; Chronos [9], §3.

中文提示：只评价实际测过的流程，不能扩大为整个 LLM 家族失败。 详细说明：内部报告 Q21。

## 9. Why might text have no effect, and did the tests pass?

In the inspected default path, time positions precede text, causal attention blocks later information and the head reads time positions. The supplied JUnit and CPU log record three named fixed-weight assertions passed with zero skips. They were not rerun in this review. Other fusion paths and independent training trajectories need separate checks.

**Paper basis and connection.** The Transformer paper explains masking that prevents attention to subsequent positions [24, §3.1]. With the inspected ordering, time positions cannot acquire later text through these layers, and the head reads time positions. This is a structural argument about a fixed forward path, not certification of repository runtime or bitwise equality. The three archived assertions must control weights, inputs and evaluation randomness when comparing changed text and matched full/no-text outputs. The supplied JUnit now records three CPU assertions passed with zero skips; they were not rerun in this review. Independent training can consume randomness differently and requires its own test.

**Read:** Vaswani et al. [24], §3.1 Decoder; local ForecastingLLM.forward and archived assertions.

中文提示：区分执行端三项通过与本次日志核查；不扩大到训练轨迹。 详细说明：内部报告 Q22–Q23。

## 10. What would you do with one more month or one more GPU?

I would first harmonise cropped and full-window scoring and recover complete MIFlu exports, then prioritise rolling origins, regions and modern numerical controls under O1. A spare GPU does not fix a flawed inference design. Optional O2 needs auditable validation predictions before fitting. Its additional wall time or GPU budget should follow a pilot, not an invented estimate.

**Paper basis and connection.** Simple-linear and LLM-removal critiques predate this project [4, 13]; Qiu et al.’s preprint reports conditional gains in larger cross-dataset settings [14]. Our narrower contribution connects audited influenza accuracy, peak endpoints, a cost subset and corrected inference. O1 checks persistence across origins/regions; Tashman motivates rolling-origin evaluation [23]. O2 adds validation-fitted height adjustment only if suitable prediction exports exist. A new mechanism cannot replace those checks or establish a universal verdict about LLM forecasting.

**Read:** Zeng et al. [4], §4; Tan et al. [13], §3.2; Qiu et al. [14], abstract and §§3–5 (preprint); Tashman [23], publisher-indexed abstract.

中文提示：先补最影响结论的证据，再决定是否投入新机制。 详细说明：内部报告 Q24–Q25。

## References

[2] Sarah C. Kramer and Jeffrey Shaman, “Development and validation of influenza forecasting for 64 temperate and tropical countries,” PLOS Computational Biology 15(2), e1006742, 2019. https://doi.org/10.1371/journal.pcbi.1006742

[3] Yuqi Nie, Nam H. Nguyen, Phanwadee Sinthong and Jayant Kalagnanam, “A Time Series is Worth 64 Words: Long-term Forecasting with Transformers,” ICLR, 2023. https://arxiv.org/abs/2211.14730

[4] Ailing Zeng, Muxi Chen, Lei Zhang and Qiang Xu, “Are Transformers Effective for Time Series Forecasting?,” AAAI (preprint record opened), 2023. https://arxiv.org/abs/2205.13504

[5] Yong Liu et al., “iTransformer: Inverted Transformers Are Effective for Time Series Forecasting,” ICLR (preprint record opened), 2024. https://arxiv.org/abs/2310.06625

[6] Ming Jin et al., “Time-LLM: Time Series Forecasting by Reprogramming Large Language Models,” ICLR, 2024. https://arxiv.org/abs/2310.01728

[9] Abdul Fatir Ansari et al., “Chronos: Learning the Language of Time Series,” Transactions on Machine Learning Research, 2024. https://arxiv.org/abs/2403.07815

[13] Mingtian Tan, Mike A. Merrill, Vinayak Gupta, Tim Althoff and Thomas Hartvigsen, “Are Language Models Actually Useful for Time Series Forecasting?,” NeurIPS 37, 2024. https://arxiv.org/abs/2406.16964

[14] Xin Qiu et al., “Rethinking the Role of LLMs in Time Series Forecasting,” arXiv:2602.14744 v1, preprint, 2026. https://arxiv.org/abs/2602.14744

[19] Xavier Bouthillier et al., “Accounting for Variance in Machine Learning Benchmarks,” Proceedings of Machine Learning and Systems 3, 2021. https://proceedings.mlsys.org/paper_files/paper/2021/file/0184b0cd3cfb185989f858a1d9f5c1eb-Paper.pdf

[21] Rob J. Hyndman and Anne B. Koehler, “Another look at measures of forecast accuracy,” International Journal of Forecasting 22(4), 679–688, 2006. https://doi.org/10.1016/j.ijforecast.2006.03.001

[23] Leonard J. Tashman, “Out-of-sample tests of forecasting accuracy: an analysis and review,” International Journal of Forecasting 16(4), 437–450, 2000. https://doi.org/10.1016/S0169-2070(00)00065-0

[24] Ashish Vaswani et al., “Attention Is All You Need,” Advances in Neural Information Processing Systems 30, 2017. https://papers.neurips.cc/paper/7181-attention-is-all-you-need.pdf

[25] Daniël Lakens, “Equivalence Tests: A Practical Primer for t Tests, Correlations, and Meta-Analyses,” Social Psychological and Personality Science 8(4), 355–362, 2017. https://doi.org/10.1177/1948550617697177
