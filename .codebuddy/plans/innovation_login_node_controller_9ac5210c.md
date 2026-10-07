---
name: innovation_login_node_controller
overview: 在 HPC 登录节点上建立一个持久化、可恢复的队列安全控制器（HPC_GUIDE §3b/§11 明确允许的 "background auto-submit loop"），按当前自治会话已授权的阶段 A→N 一次提交一个作业、等待终态、校验产物、fail-stop、写入心跳/状态/台账，并在每个新阶段前做资源预算与合规核算；Test 评估（阶段 L）仅在完成矩阵无未决强制校验项且冠军冻结审计通过后才会被放行。
todos:
  - id: create-state-lib
    content: 创建 hpc_scripts/autonomous/{state.py,lib.sh}：状态/台账/预算/完成矩阵/Test门控/阶段天花板纯逻辑与 Bash 辅助函数
    status: completed
  - id: author-controller
    content: 编写 hpc_scripts/autonomous/controller.sh：单实例锁、一次一作业、轮询、推进前校验、回拷、FAIL-STOP、可恢复、阶段天花板、--dry-run
    status: completed
    dependencies:
      - create-state-lib
  - id: define-stage-plan
    content: 定义 stage_plan.json 与 completion_matrix.md，更新 session_manifest.json（controller段/ceiling）与 decision_log.md（D4）
    status: completed
    dependencies:
      - create-state-lib
  - id: controller-tests
    content: 新增 tests/innovation/test_autonomous_controller.py 单测 12 条硬要求与预算/Test门控/天花板
    status: completed
    dependencies:
      - author-controller
  - id: v2-5-cascade
    content: 执行 v2.5 源码级联：版本升 v2.5、重建快照/manifest、重生成 specs 与脚本、双构建确定性 bundle、部署到新隔离根并显式根复验 76/76
    status: completed
    dependencies:
      - controller-tests
      - define-stage-plan
  - id: launch-controller
    content: 上传控制器到隔离根，nohup 常驻登录节点并记录 PID，dry-run 复核后再放行首个 v2.5 Pilot 提交
    status: completed
    dependencies:
      - v2-5-cascade
---

## 用户需求概述

在提交首个 v2.5 Pilot 前，先依据 HPC_GUIDE.md 判定是否允许"登录节点常驻控制器"。经核查 HPC_GUIDE.md §3b 与 §11 明确写道"poll squeue 或 run a background auto-submit loop"，且红线仅针对资源虚报（§10/§11），故**允许**常驻登录节点控制器——前提是它不请求 GPU、不占用 stingy 单作业配额，仅做轮询与提交。

## 核心功能

1. 在冻结模型源码之外（冻结哈希仅覆盖 `scripts/innovation/**` 与 `tests/innovation/**`，故放在 `hpc_scripts/`）创建可恢复、队列安全的常驻控制器，满足 12 条硬要求：单实例锁、提交前记作业 ID、一次最多一作业、合理轮询等终态、推进前校验产物、遇确定性失败/源码不匹配/元数据不匹配/Test 越权/产物缺失即停、绝不静默重试、仅追加台账、中断可恢复不重复提交、不越权阶段、写心跳与 current_state.json、每作业后回拷关键 scratch 产物到持久存储。
2. 每个新阶段启动前计算精确作业数、预估 GPU 小时、可用存储、队列合规、所需源码版本、依赖可用性；超出授权/额度时记录为 queued/deferred 而非启动。
3. 一次性 Test 评估绝不因"还有时间"启动；仅当完成矩阵无未决强制校验项且验证型冠军冻结审计全通过后，才经 `runner.run_test_evaluation`（受 `frozen_winners.json` 门控）运行一次。
4. 控制器独立于本地聊天会话，在 HPC 登录节点以 `nohup`/`setsid` 常驻；不触碰原复现仓库 `Chattime`；不修改科学协议与冻结模型源码。

## 约束

- 控制器及辅助脚本不得进入被哈希的冻结源码集（放 `hpc_scripts/`）。
- 复用既有 `submit_innovation_pilot.sh`（登录节点 chain driver，不作为作业提交）、`innovation_worker.sh`（`#SBATCH` 作业，含部署根守卫+快照校验+治理断言）、`runner.run_test_evaluation`、`governance.py`（冻结审计）。
- 阶段上限由 `session_manifest.stage_order`（A–N）与授权前沿约束；Test(L) 仅门控通过后运行。

## 技术栈与运行环境

- 登录节点常驻编排：Bash 循环（`nohup`/`setsid` 启动，自身不请求 GPU）+ 轻量 Python 辅助模块 `state.py`（纯逻辑：状态/台账/预算/门控，可单测、可导入）。
- 状态与产物：JSON（`current_state.json`、`stage_plan.json`）、CSV（`job_ledger.csv`、`budget_ledger.csv`）、Markdown（`completion_matrix.md`、`resume_instructions.md`、`decision_log.md`）、JSONL（`action_log.jsonl`）。
- Slurm CLI：`sbatch`/`sacct`/`scontrol`/`squeue`；产物回拷用 `scp`/`rsync`（遵循 HPC_GUIDE §12 每作业拉回持久存储）。
- 校验调用：控制器以子进程方式在部署根内调用既有脚本（`metadata_chain.py`、`select_best_model.py`、`governance.py`），不 import 冻结模块，故不污染源码哈希。

## 实现策略

- **单一事实来源**：`stage_plan.json` 列出已授权阶段的顺序、每阶段作业规格（model/encoder/fusion/horizon/seed/epochs/stage）、预算、以及 `authorization_ceiling`（默认到冻结 K，Test 显式排除）。
- **12 条硬要求映射**：

1. 单实例锁 → `flock -n` 锁文件（`autonomous_completion/.controller.lock`）；
2. 提交前记 ID → `job_ledger.csv` 在 `sbatch` 返回后立即追加（含 submitted_utc/state=PD）；
3. 一次一作业 → 提交前 `squeue -u $USER -h -p stingy` 为空才 `sbatch`；
4. 轮询终态 → `sacct -j <id> -X -n -o State,ExitCode`，间隔 60s，上限 240 次（约 4h）；
5. 推进前校验 → 终态后调用对应阶段校验子命令，全过才标记 done 并进入下一作业；
6. 即停 → 确定性失败/源码哈希不符/元数据不符/Test 越权/产物缺失 → 写 `STOPPED` 状态并 `exit 1`；
7. 不静默重试 → 无 retry 循环（瞬时抢占由 worker 的 `--max-seconds`+checkpoint 续跑处理，非控制器重试）；
8. 仅追加台账 → `job_ledger.csv`/`action_log.jsonl` 只 append；
9. 可恢复 → 启动时读台账，对最后一个已提交作业复核终态，跳过已完成阶段，绝不重复 `sbatch` 已有 job_id 的作业；
10. 不越权 → 拒绝提交 `stage_plan.json` 之外的阶段/超出 `authorization_ceiling` 的阶段；
11. 心跳+状态 → 每轮写 `current_state.json`（stage/last_job/heartbeat_utc/pid/lock_holder）；
12. 回拷 → 每作业 COMPLETED 后将 run 目录、`.out/.err`、metrics/checkpoints 拷回本地持久目录。

- **每阶段预算**：进入阶段前 `state.py` 计算 job_count、gpu_hours、df 存储余量、stingy 合规、manifest 源码版本、依赖（conda/GPT-2 离线缓存/数据集）可用性，写入 `budget_ledger.csv`；任一不合规或超限额（repair cascade≤4、protocol amendment≤1）则标记 `queued`/`deferred` 并停。
- **Test 门控**：`completion_matrix.md` 列全部强制校验项；仅当全 resolved 且 `governance.py` 冠军冻结审计通过，控制器才可提交一次性 Test 作业；绝不因时间剩余而运行。

## 目录结构与修改清单

```
hpc_scripts/autonomous/                 # 控制器（冻结源码之外，不进哈希）
  lib.sh            [NEW] 锁/台账追加/squeue 检查/sacct 轮询/心跳/预算/回拷/resume 等 Bash 函数
  state.py          [NEW] 纯逻辑：读写字段、台账、预算、完成矩阵、Test 门控、阶段天花板（可单测）
  controller.sh     [NEW] 常驻循环：锁→读 stage_plan→预算检查→单作业提交→轮询→校验→回拷→下一作业；FAIL-STOP
results/innovation/autonomous_completion/
  stage_plan.json          [NEW] 已授权阶段顺序+每作业规格+预算+authorization_ceiling（Test 显式排除）
  completion_matrix.md     [NEW] 强制校验项清单与 Test 放行条件
  budget_ledger.csv        [NEW] 每阶段预算与合规判定（append-only）
  resume_instructions.md   [NEW] 精确恢复步骤 + 持久化排队工作
  action_log.jsonl         [NEW] 仅追加动作日志
  current_state.json       [NEW] 心跳 + 当前状态（控制器维护）
  session_manifest.json    [MODIFY] 增加 controller 段、stage_plan_path、authorization_ceiling
  decision_log.md          [MODIFY] 追加 D4（HPC_GUIDE §3b/§11 允许登录节点控制器；设计说明）
  job_ledger.csv           [EXISTING] 仅追加（控制器写入）
tests/innovation/
  test_autonomous_controller.py  [NEW] 单测：锁/台账/恢复不重复/FAIL-STOP/预算/Test 门控/阶段天花板
```

## 关键代码结构（契约）

```python
# hpc_scripts/autonomous/state.py （可单测，控制器以子进程调用，不进入冻结源码哈希）
def load_stage_plan(path: str) -> dict: ...
def next_pending_job(plan: dict, ledger_rows: list[dict]) -> dict | None: ...
def append_ledger(row: dict) -> None: ...                 # append-only
def compute_budget(stage: dict, manifest: dict) -> dict: ...  # job_count/gpu_hours/storage/queue/source_version/deps
def budget_ok(b: dict, limits: dict) -> bool: ...
def test_gate_open(completion_matrix: dict, freeze_audit: dict) -> bool: ...
def stage_within_ceiling(stage_name: str, ceiling: str) -> bool: ...
def write_current_state(state: dict) -> None: ...         # heartbeat
```

## 验证与防回归

- `tests/innovation/test_autonomous_controller.py` 覆盖：单实例锁、台账仅追加、中断恢复不重复提交、源码/元数据/Test 越权/产物缺失即 FAIL-STOP、预算超限记录 deferred、Test 门控强制、阶段天花板强制。
- 因新增测试文件属 `tests/innovation/`（冻结哈希集），需走 v2.5 源码级联（快照→manifest→specs→脚本→测试→bundle×2→新隔离根部署）并复验 76/76；归档双构建一致。
- 部署后通过 `runtime_guard.py` 复核部署根不含 `Chattime`；`bash -n` 过控制器脚本；`controller.sh --dry-run` 输出将提交顺序而不实际 `sbatch`。