# T6_GPU_UPDATE.md — TASK 6 real GPU measurement (MIFlu)

**Date:** 2026-11-06
**Status of this update:** GPU measurement **COMPLETED for MIFlu only**. Overall TASK 6
status is `PARTIAL (IMPROVED)` — see the appended "UPDATE 2026-11-06" section of
`T6_VERDICT.md`. Five of six model rows still lack VRAM; Chronos/TimesFM remain BLOCKED.
This is **ONE cell (L=36, seed=2023)**, **NOT** the full 1120-cell panel. No full-1120
Pareto is claimed.

---

## 1. Job identity (verified by main agent; raw logs shipped down via scp)

| field | value | source log |
|---|---|---|
| sbatch job ID | **744532** | `env_probe_gpu_v8b.txt`, `t6_gpu_v8b_744532.out` |
| job name | `t6_res_gpu_v8b` | given by main agent; `t6_gpu_v8b_744532.out` header |
| partition | `stingy` | `env_probe_gpu_v8b.txt` (`SLURM_JOB_PARTITION=stingy`) |
| node | **gpu-a100-05** | `env_probe_gpu_v8b.txt` (`SLURM_JOB_NODELIST=gpu-a100-05`) |
| GPU | **NVIDIA A100-SXM4-80GB** (81920 MiB total, UUID `GPU-cf93ded8-653b-23d0-25ec-18d7496c3a80`) | `nvidia_smi_L_gpu_v8b.txt`, `gpu_identity_v8b.txt`, `nvidia_smi_sample_v8b.csv` |
| NVIDIA driver | **580.167.08** | `gpu_identity_v8b.txt` |
| CUDA toolkit / runtime version | **NOT_MEASURED** (not logged in any of these logs; only the driver version above is present) | — |
| `CUDA_VISIBLE_DEVICES` | `0` | `env_probe_gpu_v8b.txt` |
| Slurm state | COMPLETED | main agent (`sacct`); `t6_gpu_v8b_744532.out` |
| START (UTC) | **2026-11-06T15:30:57Z** | `t6_gpu_v8b_744532.out` line 1 / `env_probe_gpu_v8b.txt` `utc=` |
| END (UTC) | **2026-11-06T15:32:01Z** | `t6_gpu_v8b_744532.out` line 37 (main agent: COMPLETED at 15:32:01Z) |
| wall span | ~64 s | derived from START/END |

Sampling window in `nvidia_smi_sample_v8b.csv` is node-local time (UTC+8):
`2026/11/06 23:30:57.834` → `23:32:00.196`, i.e. 15:30:57Z → 15:32:00Z UTC,
consistent with the Slurm START/END.

---

## 2. Exact command

`/usr/bin/time -v` wrapped the following (verbatim `Command being timed:` from
`time_v_gpu_forward_v8b.txt` line 1):

```bash
/usr/bin/time -v timeout 600s /gpfs1/home/sychan552/.conda/envs/mlflu_hpc/bin/python -u /gpfs1/scratch/sychan552/stage5_a2_durable/code/export_miflu_all7.py --cells 36:2023 --ckpt /gpfs1/home/sychan552/stage5_a2_durable/author_runs/ckpt_L36_s2023/best_miflu_L36.pth --out-dir /gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/gpu_forward_out_v8b --tag t6v8b --device cuda
```

GPU VRAM sampling (run alongside, `-l 1` = 1 s interval):

```bash
nvidia-smi --query-gpu=timestamp,name,memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits -l 1
```

**Hard-rule note (AGENTS.md RULE 1):** this real model forward ran **inside sbatch on the
compute node**, NOT on the Burgundy login node. The login node was used only for light
`scp`/`ssh`/`tar` of small text logs (one connection, no retry loop). No `import torch`,
no checkpoint load, no model work ran on the login node during this update.

---

## 3. Exit codes and completion signals

`exit_codes_gpu_v8b.txt`:

```
nvidia_smi_L rc=0
gpu_identity rc=0
gpu_forward rc=0
peak_vram_derivation rc=0
```

Additional completion evidence:

- `time_v_gpu_forward_v8b.txt`: `Exit status: 0`
- `gpu_forward_v8b.out` / `t6_gpu_v8b_744532.out`: `[PASS] all requested cells exported`
- `gpu_forward_v8b.err`: only a benign `torch.load(weights_only=False)` FutureWarning; no error.
- `nvidia_smi_sample_v8b.err`: empty (0 B).
- `peak_vram_v8b.txt`: `status=MEASURED`.

---

## 4. MEASURED numbers (all traced to raw logs)

### 4.1 Peak VRAM

| metric | value |
|---|---|
| `peak_vram_mib` | **4816 MiB** (`memory.used`) |
| `min_vram_mib` | 16 MiB |
| `sample_lines` (n) | **63** |
| `gpu_names` | `NVIDIA A100-SXM4-80GB` |
| `peak_source` | `nvidia-smi memory.used MiB n_samples=63` |
| `status` | MEASURED |

Sources: `peak_vram_v8b.txt`, `t6_gpu_v8b_744532.out` (lines 30–36), and independent
re-derivation from `nvidia_smi_sample_v8b.csv` (63 rows, `max(memory.used)=4816`,
`min=16`, single GPU name). No value was invented.

### 4.2 Real model-forward wall time

`/usr/bin/time -v`, `time_v_gpu_forward_v8b.txt`:

```
Elapsed (wall clock) time (h:mm:ss or m:ss): 1:02.94   -> 62.94 s
User time (seconds): 24.55
System time (seconds): 2.34
Percent of CPU this job got: 42%
Maximum resident set size (kbytes): 1059100
Exit status: 0
```

**Recorded as `real_model_forward_wall_s = 62.94`** in `RESOURCE_MEASUREMENTS.csv`
(new clearly-labelled column, MIFlu row only).

**Interpretation (important):** 62.94 s is the **whole-process wall clock for ONE cell's
export** (data load + checkpoint load + GPU forward over all windows + CSV/NPZ/results
writing), **NOT** a repeated per-forward inference latency. `true_model_forward_latency_ms`
and every `inference_latency_*` column therefore remain `NOT_MEASURED` / NPZ-scoring-path
labelled. The NPZ scoring-path latency rows stay explicitly marked "NOT a model forward pass".

### 4.3 Model output correctness (from the real forward)

- `[PASS] all requested cells exported`
- `test MSE_7var_z = 1.624383`
- `test MSE_ILITOTAL_z = 3.324371`, `MAE_ILITOTAL_z = 1.158758`
- `[TimeEmbedder]` / `[ForecastingLLM]` shapes printed, `loaded state_dict (104 tensors)`, `trainable=2,060,580`
- `=== L=36 seed=2023 ===`, `cells=1`, `device=cuda`

### 4.4 Software versions recorded in the CSV

- **Python 3.9.25** — measured in `env_probe_gpu_v8b.txt` (`python_V=Python 3.9.25`).
- **torch 2.5.1** — project conda env `mlflu_hpc` (recorded in `versions.json` from CPU job
  744239); the GPU job logs do not print a torch version string.
- **NVIDIA driver 580.167.08** — `gpu_identity_v8b.txt`.
- **CUDA toolkit / runtime version** — `NOT_MEASURED` (not logged in these 12 files).
- GNU time 1.9 (from the original v8 `software_versions` cell).

---

## 5. Output NPZ / files produced on HPC

Out-dir: `/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/gpu_forward_out_v8b/`

**Prediction NPZ:**

```
/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/gpu_forward_out_v8b/pred_miflu_L36_t6v8b.npz
```

Also written in that out-dir: `predictions_miflu_L36_t6v8b.csv`,
`results_miflu_L36_t6v8b.csv`, `manifest_miflu_L36_t6v8b.json`.

These HPC outputs were **not** copied down (only the small text logs were scp'd); their
existence/contents are reported from `gpu_forward_v8b.out` / `t6_gpu_v8b_744532.out`.

---

## 6. Raw logs added to `v8/resource_logs/` + SHA-256

HPC source dir: `/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/logs/`
All 12 files were scp'd into `HANDOFF_20261105/v8/resource_logs/` with filenames preserved.
Hashes are SHA-256 of the local copies; the 9 files listed in the HPC-side
`logs_manifest_gpu_v8b.sha256` match byte-for-byte. These 12 lines were **appended** to
`v8/resource_logs/SHA256SUMS.txt` (append-only; the original 36 lines are unchanged).

| local log (under `HANDOFF_20261105/v8/resource_logs/`) | size | SHA-256 |
|---|---|---|
| `env_probe_gpu_v8b.txt` | 170 B | `081CD3DCB6888976FFC74C40B68484CE7D39BEF5850FA64E3A7708672415E755` |
| `nvidia_smi_L_gpu_v8b.txt` | 78 B | `92EAB43EEF950FB27174C89C6E7FA210EDEDEEB0BA3B88088DB4D0BD7231AC6A` |
| `gpu_identity_v8b.txt` | 45 B | `98A1B6D623927FADF4836790DE7101C18E591DA9B0ADDA63D2A3F86355E73AEA` |
| `nvidia_smi_sample_v8b.csv` | 3899 B | `B63BEF7E31CFE25605DACC8156FC70AD61C3AB749792F452CE44013F30908468` |
| `nvidia_smi_sample_v8b.err` | 0 B | `E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855` |
| `time_v_gpu_forward_v8b.txt` | 1091 B | `BE05530797EFDC04DBB9006BE0AE33EDEFCC4239BB442E8F74D1C699D2DF7BE2` |
| `gpu_forward_v8b.out` | 1439 B | `105717D9ED796F27BDF1BF098829AA9D371F6D7CEF6C42295F45A827661E5602` |
| `gpu_forward_v8b.err` | 990 B | `AEF97A5C01976B268734DC4EC95BCAF25D6B11F7450CB552E8FC828654A2DF07` |
| `peak_vram_v8b.txt` | 151 B | `A3CAAE87D2EB8A88B1B3CE5B544A596DB7362F7100AD9856BCABB1F2846B1116` |
| `exit_codes_gpu_v8b.txt` | 79 B | `FA701FE3D7C55DF6CD9EA01BDFD4C62124D6B0477B6916861187F9161A3EBF95` |
| `logs_manifest_gpu_v8b.sha256` | 1235 B | `137F2B5146EA0685420C1B68585C9C3215E544E5CB8F5F7A99E6CFC021E3BDD9` |
| `t6_gpu_v8b_744532.out` | 2780 B | `04C0F4F3A51E96EB342BF126B5620D2726C79A6FDCD4D9E55329A4057E287C4D` |

`nvidia_smi_sample_v8b.err` is empty (0 B) → its SHA-256 is the well-known empty-file
digest. `exit_codes_gpu_v8b.txt`, `logs_manifest_gpu_v8b.sha256` and
`t6_gpu_v8b_744532.out` are not listed in the HPC manifest and were hashed locally.

---

## 7. Scope (explicit)

- This measurement is **ONE cell: L=36, seed=2023** (`--cells 36:2023`, `cells=1`).
- It is **NOT** the full 1120-cell panel. `scope` stays `subset_only_not_full_1120`
  on every CSV row. **No full-1120 Pareto is claimed.**
- It covers **MIFlu only**. No GPU measurement job ran for any other model.
- The 62.94 s wall clock is whole-process time for one export, not a benchmark of
  repeated inference latency.

---

## 8. What is STILL NOT MEASURED (explicit list)

1. **Peak VRAM for the other 5 subset models** — NLinear, PatchTST,
   `DeepSeek-R1-Distill-Qwen-1.5B (frozen language encoder)`, Chronos, TimesFM.
   They remain `peak_vram_mib = NOT_MEASURED` with the reason
   **"no GPU measurement job ran for this model"**. No VRAM was invented for them.
   (Recorded in the new `real_model_forward_wall_s` column and kept in their existing
   `vram_source` cells.)
2. **Repeated per-forward inference latency for ALL 6 models** — warmup/repeat timing
   of an actual neural forward pass was not performed. Only ONE whole-process wall clock
   (62.94 s, MIFlu, one cell) exists. `true_model_forward_latency_ms` stays
   `NOT_MEASURED` for every row. The existing `inference_latency_*` numbers are
   **NPZ scoring-path latency ONLY, explicitly NOT a model forward pass**.
3. **Foundation models Chronos / TimesFM** — still `BLOCKED / NOT_EXECUTED`
   (TASK 2 prerequisites missing: no full pinned weights, no isolated HPC env
   `/home/sychan552/.venvs/mlflu_fm`, no 1-cell pilot). No prediction NPZ, no wall time,
   no VRAM, no latency exist for them.
4. **Full 1120-cell / 28-arm Pareto** — NOT measured, NOT claimed.
5. **CUDA toolkit / runtime version** — not logged in these files (only the NVIDIA
   driver 580.167.08 is present); recorded as NOT_MEASURED rather than guessed.
6. **VRAM scaling / batch-size sweeps / multi-cell forward timing** — not performed.

---

## 9. Files changed in this update (all within the permitted scope)

| file | change |
|---|---|
| `v8/resource_logs/*_v8b*.txt/.csv/.sha256` + `t6_gpu_v8b_744532.out` | 12 new raw logs added (no existing files deleted) |
| `v8/resource_logs/SHA256SUMS.txt` | 12 lines appended (original 36 lines byte-identical) |
| `v8/RESOURCE_MEASUREMENTS.csv` | MIFlu row updated + new column `real_model_forward_wall_s`; other 5 rows' original 24 fields unchanged |
| `v8/T6_VERDICT.md` | appended "UPDATE 2026-11-06" section; overall status → `PARTIAL (IMPROVED)` |
| `v8/T6_GPU_UPDATE.md` | this new file |

**Updated CSV SHA-256:** `D609D57DCEB5FCBA6656A40A4576D87971F5371AC46AD6589754515C95BFCFCC`

Note: `SHA256SUMS.txt` line 1 still carries the **pre-update** CSV hash
`BDE9031F4FB2B91AA0321F71FC285CBE3DF8F254D2F2F631379D4EB2F73252CD`. Per the
append-only rule it was **not** rewritten; the hash above is the authoritative
SHA-256 of the current `RESOURCE_MEASUREMENTS.csv`.

Files deliberately NOT touched: `v8/TASK_LOG.md`, `v8/MESSAGE_TO_CHATGPT.md`,
`v8/packaging/*`, `v8/RETURN_V8/*`, `HANDOFF_20261105/final/*`, `HANDOFF_20261105/v7/*`,
`02_数字表格/*`.
