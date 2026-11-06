# T2_DOWNLOAD_RESULT.md — local weight download, tar, scp, remote verification, isolated HPC env

Part of TASK 2 finalization (2026-11-06). This file records the **download / transfer /
environment** evidence only. Model results are in `T2_PILOT_AND_MATRIX.md`. The final
status is in the appended §9 of `T2_VERDICT.md`.

Everything below is already executed and verified by the main agent. **No training,
no download and no model work was re-run for this document.** No result is fabricated:
every number is quoted from an existing evidence file under `v8/evidence/foundation_t2_*`
or from a copied HPC log under `v8/foundation/t2_hpc_evidence/`.

---

## 1. Local FULL pinned-weight download (Windows, CPU-only, outside the project tree)

The earlier BLOCKED verdict (`T2_VERDICT.md` §6) recorded that only `config.json` +
`README.md` metadata probes had been fetched. That is now **superseded**: full pinned
weights were downloaded locally on Windows into `C:\models\mlflu_fm\` (outside the
project tree), by `huggingface_hub.snapshot_download` at the exact pinned revisions
**without** `allow_patterns` (so real weight tensors were fetched).

### 1.1 Mechanism (exact)

Driver: `v8/foundation/foundation_t2_download.py`. Its core call is (verbatim from
`foundation_t2_download.py:56`):

```python
from huggingface_hub import snapshot_download
path = snapshot_download(
    repo_id=args.repo_id,
    revision=args.revision,
    local_dir=args.local_dir,
    # full download: deliberately NO allow_patterns
)
```

`huggingface_hub==2.4.0` was installed with `pip install --target` into an isolated
dir and loaded from `C:\models\mlflu_fm\_deps\huggingface_hub\__init__.py` (per the
download logs `HFHUB_LOADED_FROM`); system-Python `site-packages` was not modified.
The script docstring documents `PYTHONPATH` pointing at that isolated `--target`
install and a `timeout` wrapper. No `torch` / `transformers` / `from_pretrained` /
inference is used anywhere in the downloader.

Exact CLI invocations (all arguments as recorded in the per-download manifests
`v8/evidence/foundation_t2_manifest_*.txt`; all four returned `STATUS=OK`, rc=0):

```
python "HANDOFF_20261105/v8/foundation/foundation_t2_download.py" --repo-id "amazon/chronos-bolt-tiny"        --revision "a0e552de83495b5c28c14c71c374f3e33280b340" --local-dir "C:/models/mlflu_fm/chronos_bolt_tiny"        --name "chronos_bolt_tiny"        --evidence-dir "HANDOFF_20261105/v8/evidence"
python "HANDOFF_20261105/v8/foundation/foundation_t2_download.py" --repo-id "amazon/chronos-t5-small"         --revision "a971ba21945c4f1796b17a91fe69214b5f4ad472" --local-dir "C:/models/mlflu_fm/chronos_t5_small"         --name "chronos_t5_small"         --evidence-dir "HANDOFF_20261105/v8/evidence"
python "HANDOFF_20261105/v8/foundation/foundation_t2_download.py" --repo-id "google/timesfm-1.0-200m"         --revision "8775f7531211ac864b739fe776b0b255c277e2be" --local-dir "C:/models/mlflu_fm/timesfm_1_0_200m"         --name "timesfm_1_0_200m"         --evidence-dir "HANDOFF_20261105/v8/evidence"
python "HANDOFF_20261105/v8/foundation/foundation_t2_download.py" --repo-id "google/timesfm-2.0-500m-pytorch" --revision "dc2443792ce5516872b89b37cf1bc058c3bf0c10" --local-dir "C:/models/mlflu_fm/timesfm_2_0_500m_pytorch" --name "timesfm_2_0_500m_pytorch" --evidence-dir "HANDOFF_20261105/v8/evidence"
```

Per-download facts (from `v8/evidence/foundation_t2_dl_*.log` and
`foundation_t2_manifest_*.txt`):

| # | repo_id | pinned revision | local_dir | start/end UTC | files | total bytes | status |
|---|---|---|---|---|---|---|---|
| 1 | `amazon/chronos-bolt-tiny` | `a0e552de83495b5c28c14c71c374f3e33280b340` | `C:/models/mlflu_fm/chronos_bolt_tiny` | 15:07:19–15:07:36Z | 11 | 34,634,943 | OK |
| 2 | `amazon/chronos-t5-small` | `a971ba21945c4f1796b17a91fe69214b5f4ad472` | `C:/models/mlflu_fm/chronos_t5_small` | 15:08:22–15:08:44Z | 15 | 184,875,427 | OK |
| 3 | `google/timesfm-1.0-200m` | `8775f7531211ac864b739fe776b0b255c277e2be` | `C:/models/mlflu_fm/timesfm_1_0_200m` | 15:08:50–15:09:24Z | 13 | 814,344,460 | OK |
| 4 | `google/timesfm-2.0-500m-pytorch` | `dc2443792ce5516872b89b37cf1bc058c3bf0c10` | `C:/models/mlflu_fm/timesfm_2_0_500m_pytorch` | 15:09:45–15:11:38Z | 13 | 3,990,963,772 | OK |

The only stderr item is the non-fatal HF warning
`Warning: You are sending unauthenticated requests to the HF Hub...` (a warning,
not an error; all downloads succeeded).

---

## 2. Four pinned tars (exact sizes + SHA-256)

Recorded in `v8/evidence/foundation_t2_tar_manifest.txt`. The tars live **locally** in
`C:\models\mlflu_fm\tars\` (outside the project tree).

```
f28b41b19e9348c9a4a733eb208595b577509667035ca7a8c55e38a304b81c18  34652160    chronos_bolt_tiny.tar
d6df552e68fc0f2fbad20141d8b852870af76580d51c89508b2a221021f2da16  184893440   chronos_t5_small.tar
963d6d6adf8d91c8d8f0a7362eed981bcd147d6d766e7980622141fdd0ebeb13  814376960   timesfm_1_0_200m.tar
7fef382ad503bb8489966729250e790ac78bf9cc4b9966a32d6769667ab90363  3990978560   timesfm_2_0_500m_pytorch.tar
TOTAL_TAR_BYTES=5024901120
```

Tar creation (reconstructed from the manifest; the literal `tar` command line was not
logged — stated honestly, not presented as a captured command): one `tar -cf` per
`<name>` directory into `C:/models/mlflu_fm/tars/<name>.tar`, then a single
`sha256sum *.tar`. The tar bytes/hashes above are the recorded outputs.

---

## 3. LFS integrity (local evidence)

`v8/evidence/foundation_t2_integrity_check.txt`: `ALL_LFS_MATCH=True` for **5 LFS
files across 4 repos** — each local weight file's SHA-256 equals the HF LFS
`oid sha256` from the repo metadata:

| repo | LFS file | sha256 (= HF LFS oid) | size |
|---|---|---|---|
| `chronos_bolt_tiny` | `model.safetensors` | `75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32` | 34,622,352 |
| `chronos_t5_small` | `model.safetensors` | `9c8b6fde5300f72b01c173153bf9288fa0a200614275bf0585071ad71a6a3d43` | 184,632,480 |
| `timesfm_1_0_200m` | `checkpoints/checkpoint_1100000/state/checkpoint` | `d147f95bbe40ffeb1e8d61643925dd29eeb00b5696db33bf9f6e1887682f6391` | 814,291,152 |
| `timesfm_2_0_500m_pytorch` | `model.safetensors` | `bb9d7022d8027325f4e656b7d5cf36dd919269fd79ad714eab41f5ba49cc1cfe` | 1,995,406,976 |
| `timesfm_2_0_500m_pytorch` | `torch_model.ckpt` | `a3a1362cdc26f0dde45c9790c438951ff02af96b2d1d6445fdb58f28c77e18de` | 1,995,545,448 |

---

## 4. scp destination (exact command)

`v8/evidence/foundation_t2_scp.log`, `SCP_START_UTC=2026-11-06T15:16:34Z`:

```
timeout 1800s scp -o ServerAliveInterval=0 -o ServerAliveCountMax=0 -o BatchMode=yes \
  -o PreferredAuthentications=publickey -o ConnectTimeout=10 \
  <4 tars> cityu:/gpfs1/scratch/sychan552/models/
```

Destination: `/gpfs1/scratch/sychan552/models/` on CityU Burgundy.
The scp log contains only the non-fatal OpenSSH post-quantum warning
(`connection is not using a post-quantum key exchange algorithm`); no error.

---

## 5. Remote SHA-256 verification (INSIDE sbatch job 744607)

`t2_hpc_evidence/logs/matrix_744607.out` lines 4–14 — all four remote tar SHA-256
values were re-computed **on the compute node** and **EXACTLY match** §2:

```
REMOTE chronos_bolt_tiny.tar        size=34652160    sha256=f28b41b19e9348c9a4a733eb208595b577509667035ca7a8c55e38a304b81c18
REMOTE chronos_t5_small.tar         size=184893440   sha256=d6df552e68fc0f2fbad20141d8b852870af76580d51c89508b2a221021f2da16
REMOTE timesfm_1_0_200m.tar         size=814376960   sha256=963d6d6adf8d91c8d8f0a7362eed981bcd147d6d766e7980622141fdd0ebeb13
REMOTE timesfm_2_0_500m_pytorch.tar size=3990978560  sha256=7fef382ad503bb8489966729250e790ac78bf9cc4b9966a32d6769667ab90363
TOTAL_REMOTE_TAR_BYTES=5024901120
```

Two extracted weight files were also verified against their HF LFS oid **inside sbatch**:
- `torch_model.ckpt` sha256 `a3a1362cdc26f0dde45c9790c438951ff02af96b2d1d6445fdb58f28c77e18de` == HF LFS oid (`matrix_744607.out:20-21`).
- `chronos_bolt_tiny/model.safetensors` sha256 `75068728d376d2bec670379eeef4bfb4d24c0cfe24d957451f8d19b447030a32` == HF LFS oid (`env_finish_744576.out:64-65`, `pilot_744589.out:10-11`).

---

## 6. Isolated HPC environment (`/home/sychan552/.venvs/mlflu_fm`)

All heavy work ran via `sbatch` on compute nodes; the login node was used only for
light checks / the scp transfer (AGENTS.md RULE 1). Honest two-stage record:

| job | name | partition / node | role | result |
|---|---|---|---|---|
| 744533 | `t2_env_probe` | `tiny` / `cpunode-034` | Python/PyPI/HF reachability probe | rc=0; found Python 3.11.13 in `mlflu_llm`; `pypi_json_http=200`, `hf_http=200` |
| 744574 | `t2_fm_env` | `tiny` / `cpunode-034` | create venv + install pinned pkgs | rc=0; **at this stage pandas/sklearn/utilsforecast/wandb still MISSING** → `IMPORT_FAIL pandas/chronos/timesfm` (recorded, not hidden) |
| 744576 | `t2_fm_env_finish` | `tiny` / `cpunode-034` | install remaining deps + verify ALL imports | rc=0; **ALL imports OK; offline Chronos load + CPU forward OK** |

Creation (from `t2_env_install.sbatch`, exact):
```
/home/sychan552/.venvs/mlflu_llm/bin/python -m venv /home/sychan552/.venvs/mlflu_fm
echo "/home/sychan552/.venvs/mlflu_llm/lib/python3.11/site-packages" \
  > /home/sychan552/.venvs/mlflu_fm/lib64/python3.11/site-packages/_mlflu_llm_reuse.pth
```
The `.pth` reuses the existing `mlflu_llm` Python-3.11 `site-packages` (torch /
transformers / numpy / safetensors / accelerate / huggingface_hub) so the new venv
does **not** re-install torch and does **not** modify `mlflu_hpc`. Pinned,
source-pinned packages were installed with `pip install --no-deps
chronos-forecasting==2.3.2 timesfm==1.3.0` (744574) and the remaining pure-Python
deps `pandas>=2.0,<3 scikit-learn>=1.2.2 utilsforecast>=0.1.10 wandb>=0.17.5`
(744576). `HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 WANDB_MODE=disabled` were set for
the offline runs.

Final verified versions (`env_finish_744576.out:31-43`, `env_install_744574.out:89-97`):

| package | version |
|---|---|
| Python | 3.11.13 |
| torch | 2.6.0+cu124 |
| chronos-forecasting | 2.3.2 |
| timesfm | 1.3.0 |
| pandas | 2.3.3 |
| transformers | 5.22.1 |
| numpy | 2.4.6 |
| scikit-learn | 1.9.1 |
| wandb | 0.31.0 |
| safetensors | 0.8.0 |
| einops | 0.8.2 |
| utilsforecast | 0.2.17 |
| accelerate | 1.15.0 |
| huggingface_hub | 2.4.0 |

`env_finish_744576.out` also records the offline functional check on the CPU compute
node: `OFFLINE_LOAD_OK ChronosBoltPipeline`, `CPU_FORWARD_OK (1, 9, 24) finite True`,
`OFFLINE_LOAD_RC=0`.

---

## 7. Licences (carried forward from `FOUNDATION_MODEL_PROVENANCE.md`)

All four downloaded checkpoints are Apache-2.0 (`amazon/chronos-bolt-tiny`,
`amazon/chronos-t5-small`, `google/timesfm-1.0-200m`,
`google/timesfm-2.0-500m-pytorch`). TimesFM 3.0 self-hosted weights remain excluded
(`timesfm-non-commercial-license-v1.0`); `google/timesfm-2.0-500m` (no `-pytorch`)
remains HTTP 401 / invalid.

---

## 8. What this file does NOT claim

- It does not claim 80 matrix cells were run (see `T2_PILOT_AND_MATRIX.md` §6:
  `NOT_EXECUTED_BY_PROTOCOL`).
- It does not present the TimesFM `wall_s=0.0` / `inference_latency_ms` values as
  repeated measured forward-pass latencies (see the honesty caveat in
  `T2_PILOT_AND_MATRIX.md` §5).
- The tar command line in §2 is explicitly marked as reconstructed from the manifest,
  not as a captured command.
