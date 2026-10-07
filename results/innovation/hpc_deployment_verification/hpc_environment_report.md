# HPC environment report

Collected by `hpc_scripts/hpc_env_check.sh` (facts only — it submits nothing).
Verified script SHA-256 `746bdf56…b632c` and `bash -n` (rc=0) **before** execution.

| Item | Value |
|---|---|
| Hostname | `hpclogin02` (login node) |
| SLURM job | `SLURM_JOB_ID=none` |
| Slurm version | 23.11.10 |
| Deployment root | `/home/sychan552/scratch/CHATTIME/MIFlu_innovation_deployments/innov-v2.1_dc7ee964` |
| OS | `Linux 5.14.0-687.41.1.el9_8.x86_64` |
| Python | `/home/sychan552/.conda/envs/mlflu_hpc/bin/python` — **3.9.25** |
| torch | **2.5.1** |
| transformers | **4.57.6** |
| numpy / pandas / scipy | 2.0.1 / 2.3.3 / 1.13.1 |
| scikit-learn | 1.6.1 |
| statsmodels | **0.14.6** (present — the guide's historical missing-dep issue no longer applies) |
| matplotlib | 3.9.4 |
| CUDA available | **False** |
| CUDA device count | **0** |
| `nvidia-smi` | unavailable |

## GPU assessment — `LOGIN_NODE_GPU_NOT_EXPECTED`

The check ran on an **HPC login node with no GPU allocation**, so CUDA being
unavailable is expected and is **not** automatically a pilot-readiness failure.
**No A100 verification is claimed.** An A100 can only be observed inside an
allocated Slurm job or an approved interactive GPU allocation — neither was
requested or submitted in this turn.

## Strict-offline GPT-2 load

`TRANSFORMERS_OFFLINE=1`, `HF_HUB_OFFLINE=1`, `HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache`
→ **`gpt2_offline_load=OK`** (no download attempted).

## Pilot script syntax (`bash -n`)

`pilot_dlinear_L24_seed42.sh` · `pilot_gpt2_miflu_L24_seed42.sh` ·
`pilot_patchtst_L24_seed42.sh` · `pilot_itransformer_L24_seed42.sh` ·
`innovation_worker.sh` — **all OK**.

## Residual risk to be validated BY the pilot (not assumed away)

The HPC stack differs from the local smoke environment
(local: torch 2.6.0+cu124 / transformers 4.25.0 / numpy 1.26.4;
HPC: torch 2.5.1 / transformers 4.57.6 / numpy 2.0.1). This is an environment
delta, not a source-integrity issue (source verification passed 69/69).
