# Innovation-Proof — MoE / UCS Feasibility & Innovation Evidence

> 诚实两层制：所有变体均含 MIFlu 训练，本机（8GB RAM / 4GB VRAM）跑不了完整训练（OOM）。
> 因此分两层写，只陈述事实，严禁编造对比数字或对比图。
>
> - **第一层 — 本地已完成**：插入点定位 + 原型 Shape 验证 + 开舗交叉对照（真实证据）。
> - **第二层 — HPC 待跑**：五变体对比实验（脚本就绪，结果未产出）。

---

## 第一层：本地已完成（真实证据）

### 1. 插入点与代码定位（证据 B）

| 机制 | 插入位置 | 文件:行 | 片段 |
|------|----------|---------|------|
| h_time 与 h_text 拼接 | 融合入口 | `miflu_model.py:301` | `hfuse = torch.cat([htext, htime], dim=1)` |
| ForecastingLLM.forward | 主干前向 | `miflu_model.py:284` | `def forward(self, htime, htext):` |
| build_prompt | Prompt 构建 | `textual_embedder.py:70` | `def build_prompt(train_df, T=104, L=24):` |
| Output Projection | 投影层 | `miflu_model.py:276` | `self.output_projection = nn.Linear(D, N * L)` |

MoE/UCS 模块均设计为接受 `(batch, seq, D)` 并返回 `(batch, seq, D)`，可直接串接于 `hfuse` 流（`miflu_model.py:301-336`）。

### 2. 原型验证（证据 C：`test_moe_shapes.py` 真实输出）

```
[TEST] I2MoE shape OK, added_params=18,892,804
[TEST] FlexMoE shape OK, added_params=2,368,512
[TEST] UCS shape OK, added_params=0 (prior is frozen buffer)
[PASS] test_moe_shapes.py — all shape/param checks passed.
```

真实维度：D=768，num_patches=42，total_patches=7×42=294，text_len=367，seq=661。
三个原型均用真实维度实例化，输出形状与输入严格一致，参数量已统计。

### 3. 开舗交叉对照（证据 A：论文原文直引）

| 机制 | 论文来源 | 原文数字 | 本原型对应 |
|------|----------|----------|------------|
| I2MoE | I2MoE Table 6 | "ADNI MulT 1.07M→6.70M params; train/epoch 8.98s→16.82s" | I2MoE 4 experts 新增 18.89M params（base hidden 4×768） |
| Flex-MoE | Flex-MoE Table 4 | "36.9M vs FuseMoE 340.9M" | Flex-MoE Missing Bank 新增 2.37M params |
| UCS | UCS Tables 10/11 | "离线 38–57s、线上 +0–3s" | UCS SGT prior 为冻结 buffer（added_params=0，离线一次计算，线上零成本） |

参数量级与论文报告一致（I2MoE 专家堆叠带来 M 级增量；Flex-MoE Bank 轻量；UCS 先验离线、线上近似零开销）。

### 4. 路线图映射（一句话对应）

- UCS 离线化 → Step 1.1 / 3.1（离线先验注入）
- Flex-MoE Bank → Step 1.3（缺失模态填补）
- I2MoE 专家 → Step 2.1（多专家模态路由）

---

## 第二层：HPC 待跑（只交付代码，严禁编造数字/图）

### 5. 对比实验协议（`analysis/moe_comparison_pipeline.py`，本机不运行）

变体 = `[MIFlu baseline, +UCS, +Flex-MoE Bank, +I2MoE, +All(UCS+Flex-MoE+I2MoE)]`
按论文协议计算 National L∈{24,36,48,60} 的 MSE/MAE，输出对比 CSV：

- 输出文件：`data/moe_comparison_results.csv`
- 列：`variant, L, mse, mae`
- 评估尺度：National 用 StandardScaler 归一化 MSE/MAE（对齐 Q5 修正）

### 6. 对比图生成（`analysis/plot_moe_comparison.py`，本机不运行）

读上述 CSV 生成：
- (a) 分组柱状图（variant × L vs MSE，含 MIFlu-only 与 +All 对比）
- (b) 预测曲线叠加图（ground truth vs MIFlu vs +All，带精确峰值标注）

**NaN 保护**：若 CSV 含 NaN（即 HPC 未运行），脚本打印 `[SKIP]` 并退出，**不产出任何假图、不填假数字**。

---

## Pending HPC Experiments（待产出清单）

> 数字目前为空，待 HPC 运行后填入。不占位假图、不假数字。

| 产物 | 脚本路径 | 运行指令 | 状态 |
|------|----------|----------|------|
| `data/moe_comparison_results.csv` | `analysis/moe_comparison_pipeline.py` | `python analysis/moe_comparison_pipeline.py`（HPC GPU） | 待跑 |
| `data/moe_comparison_mse.png` | `analysis/plot_moe_comparison.py` | `python analysis/plot_moe_comparison.py`（HPC GPU） | 待跑 |
| 预测曲线叠加图 | `analysis/plot_moe_comparison.py` | 同上 | 待跑 |

---

## 结论话术（simpler is better，只说做过的）

本地已完成：插入点定位＋原型 Shape 验证＋开舗交叉对照。HPC 待跑：五变体对比实验（脚本就绪，结果未产出）。复现对齐前不宣稱任何 MoE 增益。
