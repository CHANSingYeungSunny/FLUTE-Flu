# 完成表（原恢复计划第 0–5 阶段 + 十三项交付物）

生成时间：2026-09-26（Asia/Hong_Kong）。状态口径：
`COMPLETE` 有可执行证据 · `PARTIAL` 证据充分但范围受限 · `BLOCKED` 有具体外部阻塞 · `NOT_APPLICABLE` 本轮不适用 · `PENDING-QUOTA` 代码/矩阵/成本已就绪，仅缺新增计算额度。

---

## 1. 阶段完成表

| 阶段 | 工作 | 状态 | 实际证据 | 下一动作 |
|---|---|---|---|---|
| **0. 立即保全** | 归档原始快照、处理后 CSV、commit、环境、配置、prompt、checkpoint、预测、指标、访问账本；给旧结果标身份与曝光状态；哈希原件；只追加更正说明 | **COMPLETE** | 36 个 A2 checkpoint 已复制到 `/home/sychan552/stage5_a2_durable/checkpoints/`（7.4 G），**36/36 与首次锁定记录 SHA-256 逐字节一致**（`archive_log_586934.out`，job 586934，CPU-only）；`CHECKPOINT_ARCHIVE_SHA256SUMS.txt`；A2 全套产物 + 逐文件 SHA-256 在 `hpc_results/stage5_a2/` 与远端 durable；代码快照 `hpc_results/stage5_a2/code/` | 无。原件保留在 scratch 直至复制与可恢复性核验通过（已通过） |
| **1. 数据与索引审计** | 作者 CSV vs 七月快照；日历与变量映射；枚举每个输入/目标索引 | **COMPLETE** | `recovery/data_identity_report.md`、`dataset_manifest.json`、`overlap_differences.csv`、`feature_mapping.csv`、`coverage_audit.csv`；窗口索引 `window_indices_verify.md`；`hashes_stage5.json` | 无 |
| **2. 可执行审计** | 锁定作者代码；冒烟测试导入、通道、文本影响、参数冻结、checkpoint 恢复、指标、批次覆盖 | **COMPLETE** | `recovery/implementation_audit.md`；A2 计算节点预检 job 584886 PASS；**A0 本轮在 CPU 上完成可执行验证**（job 587002，见 §3） | 无 |
| **3. 聚焦复现试点** | 恢复论文设置；区分遗留重放与已记录修复；MIFlu + 匹配 no-text + NLinear + 两个朴素参考 | **PARTIAL** | A2 已完成修正重构的 36 拟合 + 8 基线 + 统一评分（`results_report_zh.md`）。**A0（发布代码诊断重放）CPU 部分完成、GPU 最小诊断未跑**（无额度） | A0 GPU 最小诊断，需 ~0.5 GPU-h |
| **4. 基准补全** | 复用已审计有效产物；只修复/重跑受影响单元；如需广谱比较则在共同协议下纳入规范实现 | **PENDING-QUOTA** | 六骨干运行器 `scripts/train_backbone_966.py` 已通过 CPU 自检与 `author_966 --containment strict` 预检；**协议同一性已证明**（job 586942：`train_backbone_966 reuses the SAME objects: True True True`，窗口数 549/74/170、537/62/158、525/50/146、513/38/134 与 A2 逐项一致）；矩阵/成本/派发脚本齐备且语法通过（job `verify_stage6_ready`，`syntax_fail=0`） | 需新增额度 **~1.8 GPU-h** |
| **5. 泛化与报告** | 保全旧 Test 结论；在未触碰区间上评价冻结主张；带时间依赖地重析损失；分轨表格与主张/状态矩阵 | **PARTIAL / BLOCKED** | 三轨已分开报告（A2=作者 966 回顾性；B=项目 1025 行既有；C=历史 Test 已暴露）。**C 轨独立泛化未完成且当前不可完成**——不存在未看过的时期，且不得改名旧区间伪造 holdout | 需导师/用户决定是否封存新未来区间 |

## 2. 十三项交付物

| # | 交付物 | 状态 | 位置 |
|---|---|---|---|
| 1 | 数据身份报告（机器可读） | COMPLETE | `recovery/data_identity_report.md`、`dataset_manifest.json` |
| 2 | 变量映射与 OT 分母同一性 | COMPLETE | `recovery/feature_mapping.csv` |
| 3 | 快照覆盖/缺口审计 | COMPLETE | `recovery/coverage_audit.csv`、`data_identity_report.md` §3 |
| 4 | 重叠与修订差异表 | COMPLETE | `recovery/overlap_differences.csv`（966 行） |
| 5 | 窗口索引与计数清单 | COMPLETE | `recovery/stage5/window_indices_verify.md`、`window_counts_verify.md` |
| 6 | 代码/数据/协议完整哈希台账 | COMPLETE | `recovery/stage5/hashes_stage5.json`（冻结时）、`hashes_stage5_executed.json`（**实际执行**） |
| 7 | 冻结协议与决定记录 | COMPLETE | `recovery/stage5/frozen_protocol_stage5.md`、`launch_decisions_stage5.md` |
| 8 | 执行/资源账本 | COMPLETE | `recovery/stage5/execution_ledger.md`、`hpc_results/stage5_a2/logs/gpu_ledger.txt` |
| 9 | checkpoint 锁定表 | COMPLETE | `hpc_results/stage5_a2/scoring/CHECKPOINT_LOCK.{json,csv}` + `CHECKPOINT_ARCHIVE_SHA256SUMS.txt` |
| 10 | 统一 Test 评分 + 独立重算 | COMPLETE | `score_matrix.csv`、`recomputed_*.csv`、`predictions/`（44 NPZ + 6688 行 origin 清单 + scaler） |
| 11 | 中文结果报告 | COMPLETE | `recovery/stage5/results_report_zh.md`、`results_tables_zh.md`、`supervisor_brief_zh.md` |
| 12 | A0 发布代码诊断 | **PARTIAL** | CPU 可执行诊断 **完成**（job 587002）；GPU 最小诊断 **未跑**（无额度）。证据：`recovery/a0/a0_cpu_audit.sh`、`a0_exec_proof.sh`、`a0_compat.py` 及对应日志 |
| 13 | A1 论文/配置/数值复现判定 | **COMPLETE** | `recovery/a1/a1_evidence_table_zh.md`（逐项四列证据表 + 无法核验原因） |

## 3. A0 已完成的 CPU 可执行诊断（job 587002，0 GPU-hours）

| 检查项 | 结果 | 证据 |
|---|---|---|
| 发布代码可导入 | 是（在已记录的兼容层下） | `OK import models.GPT4TS_lora` |
| commit 身份 | `6ed210150b8819313947cf607eb1821c87b1bee3`（2025-03-21） | `git log -1` |
| 骨干层数 | 保留 **6 / 12** 个 GPT2Block | 实测 `llmmodel.h` |
| LoRA | **未应用**（`PEFT=0` 默认，L74-90 分支不执行） | 实测 `llmmodel` 为裸 `GPT2Model` |
| 冻结 | **无效**：82,705,944 / 82,705,944 = **100% 可训练**（含 wte+wpe 的 39,383,808） | 实测参数统计；L58-61 只置 True 从不置 False |
| 真实输入投影 / 头 | `Linear(24→768)` / `Linear(32256→24)`；`DataEmbedding` 导入但从未使用 | 实测 + 源码 |
| 前向 | `(B,T,M)=(8,104,1) → (8,24,1)`，**逐特征**，从不联合七变量 | 实测 |
| 文本资产 | `text_emb_label_0507_24.txt` shape **(317, 768)**，四个 L 全部存在 | 实测 |
| **文本是否影响输出** | **否，差异恰为 `0.000e+00`**（真实文本 vs 打乱文本） | 实测前向替换 |
| **文本梯度** | **恰为 0**（`max|grad|=0.000e+00`，`norm=0.000e+00`） | 实测反向 |
| 文本失效机制 | 文本拼在时间片**之后**（偏移 5566），过 LLM（5746）后截断 `[:, :patch_num]`（5835）；因果注意力下靠前位置看不到靠后位置 | 字节偏移分析 + 数值验证 |
| Test 覆盖 | `train feat_id=[0..6]`、`val=[0..6]`、**`test=[0]`**；`drop_last` 后 170→160 | 从 `__len__`/`__getitem__` 推导 |
| 划分 | `num_train=676, num_vali=97, num_test=193`，与 A2 **完全一致** | 实测 |
| 训练中是否读 Test | **是**（L211 每 epoch `test(...)`；L225 用 `min_mse` 选；L264 保存该权重） | 静态 + 行号 |
| early stopping | 实例化但**调用被注释**（L235-236），不生效 | 静态 |

**A0 兼容层（已记录，三个阻塞）**：`einops` 缺失（已实现所需的 3 个 pattern）；`embed.py` 缺失（已从作者自己的 `__pycache__/embed.cpython-39.pyc` 反汇编恢复 8 个类，且 `GPT4TS_lora` 实际**不使用**它们）；`peft 0.17.1` 移除 `prepare_model_for_int8_training`（该符号在发布代码中**只出现在注释里**）。作者的源码树**逐字节未改**，兼容层放在独立的 `sys.path` 目录。

## 4. 本轮新增 GPU 使用

| 作业 | 用途 | GPU |
|---|---|---|
| 586934 | checkpoint 归档 + 逐字节校验 | **无**（`cpu=2,mem=8G`） |
| 586942 | A0 依赖/资产/划分审计 + 六骨干自检 + 协议同一性证明 | **无**（`cpu=2,mem=16G`） |
| 586945 | A0 阻塞项分析 | **无** |
| 586947 | `embed.py` 字节码反汇编 | **无** |
| 586950/586962/586982/586990/586995 | A0 可执行性证明（迭代修复） | **无** |
| 587002 | **A0 最终可执行诊断（含文本梯度归零）** | **无** |

**本轮 Stage 6 / A0 阶段新增 GPU 消耗 = 0.0000 GPU-hours。** A2 的账本仍为 1.1536 / 2.0，未被本轮动用。

> 注：同一账号下存在一个不属于本工作的作业 586949（`diaggen-visual`，a40 GPU），本轮所有账本与统计**均未计入**它。
