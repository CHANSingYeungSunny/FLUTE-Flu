---
name: MIFlu 创新实验 v2 — 基础设施 + 本地 smoke（第一批）
overview: 在已复现 MIFlu 的仓库中，最小侵入式地搭建可复现的创新实验基础设施：插件化接口（ForecastBackbone/TextEncoder/FusionModule）、gpt2_miflu 控制组、DLinear/NLinear+PatchTST+iTransformer 骨干、none/TF-IDF+SVD/GPT-2 文本编码器、三种融合、run_id 独立产物体系与 registry、validation-MSE 早停与最佳 ckpt 恢复、PTE/PIE 文献峰值标准、纯 validation 的冠军选择与 test-gate 失败测试，并对每个已实现候选跑 L=24/seed=42/1-epoch smoke test；生成但暂不提交 HPC 脚本。EvoForecast 与第二批模型延后。
todos:
  - id: reread-plan-and-state
    content: 重读权威计划并重算 SHA-256 与冻结值比对，读取 gate/manifest/pilot_specs 与 5 份审计报告，汇总当前状态（全程只读，不改任何文件）
    status: pending
  - id: remaining-matrix
    content: Use [subagent:code-explorer] 核对 §2/§3/§11 候选与阶段 A–M 完成度，生成 results/innovation/remaining_plan_execution_matrix.md（6 种状态逐项标记）
    status: pending
    dependencies:
      - reread-plan-and-state
  - id: bundle-builder
    content: 实现 scripts/build_innovation_hpc_bundle.py：确定性 tar.gz + .sha256 sidecar + DEPLOY_AND_VERIFY.md + hpc_deployment_prep.json；复用 collect_paths 并在源码漂移时中止报 SOURCE_SNAPSHOT_DRIFT
    status: pending
    dependencies:
      - reread-plan-and-state
  - id: env-check-script
    content: 生成 hpc_scripts/hpc_env_check.sh：hostname/deployment root/SLURM/python/torch/transformers/CUDA/cuDNN/实际 GPU/严格离线 GPT-2/对 pilot 脚本 bash -n
    status: pending
    dependencies:
      - reread-plan-and-state
  - id: build-and-verify-bundle
    content: 运行生成器产出归档与文档，校验 sidecar SHA-256，并确认冻结快照仍为 69 文件且聚合哈希 f63b524f... 未变
    status: pending
    dependencies:
      - bundle-builder
      - env-check-script
  - id: final-report-user-action
    content: 输出 USER_ACTION_REQUIRED 与 §18 的 12 项汇报：含精确 scp/tar/verify 命令、当前 Gate、test 封存状态与分别授权的下一步
    status: pending
    dependencies:
      - remaining-matrix
      - build-and-verify-bundle
---


## 用户需求
依据已完整读取的 `CodeBuddy_MIFlu_Maximum_Autonomy_Completion_Prompt.md`（仓库根目录，16.95 KB），从当前仓库状态出发，按 `Plan -> Act -> Observe -> Diagnose -> Repair -> Verify` 循环自治推进 `MIFlu_innovation_plan_v2.md` 的剩余阶段：四个基础设施 Pilot、无文本 Screening、Full Evaluation（L={24,36,48,60} × seeds 42..51）、文本编码器/融合/负对照消融、可行 LLM/TSFM、稳健性与资源分析、AUC-Best-so-far、validation-only 冠军冻结，以及**合法的一次性 Test Evaluation**。

## 必须先处理的阻断事实（真实执行证据，非推断）
- 已按授权从登录节点提交 Pilot 1 → job **556156**。
- `sacct -j 556156`：`State=FAILED, ExitCode=1:0, Node=gpu-a100-03, Elapsed=00:00:01`。
- 作业 OUT 显示 v2.4 安全修复**全部生效**：`[deployment_root] /gpfs1/.../innov-v2.4_5a4c3247`、`[runtime_guard] paths_checked=11 violations=0 / OK`、`[verify_source_snapshot] explicit_root, 77/77, expected==actual==5a4c3247…, exit_status=0`。
- 作业 ERR 显示唯一失败点：`File "<stdin>", line 2, in <module> NameError: name 'os' is not defined`。
- 根因（已定位到行）：`scripts/innovation/hpc_specs.py` 第 112 行起 `_STARTUP_PY` heredoc，第 114 行为 `import json, sys`，第 115 行却使用 `os.environ.get("PILOT_MODEL")` → 缺 `import os`。该 heredoc 在**每个** pilot 脚本与 worker 启动阶段执行，因此四个 Pilot 会以完全相同方式失败。本地 `bash -n` 与既有 17 项测试都不执行该 heredoc，故未捕获。

## 本轮必须交付
1. 用最小源码修复消除该 NameError，并补一条**真正执行 heredoc** 的回归测试（防止同类缺陷只在 HPC 暴露）。
2. 走一次完整的 `innov-v2.5` 源码级联与重新部署（本会话第 1 次，自治上限 4 次）。
3. 以 v2.5 串行重跑四个 Pilot（stingy 队列：一次仅 1 个作业，等终态再提交下一个）。
4. 建立/补齐 `results/innovation/autonomous_completion/` 全部台账，并按预算分批推进后续阶段；会话结束若仍有作业在跑，保留作业/台账/resume instructions，报告 `AUTONOMOUS_RUN_IN_PROGRESS`，**不得虚构完成**。

## 硬性边界
- Test 仅在冠军依法冻结且审计证明选择过程从未读取 Test 之后执行**一次**；此前 `test_access_allowed=false`。
- 唯一文献峰值标准 `PTE <= 1 week AND PIE <= 25%`，不引入/不报告其他阈值。
- 不混用 v2.3/v2.4/v2.5 哈希；不改写历史审计证据（v2.3 `PILOT_PRECHECK_FAILED` 必须保留）。
- 科学协议恒为 `innov-v2.0`，不因部署/元数据/脚本安全修复而改变。
- 不夸大资源请求；scratch 无备份，产物需回传本地。



## 技术栈与既有约定（沿用，不引入新模式）
- PyTorch + pandas/numpy；HPC：CityU Burgundy `stingy` 分区，`gpu:a100:1`，`--time ≤ 04:00:00`，`Jobs=1` + `Submit-Job=1`。
- 冻结源码范围：`scripts/innovation/**`、`tests/innovation/**`、`hpc_scripts/{innovation_,pilot_,submit_innovation_}*.sh`、权威计划 md、7 个被复用原始模块。任何改动都会改变 runtime 聚合哈希 → 必须级联。
- 治理契约：`paths.governance_fields()` 12 字段传播到 5 个证据层；`registry.csv`（14 行）冻结，`registry_v2.csv`（schema 2）append-only。
- 部署：确定性 bundle（两次构建哈希一致）→ 新隔离根 `innov-v2.5_<hash8>` → 显式根校验 + `runtime_guard` + 离线 GPT-2 + `bash -n`。

## 实施方案
1. **最小源码修复**：`_STARTUP_PY` 首行 `import json, sys` → `import json, os, sys`。不改任何科学逻辑、不改 runner。
2. **补强测试（关键防回归）**：新增 `tests/innovation/test_startup_heredoc.py`，从生成的 4 个 pilot 脚本与 worker 中**抽取 heredoc 的 python 段**，在临时目录写入最小 `results/innovation/source_snapshot_manifest.json` 与 `hpc_scripts/pilot_specs.json`，用 `PILOT_MODEL` 环境实际执行，覆盖三场景：正常（exit 0）、哈希不一致（非 0）、资格位非 false（非 0）。同时静态断言 heredoc 中出现的每个 `os.`/`json.`/`sys.` 引用都有对应 import。
3. **v2.5 级联**：`paths.IMPLEMENTATION_SOURCE_VERSION -> innov-v2.5` → 跑相关单测（含新增 heredoc 测试与既有 17 项）→ `source_snapshot.py` 重建 → `hpc_specs.py` 重生成 specs/脚本（pilot_specs 自动携带 v2.5 哈希）→ 需要时重跑 metadata-contract smoke（因哈希变更）→ `slurm_check` + `bash -n` → `prehpc_report` → `build_innovation_hpc_bundle.py` 连续两次（要求哈希一致）→ 部署 `innov-v2.5_<hash8>`。
4. **Pilot 执行（队列安全）**：**不把** `submit_innovation_pilot.sh` 作为作业提交（它自身带 `--gres=gpu:a100:1` 会占用唯一槽位，导致其 `sbatch` 被 `QOSMaxSubmitJobPerUserLimit` 拒绝）；改由登录节点逐个提交 `pilot_gpt2_miflu → dlinear → patchtst → itransformer`，每个等 `sacct` 终态、校验产物（run_status、checkpoint restore、4 张图、registry_v2 追加 1 行、无 test 产物）后再提交下一个。
5. **后续阶段分批推进**：C 候选实现就绪（对 TimesNet/TimeMixer/ModernTCN/fastText/BERT-MiniLM/TSFM 逐一给出 `IMPLEMENTED_AND_RUN / IMPLEMENTED_NOT_RUN / UNAVAILABLE_DEPENDENCY / DEFERRED_COMPUTE_BUDGET / EXCLUDED_WITH_JUSTIFICATION` 状态，不静默省略）→ D 无文本 Screening（L={24,60}, seeds={42,43,44}, text_encoder=none, selection_eligible=true, paper_result_eligible=false, test_access_allowed=false）→ E/F → G/H/I/J → K 冻结（先写 `frozen_winners.json` + `frozen_model_manifest.json`）→ L 一次性 Test → M 最终证据。

## 关键风险与对策
- **预算/队列风险（最高）**：Full 4×10=40 run/候选，4 候选约 160 run，加消融后极可能超出单会话。对策：按候选优先级分批提交；每批结束更新 `current_state.json`/`completion_matrix.md`/`resume_instructions.md`；会话结束时如实报告 `AUTONOMOUS_RUN_IN_PROGRESS`。
- **再次出现只在 HPC 暴露的缺陷**：对策是新增的 heredoc 实执行回归测试 + 每次提交前 `bash -n` + 首个 Pilot 先跑 1 个再批量。
- **测试未捕获语法/导入缺陷**：`bash -n` 不执行内容，必须靠实执行测试兜底。

