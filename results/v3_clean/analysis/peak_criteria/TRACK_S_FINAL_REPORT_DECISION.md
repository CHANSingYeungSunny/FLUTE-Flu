# Track S 最终报告决策（Final Report Decision）

## 判定（verdict）

```
TRACK_S_IS_SENSITIVITY_AND_SUPPLEMENTARY   (停止准则敏感性补充实验)
+ TRACK_S_IS_STALE_LABEL                    (存储 S0-S5 基础设施标签，无关)
```

## 最终报告处理

1. **Track S（停止准则早停补充实验）不作为一个独立的主要结果轨道呈现。**
2. 按规范的首选结构，主报告仅保留三条主轨道：
   - **Track H**：历史 1025 行实验（旧，被取代）。
   - **Track R**：作者 966 行论文复现。
   - **Track C**：作者 966 行严格 Test 冠军赛（冻结，权威）。
3. F1、R1-C、Track S 移至**简短的补充方法 / 限制**章节：
   - R1-C → 论文复现章节（§3）已覆盖；
   - Track S（早停敏感性）→ 在"限制 / 补充方法"中以 1–2 段陈述：
     "受控补充实验以 patience=5 早停重跑同一 MIFlu 配置，12 格中 11 格与冠军结果数值相同，
     1 格因局部验证谷回滚略差；两停止规则结果等价，不影响冠军排名。"
4. 存储 "S-track"（S0–S5）标签**不出现在最终报告**。

## 理由

- Track S 与 Track C 使用相同数据、模型、评分；仅停止规则不同，且结论为"不影响排名"。
- 它不提供独立的科学结论，故无资格作为第四主轨道。
- 把补充实验塞进主结论会混淆读者，违反"主报告聚焦冠军赛"的要求。

## 关联文件

- `TRACK_S_IDENTITY_AUDIT.md`（身份审计）
- `TRACK_S_REFERENCE_MAP.csv`（出现位置映射）
- `S1_EARLYSTOP_PROTOCOL.md`（补充实验完整记录）
- `S1ES_RESULTS_PER_FIT.csv` / `S1ES_VS_TRACK_C.csv`（实测数据）
