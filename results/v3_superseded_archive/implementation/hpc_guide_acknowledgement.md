# HPC Guide acknowledgement

The canonical local `HPC_GUIDE.md` was read in full before any SSH, transfer, queue inspection, deployment, or `sbatch` action in this remediation turn.

- SHA-256: `1cd21a655907d137914c695bf04637d8da2f09358a0732c961e739dd8e74c167`
- Size: 22,651 bytes
- Lines: 322
- Modified UTC: 2026-09-01T10:32:08.4600965Z

Binding safety rules recorded from the guide:

- Burgundy login nodes may only inspect/hash/transfer small files, submit `sbatch`, poll `squeue`/`sacct`, or run a controller that never imports Torch or loads data/models.
- Real model loading, Torch/CUDA, checkpoint restore, forward/gradient, training, inference, evaluation, and batch computation must run on Slurm compute nodes.
- Use `stingy`, `--gres=gpu:a100:1`, and a time limit no greater than `04:00:00`; bare `--gres=gpu:1` is forbidden.
- `stingy` permits one running and one pending job per user, so pilots must be submitted serially after terminal-state validation.
- HPC project root is `/home/sychan552/scratch/CHATTIME/Chattime/`; cache root is `/gpfs1/scratch/sychan552/CHATTIME/.cache`.

HPC access remains blocked until the local incident, paper-equivalence, model-free static, license/asset, source-freeze, and deployment Gates pass.
