# MLFlu L52 训练进度轮询 — 执行记录

## 2026-08-15 (hourly poll)
- 尝试 SSH 登录检查 job 504263 进度，失败。
- `burgundy.hpc.cityu.edu.hk` → 连接超时（DNS 可解析，但 22 端口连不上）。
- 备用 `hpclogin02.hpc.cityu.edu.hk` / `hpclogin01.hpc.cityu.edu.hk` / `burgundy.cityu.edu.hk` → 均无法解析主机名。
- 判断：本机当前不在 CityUHK VPN / 校园网内，无法直达 HPC。非作业问题。
- 三条查询（squeue / log tail / checkpoint）均未执行成功。
- 结论：本次轮询无有效进度数据，待网络恢复后重试。
