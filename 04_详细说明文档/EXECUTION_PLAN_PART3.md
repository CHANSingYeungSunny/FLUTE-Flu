# EXECUTION PLAN — PART THREE, ordered by value per A100-hour

**What this is.** The authoritative, ordered work plan for the remaining programme after the
night of 2026-11-01/02, the mechanism that executes it automatically, and the anti-collision
rules that keep concurrent lanes from corrupting each other. Read this before appending any
queue row or starting any new lane.

**When to read it.** At the start of every session that intends to run GPU work, and before
modifying `code/queue/master_queue.tsv`, `master_controller_v2.sh`, or any `*_lane.sh`.

**What it points to.** `04_详细说明文档/QUEUE_ROWS_PART2.md` (row specs §2–§5), `04_详细说明文档/PROGRESS_GATE.md`
(per-turn write contract), `04_详细说明文档/STORAGE_PLAN.md` (capacity + deletion), `04_详细说明文档/HPC_RUNBOOK.md`
(gotchas 17–19: spool `$0`, `batch` mem floor, `MODELS` exactness), `04_详细说明文档/LLM_ARMS.md` §7.

**Depends on.** Nothing new; it consumes what already exists.

---

## 1. THE ORDER (do not reorder without a measured reason)

| # | Item | Cost | Success odds | Value | Status entering this plan |
|---|---|---|---|---|---|
| **1** | **Table VI regional, MIFlu only** | ≈1 A100-h (21 cells × 2–3 min) | high — runner `05_程序代码/train_regional.py` exists, data on hand | **highest: one complete new table** | rows NOT in queue |
| **2** | **Remaining LLM arms** | ~16 s/cell → 132 cells ≈ 35 min | high — already producing | high: LLM vs non-LLM comparison | running as `720906` (stripe 0, stingy) |
| **3** | **Table VIII `no_lora`** | 12 cells ≈ 1–1.6 h | medium | medium: one ablation table | rows NOT in queue |
| **4** | **Table VIII K-sweep** | 48 cells ≈ 3–6 h | medium | medium | rows NOT in queue |
| **5** | **Table IX regional training time** | **0 GPU** — reads manifests | high, but depends on #1 | medium | needs #1 done first |
| **6** | **Rolling origin, 5 folds** | **155–360 A100-h** (200 MIFlu + 960 arm cells) | low — most expensive, most interruptible | high but LAST | rows NOT in queue |

**Why this order.** #1 gives a complete table for one GPU-hour — nothing else comes close.
#2 is already running and nearly free. #3/#4 are incremental ablations. #5 is CPU-only but
worthless before #1. #6 dwarfs everything else and is the only item that cannot plausibly
finish in a single allocation, so it must never block the others.

## 2. WHAT "AUTOMATIC, ONE BY ONE" REQUIRES (and what is missing today)

The scheduler mechanism already works and is proven: `720107` fired `720906` automatically
when the P0 MIFlu lane completed, and `720906` is producing `llm_cell` rows at ~16 s each.
**But `720107` then exited** — it has a 07:00 cutoff and fires at most once. So today the
chain has no continuation: when `720906` ends, nothing submits its successor.

Two things are therefore required, in this order:

1. **Rows.** #1, #3, #4 and #6 are **not in `master_queue.tsv`**. #1/#3/#4 exist only as
   `unimplemented` placeholders. The row specs are written in `04_详细说明文档/QUEUE_ROWS_PART2.md`
   §2a (200 rolling-origin MIFlu cells), §2b (960 arm fold cells), §3 (Table VI, 21 MIFlu
   cells / 336 all-arm), §4 (Table VIII 12/48/12/12), §5 (the 168 LLM cells), §6 (Table IX
   gated on Table VI). Append them with the priority letters P1/P2/P3 so the existing
   priority-ordered lane walks them in the order above.
2. **A persistent driver with NO cutoff.** One `tiny` job, max wall (5 d), whose only job is:
   if no lane of ours is running and the queue still has runnable rows, submit the next lane
   (stripe 0 to `stingy`, stripe 1 to `gpu_a100`), then sleep, then repeat — until the queue
   drains or `HALT` exists. This replaces `720107`, which fires once.

## 3. ANTI-COLLISION RULES (learned the hard way on 2026-11-01)

Violating any of these has already cost this project hours; each line is a measured incident.

| Rule | Incident it prevents |
|---|---|
| **Only ONE agent may write `code/queue/*`.** Announce ownership before editing. | `master_task.py` grew 19,260 → 28,722 B while a second agent edited it; both re-uploaded at 22:32:37 |
| **Never edit `.md`, `.json`, `.tsv` with PowerShell text round-trips.** Use Python with `encoding="utf-8"`. | `Set-Content -Encoding UTF8` turned `§`→`禮`, `·`→`繚`, `—`→`??` in `AGENTS.md` and `LEDGER.md` |
| **Never run `make_queue.py --force`** once cells are `DONE`. Edit rows in place, atomically (`.tmp` + `os.replace`), after a timestamped backup. | A reset would discard the 40 verified MIFlu markers |
| **Absolute paths only in `#SBATCH` 05_程序代码.** `sbatch` spools to `/var/spool/slurmd/job<N>/slurm_script`, so `dirname "$0"` lies and the job dies on line 1 while `squeue` shows it healthy. | jobs `720083`/`720070` would both have died at their start time |
| **A lane guard must only count `*cell` / `*probe` rows as competing controllers.** | `720106` aborted 6 s after start with `another controller of my lane is alive (job 720052)` because the writer's own `finalise` row looked like a peer |
| **Only one writer touches `02_数字表格/`** — `flock` on `analysis/.finalise.lock`. Compute lanes never write tables. | two lanes could otherwise rewrite tables from different partial subsets |
| **Every cell is claimed atomically** before execution. | the same cell would run twice |
| **Only `stingy` / `gpu_a100` may produce a paper number**; everything else is `probe_only`. | the NLinear V100/A100 hardware confound |
| **A CPU hidden-state probe must load the model**, so 8 GB is enough to download but not to probe. | `720175` died `OUT_OF_MEMORY` |

## 4. KNOWN LIMITS THAT THIS PLAN CANNOT FIX

- **Table VIII `--no-text` cannot move a number.** With `author_faithful=True` the text sits
  behind the causal mask, so `use_text=False` is **bit-identical** to the full arm. That row
  is a **structural verification**, never an ablation effect. Report it as such.
- **`deepseek-ai/DeepSeek-R1-Distill-32B`** is 61 GB bf16 on an 80 GB A100 at
  `--encoder-batch-size 1` (already the floor). An OOM there is `skip.oom`, not a halved retry.
- **`Qwen/Qwen3.8-27B-FP8`** occupies ~54.7 GB after fp8→bf16 dequantisation on sm_80, also
  batch 1. Not downloaded at the time of writing.
- **`tencent/Penguin-Encoder`** needs `trust_remote_code`; **`tencent/Youtu-HiChunk`** cannot
  emit per-layer hidden states; **`tencent/KaLM-Embedding-Gemma3-12B`** failed to download.
  Those three arms are `UNSUPPORTED` / `FAILED` and must never be retried.
- **Rolling origin is 155–360 A100-hours.** It will occupy the cluster for one to two weeks of
  continuous allocation. Start it only when everything above is complete.

## 5. VERIFICATION — how to know each item actually happened

| Item | Evidence that proves it |
|---|---|
| #1 Table VI | `03_预测数据_证据/regional/<region>/<model>_L<L>_s<seed>/` contains `pred_*.npz` + manifest with GPU/partition/node/job id |
| #2 LLM arms | `code/queue/queue_state.tsv` shows `DONE` for all 12 cells of an arm; `03_预测数据_证据/expanded_runs/llm_<label>_L*_s*/` present |
| #3/#4 Table VIII | same as #2 with `ablation_label` in the manifest |
| #5 Table IX | `05_程序代码/build_table_ix.py` exits **0** (it exits 3 while nothing is measured) |
| #6 Rolling origin | each fold has its own `pred_*.npz`; `walk_forward.assert_folds` passes; test blocks disjoint |
| Whole plan | `02_数字表格/*.csv` mtime advances **after** the cells, i.e. the writer rebuilt from the new data |

## 6. THE SENTENCE TO REMEMBER

**Rows in the queue + a driver with no cutoff = automatic progress. Code without rows = zero
progress, however good the code is.** Three of the six items above are in that state today.
