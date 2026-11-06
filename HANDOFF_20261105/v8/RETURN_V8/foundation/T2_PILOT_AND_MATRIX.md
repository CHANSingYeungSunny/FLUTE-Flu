# T2_PILOT_AND_MATRIX.md — TASK 2 pilot + zero-shot matrix execution record

Part of TASK 2 finalization. **Document date: 2026-11-07 (HKT) / 2026-11-06 (UTC).**
All HPC runs below were **executed on 2026-11-06 UTC**. This file is the full dated
record of the **pilot** (job 744589) and the **matrix** (job 744607). The download /
tar / scp / remote SHA-256 / isolated-env record is in `T2_DOWNLOAD_RESULT.md`; the
copied-evidence hashes are in `T2_EVIDENCE_HASHES.txt`; the final status is the
appended `## FINAL UPDATE 2026-11-06 — TASK 2 EXECUTED` section of `T2_VERDICT.md`.

**No training, no download and no HPC job was re-run to produce this document.**
Every number is quoted from an already-copied, byte-identical HPC log under
`v8/foundation/t2_hpc_evidence/` (verified by `T2_EVIDENCE_HASHES.txt`,
`CROSS_VERIFY=ALL_MATCH`) or re-computed locally from the 8 copied NPZ files.
No result is fabricated. All HPC model work (tar extract, SHA verify, torch load,
forward) ran INSIDE the sbatch jobs on GPU compute nodes (AGENTS.md RULE 1).

---

## 1. Environment chain (context, already recorded)

The isolated env `/home/sychan552/.venvs/mlflu_fm` was built and verified by three
earlier `tiny`-partition jobs on `cpunode-034` (full record: `T2_DOWNLOAD_RESULT.md` §6):

| job | name | partition / node | role | rc |
|---|---|---|---|---|
| 744533 | `t2_env_probe` | `tiny` / `cpunode-034` | reachability probe | 0 |
| 744574 | `t2_fm_env` | `tiny` / `cpunode-034` | create venv + install pinned pkgs | 0 |
| 744576 | `t2_fm_env_finish` | `tiny` / `cpunode-034` | install remaining deps + verify ALL imports; offline Chronos load + CPU forward OK | 0 |

Verified final versions: Python 3.11.13, torch 2.6.0+cu124,
chronos-forecasting 2.3.2, timesfm 1.3.0, pandas 2.3.3, transformers 5.22.1,
numpy 2.4.6. Offline runs set `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
WANDB_MODE=disabled`.

---

## 2. Pilot — job 744589 (`t2_fm_pilot`)

### 2.1 Exact sbatch command / directives

Submitted via `sbatch` of `v8/foundation/t2_hpc_evidence/t2_pilot.sbatch`. The
`#SBATCH` directives (verbatim, `t2_pilot.sbatch:2-11`) and the timed inner
command (verbatim, `t2_pilot.sbatch:42-45`) are the authoritative exact commands:

```
#SBATCH --job-name=t2_fm_pilot
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=00:35:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/pilot_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/pilot_%j.err
```
```
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled \
  /usr/bin/time -v -o "$LOGS/pilot_time_v.txt" \
  timeout 900s "$VENV/bin/python" -u "$BASE/t2_pilot.py" \
  > "$LOGS/pilot_stdout.txt" 2> "$LOGS/pilot_stderr.txt"
```
where `VENV=/home/sychan552/.venvs/mlflu_fm`,
`BASE=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm`.
(The literal login-node `sbatch <file>` submission line was not captured in the
copied logs; the SLURM job id 744589 and the resolved output file `pilot_744589.out`
from `pilot_%j.out` are the recorded proof of submission. The sbatch script body
above is copied verbatim from the job's own script.)

### 2.2 Dated run facts

| item | value | source |
|---|---|---|
| JOB ID | 744589 | `pilot_744589.out:1` |
| job name | `t2_fm_pilot` | `t2_pilot.sbatch:2` |
| partition | `stingy` | `t2_pilot.sbatch:3` |
| node / host | `gpu-a100-05` | `pilot_744589.out:1` |
| GPU model | `NVIDIA A100-SXM4-80GB` (UUID `GPU-cf93ded8-653b-23d0-25ec-18d7496c3a80`) | `pilot_744589.out:3` |
| driver / VRAM total | `580.167.08` / `81920 MiB` | `pilot_744589.out:4` |
| START UTC | `2026-11-06T15:51:31Z` | `pilot_744589.out:1` |
| END UTC | `2026-11-06T15:52:00Z` | `pilot_744589.out:122` |
| `PILOT_RC` | 0 | `pilot_744589.out:14` |
| `/usr/bin/time -v` Exit status | 0 | `pilot_time_v.txt:23` |
| `PILOT_STATUS` | `COMPLETED` | `pilot_744589.out:89` |

### 2.3 `/usr/bin/time -v` values (`t2_pilot.sbatch` job, `pilot_time_v.txt`)

| field | value |
|---|---|
| Command timed | `timeout 900s /home/sychan552/.venvs/mlflu_fm/bin/python -u .../t2_fm/t2_pilot.py` |
| User time | 5.19 s |
| System time | 1.50 s |
| Percent of CPU | 24% |
| Elapsed (wall clock) | **0:27.35** (27.35 s) |
| Maximum resident set size | 1,175,612 KB |
| Major page faults | 0 |
| Minor page faults | 282,183 |
| Voluntary context switches | 19,790 |
| Involuntary context switches | 68 |
| Swaps | 0 |
| Page size | 4096 bytes |
| Exit status | 0 |

### 2.4 Peak VRAM, load, latency, predictions

- **peak_vram_mib = 596**, from **n_samples = 28** `nvidia-smi` 1-second samples
  (`pilot_744589.out:16-17`; `logs/pilot_vram_sample.csv`, 28 lines).
- Model load wall time = **0.4794 s** (`pilot_744589.out:19`, `pilot_result.json`).
- **Repeated measured inference latency (the only one of its kind):** warm-up 1,
  repeat 5, **mean 10.191 ms / std 0.446 ms**, all runs
  `[11.073, 9.988, 10.062, 9.858, 9.973]` (`pilot_result.json`).
- `all_finite = true`; **MSE_7var_z = 0.391328494214842**,
  **MAE_7var_z = 0.38354600155631297** (`pilot_result.json`).
- Model `amazon/chronos-bolt-tiny` @ revision
  `a0e552de83495b5c28c14c71c374f3e33280b340`; device `cuda`; point estimator =
  median quantile; `quantile_shape=[7,9,24]`, `point_shape=[24,7]`.
- Prediction NPZ: `pilot_out/pred_foundation_chronos_bolt_tiny_L24_s2021.npz`,
  SHA-256 `ac4a7e2144cc5f46cd806ff214d4ed216ed9601594793ebe02c188435f64ce80`
  (`T2_EVIDENCE_HASHES.txt:45`).
- In-job SHA-256 verification: `chronos_bolt_tiny.tar` =
  `f28b41b19e9348c9a4a733eb208595b577509667035ca7a8c55e38a304b81c18`,
  `model.safetensors` =
  `75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32` == HF LFS oid.

---

## 3. Matrix — job 744607 (`t2_fm_matrix`)

### 3.1 Exact sbatch command / directives

Submitted via `sbatch` of `v8/foundation/t2_hpc_evidence/t2_matrix.sbatch`.
`#SBATCH` directives (verbatim, `t2_matrix.sbatch:2-11`) and timed inner command
(verbatim, `t2_matrix.sbatch:50-53`):

```
#SBATCH --job-name=t2_fm_matrix
#SBATCH --partition=stingy
#SBATCH --gres=gpu:a100:1
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=01:00:00
#SBATCH --output=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/matrix_%j.out
#SBATCH --error=/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/logs/matrix_%j.err
```
```
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled \
  /usr/bin/time -v -o "$LOGS/matrix_time_v.txt" \
  timeout 3000s "$VENV/bin/python" -u "$BASE/t2_matrix.py" \
  > "$LOGS/matrix_stdout.txt" 2> "$LOGS/matrix_stderr.txt"
```
(As for the pilot: the literal login-node `sbatch <file>` line was not captured;
job id 744607 and the resolved `matrix_744607.out` from `matrix_%j.out` are the
recorded proof of submission. The script body above is copied verbatim.)

### 3.2 Dated run facts

| item | value | source |
|---|---|---|
| JOB ID | 744607 | `matrix_744607.out:1` |
| job name | `t2_fm_matrix` | `t2_matrix.sbatch:2` |
| partition | `stingy` | `t2_matrix.sbatch:3` |
| node / host | `gpu-a100-05` | `matrix_744607.out:1` |
| GPU model | `NVIDIA A100-SXM4-80GB` (UUID `GPU-cf93ded8-653b-23d0-25ec-18d7496c3a80`) | `matrix_744607.out:2` |
| driver / VRAM total | `580.167.08` / `81920 MiB` | `matrix_744607.out:3` |
| START UTC | `2026-11-06T15:57:33Z` | `matrix_744607.out:1` |
| END UTC | `2026-11-06T15:58:04Z` | `matrix_744607.out:90` |
| `MATRIX_RC` | 0 | `matrix_744607.out:22` |
| `/usr/bin/time -v` Exit status | 0 | `matrix_time_v.txt:23` |
| `MATRIX_SUMMARY` | `{"cells": 8, "ok": 8}` | `matrix_stdout.txt:13` |

All 8 cells `ok`, `all_finite=true` for every cell.

### 3.3 In-job remote integrity verification (inside 744607)

`matrix_744607.out:10-21` re-computed all four remote tar SHA-256 values on the
compute node; all EXACTLY match the local Windows tars (`T2_DOWNLOAD_RESULT.md` §2),
`TOTAL_REMOTE_TAR_BYTES=5024901120`. Also verified:
- `torch_model.ckpt` sha256
  `a3a1362cdc26f0dde45c9790c438951ff02af96b2d1d6445fdb58f28c77e18de` == HF LFS oid.
- `chronos_bolt_tiny/model.safetensors` sha256
  `75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32` == HF LFS oid.

### 3.4 `/usr/bin/time -v` values (`t2_matrix.sbatch` job, `matrix_time_v.txt`)

| field | value |
|---|---|
| Command timed | `timeout 3000s /home/sychan552/.venvs/mlflu_fm/bin/python -u .../t2_fm/t2_matrix.py` |
| User time | 10.19 s |
| System time | 2.07 s |
| Percent of CPU | 68% |
| Elapsed (wall clock) | **0:18.00** (18.00 s) |
| Maximum resident set size | **5,083,268 KB** (Max RSS) |
| Major page faults | 0 |
| Minor page faults | 521,414 |
| Voluntary context switches | 2,533 |
| Involuntary context switches | 113 |
| Swaps | 0 |
| Page size | 4096 bytes |
| Exit status | 0 |

### 3.5 Peak VRAM

- **peak_vram_mib = 2608**, from **n_samples = 18** `nvidia-smi` 1-second samples
  (`matrix_744607.out:24-25`; `logs/matrix_vram_sample.csv`, 18 lines). This is the
  peak of the whole 744607 job (both models share the job / GPU), NOT a per-model
  allocation.

---

## 4. The 8 executed cells — MSE/MAE, NPZ paths, local SHA-256

Values are the exact full-precision numbers in
`t2_hpc_evidence/matrix_out/FOUNDATION_CELLS.csv` (and the `CELL` lines in
`matrix_stdout.txt` / `matrix_744607.out:30-38`). `seed=2021`, `T=104`, `device=cuda`,
`status=ok`, `all_finite=True`, `scope=foundation_zero_shot_subset_not_1120_panel`.
SHA-256 values below were **computed locally on Windows** from the copied NPZ files
on 2026-11-07 (HKT) and EXACTLY match `T2_EVIDENCE_HASHES.txt:36-43`.

| # | label | L | MSE_7var_z | MAE_7var_z | NPZ path (relative to `t2_hpc_evidence/matrix_out/`) | SHA-256 |
|---|---|---|---|---|---|---|
| 1 | foundation_chronos | 24 | 0.391328494214842 | 0.38354600155631297 | `pred_foundation_chronos_L24_s2021.npz` | `66db381a477bd834b3ded81ecc7060578f38a34711d78008360a46f5928ce1d0` |
| 2 | foundation_chronos | 36 | 2.2073974038407127 | 0.8228125978793258 | `pred_foundation_chronos_L36_s2021.npz` | `da5d2ad1cafe9f0f0f85a9ecefbe03106e8465ce1784ec340669c7beba254643` |
| 3 | foundation_chronos | 48 | 1.7135358177616078 | 0.7144444235980304 | `pred_foundation_chronos_L48_s2021.npz` | `2cabfe88102b2e5f86c104a4afc8f1c225d65eef913d6d84a2431d5808e37bd1` |
| 4 | foundation_chronos | 60 | 1.4002307209877294 | 0.6290749702336526 | `pred_foundation_chronos_L60_s2021.npz` | `c91ffde8102f15a812c263e92a0088e8ab36439f53b08c0c60078e1704971d77` |
| 5 | foundation_timesfm | 24 | 0.7297525333525895 | 0.55222854102346 | `pred_foundation_timesfm_L24_s2021.npz` | `2bc96089b586ddfa36eac031824e17f53bfd3c386d9e82d8dab56836815562e7` |
| 6 | foundation_timesfm | 36 | 2.654955323576468 | 0.9666897748733104 | `pred_foundation_timesfm_L36_s2021.npz` | `a9830074966dd64ea9f69f3f5debeb253850f6b0d70fa62cea44cd3d73d9ee32` |
| 7 | foundation_timesfm | 48 | 2.031110049314629 | 0.7960082834044987 | `pred_foundation_timesfm_L48_s2021.npz` | `f7190dd18d0535ad1ca447ed9c37bc6a25d88bfc96bc23f83995672d3f045d1d` |
| 8 | foundation_timesfm | 60 | 1.6629733698689972 | 0.6950911470769424 | `pred_foundation_timesfm_L60_s2021.npz` | `1c5fcd043442d1854a66f3ca1fdad03affcf5011ef12b16727af4c80b495667d` |

Labels `foundation_chronos` / `foundation_timesfm` belong to a **SEPARATE roster**
(`FOUNDATION_ROSTER.csv`) and are **never merged** into the frozen 28-arm family.

Models / pins actually used (both Apache-2.0, zero-shot, NOT retrained):
- `foundation_chronos` → `amazon/chronos-bolt-tiny` @ `a0e552de83495b5c28c14c71c374f3e33280b340` (chronos-forecasting 2.3.2). Point = median quantile; `quantile_shape=[7,9,L]`.
- `foundation_timesfm` → `google/timesfm-2.0-500m-pytorch` @ `dc2443792ce5516872b89b37cf1bc058c3bf0c10` (timesfm 1.3.0). Point = mean forecast; `forecast_shape=[7,128]`, `freq_indicator=1`, horizon_len=128 sliced to L.

Benchmark contract (`FOUNDATION_MATRIX_REPORT.json`): `T=104`, `seed=2021`,
`test_start_row=773`, data `national_illness_author_repo_966.csv` (966 rows),
scaler `scaler_miflu_author966.json`, channels `1..6, OT` (7 standardized channels).

---

## 5. Adapter and its scientific limits (must be read with every result above)

Both executed checkpoints are **UNIVARIATE**. The 7 benchmark channels are passed as
a **BATCH of 7 independent series** ("per-channel independent univariate
forecasting", 2-D input = batch): each channel's length-104 lookback is forecast in
isolation, then the 7 results are stacked and scored in benchmark z-space.

Documented limits (`FOUNDATION_MODEL_PROVENANCE.md` §3, `pilot_result.json`,
`FOUNDATION_MATRIX_REPORT.json`):

1. **Discards cross-channel dependence.** No inter-channel correlation, lead–lag or
   cross-region/cross-signal coupling is modelled. The result is a
   *channel-independent univariate zero-shot* baseline, **NOT** a multivariate model,
   and is **NOT information-set-matched** to the multivariate arms. It must never be
   described as multivariate.
2. **Internal normalization vs benchmark z-space.** Each model applies its OWN
   internal scaling/normalization (Chronos: scaling + quantization; TimesFM 1.0/2.0
   cards document no normalization). The benchmark z-space is **passed through**
   unchanged — no de-standardization / re-standardization was applied. Metrics are
   only meaningful under this single recorded convention; it is not equivalent to
   feeding original-scale series.
3. **TimesFM freq indicator = 1 (weekly)**, `horizon_len=128` sliced to `L`; a
   recommendation of the model card, specific to 1.0/2.0 (2.5+ dropped the indicator).
4. **Zero-shot only** — both models are frozen; no training / fine-tuning / retraining
   was performed.
5. **Licence / exclusions** — TimesFM 3.0 self-hosted weights
   (`timesfm-non-commercial-license-v1.0`) remain excluded on licence grounds;
   `google/timesfm-2.0-500m` (no `-pytorch`) remains HTTP 401 / invalid.
6. **Pretraining domain proximity (not leakage)** — TimesFM's Google Trends / Wiki
   pageview pretraining is indirect domain proximity, not CDC ILI / influenza label
   leakage (`FOUNDATION_MODEL_PROVENANCE.md` §4).

### 5.1 HONESTY CAVEAT — the latency / wall-time columns are NOT repeated measurements

This must be stated explicitly wherever `FOUNDATION_CELLS.csv` is quoted:

- **TimesFM** `wall_s = 0.0` and its `inference_latency_ms` values
  (**0.004 / 2.483 / 4.489 / 6.492** for L=24/36/48/60) are **loop / slicing
  timings from ONE shared `tfm.forecast` call** (`TIMESFM_FORECAST_OK (7, 128)`),
  whose single 128-step output is sliced to the 4 different L values. They are
  **NOT four independent forward-pass latencies**.
- **Chronos L24** `inference_latency_ms = 221.835` **includes one-time CUDA
  initialisation** (the first Chronos cell in the job); the later Chronos cells
  (~10 ms) do not. It is not a steady-state latency.
- **Therefore none of these `FOUNDATION_CELLS.csv` latency / wall_s values may be
  presented as repeated measured inference latencies.** The ONLY repeated,
  properly warmed-up inference-latency measurement in TASK 2 is the **PILOT**
  (§2.4): warm-up 1, repeat 5, mean 10.191 ms / std 0.446 ms.
- The trustworthy resource figures are the job-level `/usr/bin/time -v` walls
  (pilot 27.35 s, matrix 18.00 s), Max RSS (1,175,612 / 5,083,268 KB), and the
  nvidia-smi peak VRAM (596 / 2608 MiB).

---

## 6. Why the requested 80-cell expansion is `NOT_EXECUTED_BY_PROTOCOL`

`FOUNDATION_MATRIX_REPORT.json` records:

```
"protocol": "frozen zero-shot; smallest faithful subset = 2 models x 4 L = 8 cells",
"requested_80_cells": "NOT_EXECUTED_BY_PROTOCOL",
"reason": "no training seed dimension in a frozen zero-shot model; 10 seeds would produce 10 identical predictions"
```

The originally-scoped `2 models × 4 L × 10 seeds = 80` cells assume a **training seed
dimension**. Frozen zero-shot foundation models have **no training seed**: for a
fixed (model, L, input) the prediction is deterministic, so 10 seeds would yield 10
**identical** predictions — padding the panel with duplicates, not new information.
The smallest faithful, non-duplicated subset was therefore executed instead:
**2 models × 4 L = 8 cells** (all 8 `ok`, all finite, 8 NPZ files written). This is a
protocol decision recorded by the run, **not** a failure or a partial crash, and it
is **not** presented as the 80-cell panel.

---

## 7. Explicit list of what REMAINS (not done, not claimed)

1. **No 10-seed / 80-cell expansion** — `NOT_EXECUTED_BY_PROTOCOL` (§6), for the
   exact deterministic-zero-shot reason above.
2. **No multivariate-native checkpoint** — Chronos-2 / TimesFM-3.0 (natively
   multivariate) were not run. TimesFM 3.0 self-hosted weights are excluded on
   non-commercial-licence grounds; Chronos-2 was downloaded as a tar but its
   checkpoint was not executed.
3. **No full 1120-panel comparison** — the run scope is explicitly
   `foundation_zero_shot_subset_not_1120_panel`; there is no comparison against the
   full 1120-panel / 28-arm family results.
4. **No merge into the 28-arm family** — labels `foundation_chronos` /
   `foundation_timesfm` remain on the separate `FOUNDATION_ROSTER.csv`.
5. **No information-set-matched multivariate adapter** — the per-channel-independent
   adapter discards cross-channel dependence and is not matched to the multivariate
   arms (§5).
6. **No z-space de-standardization / re-standardization** — benchmark z-space was
   passed through; a convention-matched adapter was not implemented (§5, limit 2).
7. **No training / fine-tuning / retraining** — both models are frozen zero-shot.
8. **Other downloaded checkpoints NOT executed** — `amazon/chronos-t5-small` and
   `google/timesfm-1.0-200m` tars were downloaded and scp'd but were not used in the
   pilot or matrix; their rows remain `NOT_EXECUTED` in `FOUNDATION_ROSTER.csv`.
9. **No per-model steady-state latency / per-model VRAM** — only job-level peak VRAM
   (596 / 2608 MiB) and one warmed-up pilot latency measurement exist (§5.1).
10. **No repeated measured TimesFM inference latencies** (§5.1).
11. **Downstream tasks untouched** — T6 (resource measurements) and T7 (v8 docs)
    are separate tasks; `TASK_LOG.md`, `MESSAGE_TO_CHATGPT.md`,
    `SCIENTIFIC_AUDIT.md`, `BLOCKED_AND_UNVERIFIED.md`, `DOCUMENT_UPDATE_MAP.csv`,
    `v8/docs/*`, `v8/packaging/*`, `v8/RETURN_V8/*`, `v8/T6_*`, `01_最终报告/*`,
    `HANDOFF_20261105/final/*`, `HANDOFF_20261105/v7/*`, `02_数字表格/*`, `AGENTS.md`
    were not modified for this deliverable.

---

## 8. Evidence integrity

All HPC evidence was copied from
`/gpfs1/scratch/sychan552/stage5_a2_durable/code/queue/t2_fm/` via ONE ssh tar
stream (login node used ONLY for this transfer, AGENTS.md RULE 1); local SHA-256 of
all 38 copied files EXACTLY matches the HPC-side sha256sum captured in the same
session (`T2_EVIDENCE_HASHES.txt`, `CROSS_VERIFY=ALL_MATCH`, diff empty). The 8 NPZ
SHA-256 values in §4 were re-computed locally on 2026-11-07 (HKT) and reproduce the
manifest exactly. No SSH was used to re-read logs for this document.
