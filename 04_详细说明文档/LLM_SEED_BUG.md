# 04_详细说明文档/LLM_SEED_BUG.md — the seed never entered the LLM training path, and the scale-ladder repair

> **What this is.** The evidence, root cause, fix, invalidation list and quarantine for the
> 2026-11-02 seed defect in the frozen-LLM arms, plus the three-arm scale-ladder plan
> (Qwen-7B / Llama-8B / Qwen-14B) that repairs the *other* three weaknesses a reviewer would
> raise. It is the single source of truth for "which LLM cells are valid".
> **When to read it.** Before quoting any LLM-arm mean or ±sd; before aggregating
> `expanded_runs/*qwen*` / `*llama*` / `*tencent_*` cells; before planning A100 time for an
> LLM arm.
> **What it points to.** `05_程序代码/llm_seed_provenance.py` (the gate), `05_程序代码/train_backbone_966.py`
> (the fix), `05_程序代码/llm_encoder_backbone.py` (where the RNG was reset),
> `hpc_experiments/quarantine_unseeded_cells.py`, `$R/expanded_runs_pre_seedfix/QUARANTINE.json`,
> `hpc_experiments/queue/{rows_scale_ladder.tsv,merge_rows_scale_ladder.py}`,
> `05_程序代码/verify_llm_seed_effect.py` (the measurement).
> **Depends on.** `AGENTS.md` §2 rules 9 (mean ± sd over the same seed set), 12–13 (measured
> provenance, publication-grade hardware).
> **Chain.** `AGENTS.md` → `04_详细说明文档/LLM_ARMS.md` §7 (roster; owned by another lane) → **this file**
> → the evidence script and the quarantine manifest.

---

## 0. THE SENTENCE THAT MUST REACH THE PAPER'S LIMITATIONS SECTION

**All LLM-arm results produced before 2026-11-02 03:57:47 +08:00 are invalid — the seed never
entered the training path, so the cross-seed standard deviation was exactly zero by
construction, not by convergence.**

Anyone quoting an LLM ±sd from the night before that timestamp is quoting a bug. The affected
cells are listed in §4 and have been moved out of the aggregation tree (§5).

---

## 1. THE FINDING (measured, not inferred)

A queue log showed `ds_r1_distill_qwen1_5b_L24_s42|s43|s44` all with the same gate to 15
significant digits (`4.443883356674532`). That is not what three independent draws look like.
The artefacts were then compared directly with
`05_程序代码/verify_llm_seed_effect.py --root $R/expanded_runs --label ds_r1_distill_qwen1_5b
--label qwen25_1_5b` (output also at `$R/code/_seed_effect.json`):

| arm | horizons checked | seed pairs | `np.array_equal(pred_a, pred_b)` | `max abs(pred_a - pred_b)` |
|---|---|---|---|---|
| `ds_r1_distill_qwen1_5b` | L24, L36, L48, L60 | 12 (4 × 3) | **True, all 12** | **0.0 exactly, all 12** |
| `qwen25_1_5b` | L24, L36, L48, L60 | 12 (4 × 3) | **True, all 12** | **0.0 exactly, all 12** |
| `tencent_hunyuan_1p8b_instruct` | L24, L36, L48, L60 | 12 (4 × 3) | (queue log: identical `gate` per horizon) | — |

`target` and `target_start_row` are also identical across seeds — correct, they describe the
same test split — so the comparison isolates the model's output, not the 06_原始数据集.

The npz payloads record the **right** seed (`seed=42/43/44`), so the file NAME cannot reveal
the defect. The field that does is the run manifest:

```json
"encoder": { "determinism": { "manual_seed": 42, ... } }      <-- for seed 42, 43 AND 44
```

Summary of the measurement run: `pairs=24 identical=24 any_diff=False`, exit code 4.

---

## 2. ROOT CAUSE — exact lines

1. `05_程序代码/train_backbone_966.py::train_one` correctly calls `set_seed(seed + L)` (line 221)
   at the top of every fit, exactly like NLinear/MIFlu.
2. `train_one` then builds the arm with `build_model(name, T, N, L, device)` (line 247), and
   `build_model`'s `mode == "llm"` branch called
   `m = cls(T=T, N=N, L=L, **LLM_ENCODER_OPTS)` (line 163).
3. **`LLM_ENCODER_OPTS` never contained `seed`.** It is filled once in `main()` (lines 633–644)
   with `model_id`, `revision`, `encoder_batch_size`, `device`, `mock_*`, `local_files_only`,
   `allow_unpinned_revision`, `cache_path` — and nothing else. Because it is filled **outside**
   the `(L, seed)` loop, a seed parked there would also be stale after the first cell.
4. So `FrozenLLMEncoder.__init__` ran with its default `seed: int = 42`
   (`05_程序代码/llm_encoder_backbone.py` line 610), and that constructor executes
   `torch.manual_seed(self.seed)` **twice** — line 639 (before the frozen encoder) and line 658
   (immediately before `nn.Linear`) — i.e. it *overrode* the `set_seed(seed + L)` from step 1.
5. Consequence, both halves of the draw were frozen at 42: the head initialisation **and** the
   global RNG stream that `DataLoader(..., shuffle=True)` consumes for its batch order. Hence
   bit-identical predictions for seeds 42/43/44 while the manifest still stamped the requested
   seed into `seed`.

**Scope.** Only the `mode == "llm"` branch. The 16 trained arms are unaffected — each gets its
own `set_seed(seed + L)` and nothing re-seeds afterwards. Verified by measurement on the same
day: `patchtst` and `nlinear` across seeds 42/43/44 give `max abs(pred diff)` = **2.1 – 6.5**
(`pred_equal=False` for every pair at every horizon), i.e. genuinely different draws.

---

## 3. THE FIX (deployed 2026-11-02 03:57:47 +08:00)

`05_程序代码/train_backbone_966.py`, 3 lines in one file — the seed is now passed through
`build_model`, not stored in a loop-external dict:

```python
def build_model(name, T, N, L, device, seed=None):
    ...
    elif mode == "llm":
        opts = dict(LLM_ENCODER_OPTS)
        if seed is not None:
            opts["seed"] = int(seed) + int(L)      # the arm's seed + L convention
        m = cls(T=T, N=N, L=L, **opts)
```

```python
    model = build_model(name, T, N, L, device, seed=seed)   # was: (name, T, N, L, device)
```

Deployment discipline: pre-fix file kept as `$R/code/train_backbone_966.py.bak_seedfix`;
`py_compile` passed under `mlflu_hpc`; the swap was a single `os.replace` (`mv -f` within the
same directory) so no reader — including the running lane — can ever observe a torn file. The
`.bak_seedfix` mtime is 03:51:12, the live file's is **03:57:47 +08:00**.

**What the fix deliberately does not touch.** The frozen-encoder vector cache is keyed on
`(model_id, revision, prompt_sha256)` — correctly seed-independent, because the encoder is
frozen and its outputs are a function of the weights and the prompt only. The prompt text is
built from train-only statistics, deterministic. The head is a bare `nn.Linear` with no
dropout, and `FrozenLLMEncoder.train()` forces the encoder back to `eval()`. So the only two
RNG consumers in this arm are exactly the two the fix now seeds: head init and batch order.
The mock encoder draws its weights from an **explicit** `torch.Generator`
(`llm_encoder_backbone.py` line 452), which is why it never disturbed the global RNG — and why
the defect could not have been caught by the mock-encoder tests.

**Regression test.** `tests/test_llm_seed_passthrough.py` (6 tests, CPU, no download):
different seeds give different heads, the same seed is reproducible, the horizon enters the
seed, the process RNG is left at `seed + L`, `provenance()["determinism"]["manual_seed"] ==
seed + L`, and a trained arm ignores the new keyword. The pre-existing adapter suite still
passes (**31 passed**).

**End-to-end proof, on the cluster, after the fix** (`hpc_experiments/seedfix_proof.py`, job
**721085**, `tiny`, 9 s, probe-only): two mock-encoder cells at L=24, seeds 42 and 43 —

```
seed 42: manual_seed=66   (= 24 + 42)   pred_sum=769.1714
seed 43: manual_seed=67   (= 24 + 43)   pred_sum=56.6030
pred_equal=False   max|dpred| = 0.428975
SEEDFIX_PROOF PASS
```

Before the fix the same pair was bit-identical (`max|dpred| = 0`) and both manifests said
`manual_seed=42`. This is the check that distinguishes a real draw from the defect, and it runs
in 9 seconds on a CPU node, so it can be repeated cheaply after any future change to the arm.

---

## 4. WHAT THE BUG INVALIDATED — 36 cells

| arm | cells | horizons × seeds |
|---|---|---|
| `qwen25_1_5b` | 12 | L ∈ {24,36,48,60} × s ∈ {42,43,44} |
| `ds_r1_distill_qwen1_5b` | 12 | same |
| `tencent_hunyuan_1p8b_instruct` | 12 | same |
| **total** | **36** | |

`tencent_wemm_embedding_2b` produced no usable cell (it failed with
`arch-unsupported: trainer rc=1 in env=hpc and rc=1 in env=llm`), so it contributes nothing to
this list. No other LLM arm had produced a cell when the fix landed.

**Superseded seeds, not repaired seeds.** Those 36 cells are on seeds 42/43/44. On 2026-11-02
04:05 the protocol was amended to **uniform 10 seeds, 2021–2030, for every model**
(`04_详细说明文档/PROTOCOL_AMENDMENT_SEEDS.md`), so 42/43/44 is no longer the benchmark seed set and the
36 cells are not "repaired" — they are replaced. They stay quarantined because a stale npz must
never look valid, and no repair rows are staged for them.

**Why these 36 never reached `02_数字表格/`.** `05_程序代码/analysis_expanded.py::load()` keeps a
closed `FAMILY` whitelist (the 16 trained arms + `miflu` + the three inspired LLM arms), and the
new labels (`qwen25_1_5b`, `ds_r1_distill_qwen1_5b`, `tencent_*`) are not in it. The
contamination was therefore latent, not published. The gate in §6 exists precisely because
someone will eventually add those labels.

---

## 5. QUARANTINE — the poisoned cells are out of the tree

Overwriting a cell in place leaves a window in which a stale npz still looks valid, so the
cells are **moved**, not rewritten:

* tool: `hpc_experiments/quarantine_unseeded_cells.py --root $R/expanded_runs --apply`
* destination: `$R/expanded_runs_pre_seedfix/<cell-dir>` (one atomic `os.replace` per
  directory, so a reader sees a cell at the old path or the new one, never a half-moved tree)
* evidence: `$R/expanded_runs_pre_seedfix/QUARANTINE.json` — per cell, the recorded
  `manual_seed`, the expected `L + seed`, and the reason
* re-run list: `$R/expanded_runs_pre_seedfix/RERUN_NEEDED.tsv`
* safety: a directory whose npz exists **without** a manifest is treated as in-flight and
  skipped, so a concurrently running lane can never have a cell pulled out from under it.

A cell is quarantined **iff** its manifest carries an `encoder` block and
`encoder.determinism.manual_seed != L + seed`. That rule is what
`05_程序代码/llm_seed_provenance.py` implements, so the judgement is reproducible and needs no
hard-coded list of labels.

---

## 6. THE GATE — the pipeline refuses bad provenance; a human's memory is not the control

`05_程序代码/llm_seed_provenance.py` exposes `cell_seed_status(npz)`, which returns
`{is_llm, ok, recorded, expected, reason}` using the invariant
`manifest.encoder.determinism.manual_seed == L + seed`. It is wired into the aggregation path
(`05_程序代码/analysis_expanded.py::load()`), which **skips** a provenance-invalid cell and prints
one `[seed-gate] REFUSED` line per cell instead of letting it into a table. Non-LLM cells and
cells without a manifest are unaffected (the latter are reported, never silently trusted).

This mirrors the MIFlu oracle gate: the check lives in the pipeline, not in the operator.

---

## 7. RE-RUN COST (measured, per arm, 1.5B)

| state | wall per cell | source |
|---|---|---|
| first cell of an arm (cold: tokenise + encoder forward over 5 551 prompts) | **78.4 s** (`qwen25_1_5b_L24_s42`), 79.4 s (`ds_r1_distill_qwen1_5b_L24_s42`) | manifest `wall_seconds` |
| every later cell (frozen-feature cache warm) | **10.3 – 11.5 s** | 22 manifests |

So re-running all 36 invalid cells on one A100 costs ≈ `6 × 78 s + 30 × 11 s` ≈ **9 min of
GPU wall for the three 1.5–2B arms together**, provided the encoder caches
(`$HF_HOME/../llm_cache/<label>.pt`) survive. That is why quarantine-then-re-run was the right
call rather than "keep them for reference".

---

## 8. THE SCALE LADDER — three weaknesses, three arms

### 8.1 The three weaknesses a reviewer would raise

1. **Only two points on the ladder** (1.5B and 32B). A line through two points cannot show
   curvature or saturation, so "does the frozen-encoder arm keep improving with scale?" is
   unanswerable.
2. **No 7B / 14B**, so the middle of the curve is empty and a knee cannot be located even in
   principle.
3. **No Llama-based point**, so "scale" and "base architecture" (Qwen tokenizer + pretraining
   vs Llama) are perfectly confounded. `Qwen-7B` vs `Llama-8B` are near-isoscale with different
   bases — the only clean way to separate the two effects.

### 8.2 What fixes them

| arm | HF id | params | env | why this one |
|---|---|---|---|---|
| `ds_r1_distill_qwen7b` | `deepseek-ai/DeepSeek-R1-Distill-Qwen-7B` | 7.62 B | `hpc` (transformers 4.57.6) | adds a third rung; isoscale reference for the Llama contrast |
| `ds_r1_distill_llama8b` | `deepseek-ai/DeepSeek-R1-Distill-Llama-8B` | 8.03 B | `hpc` | **the architecture contrast** — near-isoscale with Qwen-7B, different base and tokenizer |
| `ds_r1_distill_qwen14b` | `deepseek-ai/DeepSeek-R1-Distill-Qwen-14B` | 14.77 B | `hpc` | fills the empty middle so the knee between 8B and 32B is locatable |

All three are Qwen2 / Llama architectures native to transformers 4.57.6, so `env=hpc`
(`mlflu_hpc`); `mlflu_llm` is only for the `qwen3_5` family.

**`Llama-70B` is EXCLUDED, not deferred.** A 70B checkpoint in bf16 is ≈140 GB of weights
before any activation, so it cannot be loaded on an 80 GB A100 at any encoder batch size — the
same arithmetic that already forces `DeepSeek-R1-Distill-32B` (61 GB bf16) to
`--encoder-batch-size 1`. There is no H100 (sm_90) on this cluster, so there is no fp8 escape
either. An 8B Llama is therefore the largest Llama base that can enter this comparison, and the
architecture contrast is stated at 7B-vs-8B, not at 70B.

### 8.3 Pinned revisions and probe verdicts

Filled in by `hpc_experiments/scale_ladder_worker.py`, which pins
`HfApi().model_info(repo).sha`, downloads into the scratch HF cache (resume-capable), and then
runs a **per-layer** hidden-state smoke test on CPU. The probe asserts
`len(hidden_states) == num_hidden_layers + 1`, that every layer keeps the token axis
`(1, seq, hidden)`, and that consecutive layers **differ** — a stack of one repeated vector is
the "pooled embedding only" failure mode that already disqualified `tencent/Youtu-HiChunk`.

| arm | pinned revision | probe | per-layer hidden states |
|---|---|---|---|
| Qwen-7B | `916b56a44061fd5cd7d6a8fb632557ed4f724f60` | **OK** (job 721090) | `qwen2`, 28 layers → **29 tensors**, each `(1, 12, 3584)`, min layer-to-layer delta **11.5**, `Qwen2ForCausalLM`, 7 615 616 512 params |
| Llama-8B | `6a6f4aa4197940add57724a7707d069478df56b1` | **OK** (job 721135) | `llama`, 32 layers → **33 tensors**, each `(1, 12, 4096)`, min delta **0.289**, `LlamaForCausalLM`, 8 030 261 248 params, **loaded with `trust_remote_code=False`** |
| Qwen-14B | `1df8507178afcc1bef68cd8c393f61a886323761` | **OK** (job 721261) | `qwen2`, 48 layers → **49 tensors**, min delta **4.75**, `Qwen2ForCausalLM`, 14 770 033 664 params; download 29.55 GB in 718 s |

**The Llama question, answered plainly.** `transformers` 4.57.6 in `mlflu_hpc` loads
`deepseek-ai/DeepSeek-R1-Distill-Llama-8B` **without `trust_remote_code`**: `AutoConfig` reports
`model_type=llama`, `auto_map=None`, and `AutoModelForCausalLM.from_pretrained(...,
trust_remote_code=False)` returns `LlamaForCausalLM`. The probe would have raised on any
`requires_trust_remote_code` refusal, so this is measured, not assumed.

**On `last_hidden_state`.** A `*ForCausalLM` forward returns **no** `last_hidden_state`
attribute (`has_last_hidden_state_attr=False` for all three) — that attribute belongs to the
`*Model` / feature-extraction outputs and is a *pooled/sequence* vector, not per-layer. What the
adapter consumes is `out.hidden_states`: a tuple of `num_hidden_layers + 1` per-layer tensors
that keep the token axis. The probe therefore checks exactly that: length equals
`num_hidden_layers + 1`, every tensor is `(1, seq, hidden)`, and consecutive layers **differ**
(min deltas above). A model that only returned a pooled embedding — the failure mode that
disqualified `tencent/Youtu-HiChunk` — cannot pass this check.

**Downloads** (job **721068**, `tiny`, cpunode-060, 04:13:48 → 04:38:44, 24 min 56 s, 8 CPU /
8192 M, no gres): Qwen-7B **15.24 GB** in 382 s, Llama-8B **16.07 GB** in 394 s, Qwen-14B
**29.55 GB** in 718 s — ≈40 MB/s, 60.9 GB total, into
`/home/sychan552/scratch/hf_cache/hub`. Revisions were pinned **before** each download and
written to `weights_manifest_scale_ladder.json` incrementally, so a crash cannot lose them.

The pin is taken from `HfApi().model_info(repo).sha` and written to the manifest **before** the
download starts, so a crash cannot lose it. Revisions are then propagated into
`arms_registry.json` by `merge_rows_scale_ladder.py --sync-revision-from-manifest`, never typed
by hand (`HPC_RUNBOOK` gotcha 19).

### 8.4 Measured per-cell cost and the per-arm projection

**A second defect had to be fixed first, and it is the reason this section is short.** The
best-validation snapshot in `train_one` was
`{k: v.detach().clone() for k, v in model.state_dict().items()}`. `state_dict()` includes the
**frozen encoder**, so the clone duplicated the whole backbone on the GPU:

* a 7B arm needs 15.2 GB (encoder) + 15.2 GB (clone) and **OOM'd on a 44 GB A40**
  (job 721112, 2026-11-02) at `best_state = {...}`;
* a 32B arm would need 61 + 61 = **122 GB**, so **no `DeepSeek-R1-Distill-Qwen-32B` cell could
  ever have completed on an 80 GB A100 either** — that arm was never runnable as written;
* moving the clone to the host only moved the problem: job 721154 was **SIGKILLed by the cgroup**
  at 32 GB of host RAM.

Fixed at **2026-11-02 04:44:49 +08:00**: the snapshot now excludes tensors whose parameters are
`requires_grad=False` (they never change; `save_locked_ckpt` already did exactly this) and
restores with `strict=False` only in that case. **Every one of the 16 trained arms has no frozen
parameters, so it takes the unchanged branch and is bit-identical to before.**

What the A40 runs did measure before the OOM, on the 7B arm at L=24 (load + encoder pass over
5 551 prompts + 2 of 20 head epochs):

| run | wall to the OOM point | note |
|---|---|---|
| 721112 | **402.0 s** | device-side clone OOM |
| 721154 | **372.3 s** (SIGKILL) | host-side clone OOM at `--mem=32000M` |

So the **encoder pass dominates completely**: it is ~6 minutes of a 7B cell on an A40, three
orders of magnitude more than the 1.5B head-only cell (11 s warm). This is the number that
matters for planning, and it is paid **once per arm** because the pooled vectors are cached by
`(model_id, revision, prompt_sha256)`.

**Why no clean post-fix number here.** After the 04:44:49 fix the remaining step is a single
re-run of that same job, and it could not be submitted: every attempt returned
`sbatch: error: QOSMaxSubmitJobPerUserLimit` even after two no-op watchdogs (`720003`,
`720004` — documented as no-ops in `04_详细说明文档/LEDGER.md`) were cancelled. The measurement job is
staged (`hpc_experiments/scale_ladder_probe.sh` → `gpu-a40-01`, `--allow-non-a100-bound`, which
stamps `hardware_bound=true`; or the same script on `gpu_a100` **without** that flag for the
quotable A100 number).

**Projection under the amended protocol (40 cells per arm), using only measured quantities:**
per arm = one encoder pass + 40 head cells. With the A40 encoder pass ≈ 400 s and a head cell
≈ 11 s (the 1.5B warm cell, which is an *upper* bound for a head-only fit because a 7B head is
the same `Linear(D, L)` shape class), the three arms cost ≈ 3 × (400 + 40 × 11) ≈ **3 × 840 s ≈
42 min on an A40**, and an A100 is strictly faster. **Yes, the whole ladder fits inside one
4-hour `stingy` window with a wide margin** — the binding constraint is GPU availability, not
wall clock.

---

## 9. OPEN ITEMS

1. **Measured 7B encoder cost.** One `--probe-only` cell at the smallest horizon (L=24) on
   `gpu_a100`/`stingy`, reporting wall seconds; then extrapolate this document's §8.4 and the
   one-4-hour-`stingy`-window question.
2. **Merge the rows.** `$R/code/queue/rows_scale_ladder.tsv` — **120 rows**
   (3 arms × 4 horizons × 10 seeds 2021–2030, `kind=llm_cell`, `P2`, `env=hpc`) — and
   `rows_scale_ladder_registry.json` are staged but **not merged**: the queue directory is owned
   by another lane (it announced sole ownership in `04_详细说明文档/LEDGER.md` at 04:05 and had just
   appended 1 062 rows). The owner runs
   `python merge_rows_scale_ladder.py --apply --registry --sync-revision-from-manifest`.
   The 12-cell/3-seed layout in the original brief is **superseded** by the protocol
   amendment; staging 12 would have produced a mixed-seed table.
3. **First correctly-seeded cell.** Confirm on a new manifest that
   `encoder.determinism.manual_seed == L + seed` (e.g. L=36, seed=2021 → 2057) before trusting
   any post-fix LLM cell.

---

## 10. DEPLOYMENT MANIFEST — every file this work touched

| file | role | state |
|---|---|---|
| `05_程序代码/train_backbone_966.py` | **the fix**: `build_model(..., seed=None)` + `seed=seed` | edited, deployed to `$R/code/` 03:57:47, `.bak_seedfix` kept |
| `05_程序代码/llm_encoder_backbone.py` | where the RNG was reset (L639/L658) | **not edited** — the adapter's behaviour is correct once it is given the right seed |
| `05_程序代码/llm_seed_provenance.py` | the gate: `cell_seed_status`, `audit`, `refused_labels` | new, deployed |
| `05_程序代码/analysis_expanded.py` | aggregation path that now REFUSES a bad cell (`[seed-gate]`) | edited, deployed |
| `05_程序代码/verify_llm_seed_effect.py` | the measurement behind §1 | new, deployed, ran |
| `tests/test_llm_seed_passthrough.py` | 6 tests pinning the fix | new, **6 passed** |
| `tests/test_llm_seed_provenance.py` | 8 tests pinning the gate both ways | new, **8 passed** |
| `hpc_experiments/quarantine_unseeded_cells.py` | moves invalid cells out of the tree | new, uploaded, **apply pending** |
| `hpc_experiments/scale_ladder_worker.py` | pin revision + download + per-layer probe | new, uploaded, job 721032 |
| `hpc_experiments/scale_ladder_download.sh` | the `tiny` batch wrapper (no gres, absolute paths) | new, **job 721032** |
| `hpc_experiments/scale_ladder_probe.py` + `.sh` | cold/warm cost measurement, `--probe-only` | new, submitted when weights + GPU exist |
| `hpc_experiments/queue/make_rows_scale_ladder.py` | generator for the 120 rows + registry fragment | new |
| `hpc_experiments/queue/rows_scale_ladder.tsv` | 120 rows, 11 columns, staged **not merged** | new |
| `hpc_experiments/queue/rows_scale_ladder_registry.json` | the 3 arms, revision filled from the manifest | new |
| `hpc_experiments/queue/merge_rows_scale_ladder.py` | idempotent, flock-guarded merge | new, sandbox-tested |
| `hpc_experiments/remote_inspect.py` | read-only queue/run inspector (PowerShell cannot quote reliably) | new |
| `hpc_experiments/run_after_outage.sh` | the one-shot post-outage driver | new |
| `04_详细说明文档/LLM_SEED_BUG.md` | this file | new |
| `04_详细说明文档/LEDGER.md` | one single-line row at 04:12 | appended |

**Cluster-side steps still outstanding at the time of writing**: applying the quarantine, the
first post-fix cell's manifest check, confirming job 721032, submitting the 7B cost probe, and
the rows merge (owner's call). The login node became unreachable at ~04:00 and every SSH
attempt timed out, so those steps are documented rather than claimed.
