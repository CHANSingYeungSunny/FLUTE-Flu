# Restored explanatory questions and answers

The earlier rewrite over-condensed the internal report. This revision restores the teaching function beside the relevant tables, in English and Chinese. Scientific corrections remain in force; old unsupported causal/source claims are not restored as facts.

| Original paragraph (same EN/ZH index) | Original explanation topic | Current location | Correction retained |
|---|---|---|---|
| 20 | Why 676/97/193 | §1 Q01 | Tan et al. §3.3 supports Illness 70/10/20; iTransformer A.1 supports chronology. Exact row counts and pinned upstream identity remain separate local questions. |
| 21 | Cropped windows | §1 Q02 | Explain the full-batch rule; do not reassert an independently unverified tail-difficulty ratio. |
| 28 | Three versus ten seeds | §2 Q04 | Named-paper rationale restored and corrected: PatchTST A.6.1 / iTransformer A.2 report five-seed robustness; three remains a project compute choice. |
| 31 | Local versus author implementation differences | §2 Q05 | Local validation/all-channel behaviour is inspected; upstream defect attribution and exactly-two-cause explanation remain unverified. |
| 34 | Seven-variable loss versus ILITOTAL peaks | §2 Q06 | Restore the explanation of dimensionless aggregate loss and channel-specific inverse scaling. |
| 85 | Why the paired table shows other models | §7 Q18–Q20 | Restore row-selection explanation, complete family and correct Holm/non-equivalence meaning. |

Q03, Q07–Q17 and Q21–Q25 also restore or expand the surrounding explanatory material: scaling, two MIFlu estimates, MSE/MAE directions, oracle/plot provenance, roster/subset differences, peak-cell meaning, Pareto interpretation, effect/inference limits, frozen encoders, no-text and O1/O2. The internal report retains twelve continuous numbered sections. Questions are embedded, not moved into a separate appendix.

## Complete current question index

- Q01, §1: Why use 676 training, 97 validation and 193 test rows? / 为什么采用 676 行训练、97 行验证、193 行测试？
- Q02, §1: Why score 160 windows when 170 are available at L24? / L24 明明有 170 个窗口，为什么只评 160 个？
- Q03, §1: Why fit scaling on training data only? / 为什么标准化参数只能从训练段计算？
- Q04, §2: Why ten reproduction seeds but three benchmark seeds? / 为什么复现用十个种子，基准却用三个种子？
- Q05, §2: Which implementation differences are established? / 哪些实现差异已经核实，哪些仍只是待核实的说法？
- Q06, §2: Why use seven-variable MSE but ILITOTAL peak errors? / 为什么 MSE 用七变量，而峰值误差只用 ILITOTAL？
- Q07, §3: Why is MIFlu 1.4995 here but 1.5574 in the benchmark? / 为什么这里的 MIFlu 是 1.4995，基准表却是 1.5574？
- Q08, §3: Why do MSE and MAE give different sign patterns? / 为什么 MSE 与 MAE 的逐跨度方向不完全一致？
- Q09, §3: Do the seed oracle and plots prove a complete reproduction? / 种子 oracle 和预测曲线能证明已完整复现吗？
- Q10, §4: What do the 28 models and different subsets mean? / 28 个模型与不同分析子集各指什么？
- Q11, §4: Does the lowest MSE make MIFlu the deployment winner? / MIFlu 的 MSE 最低，是否就应直接选它部署？
- Q12, §5: Why do MIFlu and NLinear both pass 4/16? / 为什么 MIFlu 和 NLinear 都通过 4/16，却仍有不同结论？
- Q13, §5: Does 4/16 mean a 25% chance of a correct epidemic forecast? / 4/16 是否表示预测流行季成功的概率为 25%？
- Q14, §5: Why can peak rankings differ without proving decoupling? / 为什么峰值排名会改变，却不能说已经证明脱钩？
- Q15, §6: How should I explain the Pareto graph? / 我该怎样向导师解释 Pareto 图？
- Q16, §6: Does 211 times more parameters mean 211 times slower? / 参数多 211 倍，是否就慢 211 倍？
- Q17, §6: What does R squared of 0.0223 actually mean? / R² = 0.0223 实际说明什么？
- Q18, §7: Why does the paired table contain seemingly unrelated model pairs? / 为什么配对检验表里会出现看起来不相关的模型对？
- Q19, §7: Why do 128 raw significant pairs become zero after Holm? / 为什么未校正有 128 对显著，Holm 后却是零？
- Q20, §7: Does p = 0.1172 show that NLinear and PatchTST are equivalent? / p = 0.1172 是否说明 NLinear 与 PatchTST 等价？
- Q21, §8: What can the frozen-encoder negative result explain? / 冻结编码器的负面结果能解释到哪一步？
- Q22, §9: Why might no-text give identical outputs in the default path? / 为什么默认路径下去掉文本可能得到完全相同的输出？
- Q23, §9: What does 27/60 ablation completion allow us to say? / 消融完成 27/60，究竟可以说什么？
- Q24, §10: What is added beyond reproduction, and why keep O1? / 除了复现，本项目增加了什么，为什么默认仍选 O1？
- Q25, §11: What can a supervisor reproduce now, and what remains unexecuted? / 导师现在能复核什么，还有什么未执行？


## Revision 4 paper-backed explanations

All Q01–Q25 now connect a direct local answer with a named-paper argument, a specific reading location and a short supervisor response. QA_CITATION_MAP.md/.json records every link. The complete supervisor guide mirrors both languages, and the external notes/live Q&A carry matching paper support. Seven methodological references extend the internal list to 25. School and manuscript report pairs, the owner-edited PPTX/PDF and the planned English speech remain unchanged.

The original split rationale is strengthened by Tan et al. §3.3 (Illness 70/10/20) and iTransformer Appendix A.1 (chronological separation). The original three-seed citation is corrected: PatchTST A.6.1 and iTransformer A.2/Table 5 report five-seed robustness. PatchTST A.6.2 also reports ILI sensitivity to model settings. These passages explain why a three-seed compute compromise and a cross-model parameter regression do not settle robustness or tuning importance.

The added methods explain leakage, measurement scale, Holm, equivalence, causal masking and forecast evaluation. Tashman is used only at publisher-indexed abstract depth; direct publisher access was blocked. No unseen upstream defect or unexecuted model outcome is promoted to fact. This is a literature/explanation revision, with no new training or HPC result.

