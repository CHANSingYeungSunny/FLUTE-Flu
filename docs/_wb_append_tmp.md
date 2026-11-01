### 13.H Overnight queue (built and submitted 2026-11-01 22:35) — the master controller

**What this is.** A single disk-backed queue (`hpc_experiments/queue/master_queue.tsv`, 207 rows)
that two GPU controllers consume in **disjoint halves** (stripe = `cksum(task_id) % 2`) plus a CPU
worker and a watcher on `tiny`. It exists because the operator cannot monitor overnight and because
`stingy` is `MaxSubmitJobsPerUser=1` + `PreemptMode=CANCEL`, so no single job can be relied on.

| piece | file | what it does |
|---|---|---|
| queue | `hpc_experiments/queue/master_queue.tsv` | the durable state: `task_id, kind, model, L, seed, priority, state, attempts, last_job, note`; every transition written `.tmp`+`mv` under a `flock` |
| generator | `make_queue.py` + `arms_registry.json` | writes the canonical task list; without `--force` it **merges**, so re-running never destroys recorded state |
| controller | `master_controller.sh` | one worker, A100 assertion, per-task timeout, 2-attempt skip, `HALT` honoured, stale `RUNNING` reset, self-requeue (`stingy`) or `sbatch` successor (`gpu_a100`), verified continuation |
| task runner | `master_task.py` | one task: MIFlu cell (reuses `miflu_controller_v2`), LLM cell (`train_backbone_966 --backbone llm_encoder`), or CPU probe |
| CPU worker | `cpu_worker.sh` | downloads + revision pin + 2-layer hidden-state smoke; flips `BLOCKED_MISSING_WEIGHTS → TODO/SKIPPED`. No gres line, because the controller's header would otherwise ask for a GPU on `tiny` |
| watcher | `watchdog.sh` | restarts any lane whose jobs have all vanished; 30 submits / 2 days, self-requeues at end of life |

| priority | content | cells | expected |
|---|---|---|---|
| **P0** | 22 missing MIFlu reproduction cells (7-var export + per-seed oracle gate) | 22 | **finishes** ~04:45 (both stripes), highest confidence |
| **P1** | `Qwen/Qwen2.5-1.5B` × 12, label `qwen25_1_5b` — the first real LLM benchmark row | 12 | likely done by ~06:30; first-ever run of this arm, so a harness failure is possible |
| **P2** | 13 arms × 12 = 156 cells, all `BLOCKED_MISSING_WEIGHTS`; 13 probe rows drive the unblocking | 156 | **cannot finish tonight.** Gated on the CPU worker landing weights; ~12 cells per arm per hour of GPU |
| **P3** | `WORK_BREAKDOWN` §13.D leftovers (Table VI/VIII/IX, rolling origin) as `unimplemented` placeholders | 4 | only reached if P0–P2 are all resolved (they will not be) |

**Arithmetic limit, stated plainly.** 168 LLM cells × ~10 min ≈ **28 GPU-hours**. The queued GPU wall
over the next 24 h is ~26 h (12 h job A + 4 h job B + a 4 h and a 6 h later window), so the full 14-arm
roster is **not** reachable tonight; it becomes reachable only if every queued window is granted and
the CPU worker lands all the weights. MIFlu 40/40 is the outcome that matters most and does not depend
on the CPU worker at all.

**Morning read (the one file to open):** `hpc_experiments/queue/queue_state.tsv` — one row per attempted
task with `state`, `attempts`, `wall_seconds`, `gate` (the 7-var z-space MSE, always on the shared
`(W//16)*16` windows) and `last_job`. `queue_events.log` is the narrative, `logs/<task_id>.log` the raw
task output, `p2/<slug>.json` the per-model probe record (revision sha, hidden dim, or the measured
reason it failed).

