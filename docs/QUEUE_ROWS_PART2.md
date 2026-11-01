# QUEUE_ROWS_PART2 — the handover to the queue owner (part-two runners)

> **What this is.** The `task_id / kind / model / L / seed / priority / env /
> expected_artefact / gate` specification for every part-two experiment, now that
> the runners exist. Written by the coding lane (which owns **no** queue file);
> the queue owner pastes it into `hpc_experiments/queue/make_queue.py` (or the
> TSV) and owns the resulting rows.
>
> **When to read it.** Before appending any part-two row, before pricing a night,
> and before deciding what fits.
>
> **What it points to.** `scripts/walk_forward.py` (rolling origin),
> `scripts/train_regional.py` (Table VI), `scripts/build_table_ix.py` (Table IX),
> `scripts/train_miflu.py` (Table VIII flags), `hpc_experiments/weights_worker.py`
> + `cpu_download_worker.sh` (weights), `hpc_experiments/measure_llm_forward.py`
> (measured cost), `hpc_experiments/queue/master_task.py` (the dispatcher that
> needs one branch per new `kind`).
>
> **Depends on.** `AGENTS.md` §2 (rules 9–13), `docs/HPC_RUNBOOK.md`
> ("PARTITION POLICY"), `SKILL.md` §3 (evaluation windows).
>
> **Chain.** `AGENTS.md` → `docs/WORK_BREAKDOWN.md` §13 → this file →
> `hpc_experiments/queue/master_queue.tsv`.

---

## 0. THE HARD CONSTRAINT THIS DOCUMENT RESPECTS

The coding lane **does not write** `hpc_experiments/queue/*` or `code/queue/*`.
Everything below is either (a) a row to paste, or (b) a command that a row
dispatches to. No row here has been submitted by the coding lane.

**Queue schema (v2, 11 columns, `queue_store.COLUMNS`)**

```
task_id  kind  model  L  seed  priority  env  state  attempts  last_job  note
```

This document's 9 columns map onto it as: the first 7 are literal, then
`state=TODO`, `attempts=0`, `last_job=""`, and **`note` carries
`expected_artefact` + `gate`** (tab-safe, one line each). Nothing else about the
schema changes.

**New `kind`s need one dispatch branch each** in `hpc_experiments/queue/master_task.py`.
Today `miflu_cell`, `llm_cell`, `llm_probe` and the `finalise` kinds exist; an
unknown `kind` is `SKIPPED` with `unknown kind …` (exit 3), which is the honest
failure mode until the branch is added. The exact command per kind is in §1.

---

## 1. KINDS AND THEIR COMMANDS

All commands run from the repo root of the staged tree (`$R` on the cluster).
`<F>` = fold 1..5, `<L>` = horizon, `<S>` = seed, `<M>` = model, `<R>` = region.

| kind | command (one line) | env |
|---|---|---|
| `wf_miflu_cell` | `python scripts/train_miflu.py --horizon <L> --reps 10 --seed 2021 --profile author_repo_966 --containment strict --fold <F> --export-dir hpc_results/walk_forward/f<F>/L<L>_s2021 --ckpt-dir hpc_results/walk_forward/f<F>/ckpt_L<L>_s2021` then `python hpc_experiments/export_miflu_all7.py --cells <L>:2021 --ckpt hpc_results/walk_forward/f<F>/ckpt_L<L>_s2021/best_miflu_L<L>.pth --out-dir hpc_results/walk_forward/f<F>/L<L>_s2021 --device cuda` | hpc |
| `wf_arm_cell` | `python scripts/train_backbone_966.py --backbone <M> --horizon <L> --seed <S> --profile author_966 --containment strict --fold <F> --export-dir hpc_results/walk_forward/f<F>/<M>_L<L>_s<S>` | hpc |
| `wf_classical_cell` | `python hpc_experiments/train_classical_966.py --model <M> --horizon <L> --seed <S> --profile author_966 --fold <F> --export-dir hpc_results/walk_forward/f<F>/<M>_L<L>_s<S>` | hpc |
| `table6_cell` | `python scripts/train_regional.py --model <M> --region <R> --horizon <L> --seed <S> --export-root hpc_results/regional` | hpc |
| `table8_cell` | `python scripts/train_miflu.py --horizon <L> --reps 1 --seed <S> --profile author_repo_966 --containment strict <VARIANT FLAGS> --ablation-label <VAR> --export-dir hpc_results/ablations/<VAR>/L<L>_s<S> --ckpt-dir hpc_results/ablations/<VAR>/ckpt_L<L>_s<S>` | hpc |
| `table9_build` | `python scripts/build_table_ix.py` | hpc |
| `llm_cell` | unchanged: `python scripts/train_backbone_966.py --backbone llm_encoder --arm-label <label> --llm-model-id <hf_id> --llm-revision <sha> --horizon <L> --seed <S> --profile author_966 --containment strict --encoder-batch-size <bs>` | `mlflu_hpc` / `mlflu_llm` |
| `llm_probe` | unchanged (CPU): revision pin + download + hidden-state smoke (`hpc_experiments/cpu_download_worker.sh`, `weights_worker.py`) | `mlflu_hpc` |

**Partition policy** (from `docs/HPC_RUNBOOK.md`, recorded 2026-11-01):
`stingy`/`gpu_a100` are the only partitions whose output may enter
`paper_tables/`; `gpu_v100s`, `highmem_*`, `batch` are testing/IO only and must
be `probe_only=True`; `tiny` is the scheduler/watchdog role. **Downloads,
revision pinning, hidden-state probes and table rebuilds produce no measured
number, so they go anywhere free.** Every `*_cell` row below that can produce a
paper number must therefore be submitted to `stingy` (primary) or `gpu_a100`.

---

## 2. ROLLING ORIGIN (5 folds) — the geometry that the rows must respect

`python scripts/walk_forward.py --rows 966 --k 5` prints, and `assert_folds`
enforces:

| fold | rows read | train | val | test | test windows L24/L36/L48/L60 |
|---|---|---|---|---|---|
| f1 | 0–393 | 241 | 75 | 78 | 55 / 43 / 31 / 19 |
| f2 | 0–492 | 320 | 75 | 98 | 75 / 63 / 51 / 39 |
| f3 | 0–616 | 419 | 75 | 123 | 100 / 88 / 76 / 64 |
| f4 | 0–771 | 540 | 78 | 154 | 131 / 119 / 107 / 95 |
| f5 | 0–965 | **676** | **97** | **193** | **170 / 158 / 146 / 134** |

* Test blocks are 20 % of the fold window and **disjoint**; they tile
  `[315, 966)` without overlap (growth 1.25 = `1/(1-0.20)`, proved in the module
  docstring and re-checked in `tests/test_walk_forward.py`).
* Fold 5 **is** the existing published split `(676, 773, 966)` — rolling origin
  contains the protocol behind every current number instead of replacing it.
* **The validation floor is a documented deviation**: `K=5` forces fold 1 to a
  394-row window, whose 10 % validation block (39 rows) yields only 4 validation
  windows at L=36 and **−20** at L=60 — impossible with `drop_last=True`
  (batch 16). `walk_forward` therefore sizes a floor of `L_max + 16 − 1 = 75`
  rows for folds 1–3 (marked `[val floor]`), moving **only `train_end`** back:
  the scored test blocks are untouched, so 20 % and disjointness still hold. The
  published statement is: *test = 20 % of the fold window and disjoint;
  validation = 10 %, widened only where 10 % cannot yield 16 validation windows at
  the horizon trained.* A **pure** 70/10/20 `K=5` layout is arithmetically
  impossible on 966 rows at L ≥ 36; `make_folds(966, k=5, val_floor_rows=0)`
  raises with that arithmetic (tested).
* Evaluation windows are still `(W//16)*16` per fold (`eval_windows.eval_slice`),
  i.e. f5/L24 = 160 — the same rule as every existing cell.
* Fold cells are written under `hpc_results/walk_forward/f<F>/…` and the runner
  **refuses** to write one into `hpc_results/expanded_runs` (rule 10: the two
  protocols must never mix; a fold cell is not comparable with a fixed-split
  cell).

### 2a. MIFlu — 40 runs × 5 folds = **200 cells**

| field | value |
|---|---|
| `kind` | `wf_miflu_cell` |
| `model` | `miflu` |
| `L` | 24, 36, 48, 60 |
| `seed` | 2021…2030 (reproduction protocol, 10 reps inside the cell) |
| `priority` | P3 |
| `env` | `mlflu_hpc` |
| expected_artefact | `hpc_results/walk_forward/f<F>/L<L>_s2021/predictions_miflu_L<L>_seed<S>.csv`, `pred_miflu_L<L>_seed<S>.npz` `(W,7,L)`, `results_*`, `manifest_*` (checkpoint sha256) + `manifest_miflu_L<L>_s2021.json` from the runner |
| gate | the export's `pred`/`target` reproduce the fold's own first `(W//16)*16` windows; `target_start_row` length equals the fold's test-window count from the table above; `manifest.fold.fold == <F>` |

**Cost (per cell).** Measured anchor: a national MIFlu 20-epoch cell is
**~8 min** on one A100 worker (24 s/epoch, measured — LEDGER 2026-11-01). A fold
cell is smaller on average (fewer train windows in f1–f3: 241–419 vs 549) but the
reproduction protocol is 10 reps, so the cell = 10 × (20 epochs × ~10–24 s) ≈
**35–80 min**. 200 cells ≈ **120–270 A100-hours**. That is the single most
expensive item in this document and it does **not** fit a night; recommendation:
run it at **1 seed** (2021) first (§7), 20 cells ≈ 12–27 h, and treat the other 9
seeds as a later campaign.

### 2b. The 16 benchmark arms — 5 folds × 4 horizons × 3 seeds = **960 cells**

| field | value |
|---|---|
| `kind` | `wf_arm_cell` (11 neural arms) / `wf_classical_cell` (5 sklearn arms) |
| `model` | `patchtst, nlinear, dnn, cnn, rnn, lstm, gru, itransformer, qwen_time_llm, calf_llm, timecma_llm` + `decision_tree, random_forest, gradient_boosting, svr, knn` |
| `L` | 24, 36, 48, 60 |
| `seed` | 42, 43, 44 (rule 9: same seed set for every arm; **no** unequal counts) |
| `priority` | P4 |
| `env` | `mlflu_hpc` |
| expected_artefact | `hpc_results/walk_forward/f<F>/<M>_L<L>_s<S>/pred_<M>_L<L>_s<S>.npz` `(W,7,L)` + `metrics.csv` + `manifest_<M>_L<L>_s<S>.json` (written for **every** fold cell) |
| gate | npz has `fold=<F>`, `fold_test_end` equal to the table above, `pred.shape[0]` equal to the fold's test-window count; `n_eval_windows = (W//16)*16` |

**Cost per cell (measured/estimated, A100):** nlinear **6 s** (CPU-measured 4.4 s
for the fixed split, so the fold cells are the same order); dnn/cnn/rnn/lstm/gru
0.5–2 min; patchtst/itransformer 1–3 min; the three frozen-backbone arms
(`qwen_time_llm`, `calf_llm`, `timecma_llm`) 4–10 min (backbone load dominates);
sklearn arms 10 s–8 min (`svr`/`gradient_boosting` are the slow ones).
Totals for 60 cells per arm: nlinear ≈ 6 min; the 8 small neural arms ≈ 1–3 h
each; 3 LLM-inspired ≈ 4–10 h each; 5 sklearn ≈ 0.5–8 h each. **All 960 cells ≈
35–90 A100-hours.** Recommendation in §7: the 11 neural arms at 1 seed (220
cells, ≈ 4–12 h) is the defensible first tranche; the sklearn + LLM-inspired arms
can follow.

---

## 3. TABLE VI — REGIONAL HHS-10 (`table6_cell`)

The paper's **different** config is already in `configs.REGIONAL_CONFIG`
(`T=20`, `Lp=4`, `S=2`, `K=4`, 50 epochs, batch 32, lr 5e-4, 10 HHS channels);
`scripts/train_regional.py` consumes it rather than re-declaring it.

| field | value |
|---|---|
| `kind` | `table6_cell` |
| `model` | `miflu` first, then the arms |
| `L` | 2, 3, 5, 10, 13, 15, 20 |
| `seed` | 42, 43, 44 (rule 9) |
| `region` | `all` (paper config, V=10). `HHS1…HHS10` = single-region mode (V=1) |
| `priority` | P3 (MIFlu), P4 (baselines) |
| `env` | `mlflu_hpc` |
| expected_artefact | `hpc_results/regional/<region>/<M>_L<L>_s<S>/` — `pred_*.npz` `(W,V,L)`, `pred_*.csv`, `results_*.csv` (aggregate + per-region, z **and** patients), `epochs_*.csv`, `manifest_*.json` (hardware, partition, node, job id, wall seconds, ckpt sha256, data sha256, split) |
| gate | `n_eval_windows == (W//16)*16`; per-region rows = 10; `rmse_phys`/`pcc_phys` finite; `manifest.table == "VI (regional HHS-10)"`; `probe_only == False`; **partition must be `stingy`/`gpu_a100`** (rule 13) |

**Cost per cell:** MIFlu regional ≈ **2–3 min** on an A100 (ESTIMATE: 24 s/epoch
national × token ratio 49/359 × layer ratio 4/6 ≈ 2.2 s/epoch × 50 epochs ≈ 110 s,
plus export; the T=20/Lp=4 stack is 9 patches vs 42). Neural arms 10 s–2 min;
sklearn 10 s–3 min.
* MIFlu: 7 horizons × 3 seeds = **21 cells ≈ 1 h**.
* All 16 arms × 21 = 336 cells ≈ **6–15 A100-hours**.

**Data check first:** `python scripts/download_us_region.py --check` reports
`10/10 regions usable -> ALREADY PRESENT, nothing to download` (the file is on
disk: 1 119 rows, 1 084 weeks in 1997w40–2020w18). The hardened downloader
no-ops when the series are present and only fetches with `--force`.

---

## 4. TABLE VIII — ABLATIONS (`table8_cell`)

`scripts/train_miflu.py` gained additive flags; every default is unchanged
(A test asserts `resolve_variant(no flags) == CONFIG`).

| variant | flags | note |
|---|---|---|
| `full` | *(none)* | the published configuration; identical to the Table V cells |
| `no_lora` | `--no-lora` | LoRA adapters removed (blocks stay frozen, LNs train) |
| `no_text` | `--no-text` | text branch removed (`use_text=False`, embedder `none`) |
| `K2`, `K4`, `K8`, `K12` | `--num-layers K` | ForecastingLLM depth sweep (paper: 6 national / 4 regional) |
| `emb_prompt` | `--text-embedder prompt` | live GPT-2 prompt instead of the author's static file |

| field | value |
|---|---|
| `kind` | `table8_cell` |
| `model` | `miflu_<variant>` |
| `L` | 24, 36, 48, 60 (Table VIII averages over L) |
| `seed` | 42, 43, 44 |
| `priority` | P4 |
| `env` | `mlflu_hpc` |
| expected_artefact | `hpc_results/ablations/<variant>/L<L>_s<S>/predictions_miflu_L<L>_paper_protocol.csv` + `manifest_miflu_L<L>_s<S>_<variant>.json` (variant block: `use_lora`, `use_text`, `num_layers`, `text_embedder`, `is_default_config`) |
| gate | `manifest.ablation_variant == <variant>`; `manifest.variant.is_default_config == False` for every non-`full` row; the `full` row must equal the Table V cell for the same L/seed |

**Cost per cell ≈ 4–8 min** (1 rep, 20 epochs). `no_lora` (4 horizons × 3 seeds)
= 12 cells ≈ 1–1.6 h; the K sweep (4 values) = 48 cells ≈ 3–6 h; `emb_prompt`
= 12 cells ≈ 1–1.6 h; `no_text` = 12 cells ≈ 1–1.6 h (see the warning below).

> **⚠ `no_text` cannot move a number under the current architecture.** With
> `author_faithful=True` the text tokens are appended **after** the time patches
> and the attention mask is **causal**, so the forecast positions never attend to
> them. Measured on the real class:
> `tests/test_miflu_ablations.py::test_no_text_and_full_arms_agree_bitwise_on_cpu`
> asserts the two arms are **bit-identical**, and
> `test_default_text_pathway_is_masked_out_documented_state` asserts that the
> default arm itself is independent of the text tensor. This is the same
> phenomenon as `AGENTS.md` §2 rule 6 ("CPU effect exactly zero"). The `no_text`
> rows are therefore a **structural verification**, not an ablation that can move
> Table VIII; a text branch that can move a number needs `gated_inject`
> (cross-attention with text as keys), which `train_miflu.py` does **not**
> expose. Do not price `no_text` as a result-bearing row.

---

## 5. THE 168 LLM CELLS (`llm_cell`) — env routing

14 arms × 4 horizons × 3 seeds = **168 cells**. Roster and env come from
`hpc_experiments/queue/arms_registry.json` (single source of truth).

| field | value |
|---|---|
| `kind` | `llm_cell` (already implemented) |
| `model` | the 14 `hf_id`s of the registry (each with its `label`) |
| `L` | 24, 36, 48, 60 |
| `seed` | 42, 43, 44 |
| `priority` | P1 for `Qwen/Qwen2.5-1.5B` (already queued), P2 for the rest |
| `env` | **`mlflu_llm` only for the `qwen3_5`-family arm (`Qwen/Qwen3.8-27B-FP8`); `mlflu_hpc` for everything else** |
| expected_artefact | `hpc_results/expanded_runs/<label>_L<L>_s<S>/pred_<label>_L<L>_s<S>.npz` `(W,7,L)` + `metrics.csv` + `manifest_<label>_L<L>_s<S>.json` (model_id, **pinned revision sha**, encoder/head params, device, mocked=False) |
| gate | `manifest.probe_only == False`; `manifest.encoder.revision` is a 40-char sha; `manifest.encoder.mock_encoder == False`; `n_eval_windows == (W//16)*16`; **partition `stingy`/`gpu_a100`** |

### 5a. SUPPORTED / UNSUPPORTED — the pre-filter that decides whether a row can exist

The adapter (`scripts/llm_encoder_backbone.py`) mean-pools the **last hidden
state per token**, so an arm is runnable only if its class exposes per-layer
hidden states through `output_hidden_states=True`. `weights_worker.check_hidden_states`
enforces exactly that and records `UNSUPPORTED` **with a reason**.
`hpc_experiments/cpu_download_worker.sh` runs it on the CPU at download time, so
the status is known before any GPU is booked. The authoritative, current table is
the merged manifest:

```bash
python hpc_experiments/weights_worker.py merge \
    --manifest /home/sychan552/scratch/mlflu_weights/weights_manifest_A.json \
               /home/sychan552/scratch/mlflu_weights/weights_manifest_B.json \
    --out      /home/sychan552/scratch/mlflu_weights/weights_manifest.json
python hpc_experiments/weights_worker.py coverage --manifest \
    /home/sychan552/scratch/mlflu_weights/weights_manifest.json
```

**First measured verdict (2026-11-01 23:43, job 720175, CPU `tiny`):**
`tencent/Penguin-Encoder` — **UNSUPPORTED**, `requires_trust_remote_code`
(`AutoConfig.from_pretrained(..., trust_remote_code=False)` refuses the repo; the
weights downloaded fine, 882 MB, revision `62327d397d6034c6c7c91682c72f877f9fbf072d`).
The remaining ten were still downloading at hand-over; read the manifest for the
current answer instead of trusting this paragraph.

### 5b. Measured per-cell cost — replaces the unanchored 900 s default

`hpc_experiments/measure_llm_forward.py` times the **real adapter** on real
rendered prompts and prints `s_per_prompt`, `prompts_per_cell` and the projected
cell wall. A cell costs `7 × (549 + 74 + 170) = 5 551` encoder prompts **once**
(the pooled vectors are cached and reused across epochs; the shared
`Linear(D,L)` head then trains on the cache, which is negligible).

```bash
python hpc_experiments/measure_llm_forward.py --model-id Qwen/Qwen2.5-1.5B \
    --revision 8faed761d45a263340a0528343f099c05c9a4323 --batch 8 --repeats 3 \
    --gpu-factor 25 --json-out /home/sychan552/scratch/mlflu_weights/measured_llm_forward_qwen25_1p5b.json
```

Class pricing (`cost_model.py`): **S ≤3 B**, **M 4–15 B**, **L ≥27 B**, scaled
linearly in parameters from whichever measurement is available, with the A100
column explicitly labelled as a **projection** (÷ `--gpu-factor`, an assumption
until one GPU cell is measured). The measured JSON lands in
`/home/sychan552/scratch/mlflu_weights/measured_llm_forward_qwen25_1p5b.json`
(job **720218**, `tiny`, CPU); the numbers go into the ledger row for that job.
**Do not price an LLM night from this document alone — read that JSON first.**

---

## 6. TABLE IX — gated on Table VI (`table9_build`)

| field | value |
|---|---|
| `kind` | `table9_build` |
| `model`, `L`, `seed` | `-` (an aggregate, not a cell) |
| `priority` | P5 |
| `env` | `mlflu_hpc` |
| expected_artefact | `paper_tables/TABLE_IX_REGIONAL_TRAINING_TIME.csv` (per cell: wall_seconds, minutes, GPU, partition, node, job id, params, windows) + `…_MEANS.csv` (mean ± sd per model × L) |
| gate | **the row may only become `TODO` once every Table VI row it needs is `DONE`.** `python scripts/build_table_ix.py --check` exits **3** when nothing measured exists yet; a green `--check` (exit 0) is the gate. Cells whose manifest has no `wall_seconds` or `probe_only=True` are excluded and listed, never silently dropped |

`python scripts/build_table_ix.py` currently exits 3 against the real tree
(no regional cells on disk yet) and produces the CSVs from a synthetic tree — see
`tests/test_train_regional.py` and the ledger.
**Table IX is regional training time.** National timings are a different table and
must never be labelled IX.

---

## 7. WHAT FITS — the recommended tranche order (A100-hours)

| tranche | rows | A100-hours (est.) | why this order |
|---|---|---|---|
| T1 Table VI MIFlu (21 cells) | 21 | **≈1** | cheapest table, unlocks Table IX analysis, no new code path |
| T2 Table VIII `no_lora` + `emb_prompt` (24) | 24 | ≈2.5 | completes two of the four Table VIII components |
| T3 rolling origin, MIFlu **1 seed** (20) | 20 | ≈12–27 | the fold geometry proof at production scale |
| T4 LLM arms that are SUPPORTED (S class, 12 cells each) | 12/arm | see 5b | the 168-cell block is ~28 GPU-h at the old guess; measure first |
| T5 Table VIII K sweep (48) + `no_text` (12, structural only) | 60 | ≈4–8 | cheap, but `no_text` cannot move a number |
| T6 rolling origin, the 11 neural arms at 1 seed (220) | 220 | ≈4–12 | gives the arms a rolling-origin figure without 960 cells |
| T7 rolling origin, 9 remaining MIFlu seeds (180) | 180 | ≈108–243 | the largest single item; a separate campaign |
| T8 rolling origin, all arms × 3 seeds (960) | 960 | ≈35–90 | only after T6 shows the folds are informative |

Rule 9 note: an **incomplete** seed grid may not enter a comparison table, so T6
at 1 seed is a *diagnostic* pass, not a Table row. Either run all three seeds for
the arms or report the rolling-origin result as exploratory.

---

## 8. LLM LANE SPECS — `hpc_experiments/llm_lane_<slug>.sh`

The parent lane asked for ready-to-`sbatch` specs so tomorrow needs no design
work. They are generated (not hand-written) from the registry + the measured
cost, so a stale status can never be baked in:

```bash
python hpc_experiments/make_llm_lanes.py --manifest \
    /home/sychan552/scratch/mlflu_weights/weights_manifest.json \
    --out-dir /gpfs1/home/sychan552/stage5_a2_durable/code/llm_lanes
```

Each generated script is a **12-cell** driver (4 horizons × 3 seeds) with
`--arm-label`, `--llm-model-id`, `--llm-revision`, `--encoder-batch-size`,
`--export-dir`, the right `env` interpreter, a gres-free header, an A100 assert
(`torch.cuda.get_device_name(0)` must contain `A100` — rule 13), and
`probe_only=False`. **Submit them to `stingy` or `gpu_a100` only.** Arms marked
`UNSUPPORTED` in the manifest get no script; the generator prints
`SKIP <model>: <reason>` instead, which is the handover's answer to "which arms
are even runnable".

---

## 9. WHAT IS *NOT* IN THIS DOCUMENT

* No `sbatch`, no `scancel`, no cluster writes to `code/queue/*` — the coding lane
  owns none of those files.
* No number in this document is a result. The cost column is measured (nlinear,
  MIFlu national) or explicitly marked ESTIMATE; the LLM column must be replaced
  by the measured JSON before it is used to price a night.
* No Table VI/VIII/IX value. The runners exist; the cells do not.
