# Remaining plan execution matrix

Authoritative plan: `MIFlu_innovation_plan_v2.md`
Scientific protocol: `innov-v2.0` · Implementation source: `innov-v2.1`
Runtime file-set aggregate: `dc7ee9649c8d840a0453c9728b417059e5bc86fa7d859f224b5e3a67d43c07b4` (69 files)
Generated: 2026-09-14

## Status legend

| Status | Meaning |
|---|---|
| `COMPLETED` | finished and verified |
| `READY` | all prerequisites met; can run without further decisions |
| `BLOCKED` | cannot run until a named gate/authorisation clears |
| `DEFERRED` | postponed within the plan (not dropped) |
| `UNAVAILABLE` | impossible under the strict-offline / hardware constraints |
| `NOT_STARTED` | not begun |

> **Scope warning.** "Infrastructure", "local smoke" and "pre-HPC validation" are
> **NOT formal experimental results**. No formal result (screening / full
> evaluation / test) exists yet. No model is claimed to outperform any other.

## 1. Prerequisite（非实验基础设施）

| Item | Status | Evidence |
|---|---|---|
| 权威计划读取与冻结 | `COMPLETED` | plan SHA `aa4ab1c8…9e7961` recomputed = frozen | 
| innovation 基础设施（插件接口 / runner / 产物树 / registry） | `COMPLETED` | `scripts/innovation/**`, registry 8 ok / 5 failed |
| 本地 smoke（8 组合，pipeline 验证；**非正式结果**） | `COMPLETED` | `results/innovation/runs/**`（`selection_eligible=false`） |
| pre-HPC 七项检查 | `COMPLETED` | `audit/`（含 gpt2 控制组报告） |
| validation-only 资格门控 | `COMPLETED` | `model_selection_audit.json` = `no_eligible_runs` |
| test 物理隔离 | `COMPLETED` | 无 `frozen_winners.json`；`test_evaluations/` 空；runs 无 test 产物 |
| 源码快照冻结（v2.1 级联） | `COMPLETED` | `source_snapshot_manifest.json` = `dc7ee964…c07b4`，69 文件 |
| 4 个 pilot 脚本生成（**未提交**） | `COMPLETED` | `hpc_scripts/pilot_*_L24_seed42.sh` |
| 显式 deployment-root 校验器（v2.1） | `COMPLETED` | `--deployment-root`；嵌套根拒绝；10 项测试通过 |
| 剩余计划执行矩阵 | `COMPLETED` | 本文件 |

## 2. 阶段状态（权威计划 §3 / §11 阶段 A–M）

| Phase | 内容 | Status | Blocker / Note |
|---|---|---|---|
| **A** | HPC 源码部署验证 | 本地准备 `COMPLETED` / 实际 HPC 验证 `BLOCKED` | `USER_ACTION_REQUIRED`：需用户在 HPC 上传并运行显式根校验 |
| **B** | 四个 HPC pilot | `BLOCKED` | 需 `source_deployment_verified=true` 且 `pilot_submission_ready=true`；`sbatch` 需单独授权 |
| **C** | 补齐 TimesNet + TimeMixer/ModernTCN | `NOT_STARTED` | 计划要求"正式 screening 前"完成；本轮严格阶段 A 未做 |
| **D** | 正式无文本 backbone screening | `BLOCKED` | 依赖 B 全部通过 + C 完成 + 新快照在 HPC 验证 |
| **E** | 完整 backbone 评估（4 horizon × 10 seeds） | `BLOCKED` | 依赖 D 前三名 |
| **F** | 文本编码器与负对照补齐 | 部分 `NOT_STARTED` / 部分 `UNAVAILABLE` | 见 §4 |
| **G** | 文本编码器 × 融合消融 | `BLOCKED` | 依赖 E 最强两项；`none` 编码器组合应标 `NOT_APPLICABLE` |
| **H** | LLM / TSFM 候选处理 | `NOT_STARTED` / `UNAVAILABLE` / `DEFERRED` | 见 §3 与 §5 |
| **I** | 稳健性与分布漂移分析 | `BLOCKED` | 依赖 E |
| **J** | 预算感知 AUC-Best-so-far | `DEFERRED` | 次级实验；不得替代 MSE/MAE/PTE/PIE |
| **K** | 最终 validation-only 冠军选择 | `BLOCKED` | 需候选/消融/负对照/统计/资源/稳健性齐备 |
| **L** | 一次性 test 评估 | `BLOCKED` | test 仍封存；需合法 frozen winner |
| **M** | EvoForecast 决策 | `DEFERRED` (`DEFERRED_TO_FUTURE_WORK`) | 独立实验臂；不得阻塞主论文 |

## 3. 候选模型完整性（权威计划 §2/§3/§11）

| Candidate | Implementation | Fidelity | Smoke | Screening eligibility |
|---|---|---|---|---|
| `gpt2_miflu`（unimodal control） | `COMPLETED` | `REFERENCE_FAITHFUL` | done (pipeline only) | pending pilot |
| `dlinear` | `COMPLETED` | `REFERENCE_FAITHFUL` | done | pending pilot |
| `nlinear` | `COMPLETED` | `REFERENCE_FAITHFUL` | done | pending pilot |
| `patchtst`（display "PatchTST-inspired"） | `COMPLETED` | `INSPIRED_SIMPLIFICATION` | done | pending pilot |
| `itransformer`（display "…aligned, with disclosed deviations"） | `COMPLETED` | `REFERENCE_ALIGNED_WITH_DISCLOSED_DEVIATIONS` | done | pending pilot |
| `timesnet` | `NOT_STARTED` | — | — | — |
| `timemixer` | `NOT_STARTED` | — | — | — |
| `moderntcn` | `NOT_STARTED` | — | — | — |
| Time-LLM-style reprogramming | `NOT_STARTED` | — | — | — |
| CALF-inspired / TimeCMA-inspired alignment | `NOT_STARTED` | — | — | — |
| `chronos` / `timesfm` / `moirai` | `UNAVAILABLE` | — | — | strict-offline / hardware |

> 计划候选**未被静默删除**：未实现的均在此登记为 `NOT_STARTED` 或 `UNAVAILABLE`，并将在阶段 C/H 明确处置。

## 4. 文本编码器与负对照（权威计划 §2/§6）

| Item | Status | Note |
|---|---|---|
| `none` | `COMPLETED` | 已实现并 smoke |
| `tfidf_svd` | `COMPLETED` | **fixed contextual embedding baseline**（4 unique prompt，within-horizon 变差=0，跨 horizon 余弦 0.9999996） |
| `gpt2` | `COMPLETED` | 冻结 GPT-2，本地缓存离线加载 |
| `zero-text` | `NOT_STARTED` | 可离线实现，需固定可复现 seed |
| `shuffled-text` | `NOT_STARTED` | 需固定 permutation seed |
| `fasttext` | `UNAVAILABLE` | `UNAVAILABLE_LOCAL_DEPENDENCY`（严格离线，无本地权重） |
| frozen `bert` | `UNAVAILABLE` | `UNAVAILABLE_LOCAL_DEPENDENCY` |
| frozen `minilm` | `UNAVAILABLE` | `UNAVAILABLE_LOCAL_DEPENDENCY` |

## 5. 尚未开始的正式实验（0% 完成）

screening（阶段 D）、full evaluation（阶段 E）、文本/融合消融（阶段 G）、
稳健性分析（阶段 I）、AUC-Best-so-far（阶段 J）、冠军冻结（阶段 K）、
一次性 test（阶段 L）、EvoForecast（阶段 M）。

**当前没有任何正式模型结果、排名或论文性能结论。**

## 6. 当前 Gate

| Gate | Value |
|---|---|
| `pilot_generation_ready` | `true` |
| `pilot_submission_ready` | `false` |
| `full_sweep_submission_ready` | `false` |
| `blocker` | `UNVERIFIED_HPC_SOURCE_DEPLOYMENT` |
| `submission_attempted` | `false` |
| `sbatch_invoked` | `false` |
| test sealed | `true` |
