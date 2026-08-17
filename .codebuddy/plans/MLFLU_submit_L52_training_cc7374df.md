---
name: MLFLU_submit_L52_training
overview: 确认代码已上传齐全后，用 A100/stingy 节点提交 L52 训练任务（train_q1_L52.sh）。本地旧 checkpoints 保留作论文对比，HPC 旧 pth 并存不删。未来大文件传输每几秒汇报进度。
todos:
  - id: verify-no-conflict
    content: SSH 执行 squeue 确认无冲突 job 在跑
    status: completed
  - id: submit-training
    content: SSH 提交 sbatch scripts/train_q1_L52.sh 并记录 job id
    status: completed
    dependencies:
      - verify-no-conflict
  - id: verify-queue
    content: squeue -u sychan552 确认 job 进入 stingy 队列
    status: completed
    dependencies:
      - submit-training
  - id: monitor-startup
    content: 轮询 logs/train_L52-<jobid>.out 确认 env ok 与训练启动
    status: completed
    dependencies:
      - verify-queue
---

## 用户需求

在 HPC 上提交 MLFlu 的 L52 训练任务，采用新绘图标准协议（仅训练 L52 单一 horizon，生成 best_miflu_L52.pth）。

## 产品概述

通过 SSH 免密登录 CityUHK Burgundy HPC，提交已上传的训练脚本，启动 A100 GPU 上的 L52 模型训练，并验证任务正确进入队列与启动。

## 核心功能

- 提交训练任务：在 HPC 的 scratch/MLFLU 目录执行 sbatch 提交 train_q1_L52.sh
- 验证任务状态：确认 job 进入队列（stingy 分区）
- 监控启动日志：确认 conda 环境就绪、训练正常开始（规避同节点并发 NaN 问题）
- 保留所有旧 checkpoints（本地与 HPC 均不删除，留作论文对比）
- 后续大文件传输需每几秒向用户汇报进度（scp -v + 轮询远程文件大小）

## 技术栈

- 远程环境：CityUHK Burgundy HPC（登录节点 hpclogin02，别名 burgundy.hpc.cityu.edu.hk）
- 用户：`sychan552`，密钥免密 SSH
- 作业调度：SLURM（`sbatch` / `squeue`）
- 计算节点：stingy 分区 + A100 GPU（脚本已固定，保持不变）
- 训练命令：`python train_miflu.py --horizon 52 --reps 10 --epochs 20 --batch 16 --seed 42`
- 环境激活：绝对 PATH 前置 `/home/sychan552/.conda/envs/mlflu_hpc/bin`（避免 conda load 在 GPU 节点失败）
- 模块加载：`module unload default && module load old_modules`（维护后强制）

## 实现方法

### 策略

直接复用已上传齐全的代码（scripts/data/raw/docs 均已确认存在），通过单次 `ssh` 调用 `sbatch` 提交训练，再用 `squeue` + 日志轮询验证。本次仅提交单一训练任务，规避此前"同节点并发训练导致 NaN"的坑。

### 关键技术决策

1. **保持 A100/stingy 配置不变**：用户已确认节点配置正确，不修改 train_q1_L52.sh。
2. **单任务顺序提交**：仅提交 L52 一个训练，避免 GPU 节点争抢引发的 NaN（2026-08-06 教训）。
3. **不删除任何 checkpoints**：本地 4 个旧 pth 与 HPC 上 2 个旧 pth 均保留（文件名与新 best_miflu_L52.pth 不冲突），供 MLFlu 论文对比。
4. **大文件传输进度汇报**：后续若需补传（如 reference_papers、新 checkpoint），使用 `scp -v`（verbose 持续打印字节进度），并在命令执行期间每隔数秒轮询远程文件大小向用户汇报，避免干等 echo。

### 性能与可靠性

- 训练本身为 10 reps × 20 epochs，属正常计算负载；stingy 分区 A100 可能排队，属预期。
- 日志轮询仅读前若干行（env ok / 首个 epoch loss），不反复拉取全部日志，控制 I/O 开销。
- 提交前用 `squeue -u sychan552` 确认无冲突 job 在跑。

## 实现注意事项

- **blast radius 控制**：仅提交训练，不改动任何已上传文件、不删 checkpoints。
- **日志复用**：读取 `logs/train_L52-<jobid>.out` 验证，复用脚本既有输出格式。
- **进度汇报**：大文件 scp 采用 `scp -v` + 后台轮询远程 `ls -la` 大小，每几秒反馈。

## 架构设计

现有项目架构不变（HPC scratch 工作区 + SLURM 调度 + 本地控制）。本次仅触发训练流水线第一步，后续推理/绘图在训练完成后另轮执行。

## 目录结构

本次不新增/修改本地文件。仅涉及 HPC 远程执行：

```
/home/sychan552/scratch/MLFLU/
├── scripts/train_q1_L52.sh   # 已上传，提交目标
├── logs/                     # 训练日志输出目录（脚本已指定绝对路径）
└── checkpoints/              # 训练完成后生成 best_miflu_L52.pth（旧 pth 并存）
```