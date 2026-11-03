# BUG POSTMORTEM — 2026-11-01/02 night run

**What this is.** Every technical defect and every diagnostic mistake made during the
2026-11-01/02 overnight attempt, with the evidence that proves each one, its fix status, and
the concrete rule that prevents a repeat. Written because the same *class* of error recurred
five times in one night, and because three of the defects would each have silently produced
**zero usable results** while every log line looked healthy.

**When to read it.** Before touching `code/queue/*`, before restarting any driver/lane, before
claiming a cell is "done", and before writing any verification script.

**What it points to.** `04_详细说明文档/LEDGER.md` (dated rows with the raw evidence),
`04_详细说明文档/OUTAGE_RECOVERY.md`, `04_详细说明文档/PROTOCOL_AMENDMENT_SEEDS.md`, `04_详细说明文档/LLM_SEED_BUG.md`,
`04_详细说明文档/HPC_RUNBOOK.md` (gotchas 11–20).

---

## PART A — TECHNICAL DEFECTS (each proven, most fixed)

### A1. The seed never entered the LLM training path — 36 cells invalid (FIXED)
- **Symptom**: `qwen25_1_5b` and `ds_r1_distill_qwen1_5b`, all horizons × seeds 42/43/44 →
  **24/24 pairs `np.array_equal` = True, `max|dpred|` = exactly 0**.
- **Smoking gun**: `manifest.encoder.determinism.manual_seed = 42` **for seeds 43 and 44 too**.
  The npz `seed` field was correct, so the *filename* hid the bug; only the manifest exposed it.
- **Root cause**: `train_backbone_966.build_model`'s `mode=="llm"` branch built from
  `LLM_ENCODER_OPTS`, filled **once in `main()`, outside the (L, seed) loop**, and never carrying
  `seed`. `FrozenLLMEncoder` fell back to its default 42 and its `torch.manual_seed(self.seed)`
  calls (`llm_encoder_backbone.py` L639/L658) **overrode** `set_seed(seed+L)`.
- **Fix**: `build_model(..., seed=None)` sets `opts["seed"] = seed + L`; deployed 03:57:47 with
  `.bak_seedfix`. Proven on-cluster: seed 42 → `manual_seed=66`, seed 43 → 67, `pred_equal=False`,
  `max|dpred|=0.428975`.
- **Why the tests missed it**: the mock encoder used an explicit `torch.Generator`, so the mock
  path was seeded correctly while the real path was not.
- **Rule**: a determinism test must assert **files differ across seeds** on a *real* model id, not
  just that a mock is reproducible. And record `manual_seed` in the manifest so the invariant
  `manual_seed == L + seed` is machine-checkable (`05_程序代码/llm_seed_provenance.py`, now wired into
  `analysis_expanded.load()`).

### A2. A 32B arm could never have completed; 7B OOM'd (FIXED)
- **Symptom**: 7B cell OOM on a 44 GB card (job 721112); moving the copy to host got the process
  SIGKILLed at 32 GB (721154).
- **Root cause**: `train_one`'s best-val snapshot did `detach().clone()` on the **whole**
  `state_dict()`, including the **frozen** encoder → 7B needed 15.2 + 15.2 GB, 32B would need
  ~122 GB, i.e. **impossible on any 80 GB A100**.
- **Fix** (04:44:49): snapshot excludes `requires_grad=False` tensors, `strict=False` only in that
  case; the 16 trained arms take the unchanged, bit-identical branch.
- **Rule**: never clone a frozen module "just in case". Assert peak VRAM against a budget before
  launching a large arm.

### A3. `revision: null` made every unblocked LLM cell terminal (FIXED)
- **Symptom**: `skip.no-revision` (terminal, no retry) on all unblocked cells.
- **Root cause**: `pinned_revision()` reads the registry, then `queue/p2/<label>.json` — and
  **there is no `p2/` directory on the cluster**. A queue-row flip that only changed `state`
  therefore produced rows that could never run.
- **Fix**: all 12 usable arms carry the **snapshot-directory sha** (which is the revision and
  matches the HF API sha).

### A4. Two HF cache layouts made 10 of 13 arms invisible (FIXED)
- **Symptom**: `from_pretrained(local_files_only=True)` failed **after** a GPU had been allocated,
  for arms whose weights were demonstrably on disk.
- **Root cause**: `hf_cache/models--X` and `hf_cache/hub/models--X` coexist; `HF_HUB_CACHE` can
  point at only one.
- **Fix**: `local_snapshot()` resolves the snapshot directory itself (config.json + ≥0.5 GiB of
  weight bytes, following symlinks) and passes that path as `--llm-model-id`.
- **Rule**: "weights present" must be verified by **loading**, not by `du`/`ls`.

### A5. `flock` is not a cross-node mutex on GPFS → every `DONE` was silently lost (PATCHED, UNVERIFIED)
- **Symptom**: `miflu_L24_s42` logged `TASK DONE gate=1.2474` **nine times in 90 minutes**; its row
  stayed `RUNNING` with `attempts=26`. Only two cells (`L24_s42`, `L24_s44`) ever cycled.
- **Root cause**: `row_set`, `state_row`, `rearm_finalise`, `finalise_pass` each do a whole-file
  read-modify-write of `master_queue.tsv` and serialise on `flock` of a **GPFS** path. The two
  lanes run on **different compute nodes**; `flock` is not reliable across nodes on GPFS, so both
  read v0, each writes its own full copy, and the last writer wins — erasing the other's `DONE`.
- **Corroboration**: the LLM band reached 132 `DONE` because during that phase the `gpu_a100` lane
  was mostly `PENDING` — effectively **one writer**, nothing to lose.
- **Fix applied**: 6 acquire/release blocks replaced with an atomic **`mkdir` lock**
  (`lk_acquire`/`lk_release`), and 10 temp-file names gained `${SLURM_JOB_ID}` so two nodes that
  share a PID cannot collide. `bash -n` = SYNTAX_OK. **Effect NOT yet verified** — see Part B6.
- **Rule**: on GPFS use `mkdir` (atomic) for mutual exclusion, never `flock`, whenever the writers
  may be on different nodes.

### A6. The attempt cap was not enforced (OPEN)
- **Symptom**: rows at `attempts=26`, `17`, `8` against a stated maximum of 2.
- **Root cause**: the counter is incremented on recovery, but selection never refuses a row whose
  attempts already exceed the cap. Every lane cancellation also increments it, so the number
  measures *cancellations*, not failures.
- **Partial mitigation applied**: the 12 `miflu_cell` rows had `attempts` reset to 0 and any
  `SKIPPED` returned to `TODO` (safe: `miflu_bench_cell()` has an `ok.already-done` branch).
- **Still to fix**: assert `attempts > MAXATT → SKIPPED` **before** dispatch.

### A7. Two pipelines could not have executed at all (FIXED)
- `miflu_cell()` was **oracle-gated** on `ORACLE[L][S-2021]`; any 42/43/44 seed returned `None` →
  `skip.no-oracle` on all 12 benchmark cells. Fixed by a new `miflu_bench_cell()`.
- The driver's liveness gate was **global** (`LANE_PREFIX="mlflu_"`), so a 7B probe on `stingy`
  stopped the idle `gpu_a100` stripe (132 runnable rows). Fixed to a **partition-scoped** gate.

### A8. `persistent_driver.sh` died at the exact moment it had work (FIXED)
- `local s=$1 p=$2 pend="${QDIR}/p3_submit_${p}.pending"` — under `set -u`, `${p}` was expanded
  before `p` was bound → `line 130: p: unbound variable`, **with 1061 runnable rows and no lane**.
- Fix: one assignment per `local` statement.

---

## PART B — MY OWN DIAGNOSTIC MISTAKES (the most important section)

These are not code bugs. They are **reasoning failures**, and they cost more time than the code
bugs because each one produced a confident wrong answer.

### B1. "It's preemption" — wrong
MIFlu produced 0 cells in 8 hours. I blamed `stingy`'s 8-minute preemption windows against an
11-minute cell. **Wrong**: the cells were completing (543 s) and being re-run.

### B2. "The export writes to a legacy `stage6/predictions/` path" — wrong
I found `pred_miflu_L24_s43.npz` under `stage6/predictions/` and declared the export path broken.
**Wrong**: those are stale artefacts from an earlier project phase. The real output root is
`RUNS/expanded_runs` (`MIFLU_BENCH_ROOT = EXPANDED`, line 263), and I had searched the wrong
subdirectory (`03_预测数据_证据/expanded_runs`).

### B3. "Training is cut off at epoch 4–19" — wrong
A 4-epoch log looked like a truncation. **Wrong**: that was one early attempt of a *different*
cell. The cells that cycled completed all 20 epochs each time.

### B4. "A lock is held / a memory copy isn't flushed / a restore overwrote it" — wrong
I read `row_set` and found `flock` **blocking** (not `-n`) and an **atomic `mv`**. Those three
hypotheses were all refuted by reading the code. The real cause was that `flock` **does not work
across nodes on GPFS** — a property of the primitive, not of the code structure.

### B5. "LLM finished because it is special" — wrong framing
LLM reached 132/156 because the other lane was mostly `PENDING` during that window (one writer).
It was luck of scheduling, not a property of the LLM path.

### B6. I wrote a verification script, it failed, and I nearly called the patch broken
My `verify_mkdir_lock.sh` reported `survived=0/20` with `mv: cannot stat ...tmp.<pid>.<pid>`.
**The script was wrong, not the lock** — `awk` never produced its temp file. A second minimal
`mkdir` test then **timed out** (the `until mkdir … done` loop never exited, most likely a quoting
artifact). **Result: the lock fix is applied but UNVERIFIED, and I say so rather than implying it
works.**

### B7. I accepted "TASK DONE gate=…" as proof a cell existed
Twice. Once for MIFlu (`1/12 done`) and once for `4/12 done`. In both cases **no artefact existed**.
The log line is emitted on the `rc==0` branch *before* any independent check that the artefact
landed where the gate will look.

**THE RULE THAT COVERS B1–B7:**
> **Never report a state from a log line, a name, or a counter alone. Report it only after reading
> the artefact path / the row state / the exit code that the next stage will actually consume.**
> If you cannot yet see that, say "unverified" — that word costs nothing and prevents every one of
> the seven mistakes above.

---

## PART C — PROCESS / ORCHESTRATION FAILURES

### C1. Five agents wrote the same queue file (worst process error)
Between 03:56 and 04:56 three separate agents held "sole ownership" of `code/queue/*` and one
(I, the parent) edited it directly twice. Consequences: `master_task.py` grew 19,260 → 28,722 bytes
mid-edit; `master_queue.tsv` was atomically replaced three times; drivers and lanes were cancelled
and resubmitted repeatedly; the result was a mixture of grids that took an hour to reconcile.
**Rule: one writer, announced in the ledger, and the parent must NOT edit a file it has delegated.**

### C2. My two "contributions" were both net-negative
- A queue builder emitting task ids like `miflu_cell|MIFlu|L24|s42` — **unparseable** by
  `master_task_v2`'s regex `(.+)_L(\d+)_s(\d+)$`, so all 204 rows were dead but looked alive.
- A dedupe whose "settled" set was `{state != TODO}`, so `SUPERSEDED`/`BLOCKED` counted as done and
  **1032 rows were retired**, taking rolling origin from 1020 to 204.
**Rule: validate a generated `task_id` by round-tripping it through the consumer's own parser
before writing any row. Never generalise "not runnable" into "settled".**

### C3. PowerShell text round-trips corrupted the memory files
`Set-Content -Encoding UTF8` turned `§`→`禮`, `·`→`繚`, `—`→`??` in `AGENTS.md` (162 chars) and
`04_详细说明文档/LEDGER.md`. Repair script: `05_程序代码/repair_mojibake.py` (still leaves 4 lossy chars in
`AGENTS.md`). **Rule: all `.md`/`.json`/`.tsv` edits go through Python with `encoding="utf-8"`
and a timestamped backup. Never PowerShell for text content.**

### C4. `sbatch` spools the script, so `$0` lies
`dirname "$0"` resolved to `/var/spool/slurmd/job<N>/`, and two queued lanes would have died on
line 1 **while `squeue` showed them healthy PENDING**. **Rule: absolute paths only in sbatch
05_程序代码.**

### C5. I mis-diagnosed the cluster as down when my own retry rate was the cause
Four outages were reported; the decisive measurement (TCP/22) was run only on the last one. When
TCP is open and ssh says `Connection closed`, the cause is our own connection rate
(`MaxStartups`), not the cluster. **Rule: measure TCP/22 before diagnosing; never retry ssh faster
than once per 60–90 s.**

### C6. Repeated shell-quoting failures in PowerShell
Roughly ten wasted tool calls from `$`, `"` and `\t` being interpreted by PowerShell instead of
bash. **Rule: for anything non-trivial, write a `*.py` or `*.sh` file locally, `scp` it, run it.
Do not compose multi-line bash inside a PowerShell double-quoted string.**

---

## PART D — THE ONE-PAGE CHECKLIST THIS NIGHT PRODUCED

Before declaring anything done:

```
[ ] Does the artefact exist at the path the NEXT stage reads? (not "a log said done")
[ ] Is the state persisted in the file the next run reads?  (read it back, grep the row)
[ ] Does a generated task_id round-trip through the consumer's parser?
[ ] Is the seed in {the agreed set}, and does the manifest record manual_seed == L+seed?
[ ] Are there exactly N rows for N cells — no duplicates by (kind, model, L, seed)?
[ ] Is there exactly ONE writer to the queue, and is it declared?
[ ] For cross-node mutual exclusion on GPFS: mkdir, not flock.
[ ] Did I measure before diagnosing (TCP/22, artefact path, row state)?
[ ] If I cannot verify: did I write the word "unverified"?
```
