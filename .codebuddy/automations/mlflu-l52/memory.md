# MLFlu L52 训练进度轮询 — 执行记录

## 2026-08-15 (hourly poll)
- 尝试 SSH 登录检查 job 504263 进度，失败。
- `burgundy.hpc.cityu.edu.hk` → 连接超时（DNS 可解析，但 22 端口连不上）。
- 备用 `hpclogin02.hpc.cityu.edu.hk` / `hpclogin01.hpc.cityu.edu.hk` / `burgundy.cityu.edu.hk` → 均无法解析主机名。
- 判断：本机当前不在 CityUHK VPN / 校园网内，无法直达 HPC。非作业问题。
- 三条查询（squeue / log tail / checkpoint）均未执行成功。
- 结论：本次轮询无有效进度数据，待网络恢复后重试。

## 2026-09-19 (hourly poll)
- SSH 连通（burgundy → hpclogin02）。
- `sacct -j 504263`：状态 **COMPLETED**，ExitCode **0:0**，结束于 2026-08-14T21:13:04（运行 28m56s），干净退出，无失败。
- Checkpoint **已生成**：`/home/sychan552/scratch/MLFLU/checkpoints/best_miflu_L52.pth`（329 MB，Aug 14 21:12）。注意项目实际在 `scratch/MLFLU`（大写），非 `MLFlu_Q1`。
- 推理脚本就位：`/home/sychan552/scratch/MLFLU/scripts/infer_walkforward_L52.sh`。
- 结论：L52 训练**已完成**，可进入下一步。建议用户在 HPC 上 `cd /home/sychan552/scratch/MLFLU && sbatch scripts/infer_walkforward_L52.sh`。
- 提示：job 早已结束，本自动化后续轮询已无必要，可考虑暂停/停止该 hourly 任务。
