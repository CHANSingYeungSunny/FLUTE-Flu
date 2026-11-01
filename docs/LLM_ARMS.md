# docs/LLM_ARMS.md — LLM roster, environments, measured load numbers, exclusions

> **What this is:** §6 of `AGENTS.md`, moved verbatim — the downloaded/verified models, the `qwen3_5` environment facts (why a conda clone was structurally impossible), the measured GPU load-test numbers (params, load time, VRAM, forward latency, the fp8→bf16 dequantisation finding), the final roster, the LLM additions still to run, the exclusions table, and the approved cross-scale + reproducibility decisions.
> **When to read it:** before touching, adding, timing, or claiming anything about an LLM arm; before writing any instruction about the environment.
> **What it points to:** `docs/HPC_RUNBOOK.md` (the cluster facts that constrain all of it — `conda` is gone, `stingy` QOS, A100 memory), `docs/STATE.md` §1.2 (how the LLM arms currently rank), `docs/WORK_BREAKDOWN.md` §13.B/§13.E (what is still ❌), `docs/BENCHMARK_MODEL_ROSTER.md`.
> **Depends on:** `AGENTS.md` §2 rules 9, 12, 13 (seed protocol, measured provenance, publication-grade runtime), `docs/METHODOLOGY_METRICS_AND_SPLIT.md`.
> **Chain:** `AGENTS.md` → `docs/STATE.md` → **this file** → `docs/HPC_RUNBOOK.md` → the job/script named in the row.

---

## 6. LLM-arm status and the model roster

**Already downloaded & verified offline-loadable:**
`Qwen/Qwen2.5-1.5B`, `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` (both qwen2, 1.544 B,
~3.1 GB each), `Qwen/Qwen3.8-27B-FP8` (28.7 GB, fp8).
**Downloading:** `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` (66 GB bf16 → needs
`load_in_8bit` ≈33 GB on A100-40G).
**`qwen3_5` environment — SOLVED 2026-11-01 (separate env, `mlflu_hpc` untouched).**
- Env: **`mlflu_llm`** = `/home/sychan552/.venvs/mlflu_llm` (a **venv**, not conda — conda is
  gone, see §4). `/home/sychan552/.venvs/mlflu_llm/bin/python`.
- Stack: **Python 3.11.13, transformers 5.22.1, torch 2.6.0+cu124, huggingface_hub 2.4.0,
  tokenizers 0.23.3, accelerate 1.15.0** (job 718928 metadata + import).
- **`qwen3_5` is recognised** — offline `AutoConfig` prints `model_type = qwen3_5`,
  `Qwen3_5Config`, hidden_size **5120**, num_hidden_layers **64**, heads **24**,
  vocab **248320**, `vision_config` present (it is the multimodal
  `Qwen3_5ForConditionalGeneration`, fp8 block-quantised, 28.7 GB on disk).
- **Why cloning was structurally impossible, not merely inconvenient:** `qwen3_5` first
  ships in **transformers 5.3.0**; every transformers 5.x requires **Python >=3.10**
  (**>=3.11 from 5.21.0**); `mlflu_hpc` is **Python 3.9.25** with cp39 binary wheels.
  A clone pins the interpreter, so `pip install -U transformers` inside it can only
  ever resolve to a 4.x release. Also transformers 5.22.1 requires **torch >=2.6**,
  so torch could not stay at 2.5.1 either.
- **`mlflu_hpc` verified untouched**: transformers **4.57.6**, torch 2.5.1, and
  `lib/python3.9/site-packages/transformers/__init__.py` mtime still
  **2026-08-06 18:34:41** (job 718946).
- Old error (job 718448, 34 s): `ValueError: … model type `qwen3_5` but Transformers
  does not recognize this architecture` — resolved by the env above.
**GPU load test — DONE 2026-11-01, job 718976 on `stingy` (A100-SXM4-80GB), `ALL_OK`.**
`code/probe_qwen38_v2.sh`, offline, loader `Qwen3_5ForConditionalGeneration` (`dtype="auto"`):
- **params 27.3567 B** (27,356,728,560), tokenizer `Qwen3_5Tokenizer`
- weight load **86 s**, `.cuda()` **21.5 s**
- **VRAM after load = 54.73 GB allocated / 54.75 GB reserved**
- forward (15 tokens): logits `(1, 15, 248320)` in **2.385 s** cold, **0.136 s** warm;
  **peak VRAM 55.10 GB** of 85.1 GB → ~30 GB headroom
- ⚠️ **THE FP8 IS NOT USED FOR COMPUTE ON AN A100.** transformers 5.22.1 prints
  *"FP8 quantized models is only supported on GPUs with compute capability >= 8.9
  (e.g 4090/H100), actual = `8.0`. We will default to dequantizing the model to bf16."*
  A100 = sm_80, so the 28.7 GB fp8 checkpoint is **dequantised to bf16 at load** (all
  27.36 B params `torch.bfloat16`). Consequences: (a) the "28.7 GB on a 40 GB A100" premise
  is moot — on A100 this model needs **~55 GB**, so only the 80 GB cards work; (b) genuine
  fp8 compute needs an **H100 (sm_90)**, which this cluster does not offer; (c) any LLM-arm
  timing measured here is **bf16** and must be labelled as such in the paper.
- ⚠️ two kernels fall back to reference PyTorch implementations (much slower):
  `causal_conv1d` and `flash-linear-attention` are not installed in `mlflu_llm`.
  Install them before any throughput measurement; correctness is unaffected.

**Final roster**
- **Non-LLM (13)**: PatchTST, iTransformer, NLinear, DNN, CNN, RNN, LSTM, GRU,
  Decision Tree, Random Forest, Gradient Boosting, SVR, KNN.
- **LLM benchmark (3 run)**: TimeCMA-LLM, Qwen-Time-LLM, CALF-LLM.
- **MIFlu**: reproduction only (row 0 of every table, not a benchmark competitor).
- **LLM additions still to run** (feasible, from Tencent's lineup):
  `tencent/Penguin-Encoder` 0.4B (feature-extraction native),
  `tencent/Hunyuan-1.8B-Instruct` 2B, `tencent/WeMM-Embedding-2B` 3B,
  `tencent/WeMM-Embedding-4B` 5B (best candidate — official embedding model),
  `tencent/Youtu-HiChunk` 4B, `tencent/Hunyuan-4B-Instruct` 4B,
  `tencent/ContextPilot-8B` 8B, `tencent/Hunyuan-7B-Instruct` 8B,
  `tencent/KaLM-Embedding-Gemma3-12B` 12B, `tencent/ContextPilot-14B` 15B,
  plus `Qwen3.8-27B-FP8` 28B and `DeepSeek-R1-Distill-32B` 33B.
- **Excluded, with measured sizes (write as a table in the paper)**: Hy4-preview 780 B,
  Hy3 299 B, Hunyuan-A13B 80 B, DeepSeek-V3.1-Terminus 349 B, Step-5-Preview 650 GB,
  GLM-5.3 756 GB, MiniMax-M3.1-Flash 252 GB, MiMo-V2.6-Pro 573 GB,
  Kimi-K3.1-pro (gated), space-bunny (141 GB GGUF, needs llama.cpp),
  and all Translation / Image-to-3D / Video models (task mismatch).

**Cross-scale methodology decision (approved):** use ③ shared head + frozen base
(already the architecture), ① Pareto/efficiency frontier as the *main figure*,
② relative-to-seasonal-naive as a *column*; report **two rankings** (absolute and
efficiency); **never claim a single winner across scale classes**.

**Reproducibility protocol (approved, to implement):** pin `revision=<sha>`,
write per-model manifest (repo, revision, file sha256, tokenizer, torch/transformers
versions), and **freeze the extracted feature table (~2.4 MB) + its hash** so the
benchmark no longer depends on the HF cache at all.

---

## 7. Adapter status (2026-11-01) — the missing conversion now exists; no arm is scored yet

**Why this section exists.** Until 2026-11-01 nothing converted an LLM's frozen
representation into the array the benchmark compares, so **none** of the arms
below could enter the benchmark at all (`SKILL.md` §11 blocker 3,
`docs/WORK_BREAKDOWN.md` §11 "the 8 new LLM arms actually trained"). That
*code-level* blocker is now closed. The *run-level* blockers are listed per model
in §7.1 and have **not** been executed: no GPU was used and no checkpoint was
downloaded for this work (`AGENTS.md` §2 rule 13(b): probe-only).

| item | artefact |
|---|---|
| arm | `scripts/llm_encoder_backbone.py` — `FrozenLLMEncoder`: frozen causal/instruct LLM (`requires_grad=False`, `eval()` always, no dropout, last hidden layer, tuple outputs handled by `extract_last_hidden_state`) + **ONE** `nn.Linear(D, L)` shared across the 7 channels (`_ChannelIndependent` convention) |
| protocol wiring | `scripts/train_backbone_966.py --backbone llm_encoder` — registry-loaded by file path like the other arms, so it reuses `build_windows` (T=104, `containment="strict"`, 676/773 split), the train-only scaler, `set_seed(seed+L)`, Adam lr=5e-4 / 20 epochs / batch 16, validation-selected checkpoint, and the single Test evaluation |
| cell contract | `pred_*.npz` with `pred`/`target` `(W, 7, L)` + `target_start_row`, `L`, `seed`, `var_cols`, `model`, `profile`, `containment`, `space`; `save_pred_cell()` calls `scripts/eval_windows.py::check_cell_layout` **before** writing, so a transposed `(7, W, L)` array cannot reach the disk |
| per-arm identity | `--arm-label llm_<slug>` — the backbone is one code path but each model must be its own row: `analysis_expanded.py` keys models off the filename `pred_<label>_L<L>_s<seed>.npz`, so 14 arms sharing the label `llm_encoder` would collapse into one |
| determinism | `torch.manual_seed(seed)` before the head; encoder forced to `eval()` even when the runner calls `model.train()`; one forward pass, no sampling/`generate()`; pooled vectors cached by `(model_id, revision, prompt_sha256)` |
| memory | encoder runs only under `torch.no_grad()` in `--encoder-batch-size` chunks; pooled vectors are cached on **CPU** float32; `release_encoder_to_cpu()` parks a 55 GB encoder after its pass — encoder and a full-dataset activation graph never coexist |
| cache | in-memory by default plus `--encoder-cache <path>` (torch save) so a re-run is cheap and bit-identical; a cache from another `(model_id, revision, D)` is refused |
| provenance | per-cell run manifest: model id, **pinned revision sha**, torch/transformers/python versions, encoder params (total **and** trainable), head params, pooling rule, device actually used, cache stats, measured hardware, Slurm ids, code sha256, plus `probe_only` / `mock_encoder` / `artefact_is_a_result` |
| CPU path | `--mock-encoder` (tiny frozen mock, no download, no `import transformers` — asserted by a test) and `--dry-run` (CPU, 1 epoch, 32/16 train/val windows, probe-only export dir; refuses to write under `expanded_runs`) |
| unit tests | `tests/test_llm_encoder_backbone.py` — **31 passed**, CPU only: shape (4 horizons × 3 batch sizes), channel permutation, frozen-encoder bit-equality after `optimizer.step()`, `(W,7,L)` layout + transposed rejection, seed determinism, cache call-count, encoder-batch-size exactness, prompt rendering, hidden-state extraction, provenance, no-transformers-import |
| dry-run proof | `--dry-run` on L=24/seed=42 wrote one real cell with `pred`/`target` `(170, 7, 24)`, `check_cell_layout → W=170, n_eval=160`, `target`/`target_start_row` **bit-identical** to `calf_llm_L24_s42`; the npz and the mock `metrics.csv` were then **deleted**. Record: `_dryrun/llm_encoder/DRYRUN_RECORD.md` + the probe-only manifests |

### 7.1 The 14 arms, and what still blocks each one from a benchmark row

The roster resolves to **14 distinct model checkpoints** = the 12 entries of the
"LLM additions still to run" list **plus** `Qwen/Qwen2.5-1.5B` and
`deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` (downloaded, but never scored as
frozen-encoder arms). The three inspired arms (TimeCMA-LLM, Qwen-Time-LLM,
CALF-LLM) already have benchmark cells and keep them; `Qwen3.8-27B-FP8` and
`DeepSeek-R1-Distill-32B` each appear once. (`WORK_BREAKDOWN.md` §11 says "8 new
LLM arms", the additions list has 12 entries, and the brief says 14 — the 14 is
the distinct-checkpoint count this file's roster supports.)

**Common blockers A–F — every arm needs all six before a row exists:**

- **A. Weights in the compute-node cache.** `/home/sychan552/scratch/hf_cache`
  with **both** `HF_HOME` and `HF_HUB_CACHE` set (`HPC_RUNBOOK` gotcha 1); compute
  nodes have no internet (gotcha 2), and large downloads must run as a `batch`
  job, never on the login node (gotchas 9–12).
- **B. Pinned revision sha** recorded in the manifest. Only `Qwen2.5-1.5B` has
  one in this repo (`8faed761d45a263340a0528343f099c05c9a4323`,
  `innovation/assets.py`); every other model needs its sha resolved and written.
- **C. The right environment.** `mlflu_llm` (Python 3.11.13 / transformers
  5.22.1 / torch 2.6.0) for `qwen3_5`-family configs; `mlflu_hpc` (Python 3.9.25 /
  transformers 4.57.6) for everything else. The adapter accepts both the 4.x
  `torch_dtype=` and the 5.x `dtype=` keyword and records which one worked.
- **D. 12 cells per arm** = L ∈ {24, 36, 48, 60} × seeds **42/43/44**, on
  **A100/`stingy`**, with `probe_only=False`, plus the frozen feature table
  (~2.4 MB) + its hash (the reproducibility protocol above). No A100-asserting
  `sbatch` wrapper or 12-cell controller exists yet for these arms — the MIFlu
  (`code/miflu_a100_controller.sh`) and NLinear (`code/submit_nlinear_a100.sh`)
  ones are not reusable as-is.
- **E. The shared-window rule.** Every cell is scored on
  `eval_slice(W) = (W//16)*16` = **160/144/144/128** windows, never the full
  170/158/146/134, and the arm must sit in
  `hpc_results/expanded_runs/llm_<slug>_L<L>_s<seed>/` so `analysis_expanded.py`
  picks it up under its own name.
- **F. The shared head + identical budget.** 20 epochs, lr 5e-4, batch 16,
  validation-selected checkpoint, one `Linear(D, L)` per arm — supplied by
  `train_backbone_966.py`; no per-model tuning is allowed, or the cross-scale
  comparison (methodology ③) stops being legitimate.

| # | model (HF id) | size | env | weights / revision | still blocking (beyond A–F) |
|---:|---|---:|---|---|---|
| 1 | `Qwen/Qwen2.5-1.5B` | 1.5 B | `mlflu_hpc` | downloaded; revision pinned | 12 A100 cells; feature table + hash |
| 2 | `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` | 1.5 B | `mlflu_hpc` | downloaded (~3.1 GB, qwen2 arch) | revision sha not pinned in this repo; 12 A100 cells; feature table |
| 3 | `tencent/Penguin-Encoder` | 0.4 B | TBD (`mlflu_hpc` first try) | **not downloaded** | batch-partition download; revision sha; confirm the config loads (`AutoModel` path) and that mean-pooling is the right read-out for a feature-extraction-native encoder; 12 A100 cells |
| 4 | `tencent/Hunyuan-1.8B-Instruct` | 2 B | TBD | **not downloaded** | download; revision sha; arch/config support check in 4.57.6; chat template must not be applied (we render a plain numeric prompt); 12 A100 cells |
| 5 | `tencent/WeMM-Embedding-2B` | 3 B | TBD | **not downloaded** | download; revision sha; embedding model → verify the `AutoModel` branch returns hidden states (not only a pooled vector); 12 A100 cells |
| 6 | `tencent/Youtu-HiChunk` | 4 B | TBD | **not downloaded** | download; revision sha; arch support check; 12 A100 cells |
| 7 | `tencent/Hunyuan-4B-Instruct` | 4 B | TBD | **not downloaded** | download; revision sha; chat template stripped; 12 A100 cells |
| 8 | `tencent/WeMM-Embedding-4B` | 5 B | TBD | **not downloaded** | as #5 at 5 B (bf16 ≈ 10 GB, one A100 is ample); 12 A100 cells |
| 9 | `tencent/ContextPilot-8B` | 8 B | TBD | **not downloaded** | download; revision sha; arch support check; 12 A100 cells |
| 10 | `tencent/Hunyuan-7B-Instruct` | 8 B | TBD | **not downloaded** | download; revision sha; chat template stripped; 12 A100 cells |
| 11 | `tencent/KaLM-Embedding-Gemma3-12B` | 12 B | TBD | **not downloaded** | download; revision sha; Gemma-3 arch support (may need `mlflu_llm`); embedding read-out check; 12 A100 cells |
| 12 | `tencent/ContextPilot-14B` | 15 B | TBD | **not downloaded** | download; revision sha; arch support check; bf16 ≈ 30 GB → `--encoder-batch-size` 2–4; 12 A100 cells |
| 13 | `Qwen/Qwen3.8-27B-FP8` | 27.36 B | **`mlflu_llm` only** | downloaded (28.7 GB fp8) | **fp8 is dequantised to bf16 on sm_80 → 54.73 GB VRAM** (load test, job 718976): must run on the 80 GB A100s, `--encoder-batch-size` 1–2, expect slow reference kernels (`causal_conv1d` / `flash-linear-attention` missing); `AutoModelForCausalLM` load path must be verified in transformers 5.22.1; revision sha; 12 A100 cells |
| 14 | `deepseek-ai/DeepSeek-R1-Distill-Qwen-32B` | 33 B | `mlflu_hpc` (`load_in_8bit`) | **download in progress** (66 GB bf16) | finish the transfer as a `batch` job; revision sha; 8-bit or bf16 + `--encoder-batch-size` 1; 12 A100 cells |

**Excluded, unchanged** (measured sizes in §6): Hy4-preview, Hy3,
Hunyuan-A13B, DeepSeek-V3.1-Terminus, Step-5-Preview, GLM-5.3,
MiniMax-M3.1-Flash, MiMo-V2.6-Pro, Kimi-K3.1-pro (gated), space-bunny, and every
Translation / Image-to-3D / Video model.

### 7.2 Operational recipe once `stingy` frees up (one cell shown)

```bash
python scripts/train_backbone_966.py --backbone llm_encoder \
    --arm-label llm_qwen2p5_1p5b \
    --llm-model-id Qwen/Qwen2.5-1.5B --llm-revision 8faed761d45a263340a0528343f099c05c9a4323 \
    --encoder-batch-size 8 --profile author_966 --containment strict \
    --horizon 24 --seed 42 \
    --export-dir hpc_results/expanded_runs/llm_qwen2p5_1p5b_L24_s42 \
    --ckpt-dir checkpoints/llm_encoder/llm_qwen2p5_1p5b \
    --encoder-cache "$HF_HOME/../llm_cache/qwen2p5_1p5b.pt"
```

Run it 12× per model (4 horizons × 3 seeds) inside an A100-asserting wrapper
(`torch.cuda.get_device_name(0)` must contain `A100`, exiting non-zero
otherwise — `AGENTS.md` §2 rules 12–13). Every cell then has its own
`manifest_<label>_L<L>_s<seed>.json`, its cell, and its `metrics.csv` row; only
then may the arms be aggregated, and the timing column must be labelled **bf16
on A100-SXM4-80GB, `stingy`**. Never mix a mock/CPU cell into a table
(`probe_only=True` is set automatically for those).

