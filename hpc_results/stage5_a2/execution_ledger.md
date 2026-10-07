# Stage 5 A2 — 执行与资源账本（本轮）

生成时间：2026-09-26 00:30 Asia/Hong_Kong（= 2026-09-25 16:30 UTC）。
调度器原始时间戳为集群本地时区（HKT, UTC+8）；下文 UTC 列由 `date -u` 记录。
本文件替代旧的叙述性记录；机器可读原始表见 `hpc_results/stage5_a2/logs/gpu_ledger.txt`。

## 1. 预算口径

- 用户授权：**本轮累计上限 2 GPU-hours**（整个本轮，不因更换对话重置）。
- 计时范围：从最早授权预检开始，所有实际分配到 GPU 的时间，包括失败、OOM、重试、预检、训练、验证、推理、占 GPU 的基线任务。排队但未分配 GPU 的时间不计入。
- 计量方法：`sacct -X`（只取顶层作业，避免 `.batch`/`.extern` step 对同一次分配重复计费）；本轮每个作业都是 `gres/gpu:a100=1`、分区 `stingy`。
- 未确认项：无。`sacct` 覆盖本轮全部 38 个作业，无缺失记录。

## 2. 逐作业明细（UTC 提交时间；GPU-h = 分配时长 × 1 GPU）

| job_id | 名称 | 状态 | 时长 | GPU | GPU-h | 类别 | 用途 / 结果 |
|---|---|---|---:|---:|---:|---|---|
| 584875 | s5_preflight | FAILED | 00:00:00 | 1 | 0.0000 | preflight | 立即失败，未实际训练 |
| 584876 | s5_preflight | FAILED | 00:01:17 | 1 | 0.0214 | preflight | 默认主机内存 1,024 MB 不足 |
| 584877 | s5_preflight | FAILED | 00:00:06 | 1 | 0.0017 | preflight | — |
| 584878 | s5_preflight | OUT_OF_MEMORY | 00:00:09 | 1 | 0.0025 | preflight | **主机内存** OOM（1G），非 A100 显存 |
| 584884 | s5_preflight | FAILED | 00:00:08 | 1 | 0.0022 | preflight | 加 `--mem=16G` 后仍失败（依赖缺失） |
| 584886 | s5_preflight | COMPLETED | 00:00:07 | 1 | 0.0019 | preflight | **通过**：A100-SXM4-80GB、py3.9.25/torch2.5.1、本地 GPT-2、输出 (4,7,24)、trainable 1,030,056 / frozen 81,106,176、LoRA 存在、ckpt 往返逐 tensor 一致、文本替换后输出变化 ≈1.6e-3、峰值显存 ≈1.43 GB |
| 584888 | s5_verify | COMPLETED | 00:00:05 | 1 | 0.0014 | verify | HPC 部署导入核验（`recipes` / `early_stopping` 依赖补齐） |
| 584889 | s5_task | FAILED | 00:00:07 | 1 | 0.0019 | fit | 部署仍不完整 |
| 584893 | s5_task | FAILED | 00:00:06 | 1 | 0.0017 | fit | 部署仍不完整 |
| 585525 | s5_task | COMPLETED | 00:00:16 | 1 | 0.0044 | fit | 冒烟 |
| 585530 | s5_task | FAILED | 00:00:11 | 1 | 0.0031 | fit | 冒烟失败 |
| 585540 | s5_task | FAILED | 00:02:43 | 1 | 0.0453 | fit | miflu L=24 中断（被后续干净重跑取代） |
| 585544 | s5_task | FAILED | 00:02:39 | 1 | 0.0442 | fit | 同上 |
| 585555 | s5_task | COMPLETED | 00:07:49 | 1 | 0.1303 | fit | miflu L=24（**被 585794 同配置重跑取代**） |
| 585581 | s5_task | COMPLETED | 00:07:33 | 1 | 0.1258 | fit | miflu L=36（**被 585798 同配置重跑取代**） |
| 585794 | s5_task | COMPLETED | 00:07:50 | 1 | 0.1306 | fit | **采用**：miflu L=24 × 3 seeds |
| 585798 | s5_task | COMPLETED | 00:07:30 | 1 | 0.1250 | fit | **采用**：miflu L=36 × 3 seeds |
| 585802 | s5_task | COMPLETED | 00:07:17 | 1 | 0.1214 | fit | **采用**：miflu L=48 × 3 seeds |
| 585813 | s5_task | COMPLETED | 00:07:04 | 1 | 0.1178 | fit | **采用**：miflu L=60 × 3 seeds |
| 585821 | s5_task | FAILED | 00:01:06 | 1 | 0.0183 | fit | notext L=24 seed42：训练与选模成功、checkpoint 已存；收尾打印在 `DEFER_TEST` 下对 `None` 求均值触发 TypeError，进程退出 1 |
| 585823 | s5_task | FAILED | 00:01:04 | 1 | 0.0178 | fit | 同上（notext L=36 seed42，**采用**） |
| 585825 | s5_task | FAILED | 00:01:03 | 1 | 0.0175 | fit | 同上（notext L=48 seed42，**采用**） |
| 585827 | s5_task | FAILED | 00:01:02 | 1 | 0.0172 | fit | 同上（notext L=60 seed42，**采用**） |
| 585828 | s5_task | COMPLETED | 00:00:13 | 1 | 0.0036 | fit | nlinear L=24 × 3 seeds |
| 585830 | s5_task | COMPLETED | 00:00:14 | 1 | 0.0039 | fit | nlinear L=36 × 3 seeds |
| 585832 | s5_task | COMPLETED | 00:00:13 | 1 | 0.0036 | fit | nlinear L=48 × 3 seeds |
| 585833 | s5_task | COMPLETED | 00:00:14 | 1 | 0.0039 | fit | nlinear L=60 × 3 seeds |
| 585836 | s5_task | COMPLETED | 00:00:05 | 1 | 0.0014 | fit | 8 条确定性基线（`DEFER_TEST=0`） |
| 585843 | s5_task | COMPLETED | 00:00:17 | 1 | 0.0047 | fit | **空跑**：resume 判据缺陷把 4 个 (L,rep) 判为已完成，seed 43/44 被静默跳过；无新拟合 |
| 585844 | s5_task | COMPLETED | 00:00:16 | 1 | 0.0044 | fit | 同上（空跑） |
| 585845 | s5_task | COMPLETED | 00:00:16 | 1 | 0.0044 | fit | 同上（空跑） |
| 585846 | s5_task | COMPLETED | 00:00:16 | 1 | 0.0044 | fit | 同上（空跑） |
| **585865** | s5_task | COMPLETED | 00:02:16 | 1 | 0.0378 | fit | **本轮接管补做**：修好 seed 感知 resume 后，notext L=24 seed43/44；seed42 按 ckpt 存在跳过并复用 |
| **585874** | s5_task | COMPLETED | 00:02:13 | 1 | 0.0369 | fit | **本轮接管补做**：notext L=36 seed43/44 |
| **585875** | s5_task | COMPLETED | 00:02:08 | 1 | 0.0356 | fit | **本轮接管补做**：notext L=48 seed43/44 |
| **585876** | s5_task | COMPLETED | 00:02:06 | 1 | 0.0350 | fit | **本轮接管补做**：notext L=60 seed43/44 |
| 585878 | s5_score | FAILED | 00:00:25 | 1 | 0.0069 | scoring | checkpoint 锁定**成功**；随后 `predict_nlinear` 抛 `AttributeError: 'NLinear' object has no attribute 'device'` 而中断 |
| **585883** | s5_score | COMPLETED | 00:00:49 | 1 | 0.0136 | scoring | **采用**：锁 36/36 → Test 推理 36 ckpt + 8 基线 → 独立重算 PASS |

## 3. 分类合计

| 类别 | GPU-h |
|---|---:|
| preflight | 0.0297 |
| verify（部署导入核验） | 0.0014 |
| fit（训练/基线/空跑/失败重试） | 1.1019 |
| scoring（统一 Test 评分 + 锁定 + 重算） | 0.0206 |
| **合计** | **1.1536**（= 4153 GPU-s） |
| 上限 | 2.0000 |
| **剩余** | **0.8464** |

被同配置重跑取代而未进入报告的作业：585540、585544、585555、585581、585843–585846，合计 0.4400 GPU-h。这些成本**已计入**上表总额（不因结果被取代而不计费）。

## 4. 完成度

| 计划项 | 计划数 | 完成 | 状态 |
|---|---:|---:|---|
| 学习模型独立拟合（MIFlu / no-text / NLinear × 4L × 3 seeds） | 36 | 36 | COMPLETED |
| 确定性基线评价（Last Value / Seasonal Naive × 4L） | 8 | 8 | COMPLETED |
| checkpoint 锁定（SHA-256 + 验证选模证据） | 36 | 36 | COMPLETED（`CHECKPOINT_LOCK.json`，2026-09-25T16:13:29Z，早于任何 Test 推理） |
| 统一 Test 评分 | 44 | 44 | COMPLETED（`score_matrix.csv`） |
| 从工件独立重算主指标 | 44 | 44 | PASS（最大偏差 4.44e-16） |
| A0（作者发布代码逐字重放） | 1 | 0 | **BLOCKED / 未执行**（`a0_diagnostic_record.csv`） |

## 5. 执行安全措施

- 接管时确认：队列空、无 tmux、无后台 dispatcher 进程 ⇒ 不存在重复派发者。
- 补做派发使用带归属的执行锁 `results/stage5/logs/EXEC_LOCK`；脚本启动时若发现他人锁则拒绝运行；派发完成后自行释放。
- 补做范围严格限定为缺失的 8 个 no-text 拟合；28 个已完成的拟合一个都没有重跑，seed 42 的 checkpoint 按 SHA-256 原样复用。
- 全部 GPU 作业经 `sbatch` 提交到 `stingy` 分区（1 运行 + 1 排队）；登录节点只做提交、轮询与小文件读取，未在登录节点跑任何训练/推理。
