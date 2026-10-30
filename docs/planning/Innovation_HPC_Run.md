# MIFlu Innovation (MoE / UCS) — HPC 运行说明

> 配套脚本：`analysis/moe_comparison_pipeline.py` + `analysis/plot_moe_comparison.py`
> 适用环境：**CityUHK HPC `burgundy` 集群**（GPU 节点，通过 SSH 提交）
> 运行方式：先训练对比（`moe_comparison_pipeline.py`）→ 再出图（`plot_moe_comparison.py`）

本文档面向使用者本人，说明 Innovation 模块（MoE/UCS 五变体对比实验）的数据来源、运行流程与最终产出，便于在 HPC 上一次跑通并核对需上传的文件。

---

## 一、输入 (Input)

### 1.1 数据

| 项目 | 说明 |
|------|------|
| 文件 | `data/national_illness_raw.csv` |
| 时间跨度 | 2002–2021（美国全国 ILINet 监测数据） |
| 样本量 | 共 **1025 周**，epiweek `200201`–`202152` |
| 变量 | 7 通道：`% WEIGHTED ILI`、`% UNWEIGHTED ILI`、`AGE 0-4`、`AGE 5-24`、`ILITOTAL`、`NUM. OF PROVIDERS`、`OT` |
| 任务 | National 长程预测，horizon L ∈ {24, 36, 48, 60} |

### 1.2 模型与扩展依赖

- **基础 MIFlu**：`miflu_model.py`（GPT2 + LoRA）、`textual_embedder.py`（冻结 GPT2 文本编码）。
- **MoE/UCS 扩展**：`moe_extension.py`（I2MoE 4 专家 / Flex-MoE Missing Bank / UCS SGT 先验，均为真实维度 D=768、num_patches=42 原型）。
- **预训练权重**：运行时由 `transformers` 自动下载 GPT-2（`gpt2`）。**burgundy 节点若不能直连 Hugging Face，需提前把权重放到 `~/.cache/huggingface` 再提交作业**（见第四节注意事项）。
- **运行依赖**：`torch`、`transformers`、`numpy`、`pandas`、`scipy`、`matplotlib`、`statsmodels`（仅本地因果脚本需要，HPC 对比脚本本身不依赖 statsmodels）。

### 1.3 五变体定义

| 变体 | 说明 |
|------|------|
| `MIFlu` | 基线（无 MoE/UCS） |
| `+UCS` | 注入 UCS SGT 离线先验 |
| `+Flex-MoE` | 加入 Flex-MoE Missing Bank |
| `+I2MoE` | 加入 I2MoE 4 专家路由 |
| `+All` | UCS + Flex-MoE + I2MoE 全叠加 |

---

## 二、过程 (Process / Methodology)

### 2.1 训练对比流程（`analysis/moe_comparison_pipeline.py`）

对每个变体、每个 L ∈ {24,36,48,60}：

1. 构建 MIFlu 模型 + 对应 MoE/UCS 扩展模块（`build_variant_model`）。
2. 加载训练期统计（`mean/std`，前 70%）做 StandardScaler 归一化。
3. 用 `TextualInputEmbedder` 编码 Prompt → `htext`（冻结）。
4. 训练：Adam(lr=1e-4) + MSE，固定 20 epoch（与 `make_forecast_figure.py` 一致，无 early stopping）。
5. 在测试集评估 **归一化尺度** 的 MSE / MAE（对齐 MIFlu Section V-B 协议）。
6. 追加一行到 `data/moe_comparison_results.csv`。

> 注意：脚本当前 `mse` / `mae` 占位为 `nan`，**需补全训练+评估循环后**在 HPC 实跑填入真实数字。本地不运行（OOM）。

### 2.2 出图流程（`analysis/plot_moe_comparison.py`）

读取上一步 CSV：

- (a) 分组柱状图：`variant × L vs MSE`（含 `MIFlu` 与 `+All` 对比）→ `data/moe_comparison_mse.png`
- (b) 预测曲线叠加图：ground truth vs MIFlu vs +All（带精确峰值标注）

**NaN 保护**：若 CSV 仍含 `nan`（即未跑），脚本打印 `[SKIP]` 并退出，**不产出任何假图、不填假数字**。

### 2.3 SSH 提交示意（burgundy 集群）

```bash
# 1) 本地打包上传（见第四节清单，共 5 个文件）
scp make_forecast_figure.py miflu_model.py textual_embedder.py \
      moe_extension.py analysis/moe_comparison_pipeline.py \
      data/national_illness_raw.csv <your_id>@burgundy.cityu.edu.hk:~/MLFlu/

# 2) SSH 登录
ssh <your_id>@burgundy.cityu.edu.hk

# 3) 申请 GPU 并提交（示例 Slurm 作业）
cd ~/MLFlu
cat > run_moe.slurm <<'EOF'
#!/bin/bash
#SBATCH --job-name=moe_cmp
#SBATCH --gres=gpu:1
#SBATCH --mem=32G
#SBATCH --time=24:00:00
module load python/3.9
pip install --user torch transformers numpy pandas scipy matplotlib
python analysis/moe_comparison_pipeline.py
python analysis/plot_moe_comparison.py
EOF
sbatch run_moe.slurm
```

> 具体 `#SBATCH` 参数（partition / GPU 型号 / 时长）以 burgundy 集群实际文档为准；GPT2 权重联网下载或预缓存见第四节。

---

## 三、输出 (Output)

脚本在 `data/` 目录下产出：

| 产物 | 路径 | 说明 |
|------|------|------|
| 对比结果表 | `data/moe_comparison_results.csv` | 列：`variant, L, mse, mae`（归一化尺度） |
| 对比柱状图 | `data/moe_comparison_mse.png` | variant × L vs MSE |
| 预测叠加图 | （同脚本生成） | ground truth vs MIFlu vs +All，带峰值标注 |

所有数字与图均来自 HPC 实跑；**本地不生成任何对比图或假数字**。

---

## 四、上传文件清单（需传到 HPC 的文件数）

共 **5 个文件**（其余文件 HPC 上不需上传，脚本不依赖）：

| # | 文件 | 用途 |
|---|------|------|
| 1 | `make_forecast_figure.py` | 同目录依赖（部分共享逻辑）— 若仅跑对比可省略，但建议带上以保证环境一致 |
| 2 | `miflu_model.py` | 基础模型（必需） |
| 3 | `textual_embedder.py` | 文本编码（必需） |
| 4 | `moe_extension.py` | MoE/UCS 原型（必需） |
| 5 | `analysis/moe_comparison_pipeline.py` | 五变体对比主脚本（必需） |
| 6 | `data/national_illness_raw.csv` | 输入数据（必需） |

> 若 `analysis/` 目录在 HPC 上与本地结构一致，`plot_moe_comparison.py` 也一并上传（用于第二步出图）。即实际传 **6 个文件 + 1 个数据**。

### 注意事项

- **GPT-2 权重**：`burgundy` 计算节点若无法访问 Hugging Face，先在登录节点或可联网机器下载至 `~/.cache/huggingface`，再提交作业复用缓存。
- **内存**：五变体中最重的是 `+All`（I2MoE 新增 ~18.9M 参数 + Flex-MoE Bank），建议 `--mem=32G` 起。
- **输出取回**：作业完成后用 `scp <your_id>@burgundy.cityu.edu.hk:~/MLFlu/data/moe_comparison_*.csv ~/...` 取回本地，再填入 `Innovation-Proof.md` 的 "Pending HPC Experiments" 小节。

---

*附录：本实验对应 `Innovation-Proof.md` 第二层（HPC 待跑）。第一层（本地原型验证：I2MoE +18.89M / Flex-MoE +2.37M / UCS 0 参数）已完成，详见该报告。*
