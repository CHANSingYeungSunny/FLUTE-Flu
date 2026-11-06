# HPC LOGIN-NODE D-STATE RECOVERY — reusable SOP (validated 2026-11-05)

**What this is.** The exact method that recovered CityU Burgundy on
2026-11-05 after a login node stop spawning shells. It worked on the first
attempt. Use it instead of re-deriving from `OUTAGE_RECOVERY.md` / `HPC_RUNBOOK.md`
gotchas 10–12, which this file refines.

**When to read it.** `ssh cityu` authenticates but returns zero bytes; or
`ssh` prints `Timeout, server ... not responding` while TCP/22 is open.

---

## 0. The signature (measure first, no shell needed)

| Probe | Observed 2026-11-05 |
|---|---|
| DNS `burgundy.hpc.cityu.edu.hk` | single A `144.214.138.99` |
| ICMP ping | 100% loss — **ICMP is blocked, not a node-down signal** |
| TCP/22 | **OK in 0.17–0.35 s**, banner `SSH-2.0-OpenSSH_9.9` |
| `ssh -v` auth | `Authenticated ... using "publickey"` **succeeds** |
| after `Entering interactive session` / `pledge: filesystem` | **zero bytes** |
| `ssh -s ... sftp` (subsystem) | also hangs |
| `uptime` in a brief window | `load average: 20.37, 23.73, 25.52`, `76 users` |

Diagnosis: `HPC_RUNBOOK.md` gotcha 11. **Not** credentials, **not** firewall,
**not** `MaxStartups` (that one gives `Connection closed`, see
`BUG_POSTMORTEM_20261102.md` C5). The login shell cannot be spawned.

### The trap that wasted ~20 minutes
`-o ServerAliveInterval=8 -o ServerAliveCountMax=2` makes **our own client**
abort with `Timeout, server burgundy.hpc.cityu.edu.hk not responding`.
That string is our timer, not a server reply. Set both to `0` before
concluding anything.

## 1. The key insight (user, 2026-11-05): kill IN the gap

> D-state jobs ARE killable; we just weren't issuing the kill during the
> few-second window when a shell exists.

`OUTAGE_RECOVERY.md` says "a remote `pkill` is impossible because no shell
runs" — that is **conditional**, not absolute. A `D` (`TASK_UNINTERRUPTIBLE`)
task does not discard `SIGKILL`: the signal is set **pending** and is delivered
the instant the task returns from I/O. Its non-D parent `bash -c` wrapper dies
immediately. So a kill issued during a short window is effective and
prevents the process re-occupying the session slot.

**Corollary — order matters.** In the 14:43:55 UTC window a `ps ... | head -40`
ran first; it stalled and the 16-second window was lost. The recovered method
puts `pkill` as the **literal first remote command**, before any observation
or capture.

## 2. Working recipe (one connection, no retries)

```
ssh -n -o BatchMode=yes -o IdentitiesOnly=yes -i ~/.ssh/id_ed25519 \
    -o PreferredAuthentications=publickey -o ConnectTimeout=10 \
    -o ServerAliveInterval=0 -o ServerAliveCountMax=0 \
    -o TCPKeepAlive=yes sychan552@burgundy.hpc.cityu.edu.hk "<commands>"
```

Remote command — **kill first, in this order**:

```bash
# bracket trick: patterns must NOT match this very bash -c command line
timeout 4 pkill -9 -u "$USER" -f 'impo[r]t transformers'; echo PKILL_A=$?
timeout 4 pkill -9 -u "$USER" -f 'd[u] -sh';            echo PKILL_B=$?
timeout 4 pkill -9 -u "$USER" -f 'dl_ds3[2].py';        echo PKILL_C=$?
timeout 4 pkill -9 -u "$USER" -f 'export_miflu_7[c]h';  echo PKILL_D=$?
timeout 4 pkill -9 -u "$USER" -f 'export_miflu_all[7]'; echo PKILL_E=$?
echo KILL_COMMANDS_ISSUED
# ONLY NOW the light capture (never ps, never du -sh, never import torch)
date -u; timeout 8 squeue -u sychan552 -h -o "%i|%j|%T|%M"
timeout 20 python cellok.py count all/export all/cells_all.tsv
timeout 8 find <root>/core/export7ch -name '*.npz' | wc -l
timeout 8 mmlsquota -u sychan552 | grep -e home -e scratch
echo CAPTURE_DONE
timeout 4 pkill -9 -u "$USER" -f 'impo[r]t transformers'; echo PKILL_ROUND2=$?
```

Rules, each one paid for:
1. **ONE persistent connection, no retry loop.** Rapid retries cause
   `MaxStartups` `Connection closed` (C5). If you must retry, wait 60–90 s.
2. **Client liveness timeout disabled** (`ServerAliveInterval=0`).
3. **`-u "$USER"` + bracket self-exclusion** — otherwise `pkill -f` matches
   its own `bash -c` line and kills the session you just recovered.
4. **`timeout 4` on every kill and `timeout N` on every capture line** — a
   `/proc` scan over D-state entries can hang and consume the whole window.
5. **Never `ps`, `du -sh`, `import torch/transformers` on the login node**
   while recovering (gotchas 10, 12).
6. **Never `scancel`, never submit a job** from the recovery connection.
   Verify with `sacct` afterwards that no Slurm job changed state.
7. Reusable implementation: `05_程序代码/hpc_login_node_recover.py`.

## 3. Root cause to prevent (see INCIDENT record)

The wedge came from an **interactive CPU inference**
(`code/export_miflu_7ch.py`) launched on the **login node** by an interrupted
handoff turn. It imports `torch` + `transformers` from GPFS and performs ~938
channel-window forwards; it entered `D` state and blocked shell spawning.

**Prevention (hard rule): any model forward pass, checkpoint load, HF import,
or recursive `du` must go through `sbatch` on a compute node.** The login node
is for `squeue`, `sacct`, `scontrol`, `mmlsquota`, short `cat`/`ls` only.
A correct GPU batch version already exists:
`code/export7ch_all.sbatch` -> job `739549` (submitted, PENDING).

## 4. Do not confuse with the other two signatures

| Signature | Meaning | Remote remedy |
|---|---|---|
| TCP/22 closed | node isolated/down | none; wait / sysadmin |
| TCP/22 open, auth OK, zero bytes | **this SOP** | kill-first in a window — **works** |
| `Connection closed` during banner | own retry rate / `MaxStartups` | slow down to 60–90 s |

See `OUTAGE_RECOVERY.md` §0 and `LEDGER.md` rows 2026-11-01 / 2026-11-05.

## 5. Job-state verification caveat (found 2026-11-05)

`squeue -h` on this cluster still emits `Last update in … seconds ago`, so
`squeue -h -n <name> | grep -q .` is **not** a valid "does this job exist" guard.
Use `squeue -u <user> -h -o "%j" | grep -qx '<name>'` and cross-check with
`scontrol show job <id>`, which is authoritative (`HPC_RUNBOOK.md`, persistent_driver
comments). Also note `legacy_lane.sh` writes a task into `legacy_done.tsv` after
ANY attempt including `rc=3 / skip.impossible` — a DONE line is not a valid cell.


## 6. HF cache has TWO layouts; never override HF_HOME globally (2026-11-06)

Measured on compute nodes while recovering the 7-channel MIFlu export:

| Model family | Correct `HF_HUB_CACHE` |
|---|---|
| 14 encoder models | `/gpfs1/scratch/sychan552/hf_cache/hub` |
| `ds_r1_distill_qwen1_5b` (pinned `ad9f0ae…`) | `/gpfs1/scratch/sychan552/hf_cache` (legacy top-level `models--…`) |
| **MIFlu / GPT-2** | `/gpfs1/home/sychan552/.cache/huggingface/hub` (DEFAULT user cache) |

Setting `HF_HOME=hf_cache` for a MIFlu inference makes
`GPT2Model.from_pretrained("gpt2")` raise `LocalEntryNotFoundError` (pilot 740296).
Keep `HF_HOME`/`HF_HUB_CACHE` overrides **inline and scoped to encoder cells only**;
leave MIFlu on the default cache. Verify with
`huggingface_hub.try_to_load_from_cache(repo, file, revision=..., cache_dir=...)`.
