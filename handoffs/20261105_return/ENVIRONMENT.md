# ENVIRONMENT

## Local (Windows, analysis + CPU runtime)
- Python 3.9.0; numpy 1.26.4; pandas 2.2.3; scipy 1.13.1
- torch 2.6.0+cu124 (CPU used for the no-text test; CUDA not used locally)
- transformers 4.25.0; python-docx 1.2.0; PyMuPDF 1.26.5
- Cached GPT-2 in the user's normal HuggingFace cache (offline mode for the test)
- Full lock files: `environment/pip_freeze_local.txt`, `environment/python_local.txt`

## HPC (CityU Burgundy)
- `hpclogin02`, user `sychan552`; env
  `/gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python` (Python 3.9.25,
  torch 2.5.1 CUDA 11.8, transformers 4.57.6)
- Partitions observed: `gpu_a100` (6 nodes, MaxTime 5 days), `stingy`
  (34 nodes, MaxTime UNLIMITED but QOS wall 06:00:00 and 1 job/user),
  `tiny` (31 nodes, 5 days), `gpu_v100s` (6 nodes). See
  `logs/trackB_v2/quota.txt` and `live_squeue.txt`.
- Login node has no GPU; training runs only on compute nodes via Slurm.
- Account association `ga_bms_kk+` / `normal`; no QOS override was used.
- No SSH private key, password, token or secret is included anywhere in this
  return package.

## Data identity (measured; see `PROFILE_COMPARISON.md`)
- `author_966` (backbone/classical/encoder cells): 966 x 9,
  sha256 `31ffc1693de205ca8de5e966d40c93252e0a0076a212fffc54d1418e1a13b87a`
- `author_repo_966` (MIFlu cells): 966 x 8,
  sha256 `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5`
- The 7 MODEL CHANNELS are numerically identical (max abs diff 0.0). Byte
  hashes differ because metadata columns and column names differ.
- Boundaries 0/676/773/966; split 676/97/193; T=104; L in 24/36/48/60.
- Real CDC calendar / epiweek mapping NOT verified.
