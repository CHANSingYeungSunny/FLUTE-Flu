# Stage 5 — 仍需确认的授权（一次性集中列出）

已完成所有不依赖该授权的工作：分类修正、协议冻结、窗口规则修正与核对、清单与哈希、预检脚本与启动命令。
**以下内容缺失，未获授权前不会提交任何 GPU 作业（包括"很小"的预检）。**

## 1. D-compute — GPU 预算与队列（阻塞全部 36 拟合 + 8 评价）

需要确认：

1. **GPU 小时上限**（例如 ≤ 2 GPU-h 或 ≤ 5 GPU-h）；
2. **可用队列 / 分区与硬件**：项目既有约定为 `stingy` 分区、`--gres=gpu:a100:1`、单作业 `--time` 上限 04:00:00，且该 QOS 限制 **1 运行 + 1 排队**，因此必须链式提交；
3. **并发上限**：0.88 GB/拟合的显存允许同节点多份，但 QOS 只许 1 运行 + 1 待调度 ⇒ 实际串行；
4. 是否允许使用与既有作业相同的 `/home/sychan552` 环境（`mlflu_hpc` conda 环境 + 本地 GPT-2 cache）。

已测算（**测量值**，来源 `hpc_results/paper_exact/training_miflu_log_514859.txt`，A100-SXM4-80GB）：

| 项 | 值 | 性质 |
|---|---|---|
| 显存 | ~0.88 GB / 拟合 | 测量 |
| 单 epoch 时间（修正 MIFlu，LoRA r=4，batch 16，966 行） | ~7.8–8.3 s | 测量 |
| epochs | 20 | 冻结配置 |
| 单拟合墙钟 | ~160 s ≈ 2.7 min | **外推**（测量值 × 20） |
| A2-MIFlu 12 拟合 | ~32 min ≈ 0.53 GPU-h | 外推 |
| A2-NOTEXT 12 拟合 | ~32 min ≈ 0.53 GPU-h | 外推 |
| A2-NLIN 12 拟合 | **未测量**（线性模型，预计 ≪ MIFlu） | 未测量 |
| 8 个确定性评价 | < 1 min ≈ 0.02 GPU-h | 未测量（CPU 亦可） |
| **合计** | **≲ 70 min 串行 ≈ ≲ 1.2 GPU-h** | 外推 |
| 预检作业 | ~0.05–0.1 GPU-h（30 min 上限，实际远小于） | 外推 |

## 2. D-a0-env — A0 重放环境（仅阻塞 A0-01）

需要：GPU 节点 + 作者仓库 `recovery/author_repo/` 的依赖环境 + 作者 gpt2 cache 路径。
A0 是**全量微调**（作者 `PEFT=0`、`freeze` 为空操作），单 epoch 成本高于本项目 8 s，且每 checkpoint 约 500 MB；**不得**由 A2 的外推值推估。

## 3. 已确认、不再询问

- D-adapter、D-nlinear：Stage 4 已完成。
- D-split（676/97/193）、D-target（`average_MSE_4L`）、D-windows（strict 目标完整包含）、D-holdout（仅对已暴露 Test 做一次性回顾性评价）：由本执行指令记录，来源已注明为执行指令而非导师批准。

## 4. 授权后的执行顺序

1. `sbatch recovery/stage5/preflight_sbatch.sh`（预检，含 text-tensor 敏感性 #7 与资源实测）；
2. 预检通过后，按 `launch_commands.md` 链式提交 36 拟合（每 4–12 个一包，遵守 1 运行 + 1 排队）；
3. 8 个确定性评价（可与拟合同批或 CPU 完成）；
4. 全部 checkpoint 选定并锁定清单后，用独立评价入口统一评分 Test；
5. A0 仅在 D-a0-env 解决后进行。
