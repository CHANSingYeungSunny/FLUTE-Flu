# T2_VERDICT.md — TASK 2 (Numerical foundation models: Chronos, TimesFM)

```
status: BLOCKED
start_utc: 2026-11-06T13:21:18Z
end_utc: 2026-11-06T13:39:51Z
```

**Scope of the status.** `BLOCKED` applies to the **end-to-end TASK 2 acceptance**
criterion (1-cell pilot + `2 models × 4 L × 10 seeds = 80` valid cells with
predictions and measured resources, per `NEXT_DEEPSEEK_PROMPT.md` TASK 2).
The **scoped deliverables assigned in this run** — provenance, separate roster,
URL/revision/licence verification, exact HTTP status codes, and the local
pinned-revision connectivity probe — are **COMPLETED** and are listed in §5.
No measured model result is claimed anywhere.

Per `AGENTS.md` RULE 5 and `NEXT_DEEPSEEK_PROMPT.md` HARD RULE 7, a `BLOCKED`
record is written with the exact missing inputs and the smallest next action.
**Important: nothing "crashed".** All commands below exited 0 and network / Hub
access did **not** fail. The block is a documented missing-input condition (no
full weights, no isolated HPC env), not a fabricated error.

---

## 1. Hard rules honoured

- No `import torch` / `transformers` / `torch.load` / `from_pretrained` / model
  inference anywhere. The probe only calls `huggingface_hub.snapshot_download`
  with `allow_patterns=["config.json","README.md"]`.
- **No HPC at all**: no `ssh`, no `sbatch`, no `squeue`, no login-node commands,
  no submission. HPC was avoided entirely as instructed.
- No frozen CSV / raw prediction / owner-edited PPTX was deleted or modified.
- Downloads are local Windows only, into `v8/foundation/weights/`.
- `huggingface_hub` was installed with `--target` into an **OS temp dir**
  (`C:/Users/Asus/AppData/Local/Temp/mlflu_hfhub_20261106`); system Python
  `site-packages` was NOT modified (`loaded_from` confirms the temp path).
- Writes are confined to `HANDOFF_20261105/v8/foundation/` and
  `HANDOFF_20261105/v8/evidence/foundation_*` (plus the transient temp install
  outside the project). `TASK_LOG.md` and all other project files untouched.

---

## 2. Commands (exact) and exit codes

| # | command (abbreviated only by the shared `E`/`HUBDIR` variable definitions) | exit code | stdout/stderr |
|---|---|---|---|
| C1 | `date -u +"%Y-%m-%dT%H:%M:%SZ"` + `command -v curl python python3 timeout tar sha256sum` + `python --version` + `python -c "import huggingface_hub..."` | 0 | (inline) — recorded `ModuleNotFoundError: No module named 'huggingface_hub'` (pre-condition for C6) |
| C2 | `curl -sS -o /dev/null --connect-timeout 6 --max-time 20 -A MLFlu-provenance-probe/1.0 -w "%{http_code}|%{url_effective}|%{redirect_url}" ...` over 18 key URLs | 0 | `v8/evidence/foundation_http_status.txt` |
| C3 | `curl -sS ... -o <file> -w "... http_code=%{http_code} bytes=%{size_download}"` for 11 HF/GitHub/PyPI JSON bodies + python field parse | 0 | 11 `foundation_*.json`, parsed inline |
| C4 | `WebFetch` × 3: Chronos-2 model card, TimesFM-1.0-200m card, `github.com/google-research/timesfm` README | n/a (tool) | content transcribed into `FOUNDATION_MODEL_PROVENANCE.md` |
| C5 | `curl ... -o foundation_commit_and_pin_verification.txt` (401 body, GitHub release/tags/3 commit SHAs, 12 pinned `resolve` probes, siblings lists) | 0 | `v8/evidence/foundation_commit_and_pin_verification.txt` |
| C6 | `python -m pip install --disable-pip-version-check --no-input --no-cache-dir --target C:/Users/Asus/AppData/Local/Temp/mlflu_hfhub_20261106 huggingface_hub` | `pip_exit_code=0`, `verify_exit_code=0` | `v8/evidence/foundation_pip_install.log`; installed `huggingface_hub 2.4.0` |
| C7 | `Write` `v8/foundation/foundation_hf_probe.py` | n/a (tool) | file created |
| C8 | `timeout 180s env PYTHONPATH=C:/Users/Asus/AppData/Local/Temp/mlflu_hfhub_20261106 HF_HUB_DISABLE_TELEMETRY=1 HF_HUB_DISABLE_PROGRESS_BARS=1 HF_HUB_ETAG_TIMEOUT=15 HF_HUB_DOWNLOAD_TIMEOUT=60 python "HANDOFF_20261105/v8/foundation/foundation_hf_probe.py" --repo-id "<repo>" --revision "<sha>" --local-dir "HANDOFF_20261105/v8/foundation/weights/<slug>" --allow-patterns config.json README.md` × 3 | `probe_exit_code=0` for all three (`STATUS=OK`) | `foundation_probe_chronos_bolt_tiny.log`, `foundation_probe_chronos_t5_small.log`, `foundation_probe_timesfm_1_0_200m.log` |
| C9 | extra `curl` verification of `amazon/chronos-bolt-base` + `autogluon/chronos_datasets` config count | 0 | `foundation_extra_verification.txt`, `foundation_hf_api_chronos_bolt_base.json`, `foundation_hf_api_chronos_datasets.json` |
| C10 | `WebFetch` × 3: TimesFM-2.0-500m-pytorch card, Chronos-T5-Small card, `arxiv.org/html/2310.10688v4` (Table 1) | n/a (tool) | content transcribed into provenance |
| C11 | UTF-8 BOM strip on `FOUNDATION_ROSTER.csv` + `csv.reader` validation (11 cols, 8 rows, 0 bad rows) | 0 | inline |
| C12 | generate `foundation_all_files.sha256` + `foundation_timeline.txt` | 0 | both files |

Three pinned probes (C8), all at exact SHAs, all `STATUS=OK` / rc=0:

| slug | repo_id | revision | files | total bytes |
|---|---|---|---|---|
| `chronos_bolt_tiny` | `amazon/chronos-bolt-tiny` | `a0e552de83495b5c28c14c71c374f3e33280b340` | 7 | 10841 |
| `chronos_t5_small` | `amazon/chronos-t5-small` | `a971ba21945c4f1796b17a91fe69214b5f4ad472` | 7 | 8554 |
| `timesfm_1_0_200m` | `google/timesfm-1.0-200m` | `8775f7531211ac864b739fe776b0b255c277e2be` | 5 | 6906 |

Probe logs contain per-file `bytes` + `sha256` for every fetched file. The only
non-fatal stderr item is `Warning: You are sending unauthenticated requests to
the HF Hub. Please set a HF_TOKEN ...` (a warning, not an error; probes succeeded).

---

## 3. Exact HTTP status codes observed (2026-11-06 UTC)

`curl 8.21.0 (Windows) libcurl/8.21.0 Schannel`. Full raw log:
`v8/evidence/foundation_http_status.txt`.

| HTTP code | URLs (exact) |
|---|---|
| **200** | `https://huggingface.co`; `https://huggingface.co/api/models/amazon/chronos-bolt-tiny`, `.../amazon/chronos-t5-small`, `.../amazon/chronos-bolt-base`, `.../amazon/chronos-2`, `.../google/timesfm-1.0-200m`, `.../google/timesfm-2.0-500m-pytorch`, `.../google/timesfm-3.0-pytorch`; `https://huggingface.co/api/datasets/autogluon/chronos_datasets`; `https://github.com/amazon-science/chronos-forecasting`; `https://github.com/google-research/timesfm`; `https://api.github.com/repos/amazon-science/chronos-forecasting/releases/latest`; `https://api.github.com/repos/google-research/timesfm/tags`; `.../commits/0aba28e9360b6355d5a919596c90b16c25939f02`, `.../commits/331c6d33cb1ac2611de3056d0ac7164aab6301eb`, `.../commits/e77303c5513c84aa8b32639851c3f7f92f59645e`; `https://pypi.org/pypi/chronos-forecasting/json`; `https://pypi.org/pypi/timesfm/json`; `https://arxiv.org/abs/2310.10688v4` |
| **401** | `https://huggingface.co/api/models/google/timesfm-2.0-500m` → body `{"error":"Invalid username or password."}`; `https://huggingface.co/google/timesfm-2.0-500m/resolve/main/config.json` → 401 |
| **307** | all 12 pinned `https://huggingface.co/<repo>/resolve/<sha>/{config.json,README.md}` probes for the 6 pinned revisions (HF CDN redirect = revision resolves), **except** the 404 below |
| **404** | `https://huggingface.co/google/timesfm-1.0-200m/resolve/8775f7531211ac864b739fe776b0b255c277e2be/config.json` (this Flax repo has no `config.json`; siblings confirm) |

`WebFetch` calls returned content for all 6 pages (Chronos-2 card, Chronos-T5
card, TimesFM 1.0 card, TimesFM 2.0 card, timesfm GitHub README, arXiv HTML v4);
the tool does not expose numeric HTTP status codes, so none are claimed for it.

**Interpretation:** every required URL is reachable; the only 401s belong to the
deliberately-invalid repo `google/timesfm-2.0-500m` (matching the handoff fact),
and the single 404 is the documented absence of `config.json` in the TimesFM 1.0
Flax checkpoint repo. There is **no network/Hub failure to report**.

---

## 4. Outputs (paths + SHA-256)

Primary deliverables (SHA-256 computed after the BOM fix on the CSV):

| path | sha256 |
|---|---|
| `HANDOFF_20261105/v8/foundation/FOUNDATION_MODEL_PROVENANCE.md` | `0fd37415117c391297275eeacb48d9b14101941f2bf51b988d6882af4bb0f4b9` |
| `HANDOFF_20261105/v8/foundation/FOUNDATION_ROSTER.csv` | `4712fe6a4481e7a92e47296d5afa026f118b04d654951e16a32983f2a1f1c5bc` |
| `HANDOFF_20261105/v8/foundation/foundation_hf_probe.py` | `5a64f5c555350e162f1e986adc593005e48506a6e2e42e6d4e5f10f266d91538` |
| `HANDOFF_20261105/v8/foundation/T2_VERDICT.md` | this file (not self-hashed; see exhaustive manifest) |

Exhaustive SHA-256 manifest of **every** file under `v8/foundation/` (recursive,
including all probe downloads) and every `v8/evidence/foundation_*` file:
`HANDOFF_20261105/v8/evidence/foundation_all_files.sha256` (self-excluded).
UTC timeline: `HANDOFF_20261105/v8/evidence/foundation_timeline.txt`.

Other written paths (all hashed in the manifest):
- `v8/foundation/weights/{chronos_bolt_tiny,chronos_t5_small,timesfm_1_0_200m}/`
  — `config.json` / `README.md` + `.cache/huggingface/` metadata only.
- `v8/evidence/foundation_http_status.txt`, `foundation_commit_and_pin_verification.txt`,
  `foundation_extra_verification.txt`, `foundation_pip_install.log`,
  `foundation_probe_*.log` (3), and 14 `foundation_*.json` API bodies.

---

## 5. Evidence (COMPLETED within this run's scope)

1. **Source-pinned provenance** — `FOUNDATION_MODEL_PROVENANCE.md`: exact repo id,
   revision, licence, version/tag, context/prediction limits, channel handling,
   the documented per-channel-independent adapter and its 6 scientific limits,
   TimesFM `freq=1` for weekly, TimesFM 3.0 non-commercial exclusion, and
   pretraining overlap facts with exact URLs.
2. **Separate roster** — `FOUNDATION_ROSTER.csv`: 8 rows, 11 columns, machine-readable,
   explicitly NOT merged into the 28-arm family.
3. **Verified pins / versions / licences**: HF API `sha` + `cardData.license` for
   all 7 relevant repos (all 200), GitHub `v2.3.2` release dated
   `2026-09-08T14:06:51Z`, commit `0aba28e9360b6355d5a919596c90b16c25939f02`
   (`Bump version to 2.3.2 (#533)`), timesfm tags `v3.0.0`→`331c6d33...` and
   `v1.2.6`→`e77303...`, PyPI `chronos-forecasting 2.3.2` / `timesfm 3.0.2`.
4. **Capability facts**: official Chronos-2 model card table
   (`Multivariate Forecasting | ✅ | ❌ | ❌`, `Max. Context 8192/2048/512`,
   `Max. Prediction 1024/64/64`); TimesFM 1.0/2.0 cards (univariate, 512/2048,
   any horizon, `freq∈{0,1,2}`, weekly→1); TimesFM 3.0 licence quote;
   `autogluon/chronos_datasets` `configs len = 67`; arXiv:2310.10688v4 Table 1
   (Google Trends + Wiki pageviews + synthetic + other real data; **no** CDC ILI /
   influenza / health-surveillance pretraining source).
5. **Local pinned-revision probes**: 3 × `snapshot_download(..., revision=<pinned
   SHA>, allow_patterns=["config.json","README.md"])` → rc=0, `STATUS=OK`, with
   exact byte counts and SHA-256 per file.

---

## 6. Why BLOCKED — exact evidence of the missing inputs

`NEXT_DEEPSEEK_PROMPT.md` TASK 2 acceptance: *"either 80 valid cells with
predictions + measured resources, or a BLOCKED record with evidence. No claim
that frozen language encoders are these models."* Neither 80 cells nor a pilot
exists. Exact missing inputs:

1. **No full pinned weights on disk.** The probes were deliberately restricted
   by `allow_patterns=["config.json","README.md"]` (per the time-box / connectivity-
   pin-probe allowance). Totals are 10841 / 8554 / 6906 bytes — metadata only.
   The exact weight files that are **absent** (from HF API `siblings`):
   - `v8/foundation/weights/chronos_bolt_tiny/model.safetensors`
   - `v8/foundation/weights/chronos_t5_small/model.safetensors`
   - `v8/foundation/weights/timesfm_1_0_200m/checkpoints/checkpoint_1100000/state/checkpoint`
     (and `.../metadata/metadata`, `.../descriptor/descriptor.pbtxt`)
   Full weight download is explicitly recorded as **NOT COMPLETED**.
2. **No tar created and NO `scp` performed.** The instruction's condition
   ("If (and only if) full weights were downloaded") is false → step 3 was
   skipped. **No claim of scp is made.** No SSH was used at all.
3. **No isolated HPC env.** `/home/sychan552/.venvs/mlflu_fm` was not created;
   no `sbatch`, no `squeue`, no `ssh`. HPC was avoided entirely as instructed.
   (If HPC is used later: ONE connection via
   `ssh -o ServerAliveInterval=0 -o ServerAliveCountMax=0 -o BatchMode=yes sychan552@burgundy.hpc.cityu.edu.hk`
   wrapped in `timeout 25s`, light commands only, NO model work — per `AGENTS.md`
   RULE 1.)
4. **Therefore pilot / matrix are NOT EXECUTED.**
   - Pilot (`1 model × L24 × seed 2021` on `stingy` A100): **NOT EXECUTED** —
     needs full weights + isolated HPC env + `sbatch`; none exist.
   - 80-cell matrix (`2 × 4 × 10`, labels `foundation_chronos` /
     `foundation_timesfm`): **NOT EXECUTED** — same reason; also requires a
     passing pilot first.
   - No wall time / peak VRAM / finite predictions were measured. **No measured
     model result is claimed.**

**Not a failure:** all commands exited 0; all needed URLs returned 200/307; the
401s/404 are the documented invalid repo and absent `config.json` (§3). The
verdict is `BLOCKED` on missing inputs (HARD RULE 7), not on a network error.
No error string such as a connection failure exists to quote — inventing one
would violate AGENTS.md RULE 5, so none is invented.

---

## 7. Remaining

- Full pinned weight download (local Windows) for the two chosen Apache-2.0
  controls (e.g. `amazon/chronos-bolt-tiny` + `google/timesfm-1.0-200m`, or the
  `chronos-t5-small` + `timesfm-2.0-500m-pytorch` pair).
- `tar` + SHA-256 + `scp` to `/gpfs1/scratch/sychan552/models/`.
- Isolated env `/home/sychan552/.venvs/mlflu_fm`; extract the tar **inside an
  sbatch job** on `tiny`; verify SHA-256; record licence.
- 1-cell pilot on `stingy` A100 via `sbatch` (wall time, peak VRAM, finite
  predictions). Do not run the full matrix if the pilot fails.
- If the pilot passes: `2 × 4 × 10 = 80` cells with predictions + measured
  resources, labelled separately, using `FOUNDATION_ROSTER.csv` as the roster.
- Downstream v8 docs (TASK 7) and resource measurements (TASK 6) are separate
  tasks, not touched here.

**Known licence constraint to carry forward:** TimesFM 3.0 self-hosted weights
are `timesfm-non-commercial-license-v1.0` (non-commercial, non-production) →
excluded; use Apache-2.0 weights ≤ 2.5. `google/timesfm-2.0-500m` (no
`-pytorch`) is HTTP 401, not a valid repo.

---

## 8. Smallest next action

Complete the single missing **local** input: download the full pinned weights
locally on Windows (no HPC, no login node), e.g.

```
huggingface_hub.snapshot_download(
    repo_id="amazon/chronos-bolt-tiny",
    revision="a0e552de83495b5c28c14c71c374f3e33280b340",
    local_dir="v8/foundation/weights/chronos_bolt_tiny",
)   # WITHOUT allow_patterns -> fetches model.safetensors
```

and the equivalent for `google/timesfm-1.0-200m` @
`8775f7531211ac864b739fe776b0b255c277e2be`; then verify SHA-256, tar, `scp` to
`/gpfs1/scratch/sychan552/models/`, and only then create the isolated HPC env
and run the 1-cell pilot via `sbatch`. Until that chain exists, TASK 2 stays
`BLOCKED` and pilot/matrix stay `NOT_EXECUTED`.

---

## FINAL UPDATE 2026-11-06 — TASK 2 EXECUTED

```
status: COMPLETED_WITH_DOCUMENTED_SCOPE
update_utc: 2026-11-06
document_date: 2026-11-07 (HKT) / 2026-11-06 (UTC)
```

**This section supersedes the earlier `BLOCKED` verdict recorded above (§1–§8).**
Everything in §1–§8 remains valid as the historical record of the *earlier* run
(2026-11-06T13:21:18Z–13:39:51Z, metadata-only probes, no HPC). It is kept verbatim
and is NOT erased. The earlier `BLOCKED` status applied to a missing-input condition
that has since been **eliminated by actual, verified work**: the full pinned weight
download, the isolated HPC env, the 1-cell pilot, and the zero-shot matrix were all
subsequently executed on 2026-11-06 UTC. Full records:
`T2_DOWNLOAD_RESULT.md` (download / tar / scp / env) and
`T2_PILOT_AND_MATRIX.md` (pilot + matrix). No training, download or HPC job was
re-run to produce this update.

### What was actually done (JOB IDs)

| JOB ID | name | partition / node | role | rc |
|---|---|---|---|---|
| 744533 | `t2_env_probe` | `tiny` / `cpunode-034` | reachability probe | 0 |
| 744574 | `t2_fm_env` | `tiny` / `cpunode-034` | create venv + install pinned pkgs | 0 |
| 744576 | `t2_fm_env_finish` | `tiny` / `cpunode-034` | all imports OK; offline Chronos CPU forward OK | 0 |
| **744589** | `t2_fm_pilot` | `stingy` / `gpu-a100-05` | 1-cell pilot (Chronos-Bolt-Tiny, L24) | 0 — `PILOT_STATUS COMPLETED` |
| **744607** | `t2_fm_matrix` | `stingy` / `gpu-a100-05` | 8-cell zero-shot matrix | 0 — `MATRIX_SUMMARY {"cells": 8, "ok": 8}` |

GPU on both GPU jobs: `NVIDIA A100-SXM4-80GB`, driver `580.167.08`.
Env: `/home/sychan552/.venvs/mlflu_fm` — Python 3.11.13, torch 2.6.0+cu124,
chronos-forecasting 2.3.2, timesfm 1.3.0, pandas 2.3.3, transformers 5.22.1,
numpy 2.4.6.
Pilot peak VRAM 596 MiB (28 nvidia-smi samples), wall 27.35 s, Max RSS 1,175,612 KB.
Matrix peak VRAM 2608 MiB (18 samples), wall 18.00 s, Max RSS 5,083,268 KB.

### 8 faithful cells were run with REAL predictions

Both models are frozen **zero-shot**, labelled `foundation_chronos` /
`foundation_timesfm` on the SEPARATE `FOUNDATION_ROSTER.csv` (never merged into the
28-arm family). All 8 cells `ok`, `all_finite=true`, 8 NPZ files written and hashed.

| label | L | MSE_7var_z | MAE_7var_z |
|---|---|---|---|
| foundation_chronos | 24 | 0.391328494214842 | 0.38354600155631297 |
| foundation_chronos | 36 | 2.2073974038407127 | 0.8228125978793258 |
| foundation_chronos | 48 | 1.7135358177616078 | 0.7144444235980304 |
| foundation_chronos | 60 | 1.4002307209877294 | 0.6290749702336526 |
| foundation_timesfm | 24 | 0.7297525333525895 | 0.55222854102346 |
| foundation_timesfm | 36 | 2.654955323576468 | 0.9666897748733104 |
| foundation_timesfm | 48 | 2.031110049314629 | 0.7960082834044987 |
| foundation_timesfm | 60 | 1.6629733698689972 | 0.6950911470769424 |

Pilot (same L24 Chronos cell) reproduced `MSE=0.391328494214842`,
`MAE=0.38354600155631297`, `all_finite=true`, with the only warmed-up repeated
inference latency: mean 10.191 ms / std 0.446 (warm-up 1, repeat 5).

### Key hashes (verified, not invented)

- 4 pinned tars, local Windows total **5,024,901,120 B**; all scp'd to
  `/gpfs1/scratch/sychan552/models/`; all 4 remote SHA-256 re-computed **inside
  sbatch job 744607** and EXACTLY matched local (`T2_DOWNLOAD_RESULT.md` §2/§5):
  - `chronos_bolt_tiny.tar` `f28b41b19e9348c9a4a733eb208595b577509667035ca7a8c55e38a304b81c18`
  - `chronos_t5_small.tar` `d6df552e68fc0f2fbad20141d8b852870af76580d51c89508b2a221021f2da16`
  - `timesfm_1_0_200m.tar` `963d6d6adf8d91c8d8f0a7362eed981bcd147d6d766e7980622141fdd0ebeb13`
  - `timesfm_2_0_500m_pytorch.tar` `7fef382ad503bb8489966729250e790ac78bf9cc4b9966a32d6769667ab90363`
- `torch_model.ckpt` sha256
  `a3a1362cdc26f0dde45c9790c438951ff02af96b2d1d6445fdb58f28c77e18de` == HF LFS oid (verified in 744607).
- `chronos_bolt_tiny/model.safetensors` sha256
  `75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32` == HF LFS oid (verified in 744576 / 744589).
- The 8 NPZ SHA-256 values (computed locally, CROSS_VERIFY=ALL_MATCH with the
  HPC-side manifest) are listed with their full paths in `T2_PILOT_AND_MATRIX.md` §4
  and `T2_EVIDENCE_HASHES.txt`; all 38 copied HPC evidence files are byte-identical
  to the HPC originals.

### The 80-cell expansion remains `NOT_EXECUTED_BY_PROTOCOL` — exact reason

`FOUNDATION_MATRIX_REPORT.json` records
`"requested_80_cells": "NOT_EXECUTED_BY_PROTOCOL"` with reason:
**"no training seed dimension in a frozen zero-shot model; 10 seeds would produce
10 identical predictions"**. The originally-scoped `2 models × 4 L × 10 seeds = 80`
cells assume a training seed; for a frozen zero-shot model a fixed (model, L, input)
is deterministic, so 10 seeds would duplicate predictions rather than add
information. The **smallest faithful subset** — `2 models × 4 L = 8 cells` — was run
instead. This is a documented protocol decision, **not** a failure and **not** a
claim that 80 cells were run.

### No result was fabricated — and what remains out of scope

Every number above and in `T2_PILOT_AND_MATRIX.md` is quoted from copied, hashed HPC
logs or re-computed locally from the copied NPZ files. **No measured result was
invented.** Explicitly NOT claimed / NOT done (full list in `T2_PILOT_AND_MATRIX.md` §7):
- no 10-seed / 80-cell expansion, no multivariate-native checkpoint (Chronos-2 /
  TimesFM-3.0), no full-1120-panel comparison, no merge into the 28-arm family;
- both executed checkpoints are **univariate**; 7 channels are passed as a batch of
  7 independent series, which **discards cross-channel dependence** and is **NOT
  information-set-matched** to the multivariate arms; benchmark z-space is passed
  through with each model's own internal normalization; TimesFM uses
  `freq_indicator=1` (weekly), `horizon_len=128` sliced to L; both are zero-shot,
  not retrained;
- **honesty caveat:** TimesFM `wall_s=0.0` and its `inference_latency_ms`
  (0.004 / 2.483 / 4.489 / 6.492) are loop/slicing timings from ONE shared
  `tfm.forecast` call across the 4 L values — NOT four independent forward-pass
  latencies; Chronos L24 `inference_latency_ms=221.835` includes one-time CUDA
  initialisation. These are NOT presented as repeated measured inference latencies.

`FOUNDATION_ROSTER.csv` now marks the two executed checkpoints
`PILOT_AND_4L_COMPLETED` (with `separate_roster=yes`) and keeps all other rows
`NOT_EXECUTED`; no row was deleted. Downstream T6 / T7 / v8 docs remain separate
tasks and were not modified here.


---

## FINAL UPDATE 2026-11-06 — FULL 80-CELL MATRIX COMPLETED

`status: COMPLETED (80/80 valid cells; documented rolling-origin protocol)`.
The earlier `COMPLETED_WITH_DOCUMENTED_SCOPE` (8 cells) and the original `BLOCKED`
verdicts are SUPERSEDED.

- Job **744886** `t2_fm_full80` on `stingy` / A100-SXM4-80GB produced
  `FOUNDATION_80_CELLS.csv`: **80/80 `ok`, all finite, 80 real prediction NPZ**
  under `v8/foundation/t2_hpc_evidence/full80_out/`.
- Matrix = 2 models x 4 L (24/36/48/60) x 10 replicates. Both checkpoints are
  FROZEN ZERO-SHOT with no training seed dimension, so 10 seeds would give 10
  identical predictions. The 10 replicates are therefore **10 DISTINCT FORECAST
  ORIGINS** (rows 773-782), each with its own context and target.
  `seed_semantics=NOT_APPLICABLE`, `replicate_kind=rolling_origin`.
  The literal 10-seed expansion remains `NOT_EXECUTED_BY_PROTOCOL` with that exact
  reason — this is a documented protocol deviation, NOT a fabricated seed dimension.
- Measured resources: peak VRAM 2608 MiB (51 nvidia-smi samples), `/usr/bin/time -v`
  wall 50.71 s, Chronos latency 10.229 +/- 1.074 ms (warm-up 1 / repeat 10),
  TimesFM 50.906 +/- 4.459 ms (warm-up 1 / repeat 5).
- Labels `foundation_chronos` / `foundation_timesfm` remain a SEPARATE ROSTER.
  Both checkpoints are UNIVARIATE; the per-channel adapter DISCARDS cross-channel
  dependence and is NOT information-set matched to the multivariate arms. No
  training/fine-tuning, no full-1120 comparison.
- Full record: `v8/foundation/T2_FULL80.md`; per-NPZ hashes:
  `v8/foundation/T2_EVIDENCE_HASHES_FULL80.txt`.
