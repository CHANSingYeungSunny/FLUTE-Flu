# 局限性（稿件可用，中文）

1. **基线 seed 数量。** 冻结 MIFlu 基线仅提供 3 个 seed，因此每 horizon 的配对推断有效
   样本量为 3。不声称广泛的统计优越性；Holm 校正后仅一项比较显著。
2. **不可用候选族。** TimesNet、TimeMixer/ModernTCN、TF-IDF+SVD、fastText、BERT/MiniLM、
   zero-text 与 shuffled-text 负对照、Time-LLM 风格 reprogramming、CALF/TimeCMA 风格对齐，
   以及 Chronos/TimesFM/Moirai 均不可用或未完成，结论不推广至这些族。
3. **历史仓库完整性。** 某一个指标脚本在事故前的字节同一性无法确立；现行规范脚本系前瞻性
   采纳，并以事故前可信预测文件做回归校验。这是可复现性限制，不是科学结果。
4. **源码版本修复史。** 经历 v2.1–v2.10 共十次实现版本修订，均未改变科学协议、切分、
   scaler、prompt 统计、指标、阈值或早停策略。
5. **登录节点事故（2026-09-16）。** 一次性 Test 最初以 `nohup` 在登录节点执行（违规），
   进入 D 状态并阻塞新建 SSH 会话。该进程被终止后，剩余不可变单元通过合规的 `sbatch`
   作业完成，复用同一收据、同一清单与同一评估 ID。此事作为**流程**事故在可复现性材料中
   披露，未改变任何科学输入、checkpoint 或指标。
6. **EvoForecast。** 可选的 AlphaEvolve 启发分支未尝试，不得描述为已完成。
7. **COVID / pre-COVID 分段。** 未预注册，不作为验证性分析呈现。
