# HPC Guide — CityUHK Burgundy (ChatTime project)

Long-term reference for running ChatTime jobs on the Burgundy HPC cluster.
Last updated: 2026-08-16 (§6 rewritten to Phase-1 paper protocol + divergence GOTCHA).

## 1. Connection & Auth

- Login FQDN: `burgundy.hpc.cityu.edu.hk`.
- User: `sychan552`.
- **Passwordless SSH key auth is NOW ACTIVE (2026-08-14).** The assistant can
  log in, run commands, upload, check, and delete files on HPC **without any
  password prompt**. This enables fully autonomous HPC operation.

### 1a. Recommended login (passwordless — USE THIS)
```
ssh sychan552@burgundy.hpc.cityu.edu.hk
```
- This full-domain form authenticates via the ed25519 key with **no prompt**.
- Use it for all assistant-driven remote commands (`ssh host 'cmd'`, `scp`,
  `rsync`, job submission/monitoring, file cleanup).

### 1b. SSH config alias `cityu` (password-based — fallback only)
- The `~/.ssh/config` alias still exists but is **password/keyboard-interactive**:
  ```
  Host cityu
    HostName burgundy.hpc.cityu.edu.hk
    User sychan552
    Port 22
    KbdInteractiveAuthentication yes
    PreferredAuthentications keyboard-interactive,password
  ```
  → `ssh cityu` / `scp ... cityu:/path` still **prompts for a password**.
  Only use it when the assistant is NOT driving (e.g. the user's own manual login).

### 1c. Key setup (already done — do NOT repeat)
- Local Windows key: `C:\Users\Asus\.ssh\id_ed25519` (ed25519, empty passphrase).
- Public key appended to `~/.ssh/authorized_keys` on the HPC.
- If re-setup is ever needed (e.g. key lost):
  ```powershell
  # LOCAL Windows PowerShell — generate (skip if file exists)
  ssh-keygen -t ed25519 -f "$HOME\.ssh\id_ed25519" -N '""'
  # copy public key to HPC (prompts password once, for the alias/first time)
  cat "$HOME\.ssh\id_ed25519.pub" | ssh sychan552@burgundy.hpc.cityu.edu.hk "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
  ```
  **GOTCHA**: generate the key on LOCAL Windows, never on the HPC. Running
  `ssh-keygen` on the HPC + `ssh cityu` from the HPC fails (the `cityu` alias is
  undefined there). PowerShell `ssh-keygen -N ""` errors (`option requires an
  argument -- N`) → use `-N '""'` (single-quoted empty string).

### 1d. Autonomous command patterns (assistant-driven, passwordless)
```powershell
# Run a single remote command (no TTY needed)
ssh sychan552@burgundy.hpc.cityu.edu.hk "hostname; sinfo -s | head"

# Submit a job from local
ssh sychan552@burgundy.hpc.cityu.edu.hk "sbatch /home/sychan552/scratch/CHATTIME/Chattime/submit_ili_fulltest.sh"

# Check queue / job state
ssh sychan552@burgundy.hpc.cityu.edu.hk "squeue -u sychan552"

# Tail a running job log
ssh sychan552@burgundy.hpc.cityu.edu.hk "tail -n 40 /home/sychan552/scratch/CHATTIME/Chattime/logs/ili_fulltest_slurm_<JOBID>.out"

# Cancel a job
ssh sychan552@burgundy.hpc.cityu.edu.hk "scancel <JOBID>"

# Delete / clean files on HPC (rm -rf is safe here — it is the scratch copy)
ssh sychan552@burgundy.hpc.cityu.edu.hk "rm -rf /home/sychan552/scratch/CHATTIME/Chattime/results/ili/pc_results/stale_run"
```
> **Security note**: the private key and any HPC password must NEVER be written
> into repo `.md` files or committed (git history leak risk). The key lives only
> in `C:\Users\Asus\.ssh\` (local) + `~/.ssh/authorized_keys` (HPC).

## 2. Scratch Layout

- `/home/sychan552/scratch/CHATTIME` is a **symlink** to `/gpfs1/scratch/sychan552/CHATTIME`.
  Both paths are interchangeable; `HF_HOME` set to either resolves identically.
- Project code: `/home/sychan552/scratch/CHATTIME/Chattime/`
- Model weights cache: `/gpfs1/scratch/sychan552/CHATTIME/.cache/models--ChengsenWang--ChatTime-1-7B-Chat/snapshots/<hash>/`
  (this is the layout `transformers` expects when calling
  `from_pretrained("ChengsenWang/ChatTime-1-7B-Chat")` with `HF_HOME` set).
- Logs: `Chattime/logs/ili_slurm_<JOBID>.out` / `.err`

## 3. Partition Policy (IMPORTANT)

| Partition | GPU | Wall limit | Notes |
|---|---|---|---|
| `gpu_a100` | A100-40G | up to 12h | Usually **fully allocated**, jobs sit in `PD (Priority)` for a long time. |
| `stingy` | mixed (incl. `gpu-a100-03~06`) | **QOS-capped at 04:00:00** | Often has **idle A100s** → faster start. Use this by default. |
| `gpu_v100s` | V100 | — | Avoid for 7B float16 (easy OOM). |

**Default for all submit scripts:** `#SBATCH --partition=stingy` + `#SBATCH --gres=gpu:a100:1`.
- **Never** use bare `--gres=gpu:1` on `stingy` — it can schedule onto a V100 (mix node) → OOM.
- **HARD RULE — `stingy` QOS wall-clock cap = `04:00:00` (4h).** Submitting with
  `--time=12:00:00` (or any value > 4h) FAILS immediately with
  `QOSMaxWallDurationPerJobLimit` (`sbatch` rejects before the job even queues). Always
  set `--time=04:00:00` (or lower: `02:00:00`, `01:00:00`). The full ILI walk-forward job
  runs in <30 min, so 4h is ample headroom. **Never write a `--time` larger than 04:00:00
  on `stingy`.** (If you genuinely need >4h, use `#SBATCH --partition=gpu_a100` instead —
  but expect a long `PD` wait since it is usually fully allocated.)

Submit with override if needed:
```bash
sbatch --partition=stingy --gres=gpu:a100:1 --time=04:00:00 \
  /home/sychan552/scratch/CHATTIME/Chattime/submit_ili_fulltest.sh
```

## 4. Environment (conda `mlflu_hpc`, Python 3.9.25)

- **Activate via PATH-prepend, NOT `conda activate`** (fails on GPU nodes):
  ```bash
  export PATH="/home/sychan552/.conda/envs/mlflu_hpc/bin:$PATH"
  ```
- Module preamble (run FIRST on any node):
  ```bash
  module unload default && module load old_modules
  ```
- HF cache (set before any python that loads the model):
  ```bash
  export HF_HOME=/gpfs1/scratch/sychan552/CHATTIME/.cache
  export TRANSFORMERS_CACHE=$HF_HOME
  export HF_DATASETS_CACHE=$HF_HOME
  ```

### Required runtime deps (install with `--no-deps` to protect numpy/torch)
Verified-present: `sentencepiece`, `protobuf` (6.33.6), `scipy`, `matplotlib`, `scikit-learn` (1.6.1),
`datasets` (4.5.0), `gdown` (5.2.2), `accelerate`, `huggingface-hub`.

**MISSING (hit on 2026-08-13, job 502105 failed at deps guard):**
- `statsmodels` — needed by `similarity_screen.py` (ADF + STL).
  Install: `pip install --no-deps statsmodels`
- `patsy` — required by `statsmodels` at import time (NOT pulled by `--no-deps`).
  Install: `pip install --no-deps patsy`
  → After both: `python -c "import statsmodels; print(statsmodels.__version__)"` must print.

> The `setup_chattime_hpc.sh` install list omitted `statsmodels`+`patsy`. Re-run setup
> after adding them, or install manually once per fresh env.

## 5. Model Weights

- Repo: `ChengsenWang/ChatTime-1-7B-Chat` (public, base LLaMA-2-7B).
- Cached via `huggingface_hub.snapshot_download` into `HF_HOME` (13 files, ~40s on first pull).
- `reference/ChatTime/model/model.py` calls `LlamaForCausalLM.from_pretrained(model_path)`
  with `model_path="ChengsenWang/ChatTime-1-7B-Chat"` (a **repo ID**, resolved via `HF_HOME`).
  The `models--ChengsenWang--ChatTime-1-7B-Chat/snapshots/<hash>/` dir must exist — it does.
- A stray symlink `models--ChengsenWang/ChatTime-1-7B-Chat -> weights/...` is harmless
  (transformers ignores it; only the double-dash cache dir is used).

## 6. Upload from Local (Windows)

- `rsync` is **not** in plain PowerShell. Use **Git Bash** (ships rsync):
  ```bash
  cd /c/Users/Asus/Desktop/Chattime
  rsync -avz --delete \
    --exclude='.git' --exclude='__pycache__' --exclude='*.pyc' \
    --exclude='.cache' --exclude='results/local_dry_run/' \
    ./ sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/Chattime/
  ```
- **PowerShell `scp` fallback** (no `--delete`; also uploads `.git/`+`__pycache__/`):
  ```powershell
  scp -r scripts data reference/ChatTime submit_ili_fulltest.sh submit_chattime_repro.sh ILI.csv `
    sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/Chattime/
  ```
  Lean upload: first `Remove-Item -Recurse -Force .git, __pycache__` locally.

> **GOTCHA (2026-08-13, job 502122)**: editing a submit script LOCALLY does NOT auto-sync to
> HPC. If you only `scp` the `.py` files, the HPC still runs the OLD submit script → wrong
> partition / params. **Always re-upload every changed `submit_*.sh` alongside the `.py` edits.**
> Verify on HPC after upload: `ssh sychan552@burgundy.hpc.cityu.edu.hk "grep -n 'partition' /home/sychan552/scratch/CHATTIME/Chattime/submit_ili_fulltest.sh"`
> (expect `#SBATCH --partition=stingy`).

### Figure output convention — Phase 1 MIFlu paper-protocol (AUTHORITATIVE, 2026-08-16)

**The authoritative MIFlu pipeline IS the L=24/36/48/60 four-horizon INDEPENDENT sweep.**
This is the only result source for the paper-protocol deliverable. See
`docs/full_repo_audit_report.md` §A.3 and §B for the full rationale (and why the old
ChatTime L=52 line was archived).

- Model: fine-tuned **MIFlu** (`scripts/train_miflu.py` + `miflu_model.py` +
  `textual_embedder.py`), NOT the 7B ChatTime base.
- Protocol: `L ∈ {24, 36, 48, 60}` are FOUR SEPARATE runs (each 10 reps, 70:10:20 split,
  scaler fit on TRAIN only, test target start strictly > val end). NOT a single rolling
  L=52 walk-forward.
- Pipeline entry point: `scripts/submit_miflu_paper_protocol.sh`. Submit the four horizons
  as FOUR independent `stingy` jobs (one GPU each):
  ```bash
  for L in 24 36 48 60; do
    MIFLU_HORIZON=$L sbatch /home/sychan552/scratch/CHATTIME/Chattime/scripts/submit_miflu_paper_protocol.sh
  done
  ```
- Outputs (never confuse with the deprecated walk-forward CSV):
  - `data/results_miflu_paper_protocol_*.csv` (raw per-rep)
  - `data/results_miflu_paper_protocol_table_*.csv` (tidy table — the conclusion source)
  - `data/predictions_miflu_L{L}_paper_protocol.csv` (per-horizon, `split` column)
  - `checkpoints/best_miflu_L{L}.pth`
  - Figures via `scripts/make_miflu_evaluation_figure.py` (reads the split-CSV, **test only**):
    `fig_miflu_eval_continuous_L{L}.png` etc.
- Metric/indicator computation: `scripts/compute_miflu_indicators.py` (per-horizon Timing /
  Peak-Hit / Peak-Intensity, Fix-Brief #3 semantics). Feature check: `feature_verification.py`.

> **DEPRECATED (Phase 2 ChatTime comparison line — archived, do NOT run for Phase 1):**
> The old ChatTime-1-7B-Chat L=52 continuous walk-forward (`Hist=104/Pred=52/stride=52`)
> was archived on 2026-08-16 to `*_DEPRECATED.*`:
> `submit_ili_fulltest_DEPRECATED.sh`, `scripts/run_ili_walkforward_DEPRECATED.py`,
> `scripts/make_ili_fulltest_figure_DEPRECATED.py`, `scripts/compute_peak_metrics_DEPRECATED.py`.
> Its figure was `results/ili/figures/fig_ili_fulltest_continuous.png` (FluSight aggregate MAE
> over the full test period). It is kept only as a Phase-2 reference, NOT a Phase-1 deliverable.

### GOTCHA — local↔remote divergence caused two forked pipelines (2026-08-16)
On 2026-08-16 the local `train_miflu.py` was rewritten for the paper protocol (L=24/36/48/60
independent sweep) but had **never been uploaded to HPC**. The remote still carried only the
old ChatTime L=52 line, so two silently divergent pipelines existed. **Checklist before ANY
future HPC run:**
1. After editing any `scripts/*.py` or `submit_*.sh` LOCALLY, **re-upload it to HPC** (the
   sandbox does NOT auto-sync). Verify with `ssh ... "ls -la --time-style=+%Y-%m-%d_%H:%M scripts/train_miflu.py"`
   and confirm the mtime matches your local edit + `grep -n 'L_list' scripts/train_miflu.py`
   shows `[24, 36, 48, 60]`.
2. After editing `HPC_GUIDE.md` LOCALLY, **also update the copy on HPC** (HPC runs consult the
   remote copy). They drifted: the remote §6 still banned the L=24/36/48/60 sweep.
3. Confirm the active `submit_*.sh` on HPC matches the intended protocol. If you see
   `submit_ili_fulltest*.sh` (non-DEPRECATED) or `run_ili_walkforward.py` active, you are on
   the OLD ChatTime line — stop and use `submit_miflu_paper_protocol.sh`.
4. Re-run `docs/full_repo_audit_report.md` §B.5 sync check whenever protocol changes.

## 7. Download Results Back

> **MANDATORY (user rule, 2026-08-13)**: After EVERY HPC graph/training run, the produced
> figures MUST be pulled back to the LOCAL project for viewing + evidence. The HPC copy alone
> is not sufficient — the user needs the PNGs on their own machine. Treat this as a required
> final step of any job that emits figures (not optional).
> Local landing dir convention: `results/ili/pc_results/`.

```powershell
# Local PowerShell — pull the main continuous figure + metrics JSON (passwordless)
New-Item -ItemType Directory -Force -Path "C:\Users\Asus\Desktop\Chattime\results\ili\pc_results" | Out-Null
scp "sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/Chattime/results/ili/figures/fig_ili_fulltest_continuous.png" `
    "C:\Users\Asus\Desktop\Chattime\results\ili\pc_results\"
scp "sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/Chattime/results/ili/ili_peak_metrics.json" `
    "C:\Users\Asus\Desktop\Chattime\results\ili\pc_results\"
scp "sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/Chattime/results/ili/ili_fulltest_walkforward.csv" `
    "C:\Users\Asus\Desktop\Chattime\results\ili\pc_results\"
ls "C:\Users\Asus\Desktop\Chattime\results\ili\pc_results\"
```

```bash
# Git Bash / local — full results tree + latest log (passwordless)
scp -r sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/Chattime/results/ili/ ./results/ili/
scp sychan552@burgundy.hpc.cityu.edu.hk:/home/sychan552/scratch/CHATTIME/Chattime/logs/ili_slurm_*.out ./logs/
```

## 8. Job Lifecycle (passwordless — assistant-driven)

```bash
# Submit + monitor, all via the full-domain host (no password prompt)
ssh sychan552@burgundy.hpc.cityu.edu.hk "sbatch /home/sychan552/scratch/CHATTIME/Chattime/submit_ili_fulltest.sh"
ssh sychan552@burgundy.hpc.cityu.edu.hk "squeue -u sychan552"
ssh sychan552@burgundy.hpc.cityu.edu.hk "tail -f /home/sychan552/scratch/CHATTIME/Chattime/logs/ili_fulltest_slurm_<JOBID>.out"
ssh sychan552@burgundy.hpc.cityu.edu.hk "scancel <JOBID>"   # cancel a pending/running job
```

## 8b. ILI CGTSF Ablation — Three Orthogonal Context Arms

The ILI CGTSF walk-forward (`submit_ili_cgtsf.sh`) runs **three independent
context arms**, never mixed:

| STAGE | `--mode` | Context | Output dir | Prefix |
|---|---|---|---|---|
| A  | `national`  | PURE Open-Meteo weather (centroid 39.8,-98.6) — NO text | `results/ili/ablation_national/` | `cgtsf_` |
| A2 | `phase25`   | PURE LLM-text (multivariate + OxCGRT) — NO weather      | `results/ili/ablation_phase25/`  | `phase25_` |
| B  | `regional`  | PURE Open-Meteo weather (10-HHS blend) — NO text       | `results/ili/ablation_regional/` | `cgtsf_regional_` |

- A and B need the Open-Meteo weekly CSVs (fetched in step (0)); A2 needs NO weather.
- `SKIP_WEATHER=1` skips weather fetch + STAGES A & B; **STAGE A2 still runs**
  (fast pure-text re-run). Do NOT confuse A2 with A — they are different arms.
- `national` is pure weather ONLY (reproduces job 502355). The old "Phase 2.5
  hijacked `--mode national`" bug is fixed; `--mode phase25` is its own flag.
- Lean upload for a re-run: `scripts/` + `reference/ChatTime/` +
  `submit_ili_cgtsf.sh` + `PROJECT_STATE.md` (weather cache is uploaded with the
  project, so step (0) is a fast no-op if present).

## 9. Known Blockers (phase-dependent, NOT ILI-job blockers)

- CGTSF `MSPG.csv` / `LEU.csv`: 404 on HF `ChengsenWang/CGTSF` (only PTF ships in repo).
- ZSTSF (ETT/Weather/Electric/Exchange/Traffic): Google Drive **folder** link, not
  auto-downloadable → manual fetch required. These block full Table 4/5 reproduction
  only; the ILI full-test walk-forward job (`submit_ili_fulltest.sh`) loads
  `data/raw/national_ili.csv` directly + cached model and is unaffected.

## 10. 🔴 RESOURCE-REQUEST RED LINE (official manual, highest priority)

> Official manual verbatim: "intentionally requesting excessive resource to take
> advantage of this policy is strictly prohibited. Users' actual workloads are closely
> monitored, and repeat offences of this rule will lead to **account suspension**."

**HARD RULE — never inflate resource requests to jump the queue or dodge QOS:**
- ❌ Do NOT request a full node (`-N 1 --exclusive`) when you only need 1 GPU.
- ❌ Do NOT request multiple GPUs (`--gres=gpu:a100:2+`) when the job uses only 1.
- ❌ Do NOT pad `--time` beyond real training need (e.g. asking 04:00:00 for a 30-min job
  is borderline; only do it for genuine headroom, never as a queue tactic).
- ✅ LEGITIMATE scheduling strategies (allowed, NOT abuse):
  - `--array=0-N%1` job arrays (serially throttled) — see §11 for the QOS caveat.
  - `--dependency=afterany:<prev>` chains (one pending slot at a time).
- **Self-check before EVERY `sbatch`**: confirm the partition/GRES/time match the job's
  actual demand. If you cannot justify each requested resource from the real workload,
  do not submit.

## 11. QOS / Job Reason Codes (verified against official manual, 2026-08-17)

- Per-user `stingy` QOS caps: **`Jobs = 1`, `Submit Job = 1`** (i.e. **max 1 PENDING job
  per user**). A second pending job (or pending dependency) is rejected with:
  - **Reason code `QOSMaxSubmitJobPerUserLimit`** — this is the exact error hit when
    submitting the L=36/48/60 array (and when trying to chain L=60 behind L=48 while L=48
    was still pending). It belongs to the **QOS(Resource)Limit** family, specifically the
    *Max Submit Jobs Per User* sub-limit (NOT `MaxJobsPerAccount` / `GrpTRES` / `GrpWall`).
- **Practical consequence**: at any moment only ONE job may be in `PD`. To run a sequence
  (L=48 → L=60) you must wait until the first is `R` (or done) before submitting the next,
  OR rely on a background auto-submit loop (used for L=60 here). A static
  `--dependency=afterany` chain is rejected while the predecessor is still pending.
- **`job_array` QOS exists** (MaxJobs=500) but our training jobs run under the `stingy`
  QOS, so an array still counts toward the `stingy` Submit-Job=1 limit → arrays are
  rejected the same way. (Array is fine only if the account's QOS permits >1 pending.)
- **Always diagnose with `showqos` first** when a submit fails — do NOT guess:
  ```bash
  showqos                                   # lists all QoS rules for this account
  squeue -u sychan552                       # current jobs (note: this cluster's squeue
                                            # rejects bare `-V`; use `squeue -j <id>`)
  sacct -u sychan552 --starttime 2026-08-15 # historical job states
  ```
- **Backfilling**: setting `--time` *shorter* (but still safely above real runtime) can
  shorten queue wait, because the scheduler backfills "gap-filling" short jobs. Our
  `submit_miflu_paper_protocol.sh` uses `--time=04:00:00`; real training is ~30 min
  (L=36 took 30 min). **Do NOT lower it blindly** — first confirm historical elapsed
  times, then consider `02:00:00` if consistently <90 min. Keep stingy's 4h hard cap.

## 12. Scratch Data-Retention Policy (official manual)

- `scratch` (`/gpfs1/scratch/...`) has **NO backup**. "Unused files will be erased
  regularly" — the cluster purges stale scratch data without notice.
- **HARD RULE — pull important outputs off HPC after each job**:
  - After **every horizon completes**, `scp` back `checkpoints/best_miflu_L{L}.pth` AND
    `data/predictions_miflu_L{L}_paper_protocol.csv` (and the results CSVs) to LOCAL.
  - Do NOT rely on HPC scratch as long-term storage. Local landing dir:
    `checkpoints/` + `data/` in this repo (already the convention).
  - This applies to Regional runs too (Table VI): `best_miflu_regional_L*.pth` etc.

## 13. Connection Reference (official)

- **Login (use this):** `ssh <EID>@burgundy.hpc.cityu.edu.hk`.
- **Backup IP (if DNS fails):** `ssh <EID>@144.214.138.99`.
- Passwordless key auth is active (see §1); the assistant drives remote ops via
  `ssh sychan552@burgundy.hpc.cityu.edu.hk "cmd"`.
- If `squeue`/Slurm client misbehaves on a given login node, retry
  (observed 2026-08-17: `squeue -u sychan552` errored on one node, `squeue -j <id>` worked).
