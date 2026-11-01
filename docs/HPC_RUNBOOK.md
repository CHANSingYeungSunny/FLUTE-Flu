# docs/HPC_RUNBOOK.md — CityU HPC Burgundy, operational

> **What this is:** everything needed to *operate* the cluster, moved verbatim out of `AGENTS.md` §4 — the ssh incantation, paths, partitions, disk, the environment-tooling facts (`conda` is gone), A100 memory measurements, `stingy` QOS, and the twelve gotchas each of which already cost hours. Ends with `AGENTS.md` §2 rule 13 restated as an operator checklist.
> **When to read it:** before the first `ssh`/`scp`/`sbatch` of a session, before any GPU submission, and before writing an instruction that tells a future agent to create an environment.
> **What it points to:** `docs/LLM_ARMS.md` (the `mlflu_llm` venv, fp8/bf16 facts, load-test numbers), `docs/STATE.md` (which runs exist), `docs/WORK_BREAKDOWN.md` §13.E (operational status), `paper_tables/BENCH_GPU_PROVENANCE.csv` (which hardware produced which cell).
> **Depends on:** `AGENTS.md` §2 rules 12 and 13 (provenance and publication-grade runtime policy — normative), `LOOP_ENGINEERING.md` §4 (harness facts the loop depends on).
> **Chain:** `AGENTS.md` → **this file** → `docs/LLM_ARMS.md` / `docs/MIFLU_MERGE_BLOCKED_20261101.md` for the specific job.

---

## 4. HPC (CityU Burgundy) — operational knowledge

```bash
# working SSH incantation from Windows PowerShell (alias `cityu`)
ssh -n -o BatchMode=yes -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 \
    -o PreferredAuthentications=publickey cityu "<cmd>"
```
Without `PreferredAuthentications=publickey` auth falls through and fails.

| Item | Value |
|---|---|
| Code dir on HPC | `/gpfs1/home/sychan552/stage5_a2_durable/code` (flat, no `scripts/`) |
| Data dir | `/gpfs1/home/sychan552/stage5_a2_durable/data` |
| Runs | `author_runs/` (MIFlu), `expanded_runs/` (benchmark) |
| HF cache | `/home/sychan552/scratch/hf_cache` (on **scratch**, not home) |
| Conda python | `/home/sychan552/.conda/envs/mlflu_hpc/bin/python` |
| Partitions | `stingy` (**1 job/user — no pending slot**, 4 h, **preemptible**), `gpu_a100` (uncapped, 5 d, **congested**), `gpu_v100s` (uncapped, 5 d), `tiny`/`batch` (CPU), `highmem_2t` (2 TB RAM) |
| Disk | home 41/~100 GiB (**do not put models here**); scratch 353/~1024 GiB |
| **Environment tooling** | **`conda` is GONE from this cluster** (measured 2026-11-01). `module load Conda/1.10.0` fails — `module spider Conda` shows it is only an *extension* of `IJulia/1.24.2`. `MODULEPATH` contains just `default`, `old_modules`, `ood-desktop`, `ood-jupyter`; `miniconda/*` and `Miniconda3/24.7` exist but are **unloadable** (their parent modules `old_modules` / `default` load silently yet leave them unavailable). There is **no conda binary anywhere in `$HOME`** — only stale trees `/home/sychan552/.conda/{pkgs,envs}` from 2026-08-06. **Any instruction of the form "conda create / conda activate / conda clone" is wrong.** Use the system interpreter: `/usr/bin/python3.11 -m venv /home/sychan552/.venvs/<name>` |
| **A100 memory** | `stingy`'s A100s are **SXM4-80GB (81,920 MiB)**, *not* 40 GB (measured from job 718448's `nvidia-smi`; the probe reports 85.1 GB decimal). **CORRECTION (job 718976)**: the 28.7 GB fp8 checkpoint does **not** stay 28.7 GB in VRAM — transformers dequantises fp8→bf16** on sm_80, so Qwen3.8-27B actually occupies **54.73 GB after load / 55.10 GB peak**. The 80 GB cards are therefore *required*, not merely convenient; a 40 GB A100 could never have held it |
| **`stingy` QOS** | **ONE job per user — there is no pending slot.** Measured 2026-11-01: `sacctmgr show qos partition-stingy` → `MaxSubmitJobsPerUser=1, MaxJobsPerUser=1`. A running stingy job therefore **cannot submit a successor**: every `sbatch` returns `QOSMaxSubmitJobPerUserLimit` / "Job violates accounting/QOS policy". **An earlier version of this runbook said "1 submitted + 1 running"; that was WRONG. Every occurrence elsewhere in this file has been corrected to match this row.** `gpu_a100` allows 30 submitted / 15 running but its `StartTime` for a probe submitted 2026-11-01 18:10 was **2026-11-02 19:29** (congested). `gpu_v100s` cannot be substituted for fp8 work (V100 = sm_70, fp8 needs sm_89+) |
| **`stingy` is PREEMPTIBLE and does NOT auto-requeue** | `stingy` runs `PreemptMode=CANCEL`. **Observed 2026-11-01 18:53:57:** job **719030** was killed after 13 min (epoch 2/20) when a higher-tier `special_cs` job (**719072**, another user) landed on `gpu-a100-04`; `sacct` shows `PREEMPTED`, ExitCode `0:15`, and the same event preempted another user's job 718087 at the same second. It never reached its own wall-clock guard, so it never attempted a self-requeue. **Every long `stingy` job must assume it can vanish at any moment and must be externally resumable.** |
| **How to chain work on `stingy` (replaces gotcha 8)** | Do **not** rely on `sbatch`-self-requeue — structurally impossible under `MaxSubmitJobsPerUser=1`. Use **`scontrol requeue $SLURM_JOB_ID`**: same job id, no new submission, so QOS cannot reject it. Belt-and-braces: an external low-cost watcher on the CPU partition (`tiny`, e.g. 12 h) that polls `sacct` and resubmits after a preemption. Both were validated 2026-11-01 (controller 719222 + watcher 719234). |

### Critical gotchas (each cost hours already)
1. **`HF_HUB_CACHE` must be set** alongside `HF_HOME` when the cache was populated
   with `cache_dir=$HF_HOME`. Otherwise transformers looks in `$HF_HOME/hub/` and
   reports "couldn't find them in the cached files" even though the weights exist.
2. **Compute nodes have NO internet.** Download on the **login node**, train offline
   with `TRANSFORMERS_OFFLINE=1 HF_HUB_OFFLINE=1`.
3. **Some GPU nodes have `nvidia-smi` stuck in uninterruptible sleep** — a job hangs
   forever there and `timeout` cannot kill it. Test on CPU or another partition.
4. `scp` to a Windows path must **not** end with a backslash.
5. Windows PowerShell mangles quotes/`$()` inside `ssh "..."` — write remote scripts
   to a file, `scp`, `sed -i 's/\r$//'`, then run.
6. `train_backbone_966.py` is imported **by file path** (`importlib`), so
   `innovation/` must be uploaded as a package tree to the code dir.
7. `cdc_calendar.load_week_calendar` needed a patch to accept the author's `date`
   column (done, in repo).
8. ~~Chained jobs: stingy allows 1 pending, so a controller self-requeues with `sbatch`.~~
   **WRONG — do not do this.** `stingy` is `MaxSubmitJobsPerUser=1`: a running job cannot
   queue a successor, and `stingy` is `PreemptMode=CANCEL` so jobs vanish without requeue.
   Use `scontrol requeue $SLURM_JOB_ID` plus an external watcher on `tiny`. See the
   three "`stingy` QOS / PREEMPTIBLE / How to chain" rows in the table above.
9. **NEVER run large downloads on the login node.** `nohup python dl_ds32.py &`
   (a 66 GB HuggingFace download writing to `/home/sychan552/scratch/hf_cache` on
   GPFS) is the most likely cause of the repeated "auth succeeds then zero bytes"
   outages on 2026-11-01. Submit transfers as a job instead:
   `sbatch --partition=batch --wrap "HF_HOME=... HF_HUB_CACHE=... python dl_x.py"`.
   If unavoidable, `nice -n 19` it, cap concurrency, record its PID here, and kill it
   before the turn ends.
10. **Do not run concurrent recursive `du -sh` over scratch/`hpc_results`.** Parallel
   traversals of a 353 GB GPFS tree cause a metadata storm that can hang the login
   node for every user. One at a time, or use quota commands.
11. **Failure signature to recognise**: `ssh -vv` → DNS OK → TCP/22 OK →`Authenticated ... publickey` → `exec request accepted on channel 0` → **zero bytes
   forever**; plain `ssh`, `-tt` and `sftp` all hang identically. This is **not** a
   credential problem and retrying cannot fix it: the login shell cannot be spawned
   (per-user process/cgroup limit exhausted by leftover background processes, or a hung
   GPFS mount). Recovery needs the sysadmin; a remote `pkill` is impossible because no
   shell runs. First commands when access returns:
   `ps -u $USER -o pid,stat,etime,cmd | head -30`, `pkill -f dl_ds32.py`,
   `pkill -f 'du -sh'`.
12. **CORRECTION to gotcha 9 (2026-11-01, evidence from `ps` on the recovered node)** — the
   login-node outages were **NOT** caused by the 66 GB `dl_ds32.py` download. When access
   returned, `ps -u sychan552` showed **no download process at all**, and `hf_cache` was
   still 45 G. The actual culprits were **two `python -c "import transformers"` probes stuck
   in state `D` (uninterruptible sleep)** for ~5 minutes, plus their parent `bash -c`
   wrappers which also ran `du -sh` over the conda env (one for 15 minutes). Those were
   diagnostic commands issued to check the transformers version. A `D`-state process
   **ignores `kill -9`** until its I/O completes, and while it holds the login session the
   shell cannot be spawned — which is exactly the "auth OK, zero bytes" signature.
   **Practical rules**: (a) never run `import <heavy lib>` or `du -sh` over conda/GPFS trees
   on the login node as a probe — use a short `sbatch` or a cached-file check instead;
   (b) if a probe is needed, wrap it with `timeout 20s`; (c) gotcha 9's ban on login-node
   downloads still stands as hygiene, but it is **not** the proven cause of these outages.

---

## Hardware / partition policy — `AGENTS.md` §2 rule 13, restated as an operator checklist

`AGENTS.md` §2 **rule 13 is the normative text**; the list below is the same policy expressed as the steps an operator actually performs. Rule 12 (measured provenance) is the companion obligation.

1. **Classify the run first.** Ask: *can this number appear in `paper_tables/*`, any figure, or any claim?*
   - **Yes → publication-grade.** It must execute on an **A100 in the `stingy` partition** (primary choice). `gpu_a100` is acceptable **only if** its queue `StartTime` is acceptably short — it has been booked many hours to a full day ahead, which is usually not viable.
   - **No → probe.** Other partitions and other GPU models are for probing only (feasibility, deployability, "can this model load and forward at all"). Mark them `probe_only=True` in the manifest and keep them out of every aggregation; they must never enter `paper_tables/*`, a figure, or a claim.
2. **Probe, then re-run for real (mandatory pre-flight).** Before a real submission, probe on whatever node is free to confirm it deploys — then **re-run the publication-grade pass on A100/`stingy`**. The probe result is discarded; only the A100/`stingy` run counts.
3. **Assert the hardware you actually got.** At run start, read `torch.cuda.get_device_name(0)` and exit non-zero on anything that is not an A100. A V100 cell is **invalid for the comparison** and must be re-run — never "adjusted".
4. **Record provenance (§2 rule 12):** GPU model / count / compute capability, Slurm partition, `SLURM_NODELIST`, `SLURM_JOB_ID`, start and end timestamps, wall-clock seconds, library versions, code identity.
5. **Label every table.** Every result table must state in its note: **GPU = A100-SXM4-80GB, partition = `stingy`, CityU HPC Burgundy.** If any row deviates, the table is invalid until fixed. A table that unavoidably mixes GPU models must state the mix, and **no timing claim may be drawn across it**.
6. **Status of the old hardware mix.** AGENTS.md's 10-line summary item 5 still says the hardware confound is open (12 NLinear cells on V100). **That is superseded as of 2026-11-01:** all 204 benchmark cells are now A100-SXM4-80GB (paper_tables/BENCH_GPU_PROVENANCE.csv, 0 non-A100) and the V100->A100 delta left the K&S verdict unchanged. Authoritative record: docs/STATE.md §1.5.
7. **Queue reality check before you rely on a slot:** `stingy` = **1 job per user with no pending slot, and it is preemptible** (see the QOS rows above), so a running training job both starves every probe and can be killed at any moment (`docs/LLM_ARMS.md` records the measured `StartTime` evidence); `gpu_v100s` cannot substitute for fp8 work (V100 = sm_70, fp8 needs sm_89+).



---

## Cluster occupancy: squeue/sinfo are NOT authoritative here (measured 2026-11-01, cost two wrong diagnoses)

**On CityU Burgundy, squeue is user-scoped.** squeue -u <me> shows only my jobs, and even
squeue -a -t R returned **zero** GPU rows for me while **20 of 20 gpu_a100 GPUs were
allocated to other users**. sinfo likewise showed mix/idle counts that did not reflect
actual GRES allocation, because the idle nodes in stingy are **CPU-only cpunode-*** —
the GPU nodes are the explorer-* / gpu-a40-* / gpu-a100-* entries.

**Authoritative commands — use these instead:**

`ash
scontrol show node <node>            # read AllocTRES / CfgTRES for gres/gpu
sacct -a -s R -N <node>              # who is actually running on that node
scontrol show node <node> | grep -E 'State|AllocTRES'
`

**Worked example (the night of 2026-11-01):**
scontrol show node gpu-a100-{07,08,10,11,12} → gres/gpu:a100=4 allocated of 4 on **each**
= 20/20 in use; gpu-a100-09 = DOWN+DRAIN+NOT_RESPONDING. stingy → 14/14 healthy GPUs
allocated; the single idle GPU was the 4th on gpu-a100-05, a node whose CUDA context is dead
(CUDA-capable device(s) is/are busy or unavailable) and which must stay excluded.

**And do NOT try to defeat this by shortening the wall clock.** Falsified by direct test:
2 h → StartTime 02:50:39, 45 min →  2:50:39, 25 min →  2:50:39, **12 min →  2:50:39**.
A 10x wall reduction changed nothing, so the constraint is **availability, not backfill**. A
3-minute probe that started in ~40 s earlier the same day did so because a GPU happened to be
free at that instant — that is not evidence of backfill and must not be generalised.

**Practical consequence:** when the queue is full, the right move is to leave **one** parkable
job queued (Requeue=1, modest budget, --exclude the dead node) plus a low-cost 	iny
watcher, and record StartTime in the ledger. Do not churn submissions, do not shrink walls,
do not spawn parallel controllers — none of those create GPUs.

---

## PARTITION POLICY — which partitions may produce paper numbers, and which may not (user-set 2026-11-01 23:42)

| Partition | Role | May it produce a number that enters paper_tables/? |
|---|---|---|
| **stingy** | **publication-grade** (primary) | **YES** — A100-SXM4-80GB, must be recorded per rule 13 |
| **gpu_a100** | **publication-grade** (secondary) | **YES** — same A100-SXM4-80GB hardware, must be recorded |
| gpu_v100s | testing / probing only | **NO** — V100-SXM2-32GB, sm_70, no TF32; probe_only=True |
| highmem_2t, highmem_1500g, highmem_4t | testing / I/O only (downloads, smoke tests) | **NO** |
| atch | testing / I/O only | **NO** |
| 	iny | **scheduler / watchdog / driver only** (the role the login node used to play) | **NO** |
| coursework | do not use | **NO** |

**Rationale:** the benchmark's 204 cells are all A100-SXM4-80GB (rule 12/13); any number produced elsewhere is a hardware confound, not a measurement. Conversely, work that produces **no** measured number — weight downloads, revision pinning, hidden-state smoke tests, queue driving, table rebuilding from existing npz — must be pushed onto whatever partition is free, to maximise throughput without touching the results.

### Measured partition state (2026-11-01 23:40, sinfo)

`
batch*          112 nodes   all alloc          <- saturated, poor choice
tiny             13 mix / 18 alloc             <- usable for drivers
gpu_a100          5 mix / 1 drain (gpu-a100-09) <- publication-grade, contended
gpu_v100s         5 mix / 1 drain              <- testing only
highmem_2t        1 IDLE                       <- free right now, ideal for downloads
highmem_1500g     1 IDLE                       <- free right now
highmem_4t        1 alloc
stingy            8 idle (all cpunode-*) / 8 mix / 13 alloc / 5 resv
coursework        1 resv
`

**Note:** idle counts in stingy refer to **CPU-only cpunode-***; its GPU nodes are the explorer-* / gpu-a40-* / gpu-a100-* entries and are mix/esv. Never read sinfo's idle count as free GPUs — use scontrol show node <n> | grep AllocTRES.

### Standing loop-driver topology (validated)
- **Compute** → stingy (uninterrupted iff free) and gpu_a100 (earliest backfill window ≈ 02:36–02:50).
- **Single writer** for paper_tables/ + esults/bench_figures/ → one 	iny job holding nalysis/.finalise.lock.
- **Watchdog / successor submitter** → 	iny, polls every 120 s, scontrol-based (never squeue), one-shot sentinel.
- **Downloads / smoke tests** → highmem_* when idle, else 	iny/atch. Never the login node.
### Gotchas 13-16 (measured 2026-11-01 23:33-23:47, from the part-two lane)

13. **highmem_2t / highmem_1500g are NOT available to this account.** They are
    IDLE and have MaxTime=10-00:00:00, but every submission returns
    `sbatch: error: Batch job submission failed: Invalid qos specification`
    because both carry `AllowQos=highmem` while the account's only association
    (`ga_bms_kkhchan`) allows the `normal` QOS. Check entitlement BEFORE
    planning a placement: `scontrol show partition <p> | grep AllowQos` and
    `sacctmgr -n -P show assoc where user=sychan552 format=Account,QOS`.
14. **The `hpc` interpreter is a CONDA env, not a venv.**
    `/home/sychan552/.conda/envs/mlflu_hpc/bin/python` (transformers 4.57.6 +
    pandas). `/home/sychan552/.venvs/mlflu_hpc` **does not exist**. The
    `llm` env (`/home/sychan552/.venvs/mlflu_llm`, transformers 5.x) has
    **no pandas**, so `train_backbone_966.py` cannot even import there - only
    arms that need the `qwen3_5` transformers line may use it.
15. **A cache-placement guard must compare device ids, not path substrings.**
    `/home/sychan552/scratch` is a SYMLINK to `/gpfs1/scratch/sychan552`, so
    `case "$HF_HOME" in *"$HOME"*)` rejects the correct scratch path.
    Use `stat -c %d` on the `readlink -f` of both (they differ: 64 vs 63) -
    that is what `cpu_download_worker.sh` now does.
16. **Batch-mode SSH needs an explicit publickey preference.** `ssh cityu`
    offers `keyboard-interactive,password` only, so
    `ssh -o BatchMode=yes cityu ...` fails with *Permission denied
    (publickey,keyboard-interactive)*. Use
    `ssh -o BatchMode=yes -o PreferredAuthentications=publickey <user>@burgundy.hpc.cityu.edu.hk`.

### Gotcha 17 - sbatch spools the script, so "$0" lies (cost: one entire night of zero cells)
sbatch copies the batch script to /var/spool/slurmd/job<N>/slurm_script and runs THAT.
Any QDIR="$(dirname "$0")" therefore resolves into /var/spool/..., and the job dies on its
first line **while squeue still shows it as a healthy PENDING job**. Measured 2026-11-01:
job 720102 exited in 3 s with successor_lib.sh: No such file or directory then
SUCC_CUTOFF: unbound variable. Two queued lanes would have died at their start time.
**Rule: absolute paths only. Never derive a path from "$0" in an sbatch script.**

### Gotcha 18 - atch and 	iny have different memory-per-CPU floors
- 	iny: DefMemPerCPU=1024 => mem <= cpus * 1024 MB. 32 CPU / 32000 M is accepted.
- atch: rejects 32 CPU / 32000 M with *"32 CPUs-per-node and 32000 MB are too small
  for the Batch partition"* — it demands a higher mem/CPU ratio.
**Rule: size a CPU job against 	iny; before using atch run
scontrol show partition batch | grep -i mem and request at least that ratio.**
Also: a CPU hidden-state probe must LOAD the model (a 4B model needs >8 GB in RAM), so the
8 GB that is plenty for downloading is not enough for the probe - that was the OOM cause.

### Gotcha 19 - the weight fetcher's MODELS must match rms_registry.json exactly
cpu_download_worker.sh line 100 reads MODELS="${MODELS:-}"; line 199 exits 67 when the
filter matches no required arm, and line 201 requires >=11 arms when the filter is empty.
A wrong model string therefore fails in **5 seconds** having downloaded nothing (jobs 720364
and 720519 both did exactly this). **Rule: never type model ids from memory - read the
registry first, then pass the exact strings.**