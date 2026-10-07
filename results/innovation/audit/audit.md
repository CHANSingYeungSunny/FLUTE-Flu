# Repository audit — innovation infrastructure (round 1: infra + local smoke)

Authoritative plan frozen at runtime (revision 10): see `plan_sha256.json`
(recomputed each run) and `paths.PLAN_SHA256_EXPECTED`.

> Plan: `MIFlu_innovation_plan_v2.md`
> SHA-256: `AA4AB1C8842E893A4690787E17ADD0CA193C86825FFF9FD89F46952C7F9E7961`
> (runtime recomputation matched — `plan_sha256.json.matches == true`)

## A. Data, split, scaler

* Raw: `data/raw/national_illness_raw.csv` — 1025 data rows, `epiweek 200201..202152`.
* Channels (N=7): `data/../scripts/configs.py:61-68`, `ILITOTAL` at index 4.
* Split: `configs.py:75-79` `FULL_ROWS=1025, TRAIN_END=717, VAL_END=819`;
  `assert_full_window()` `:85-96` blocks the 966-row truncation;
  `derive_split()` `:99-113` re-derives and ASSERTS 717/819.
* Scaler: `scripts/scaler_utils.py:114-115` fits on `data[:train_end]` ONLY,
  `EPS=1e-8`, population std (ddof=0) — reproduced byte-for-byte.
  `load_scaler()` in the innovation pipeline re-fits from train and asserts
  agreement (`assert_consistent_with`) — never refits on val/test.
* Windows: `train_ablation.build_windows` uses stride 1 and labels a window by
  its TARGET start week (`<= val_end`). `innovation/data_pipeline.build_windows`
  mirrors this EXACTLY (verified: train/val/test = 613/103/182 windows at L=24).

## B. GPT-2 in two roles

1. **Textual input embedder** — `scripts/textual_embedder.py:170`
   `TextualInputEmbedder`; frozen by `:189-190`; `forward(prompt) ->
   last_hidden_state (1, K, 768)`. Prompt statistics from TRAIN only
   (`compute_prompt_stats` `:124-134`).
2. **Forecasting backbone** — `scripts/miflu_model.py:254` `ForecastingLLM`
   (GPT-2 K=6 layers + LoRA on `c_attn`, `:316-318`) and `:476` `MIFlu`
   (`forward(x (B,N,T), htext) -> y_hat_rev (B,N,L)`).
   `ModalityAligner` `:217` `forward(htime, htext) -> (B, P, D)`.

The innovation `gpt2_miflu` backbone is an ADAPTER around the existing model
(no second copy → no drift).

## C. Risks identified (and how this round addresses them)

| Risk | Evidence | Mitigation in this round |
|---|---|---|
| test leakage | no val/test scaler fit found (`scaler_utils.py:114`); prompt stats train-only | innovation `data_pipeline.load_scaler` asserts train-only; runner NEVER writes test artifacts |
| mean-over-lead mixing | `compute_miflu_indicators.py:297-300` fixes `fixed_step`; legacy `mean_over_lead` `:308` retained only for contrast figures | innovation uses `fixed_step, step=0` mirror only |
| artifact overwrite | existing scripts overwrite fixed filenames (e.g. `train_ablation.py:436`, `train_miflu.py:371`) | innovation run dirs are CREATE-ONLY; registry is APPEND-ONLY (`test_no_overwrite.py`) |
| non-reproducibility | `torch.load` without `weights_only` (`train_ablation.py:509`); no dependency lock | innovation loads with `weights_only=True`; per-run `environment.txt` + `git_commit.txt` + `plan_sha256.json` |
| boundary `.lt.` vs `.le.` | `train_baseline.py:65` uses `<` (1 week narrower) than the main protocol | innovation mirrors the MAIN protocol (`<=`) only |
| stale artifacts | old `metrics.csv` with removed `peak_hit_rate` columns still on disk | innovation writes fresh schema; old files untouched |

## D. Prompt variation (revision 6)

`prompt_variation_report.json`: **4 unique prompts** (one per horizon), prompt
length 1552 for all horizons, **within-horizon variation = 0**, cross-horizon
GPT-2 embedding **pairwise cosine min = 0.9999996**, per-dim mean variance
≈ 5e-6. ⇒ The TF-IDF+SVD context is a **FIXED CONTEXTUAL EMBEDDING baseline**
(constant across weeks within a horizon, near-identical across horizons). It
must not be described as a per-window text feature.

## E. Local dependency probe

`dependency_probe.json`: all of torch / transformers / numpy / pandas / scipy /
sklearn / statsmodels / matplotlib are available locally; gpt2 is in the local
HF cache. `UNAVAILABLE_LOCAL_DEPENDENCY` is recorded for fastText / BERT /
MiniLM / Chronos / TimesFM / Moirai (deferred to batch 2; never downloaded).

## F. Architecture equivalence (revision 5)

See `test_architecture_equivalence.py` and each backbone's
`architecture_report()`: DLinear/NLinear/iTransformer report `faithful=True`;
PatchTST reports `faithful="partial"` because it is trained from scratch (no
self-supervised pretraining) and therefore labelled a
**"supervised re-implementation"**, not the pretrained reference model.
