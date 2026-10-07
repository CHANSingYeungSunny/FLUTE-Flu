# 方法（稿件可用，中文）

## 数据与切分
国家级 ILI 序列。所有方法共享同一固定时序切分（train/validation/test）。scaler 与 prompt
统计仅在训练段拟合。Test 从不参与 early stopping、超参选择、模型选择或阈值制定。

## 协议
L ∈ {24, 36, 48, 60} 四个 horizon 独立训练与评分，预测绝不跨 lead time 合并。冠军臂使用
10 个 seed（42–51）；冻结 MIFlu 基线提供 3 个 seed（42–44）。

## 两层标准
第一层（何时停止训练）：仅看 validation MSE，patience=7，恢复最低 validation MSE 的
checkpoint。第二层（训练后精度验收）：PTE 与 PIE，唯一判据为文献标准 PTE ≤ 1 周且
PIE ≤ 25%。未实现也未报告任何项目自定的验收阈值。

## 冠军选择与 Test 隔离
选择仅基于 validation，在预注册的 Stage-F 队列（160 个唯一单元）上进行。冠军在任何
Test 访问之前冻结。单次授权收据只允许一次 Test 评估，其 52 单元清单不可变且在访问前创建。
Test 结果从未影响选择、重训或阈值。

## 统计
每个 horizon 报均值、标准差与百分位 bootstrap 95% CI（10,000 次重抽样，固定随机种子）。
配对比较使用相同的 (horizon, seed) 配对；效应量为 Cohen's dz；对全部配对比较族做 Holm
校正。若校正后 p 值不支持，则表述为「observed best」。
