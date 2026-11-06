# T6_VERDICT.md — TASK 6 (Resource measurements)

```
status: PARTIAL (IMPROVED)  [was, at 2026-11-06T13:59:46Z: COMPLETED (scoped deliverable produced) — with explicitly documented NOT_MEASURED cells and 2 BLOCKED models; ORIGINAL VERDICT (sections 1-9) RETAINED VERBATIM BELOW, NOT ERASED. See "UPDATE 2026-11-06 - GPU measurement COMPLETED for MIFlu" section.]
start_utc: 2026-11-06T13:45:13Z   # first HPC command (light squeue/sinfo/date)
end_utc:   2026-11-06T13:59:46Z   # file finalisation / hashes
primary_sbatch_job: 744239 (t6_res_cpu, COMPLETED, exit 0:0, 14 s)
other_job_ids: 744253 (t6_res_gpu, CANCELLED by this task), 744253 is the only other submitted ID
untouched_job: 743850 (wf_fix218) — RUNNING on gpu-a100-03 throughout, never cancelled / written to / interfered with
```

**What this verdict claims, precisely.** `HANDOFF_20261105/v8/RESOURCE_MEASUREMENTS.csv`
exists with 6 rows, 24 columns, a `scope` column (`subset_only_not_full_1120`),
4 rows with REAL measured numbers and 2 rows marked `BLOCKED / NOT_EXECUTED`.
Every numeric value traces to a raw log saved in `v8/resource_logs/`.
**No full-1120 Pareto is claimed; no VRAM or true model-forward latency is
fabricated.** `peak_vram_mib` and `true_model_forward_latency_ms` are
`NOT_MEASURED` for every row with an exact blocker.

---

## 1. Hard rules honoured (AGENTS.md)

- **RULE 1**: NO model inference / `torch.load` / `import torch` /
  `import transformers` / `from_pretrained` / recursive `du` / NPZ scan ran on
  the Burgundy login node. All Python, numpy NPZ work and `import torch`
  (in `record_versions.py`) ran **inside sbatch job 744239 on compute node
  `cpunode-034`**. Login node was used ONLY for `date`, `hostname`, `squeue`,
  `sacct`, `scontrol`, `sinfo`, short `ls`/`cat`/`sed`/`grep`, `mkdir`, `sbatch`,
  `scancel` (my own job), and small `scp`.
- **RULE 2**: one SSH connection per command, `timeout 25s` on every ssh,
  `-o ServerAliveInterval=0 -o ServerAliveCountMax=0 -o BatchMode=yes`, no retry
  loop (the single stingy resubmission is documented, not a rapid retry loop).
- **RULE 3**: job completion verified with `scontrol show job` + `sacct`, not
  `squeue -h` alone; `squeue -h` "Last update in …" artifact noted. No DONE
  label was trusted.
- **RULE 5**: no fabricated results. Everything unmeasured is `NOT_MEASURED`
  with the exact blocker. Chronos/TimesFM are `BLOCKED / NOT_EXECUTED`.
- Scope: writes ONLY into `v8/RESOURCE_MEASUREMENTS.csv`, `v8/resource_logs/`,
  `v8/T6_VERDICT.md` and HPC `/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/`.
  Job names all start `t6_res_`. No frozen CSV, checkpoint, prediction NPZ,
  PPTX, or any other project file was modified.

---

## 2. Exact commands and exit codes

Shared SSH prefix (used ONCE per command, no loop):
`timeout 25s ssh -o ServerAliveInterval=0 -o ServerAliveCountMax=0 -o BatchMode=yes sychan552@burgundy.hpc.cityu.edu.hk '<cmd>'`
SCP prefix: `timeout 60s scp -o ServerAliveInterval=0 -o ServerAliveCountMax=0 -o BatchMode=yes …`

| # | command (abbreviated only by the shared prefix / `$BASE` variable) | exit | stdout / stderr |
|---|---|---|---|
| C1 | local context reads: `AGENTS.md`, `NEXT_DEEPSEEK_PROMPT.md` (TASK 6), `v8/foundation/T2_VERDICT.md`, `v8/T5_VERDICT.md`, `v8/evidence/master_queue.tsv`, `02_数字表格/BENCH_EFFICIENCY.csv`, `BENCH_GPU_PROVENANCE.csv`, local NPZ shape probe | 0 | inline |
| C2 | `'date -u …; hostname; squeue -h -o "%i\|%j\|%T\|%M\|%R"; sinfo -h -p tiny -o "%n\|%t\|%c\|%m"'` | 0 | `2026-11-06T13:45:13Z hpclogin02` |
| C3 | `'scontrol show job 743850; sinfo -h -N -p gpu_a100; sinfo -h -N -p stingy; sinfo -h -p tiny'` | 0 | 743850 RUNNING, NodeList=gpu-a100-03, Partition=stingy |
| C4 | light path checks x5: queue dir + `master_queue.tsv` head + python env symlink; `expanded_runs/` dirs + 386 NPZ count + `paper_tables` + `wf_fix218/logs`; `shard0.log` head/tail; exact NPZ file paths + `grep -n` wall= lines; `ds_r1_distill_qwen1_5b_L24_s42/` contents | 0 | inline |
| C5 | local (Windows temp): write `record_versions.py`, `extract_wall.py`, `measure_latency.py`, `t6_res_cpu.sbatch`; `python -m py_compile …`; `bash -n t6_res_cpu.sbatch` | 0 | `PY_COMPILE_OK`, `BASH_N_OK` |
| C6 | `'mkdir -p $BASE/logs && ls -ld $BASE $BASE/logs'` | 0 | `MKDIR_OK` |
| C7 | `scp t6_res_cpu.sbatch record_versions.py extract_wall.py measure_latency.py …:$BASE/` | 0 | `SCP_OK` |
| C8 | `'cd $BASE && echo submit_utc=$(date -u …) && sbatch --parsable t6_res_cpu.sbatch'` | 0 | `submit_utc=2026-11-06T13:51:26Z` / `744239` |
| C9 | `'scontrol show job 744239; sacct -j 744239 --noheader -o …; ls -la $BASE/logs/'` | 0 | `COMPLETED`, `0:0`, `00:00:14`, 30 log files |
| C10 | `scp …:$BASE/logs/* → HANDOFF_20261105/v8/resource_logs/` | 0 | `SCP_LOGS_OK` |
| C11 | `'cd $BASE && echo submit_utc=$(date -u …) && sbatch --parsable t6_res_gpu.sbatch'` | 0 | `submit_utc=2026-11-06T13:54:48Z` / `744253` |
| C12 | `'scontrol show job 744253; scontrol show job 743850; sinfo -h -p gpu_a100; sinfo -h -N -p stingy; squeue -h -t RUNNING …'` | 0 | 744253 `PENDING Reason=Priority StartTime=2026-11-08T02:25:47Z`; 743850 RUNNING |
| C13 | `'echo scancel_utc=$(date -u …); scancel 744253; scontrol show job 744253; scontrol show job 743850'` | 0 | `scancel_utc=2026-11-06T13:56:49Z`, `scancel_rc=0`, 744253 `CANCELLED`, 743850 `RUNNING` |
| C14 | `'cd $BASE && echo submit_utc=$(date -u …) && sbatch --parsable t6_res_gpu_stingy.sbatch'` | **1** | `sbatch: error: QOSMaxSubmitJobPerUserLimit` / `Batch job submission failed: Job violates accounting/QOS policy (job submit limit, user's size and/or time limits)` — NO job id |
| C15 | single retry of C14 at `13:57:30Z` | **1** | identical QOS error — NO job id |
| C16 | `'{ date -u; scontrol show job 744253; scontrol show job 743850; sacct -j 744239,744253 …; squeue -u sychan552 …; } > $BASE/logs/gpu_attempts_state.txt'` | 0 | `STATE_CAPTURE_RC=0`, 3731 B |
| C17 | `scp …:$BASE/logs/gpu_attempts_state.txt → v8/resource_logs/` | 0 | `SCP_STATE_OK` |
| C18 | local: `python build_resource_csv.py` + `csv.DictReader` validation + `SHA256SUMS.txt` generation | 0 | 6 rows / 24 cols / all 17 required columns present |

**stdout / stderr paths (job 744239)**
- slurm stdout: `…/t6_res/logs/t6_res_cpu_744239.out` (120 B, empty stderr file)
- slurm stderr: `…/t6_res/logs/t6_res_cpu_744239.err` (0 B)
- per-step stderr: `versions.stderr.txt`, `wall_extraction.stderr.txt`,
  `npz_scoring_latency.stderr.txt` (all 0 B)
- step exit codes: `resource_logs/exit_codes.txt` — all `rc=0`
- `/usr/bin/time -v`: `time_v_versions.txt`, `time_v_wall.txt`, `time_v_latency.txt`
  (all `Exit status: 0`; max RSS 340124 / 16644 / 46256 kbytes)

**sbatch JOB IDs and authoritative states** (`scontrol show job` + `sacct`)
| ID | name | partition | state | exit | elapsed | node |
|---|---|---|---|---|---|---|
| 744239 | `t6_res_cpu` | tiny | COMPLETED | 0:0 | 00:00:14 | cpunode-034 |
| 744253 | `t6_res_gpu` | gpu_a100 | CANCELLED (by this task) | 0:0 | 00:00:00 | none (never started) |
| 743850 | `wf_fix218` | stingy | RUNNING (untouched) | — | ~02:08 at 13:56Z | gpu-a100-03 |

`t6_res_gpu_stingy` produced **no job ID** (rejected at submit, rc=1).

---

## 3. What was ACTUALLY measured (job 744239, tiny, CPU-only)

Environment (`resource_logs/env_probe.txt`, `versions.json`):
`cpunode-034`, `2026-11-06T13:51:27Z → 13:51:41Z`, `SLURM_JOB_PARTITION=tiny`,
`CUDA_VISIBLE_DEVICES=<unset>`, `ReqTRES=cpu=4,mem=8G,node=1` (no GPU gres),
Python **3.9.25**, numpy **2.0.1**, pandas **2.3.3**, torch **2.5.1**
(`torch.cuda.is_available=False` on this node), GNU time **1.9**.
`import torch` happened ONLY inside this compute-node job.

**A. REAL training wall times** — extracted from the queue logs, with exact
source file + line number. Raw logs: `training_wall_extraction.tsv` (1082 rows
with `wall=`), `training_wall_targets.tsv`, `training_wall_evidence.json`.
Corroboration: `shard0_wall_extraction.tsv` (148 complete UTC START/END pairs
from job 743850's own `wf_fix218/logs/shard0.log`, read-only).

| subset model | representative cell | wall_s | source | n cells | mean_s |
|---|---|---|---|---|---|
| MIFlu | `miflu_L36_s2027` | **581** | `master_queue.tsv:L2` (`gate=1.400796 wall=581s`, job 720105) | 34 | 515.65 |
| NLinear | `wf_f1_nlinear_L24_s42` | **6** | `master_queue.tsv:L989` (`wall=6s`, job 724404) | 45 | 4.69 |
| PatchTST | `wf_f1_patchtst_L24_s42` | **7** | `master_queue.tsv:L1001` (`wall=7s`, job 724765) | 45 | 7.20 |
| deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B (one frozen language encoder, `llm_cell`) | `ds_r1_distill_qwen1_5b_L24_s42` | **24** | `master_queue.tsv:L39` (`wall=24s`, job 721227) | 12 | 16.25 |

These are **historical, already-measured queue wall times**, NOT re-timed by T6.
Historical GPU provenance (A100-SXM4-80GB) is in
`02_数字表格/BENCH_GPU_PROVENANCE.csv`, **not re-measured here**.

**B. NPZ scoring-path latency (explicitly NOT a model forward pass)** —
`resource_logs/npz_scoring_latency.tsv` / `.json` / `.out`, wrapped by
`/usr/bin/time -v` (`time_v_latency.txt`). Operation:
`np.mean((pred - target) ** 2)` on `(W,7,L)=(170,7,24)` float32 arrays from
existing prediction NPZs, warm-up **5**, repeats **50**, timed with
`time.perf_counter()`.

| subset model | mean_ms | std_ms | batch | precision | NPZ sha256 |
|---|---|---|---|---|---|
| MIFlu | 0.029084 | 0.001775 | 170 windows | float32 | `55e95632…1989` |
| NLinear | 0.029651 | 0.001479 | 170 windows | float32 | `73c39bb3…acc5` |
| PatchTST | 0.028653 | 0.001426 | 170 windows | float32 | `25bb54a3…2d48` |
| DeepSeek-R1-Distill-Qwen-1.5B | 0.028685 | 0.001602 | 170 windows | float32 | `fffadc5b…8706` |

Full NPZ paths + full SHA-256 in `npz_scoring_latency.tsv`. These are CPU
vectorised-MSE numbers; they are **labelled `NPZ scoring-path latency ONLY`,
NOT a model forward pass**, and must not be reported as neural inference.

---

## 4. What is NOT_MEASURED and the exact blockers

1. **`peak_vram_mib` = NOT_MEASURED for ALL 6 rows.**
   - Primary reason (as required): **"no GPU allocated in this job"** — job
     744239 used `--partition=tiny` with no `--gres=gpu`; `nvidia-smi` was not
     present (`resource_logs/nvidia_smi_L.txt`: "command not found on this node
     (CPU-only tiny partition)"); `gpu_probe.txt`: `GPU_PRESENT=0`, sampling
     SKIPPED; `peak_vram_mib.txt` records the reason verbatim. Sampling with
     `nvidia-smi -l 1` was therefore **correctly not run** on the CPU job.
   - Attempt A: `744253 t6_res_gpu` (`--partition=gpu_a100 --gres=gpu:a100:1
     --exclude=gpu-a100-03`) was PENDING `Reason=Priority`, predicted
     `StartTime=2026-11-08T02:25:47Z` (~2 days out) → **time-boxed**, cancelled
     by this task at `13:56:49Z` (`scancel_rc=0`). It never ran, produced no
     `nvidia-smi` samples.
   - Attempt B: `t6_res_gpu_stingy` (`--partition=stingy --gres=gpu:a100:1
     --exclude=gpu-a100-03`) was rejected TWICE at submit with
     `sbatch: error: QOSMaxSubmitJobPerUserLimit` / `Job violates accounting/QOS
     policy (job submit limit, user's size and/or time limits)` (rc=1, no job
     ID). One single retry, not a loop.
   - Evidence: `resource_logs/gpu_attempts_state.txt` (HPC-side authoritative
     `scontrol`/`sacct`/`squeue` snapshot), `resource_logs/t6_gpu_attempts_transcript.txt`.
   - **No GPU job ever started → no VRAM samples exist → NOT_MEASURED.**

2. **True model-forward / neural inference latency = NOT_MEASURED for ALL 6
   rows.** Only the NPZ scoring path was measured (§3B). The optional GPU job
   that would have run a real MIFlu forward from the existing checkpoint
   `author_runs/ckpt_L36_s2023/best_miflu_L36.pth` via
   `export_miflu_all7.py --device cuda` never started (reasons above). No
   synthetic benchmark was substituted.

3. **`gpu_model`**: `NONE (job 744239: --partition=tiny, no --gres=gpu;
   nvidia-smi not present)` for the 4 measured rows; `NOT_MEASURED` for
   Chronos/TimesFM. The historical A100-SXM4-80GB provenance is cited as
   context only, not re-measured.

4. **`software_versions`** for Chronos/TimesFM: `NOT_MEASURED (no isolated FM
   env created)`.

5. **`batch` / `precision`** for Chronos/TimesFM: `NOT_MEASURED` (no prediction
   NPZ, no pilot).

---

## 5. BLOCKED rows (Chronos, TimesFM)

Both rows in `RESOURCE_MEASUREMENTS.csv` are `status=BLOCKED / NOT_EXECUTED`
with every resource field `NOT_MEASURED`. Exact reason (verbatim from the CSV):

> TASK 2 is BLOCKED (`v8/foundation/T2_VERDICT.md` §6/§8): no full pinned
> weights downloaded, no isolated HPC env (`/home/sychan552/.venvs/mlflu_fm`),
> no 1-cell pilot. No prediction NPZ, no wall time, no VRAM, no latency exist.

Evidence: `v8/foundation/T2_VERDICT.md`,
`v8/foundation/FOUNDATION_MODEL_PROVENANCE.md`,
`v8/foundation/FOUNDATION_ROSTER.csv`. No number was substituted.

---

## 6. Explicit list of MISSING cells / models

- **Chronos**: ALL resource dimensions missing (training wall, peak VRAM,
  inference latency, batch, precision, GPU model, software versions) —
  `BLOCKED / NOT_EXECUTED`, TASK 2 prerequisite missing.
- **TimesFM**: same as Chronos.
- **MIFlu, NLinear, PatchTST, DeepSeek-R1-Distill-Qwen-1.5B**: missing
  `peak_vram_mib`, `true_model_forward_latency_ms`, and the GPU model of a real
  forward measurement. Only training wall + NPZ scoring-path latency measured.
- **peak VRAM sampling (`nvidia-smi -l 1`)**: never executed at all (no GPU job).
- **The other 7+ of the 11 frozen language encoders, and the remaining ~22
  benchmark arms**: not in the representative subset; no resource measurements.
- **Full 1120-cell / 28-arm Pareto**: **NOT claimed, NOT measured.** `scope =
  subset_only_not_full_1120` on every row. Only 4 of 6 subset models were
  measured, on 1 representative cell each.
- **GPU job IDs that produced data**: only `744239`. `744253` and both stingy
  attempts produced no measurement.

---

## 7. Output files + SHA-256

Primary deliverables:

| path | SHA-256 |
|---|---|
| `HANDOFF_20261105/v8/RESOURCE_MEASUREMENTS.csv` | `BDE9031F4FB2B91AA0321F71FC285CBE3DF8F254D2F2F631379D4EB2F73252CD` |
| `HANDOFF_20261105/v8/resource_logs/SHA256SUMS.txt` (manifest, self-excluded) | `6EE6C7E464032FBB6E4E7E7D29A3FA6466B5B19E4CF7524C0A137C60A965F890` |
| `HANDOFF_20261105/v8/T6_VERDICT.md` | this file — own hash is self-referential, reported in the task final answer (not embedded) |

Full per-file manifest (36 paths, uppercase SHA-256 + byte size):
`HANDOFF_20261105/v8/resource_logs/SHA256SUMS.txt`. Key ones:

```
BDE9031F4FB2B91AA0321F71FC285CBE3DF8F254D2F2F631379D4EB2F73252CD  RESOURCE_MEASUREMENTS.csv (12484 B)
22C6A0E74F29CAC7BD988564609A236161090C1FF954E2DAE077358EE09DF756  env_probe.txt (472 B)
8DDF43EBB50AD2513D3E3F42CB48A1E114638BE2D717EACAE0EB22D440D85310  versions.json (391 B)
BD4BE186B5C66FC6FEC1DD1C8B6F9CBFD8C4EFD64A7BF08665D2C8CF9971222E  peak_vram_mib.txt (192 B)
63666D98439FFA45C413558F60E3F5B403CA754A2449E51AEA70E6F4D66D9586  gpu_probe.txt (98 B)
F05286EA60938B8AE50E7DA4CE62000F5B1103DDC3F63A7E62086B3FC3743F73  training_wall_targets.tsv (910 B)
82EE805AEB49C445C3F1F4F5DF0E49E68EC62AF49463F5732E6642987724C4D0  training_wall_extraction.tsv (211175 B)
CBF920A1CE6711CA5032A8A2F83C300B451686F171CD9EA9D9AEBF3CA8843DF0  shard0_wall_extraction.tsv (23230 B)
82F271C8EB41F4427737B7EE2296B39F31EB99C271227FDC2D2688BA1DBD9CA2  npz_scoring_latency.tsv (1223 B)
6ACA94912819B0F025FACD178461F4CBDDB4DCA13E5FD28E4CAF5BE527CD4735  npz_scoring_latency.json (10277 B)
2896D2806804C00436393D903E006B636D93BEA9DCE3E0B1C6D14E27BAAE89BD  time_v_latency.txt (854 B)
44D9EAB6724BDB1BE667CAA40C7A786AF90B77517344C57086AB7FC32998C2C9  gpu_attempts_state.txt (3731 B)
09448382B1A63E835C3E5660ADBE2337A23A8DB63FD5E5F3D803E05E15D55340  t6_gpu_attempts_transcript.txt (4316 B)
6FF50F6CB068A6E24C0011DF3FDD6A3DC1A7ABC7AB5E58C4E8FF63CFC8FC707E  submitted_t6_res_cpu.sbatch (6494 B)
```

The HPC-side authoritative manifest written by job 744239 itself is
`resource_logs/logs_manifest.sha256` (`6A20150DC1D2B34D86E3A4FC6EBFBB365BB46FD009E7A7B9E07961CFC95D67C9`).

---

## 8. Evidence index (all under `v8/resource_logs/`)

| file | content |
|---|---|
| `env_probe.txt`, `versions.json`, `job_timing.txt`, `exit_codes.txt`, `scontrol_job.txt` | host/date/python versions/step exit codes/job allocation (no GPU gres) |
| `nvidia_smi_L.txt`, `gpu_probe.txt`, `peak_vram_mib.txt` | GPU absence + verbatim NOT_MEASURED reason |
| `time_v_versions.txt`, `time_v_wall.txt`, `time_v_latency.txt` | `/usr/bin/time -v` raw (wall, max RSS, exit 0) |
| `training_wall_extraction.tsv`, `training_wall_targets.tsv`, `training_wall_summary_all_models.tsv`, `training_wall_evidence.json` | real `wall=` cells with line numbers |
| `shard0_wall_extraction.tsv` | 148 UTC START/END pairs from job 743850's log (corroboration) |
| `npz_scoring_latency.json`, `.tsv`, `.out` | warm-up 5 / repeat 50 per-iteration ms, shapes, dtypes, NPZ sha256 |
| `gpu_attempts_state.txt`, `t6_gpu_attempts_transcript.txt` | GPU attempts A/B, QOS errors, scancel, 743850 untouched |
| `submitted_*.sbatch`, `submitted_*.py`, `build_resource_csv.py` | exact submitted commands / CSV builder |
| `t6_res_cpu_744239.out`, `.err` | slurm stdout/stderr |
| `SHA256SUMS.txt` | full output hash manifest |

---

## 9. Remaining / smallest next actions

1. **Peak VRAM + true model-forward latency**: re-run
   `t6_res_gpu.sbatch` (or `t6_res_gpu_stingy.sbatch`) when a free A100 is
   actually allocatable. The script is ready and uses the existing checkpoint
   `author_runs/ckpt_L36_s2023/best_miflu_L36.pth`; it writes ONLY into
   `t6_res/`. Submit with `--exclude=gpu-a100-03` while job 743850 still runs.
   Smallest blocker to clear: `QOSMaxSubmitJobPerUserLimit` and the
   `gpu_a100` priority backlog (predicted start 2026-11-08T02:25:47Z).
2. **Chronos / TimesFM**: complete TASK 2 prerequisites — download full pinned
   weights locally, tar + SHA-256 + `scp` to `/gpfs1/scratch/sychan552/models/`,
   create isolated env `/home/sychan552/.venvs/mlflu_fm`, run 1-cell pilot via
   `sbatch`. Until then these rows stay `BLOCKED / NOT_EXECUTED`.
3. **Scope**: if a full picture is needed, extend the subset; do NOT present
   these 4 measured cells as a full-1120 Pareto.
4. Downstream TASK 7 (v8 docs) / TASK 8 (package) were **not** touched.

---

## UPDATE 2026-11-06 — GPU measurement COMPLETED for MIFlu

> This section APPENDS to (and does NOT erase) the original verdict above. The
> original verdict (header + sections 1-9, `status: COMPLETED` as of
> 2026-11-06T13:59:46Z) is retained verbatim and describes the state BEFORE the
> real GPU job completed.

**CURRENT OVERALL STATUS: `PARTIAL (IMPROVED)`.** The `status:` field in the header
above is updated to this value (the original `COMPLETED` value is kept inline there as
historical context). It is **still not `COMPLETED`** because **5 of the 6 model rows
still lack VRAM** and **Chronos / TimesFM remain `BLOCKED / NOT_EXECUTED`**.

### What changed on 2026-11-06

A REAL GPU MIFlu forward ran and COMPLETED:

| field | value |
|---|---|
| sbatch job | **744532** `t6_res_gpu_v8b` |
| partition / node | `stingy` / **gpu-a100-05** |
| GPU | **NVIDIA A100-SXM4-80GB** (NVIDIA driver 580.167.08) |
| START / END (UTC) | 2026-11-06T15:30:57Z / 2026-11-06T15:32:01Z |
| Slurm state | COMPLETED |
| exit codes | `nvidia_smi_L rc=0`, `gpu_identity rc=0`, `gpu_forward rc=0`, `peak_vram_derivation rc=0`; `/usr/bin/time -v` `Exit status: 0`; `[PASS] all requested cells exported` |
| **peak_vram_mib** | **4816 MiB** (`nvidia-smi memory.used`, **n = 63** samples, min 16 MiB, `status=MEASURED`) |
| **real forward wall time** | **62.94 s** (`/usr/bin/time -v` "Elapsed (wall clock) time" = `1:02.94`) |
| model result | `test MSE_7var_z = 1.624383` |
| output NPZ | `/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t6_res/gpu_forward_out_v8b/pred_miflu_L36_t6v8b.npz` |

Exact command, full 12-log SHA-256 table, and the explicit "still not measured" list
are in `v8/T6_GPU_UPDATE.md`. The 12 raw logs were added to `v8/resource_logs/` and
their hashes were APPENDED to `v8/resource_logs/SHA256SUMS.txt` (original 36 lines
byte-identical, nothing deleted).

### CSV changes (`v8/RESOURCE_MEASUREMENTS.csv`)

- **MIFlu row ONLY**: `peak_vram_mib=4816`;
  `vram_source=t6_res_gpu_v8b job 744532 nvidia-smi memory.used sampling (63 samples, gpu-a100-05, A100-SXM4-80GB)`;
  `gpu_model=NVIDIA A100-SXM4-80GB`; `software_versions` also records Python 3.9.25,
  torch 2.5.1 and NVIDIA driver 580.167.08 (CUDA toolkit/runtime version NOT logged
  -> NOT_MEASURED).
- Added a new clearly-labelled column **`real_model_forward_wall_s = 62.94`** for MIFlu;
  the other 5 rows get `NOT_MEASURED (no GPU measurement job ran for this model)`.
- `scope` stays **`subset_only_not_full_1120`** on every row. **EXPLICIT: this is ONE
  cell (L=36, seed=2023), NOT the full 1120-cell panel; NO full-1120 Pareto is claimed.**
- NPZ scoring-path latency rows remain clearly labelled **NOT a model forward pass**;
  `true_model_forward_latency_ms` remains NOT_MEASURED (the 62.94 s is whole-process
  wall clock for one export, NOT a repeated per-forward inference latency).
- NLinear / PatchTST / DeepSeek-R1-Distill-Qwen-1.5B encoder / Chronos / TimesFM:
  VRAM NOT invented — all remain `NOT_MEASURED` (no GPU measurement job ran for them).
- Updated CSV SHA-256: `D609D57DCEB5FCBA6656A40A4576D87971F5371AC46AD6589754515C95BFCFCC`
  (SHA256SUMS.txt line 1 retains the pre-update hash per the append-only rule).

### STILL NOT MEASURED (unchanged blockers)

1. Peak VRAM for the other 5 subset models — no GPU measurement job ran for them.
2. Repeated per-forward inference latency for ALL 6 models — not measured.
3. Chronos / TimesFM — BLOCKED (TASK 2 prerequisites missing: no pinned weights,
   no isolated HPC env, no 1-cell pilot).
4. Full 1120-cell / 28-arm Pareto — NOT measured, NOT claimed.
5. CUDA toolkit / runtime version — not logged; only driver 580.167.08 is present.

Because items 1-3 remain, the overall status is `PARTIAL (IMPROVED)`, not `COMPLETED`.


---

## FINAL UPDATE 2026-11-06 — all six representative models MEASURED

`status: COMPLETED (all six representative models measured)`. The earlier `PARTIAL (IMPROVED)` and the original "all VRAM NOT_MEASURED" verdicts are SUPERSEDED. Jobs 744897 (`t6_final_sweep`) and 744899 (`t6_miflu_fix`) measured peak VRAM on an A100-SXM4-80GB for MIFlu 4816 MiB, NLinear 558, PatchTST 720, GPT-2 frozen encoder 1070, Chronos 596, TimesFM 2594. Warm-up+repeated real model-forward latencies: GPT-2 6.98+/-0.097 ms, Chronos 9.854+/-0.337 ms, TimesFM 48.273+/-3.531 ms. Cross-checked by full80 job 744886 (2608 MiB combined; 10.229 / 50.906 ms) and 744532 (4816 MiB). Full record: `v8/T6_FINAL_SWEEP.md`. MIFlu/NLinear/PatchTST isolated single-forward latency remains explicitly NOT_MEASURED (their measured quantity was a real full-cell export / training job). All rows keep `scope=subset_only_not_full_1120`; no full-1120 Pareto claim.
