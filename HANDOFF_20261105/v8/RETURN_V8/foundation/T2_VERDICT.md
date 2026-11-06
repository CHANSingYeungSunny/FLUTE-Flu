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
