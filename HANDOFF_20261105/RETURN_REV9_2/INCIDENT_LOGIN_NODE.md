# INCIDENT 2026-11-05 — Burgundy login-node shell exhaustion

**Capture:** 2026-11-05T15:30:00Z / 2026-11-05 23:30 HKT. Fresh, read-only, verified on the live cluster.
**Status:** RECOVERED at 15:22:48 UTC. No Slurm job was lost.

## Timeline (UTC)

| Time | Event | Evidence |
|---|---|---|
| 14:22–14:38 | TCP/22 OK, publickey auth OK, exec + sftp zero bytes | `HANDOFF_20261105/HPC_RECOVERY_WATCH.log`, `HPC_WAIT_NODEADLINE.log` |
| 14:38:14 | `ssh -v`: `Authenticated ... using "publickey"` then hang at `Entering interactive session` | `_connect_now.py` output |
| 14:43:55 | 16-second shell window: `date`, `uptime` (load 20.37/23.73/25.52, 76 users) returned | `HPC_WAIT_NODEADLINE_OUTPUT.txt` |
| 14:44:11 | window dies at `ps -u $USER ... \| head -40`; `SSH_EXIT 255` | same file |
| 14:57 / 14:59 | fresh minimal and `date -u` attempts: zero bytes | `_check_min.py`, `_probe_tiny.py` |
| 15:20:04 | hardened kill-first watcher started (single connection, no deadline) | `HPC_KILL_WINDOW.log` |
| **15:22:05** | **shell window reappears; `pkill` issued as the FIRST command** | `HPC_KILL_WINDOW_OUTPUT.txt` |
| 15:22:05 | `PKILL_D=0` — one `export_miflu_7ch` process signalled; other patterns rc=1 (no match) | `HPC_KILL_WINDOW_STATUS.json` |
| **15:22:48** | `SSH_EXIT 0`, `KILL_COMMANDS_ISSUED`, `CAPTURE_DONE`, full capture written | `REV9_CAPTURE_RECOVERED.md` |
| 15:23–15:30 | post-recovery audit: all Slurm jobs intact | `_audit_kill.py`, `_gap_check.py`, `_diag2.py` |

## Root cause (with evidence-strength qualification, checked 16:00 UTC)

An interactive **CPU** inference of `code/export_miflu_7ch.py` was started on the
**login node** by the interrupted rev9 handoff turn (that turn reported
"CPU inference 太慢，10 分鐘仍未完成，已 kill"). Verified timestamps:
script `20:12:55 HKT`, `export7ch_all.sbatch` `20:37:55 HKT`, job 739549
`SubmitTime=2026-11-05T20:40:26` (so the batch WAS submitted, contrary to that
turn's "cannot confirm submission" note, but it never ran: no `export7ch-*.out`
log exists and `core/export7ch` is empty).

The script imports `torch`, `train_miflu`, `miflu_model`, does `torch.load` of a
checkpoint and iterates a `DataLoader` over all test windows — heavy GPFS I/O
plus a long-lived process running **directly on the login node**, matching
`HPC_RUNBOOK.md` gotchas 10/12. CPU made it slow enough (>10 min for one cell)
to sit in the session for hours.

**How strong is the evidence — be precise:**

| Claim | Status |
|---|---|
| A long-lived `export_miflu_7ch` process existed on the login node | **supported**: `PKILL_D=0` at 15:22:05 UTC means `pkill -f` matched and signalled it |
| It was literally in `STAT=D` | **NOT directly proven**: `ps` never completed during the outage (the 14:43:55 window died exactly at `ps ... \| head -40`). `D` is inferred from the gotcha-11 signature, not observed. |
| The kill caused the recovery | **supported but not proven causally**: a shell window had already appeared spontaneously at 14:43:55 without any kill; D-state tasks can finish on their own. Recovery at 15:22:05 coincided with the kill. |
| `SIGKILL` to a D-state task is pending, not discarded | correct as a Linux mechanism; does not require this specific process to have been in D |
| CPU per se was the problem | **NO** — the violation was running heavy inference on the **login node** instead of a compute node. A GPU forward on the login node would be equally wrong. |

So the accurate statement is: **running the 7-channel recovery as a long CPU
inference on the login node (rather than `sbatch`) is the most likely cause**,
consistent with the documented signature; the exact `STAT` and strict causation
were not measurable. The durable rule stands regardless: no inference,
checkpoint load, HF import or recursive `du` on the login node — use `sbatch`.

At 16:00 UTC a clean `ps` shows **no `D`-state process and no 7ch process**;
the only leftovers are 12 three-day-old `bash -c ... mkdir /.l` lock-test
wrappers in `S` state from 2026-11-02, unrelated to this incident.

## Impact — what was NOT affected (verified via `sacct`)

```
735298 trackB_v2_all_ctl     COMPLETED 21:46:21  0:0
735299 trackB_v2_post_all    COMPLETED 21:50:01  0:0
735300 trackB_v2_all_l0      COMPLETED 12:34:08  0:0
735301 trackB_v2_all_l1      COMPLETED 12:29:00  0:0
739549 miflu_7ch_export      PENDING   (Priority)
737759 legacy_todo_ctl       RUNNING
739626 mlflu_p3_driver       RUNNING
739628 mlflu_p3_s1           PENDING   (Priority)
737762 legacy_todo_ctl       PENDING   (Dependency)
```
`735313`, `736302`, `737938` TIMEOUT (06:00:20) are earlier `stingy` 6h-wall
expiries; `737711` FAILED 3:0 at 14:06 — **all before the 15:22 kill**.
No `CANCELLED` job appears in that window. **No job was killed by the pkill.**

## Why the fix worked

`SIGKILL` to a `D`-state task is pending, not discarded; it takes effect when
I/O returns. The parent `bash -c` wrapper died immediately. Issuing the kill
as the first command of the window (rather than observing first) is the whole
difference. See `04_详细说明文档/HPC_LOGIN_NODE_DSTATE_RECOVERY.md`.

## Prevention (applied)

1. Hard rule recorded in the SOP and in `HPC_RUNBOOK.md` addendum: **no
   inference / checkpoint load / HF import / recursive `du` on the login
   node**; use `sbatch`.
2. Reusable watcher `05_程序代码/hpc_login_node_recover.py` with kill-first,
   bracket self-exclusion, `timeout` guards, disabled client liveness timer,
   single connection, no auto-submit.
3. Any future long-running local watcher must be explicitly stopped by the
   owner; record its PID and `taskkill /PID <pid> /T /F`.

## Two unrelated defects found during the audit (NOT caused by the pkill)

1. **40 blocked national cells** = `ds_r1_distill_qwen1_5b` (all 40). Cause:
   HF cache **layout mismatch**, not missing weights. The pinned revision
   `ad9f0ae…b562` exists at
   `hf_cache/models--deepseek-ai--DeepSeek-R1-Distill-Qwen-1.5B/snapshots/…`
   (legacy top-level layout), but `run_lane_v2.sh` hard-codes
   `HF_HUB_CACHE=$HFC/hub` (new layout), where only
   `.no_exist/8faed761…` exists. Result: `LocalEntryNotFoundError` /
   `OSError: We couldn't connect to 'https://huggingface.co'`, rc=1,
   `BLOCKED_MAX_ATTEMPTS attempts=2`, quarantined to `all/partial/`.
   The other 14 encoder models live under `hub/` and succeeded.
2. **`legacy_lane.sbatch` has a stale `#SBATCH --dependency=afterok:737712`.**
   Job 737712 completed at 14:06; every 5-minute `legacy_ctl` cycle now fails
   with `sbatch: error: Job dependency problem`, so legacy TODO stalls at
   139/189. Fix: remove that line (the live `legacy_todo_ctl` 737759 will then
   submit lanes on its next cycle; no duplicate controller needed).


---

## Remediation actually applied (2026-11-05T15:46:49Z / 2026-11-05 23:46 HKT)

All read-only verification first, then fixes. **No `scancel`, no job cancelled,
no dataset/checkpoint/raw prediction/encoder cache deleted.**

| # | Root cause | Fix | Verification |
|---|---|---|---|
| 1 | Login-node D-state CPU inference (`export_miflu_7ch.py`) wedged shell spawning | `pkill -9` issued as FIRST command in the 15:22:05 UTC shell window; SOP + reusable watcher recorded | `SSH_EXIT 0`, full capture written; all Slurm jobs intact |
| 2 | 40 blocked cells = HF cache **layout mismatch** (pinned revision in legacy `hf_cache/models--…`, but `run_lane_v2.sh` hard-coded `HF_HUB_CACHE=$HFC/hub`) | `run_lane_v2.sh` now picks `HUFC` per cell (`$HFC/hub` if `snap` exists, else `$HFC`), logs `CACHE_LAYOUT` | `try_to_load_from_cache` with legacy layout: `config.json`, `model.safetensors`, `tokenizer.json`, `tokenizer_config.json` all `EXISTS`; `bash -n` passes; backup `run_lane_v2.sh.bak_hfcache_20261105T153748Z` |
| 3 | `legacy_lane.sbatch` had stale `#SBATCH --dependency=afterok:737712` → every 5-min cycle failed `Job dependency problem`, legacy stuck at 139/189 | removed that one line | `legacy_ctl.log` 15:39:08 `Submitted batch job 740169`; job 740169 COMPLETED 00:04:13 exit 0:0; backup `legacy_lane.sbatch.bak_staledep_20261105T153748Z` |
| 4 | 40 cells had no live lane (controller 735298 COMPLETED, `all/phase.done` written) | submitted **ONE** distinctly-labelled job `740183 trackB_v2_fix40` reading only those 40 cells, preserving quarantined partials and archiving (not deleting) old failed markers | `scontrol`: 740183 PENDING, partition gpu_a100, wall 06:00:00, `StartTime=2026-11-07T13:20:16` |

**Not resubmitted:** `739549 miflu_7ch_export` — the correct GPU batch replacement for the
killed login-node inference was **already submitted and still PENDING**. Submitting a
second one would duplicate a live job, which the rev9 prompt forbids. Both 739549 and
740183 currently show `StartTime=2026-11-07T13:20:16` on the congested 6-node
`gpu_a100` partition — that queue wait, not any code defect, is now the binding
constraint on O1.

### Guard bug found and corrected
An exact-name guard `squeue -h -n trackB_v2_fix40 | grep -q .` returned TRUE even with
no such job: this cluster's `squeue -h` still prints `Last update in … seconds ago`
(the `HPC_RUNBOOK.md` cached/user-scoped `squeue` gotcha). It caused a harmless
`ALREADY_SUBMITTED_SKIP`. Replaced with `squeue -h -o "%j" | grep -qx 'trackB_v2_fix40'`
and cross-checked with **`scontrol show job`**, which is authoritative here.

### WARNING: `legacy_done.tsv` 189/189 is NOT scientific completion
`legacy_lane.sh` appends `$task` to `legacy_done.tsv` **unconditionally after every
attempt**, even on failure. The 15:43 UTC lane log shows the last 50 tasks ending:

```
START table6_miflu_L13_s2023 table6_cell
[a100] measured gpu=NVIDIA A100-SXM4-80GB capability=(8, 0) vram=79.2GiB
BRANCH=skip.impossible
SKIP_REASON=bad table6 task id 'table6_miflu_L13_s2023'
END table6_miflu_L13_s2023 rc=3
LANE_END processed=50
```

So `139/189 → 189/189` counts **attempts**, not valid cells. Those 50 tasks need
valid task IDs / configuration matching before any Table VI or walk-forward
claim. This is exactly the rev9 rule "a directory or DONE label alone is
insufficient". Do NOT report 189/189 as completion to ChatGPT.

### Fresh state at 2026-11-05T15:46:49Z

```
core        COMPLETE 160 / 160
national    COMPLETE 1080 / 1120   (40 = ds_r1_distill_qwen1_5b, fix40 queued)
7ch npz     0 / 40                 (739549 PENDING, StartTime 2026-11-07T13:20:16)
739549 miflu_7ch_export  PENDING   739626 mlflu_p3_driver RUNNING
739628 mlflu_p3_s1       PENDING   740183 trackB_v2_fix40 PENDING
737762 legacy_todo_ctl   PENDING   (dependency successor)
737759 legacy_todo_ctl   COMPLETED 740169 legacy_todo_lane COMPLETED 0:0
CANCELLED since 15:00 UTC: NONE
home 23,374,512 KB / 50 GB soft; scratch 329,469,744 KB / 300 GB soft, grace 9 d, hard 1024 GB
```
