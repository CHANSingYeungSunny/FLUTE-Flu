# AGENTS.md — hard operational rules for ANY agent / AI working on this project

Read this **before your first SSH command**. These rules exist because a real incident
on 2026-11-05 blocked the CityU Burgundy login node for ~2 hours and lost a
16-second recovery window. Full SOP: `04_详细说明文档/HPC_LOGIN_NODE_DSTATE_RECOVERY.md`;
incident: `HANDOFF_20261105/INCIDENT_20261105_LOGIN_NODE_DSTATE.md`.

## RULE 1 (NON-NEGOTIABLE): the Burgundy login node is for light checks ONLY

**NEVER run model work on the login node.** All of these MUST go through `sbatch`
on a compute node:

- any model inference / forward pass (including "just one cell" and CPU-only)
- `torch.load` of checkpoints, `import torch`, `import transformers`, `from_pretrained`
- recursive `du -sh` over GPFS trees, large downloads, long-running Python

Allowed on the login node: `squeue`, `sacct`, `scontrol`, `mmlsquota`, `sinfo`,
short `cat`/`ls`/`find` on small paths, `date`. Wrap anything nontrivial in `timeout 20s`.

The 2026-11-05 outage was caused by an agent running
`code/export_miflu_7ch.py` (torch + checkpoint load + DataLoader over all test
windows) as a long CPU inference **directly on the login node**, not via `sbatch`.
It was NOT the CPU/GPU choice that was wrong — it was the node. A GPU forward on
the login node is equally wrong. Never use "CPU is sufficient" to justify skipping
`sbatch`.

Use absolute paths in sbatch scripts (sbatch spools the script; `$0` lies).

## RULE 2: if `ssh` authenticates but returns zero bytes, do this

Signature: DNS OK → TCP/22 OK (~0.2 s, banner `SSH-2.0-OpenSSH_9.9`) →
`Authenticated ... using "publickey"` → **zero bytes**; plain ssh, `-tt`, sftp all hang.
This is `HPC_RUNBOOK.md` gotcha 11 (login shell cannot spawn), NOT credentials,
NOT firewall, NOT `MaxStartups` (that one gives `Connection closed`).

1. `ServerAliveInterval=0`, `ServerAliveCountMax=0`. Otherwise **your own client**
   produces a misleading `Timeout, server ... not responding`.
2. ONE persistent ssh connection, **no retry loop** (rapid retries →
   `MaxStartups` `Connection closed`; wait 60–90 s if retrying).
3. In the first shell window, the **FIRST command must be `pkill`**, not `ps`,
   not a status capture. A `D`-state task does not discard `SIGKILL` — the signal
   is pending and delivered when I/O returns. The 14:43:55 UTC window was lost
   to `ps ... | head -40`; the 15:22:05 UTC window succeeded with `PKILL_D=0`.
4. Bracket self-exclusion (`'impo[r]t transformers'`) so `pkill -f` cannot match
   its own `bash -c` line; `timeout 4` on every kill, `timeout N` on every capture line.
5. Never `scancel`, never submit a job from the recovery connection. Verify with
   `sacct` afterwards that no Slurm job changed state.

Reusable tool: `05_程序代码/hpc_login_node_recover.py` (`--measure-only` is safe).

## RULE 3: never trust a DONE label or `squeue` alone

- `squeue -h` on this cluster still prints `Last update in …`, so
  `squeue -h -n NAME | grep -q .` is NOT an existence guard. Use
  `squeue -h -o "%j" | grep -qx NAME` and `scontrol show job` (authoritative).
- `legacy_lane.sh` writes a task into `legacy_done.tsv` after ANY attempt,
  including `rc=3 / skip.impossible`. A DONE row is not a validated cell.
- Validate cells by finite metrics, valid prediction files, shapes and target
  arrays — e.g. `cellok.py count`/`pending` — not by directory existence.

## RULE 4: scientific provenance

Historical frozen CSVs (`02_数字表格/*.csv`) are old-snapshot facts: 28 arms,
Holm 0/136 from `p_raw` with forward cumulative maximum (never the exported
`p_holm`), NLinear–PatchTST 0.1172, 4/16 aggregate cells. Never overwrite them
with new results; keep new panels and statistical families separately named.
Owner-edited PPTX must stay byte-identical unless explicitly asked.
A structural/hash validator PASS is `scientific_readiness: NOT_ASSESSED`.

## RULE 5: no fabricated results

Missing outputs are `BLOCKED` / `NOT_EXECUTED` with an exact reason and the
intended command. Never replace a missing measurement with a DONE label, a
"code is ready", a suite exit 0, or a predicted value.


## RULE 6: two HF cache layouts — never override `HF_HOME` globally

* Encoder models: `hf_cache/hub/models--…` (NEW), except `ds_r1_distill_qwen1_5b`
  whose pinned revision is in `hf_cache/models--…` (LEGACY top-level).
* MIFlu / GPT-2: default user cache `/gpfs1/home/sychan552/.cache/huggingface/hub`.
Scope `HF_HOME`/`HF_HUB_CACHE` inline per encoder cell only. A global override breaks
`GPT2Model.from_pretrained("gpt2")` with `LocalEntryNotFoundError` (measured job 740296).
