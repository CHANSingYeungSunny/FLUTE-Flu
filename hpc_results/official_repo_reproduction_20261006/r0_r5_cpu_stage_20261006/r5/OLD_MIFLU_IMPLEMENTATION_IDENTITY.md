# OLD (historical) MIFlu — Implementation Identity

Read-only reconstruction. Everything below is quoted from files under `C:\Users\Asus\Desktop\FYP code\MLFlu`. No file was modified.

## 1. One-line answer

The historical **`gpt2_miflu`** entry of the 4-vs-4 comparison is the **project's OWN from-scratch re-implementation** of the MIFlu paper, living at `scripts/miflu_model.py`, class `MIFlu`. It is **NOT** the author's released code. The author's official repository (which was not cloned until 2026-09-24) implements the model as `recovery/author_repo/models/GPT4TS_lora.py` and is a **separate lineage**.

## 2. Exact implementation identity

| Item | Value |
|---|---|
| Implementation file (B-track / Wave-1 / clean-v3 / A2-966) | `scripts/miflu_model.py` |
| Class | `MIFlu` (`scripts/miflu_model.py:476-583`) |
| Sub-modules in the same file | `TimeSeriesEmbedder` (`:128-210`), `ModalityAligner` (`:217-251`), `ForecastingLLM` (`:254-469`), `LoRALinear` (`:42-81`) |
| Adapter used by the 4-vs-4 comparison | `scripts/innovation/backbones/gpt2_miflu_adapter.py` — `GPT2MifluAdapter` (`name = "gpt2_miflu"`), which builds `from miflu_model import MIFlu` and returns the z-space `yh_rev` |
| Text encoder | `scripts/textual_embedder.py` — `TextualInputEmbedder` (full 12-layer GPT-2, frozen), prompt `PROMPT_TEMPLATE_7` |
| Own vs author | **PROJECT'S OWN.** `gpt2_miflu_adapter.py:1-19` docstring: "the ORIGINAL MIFlu, wrapped … it builds the existing `scripts/miflu_model.MIFlu`". The clone-time provenance audit (`hpc_results/official_repo_reproduction_20261006/REPOSITORY_PROVENANCE.md` §4, `EXPERIMENT_AND_REPOSITORY_LINEAGE.md` §1.B1) classifies it as the project's own: "`scripts/miflu_model.py` is a from-scratch re-implementation, not the author's `models/GPT4TS_lora.py`". |
| SHA-256 (current = frozen B-track snapshot) | `0e6bdb61213bfdcc72e6a5b2733fc891a613baeb3dc52b514997c1507bfc15ef` (`scripts/miflu_model.py`), byte-identical to `results/innovation/source_snapshot/scripts/miflu_model.py` |

## 3. Architecture (as coded)

```
Input x (B, N=7, T=104)  [already in StandardScaler z-space]
  └─ TimeSeriesEmbedder
        InstanceNorm(per sample, per variable)              miflu_model.py:177-183
        Patching Lp=24, S=2  -> floor((104-24)/2)+1 = 41 (+1 last patch) = 42 patches
        reshape to (B, N*42=294, 24)                        miflu_model.py:186-205
        shared Linear(24 -> 768)                            miflu_model.py:159,208  -> htime (B,294,768)
  └─ htext (B, tokens, 768) from frozen GPT-2 prompt encoder   (textual_embedder.py)
  └─ ForecastingLLM                                         miflu_model.py:254-417
        hfuse = [htext || htime]   (TEXT FIRST, causal attention)   miflu_model.py:376
        + GPT-2 wpe positional embedding (trainable)
        first K=6 GPT-2 transformer blocks; backbone frozen;
          LoRA r=4 alpha=4.0 on c_attn only; ln_1/ln_2 trainable
        final_ln (copied from GPT-2 block K-1)
        hforecast = hidden[:, -294:, :]  (time tokens)
        mean-pool over patches -> Linear(768 -> N*L=7*L)      miflu_model.py:413-415
  └─ Reverse InstanceNorm: y_hat_rev = y_hat_norm * stdevs + means   miflu_model.py:563
        -> THIS is the metric/loss space (StandardScaler z), returned by the adapter
```

`gat ed_inject` / `use_text_ln` / `use_lora` variants are selectable via constructor flags; the default configuration is the one used for `gpt2_miflu`.

## 4. Parameter counts (recorded values)

| Stage / scope | trainable params | total params |
|---|---|---|
| `gpt2_miflu` B-track (clean-v3 Wave-1), L=24 | **1,030,056** | UNRECOVERED (not recorded) |
| `gpt2_miflu` B-track, L=36 / 48 / 60 | 1,094,652 / 1,159,248 / 1,223,844 | UNRECOVERED |
| no-text control (`use_text_ln=False`) | 1,028,520 | UNRECOVERED |

Sources: `results/v3_clean/analysis/resource_storage.csv`; `results/v3_clean/analysis/analysis_dataset.csv` (`trainable_parameters` column); `scripts/configs.py:31` records `no_text_ln = 1,028,520` and `gated_inject = 17,537,449` as the "regression gate". LoRA contributes 73,728 trainable parameters (`final/final_candidate_freeze.json`; `recovery/stage6/results_report_zh.md` §2: "LoRA 73,728 参数").

**`total_parameters` for `gpt2_miflu` is genuinely not recorded in any historical artefact** — the A2/966 and B-track runs stored only `trainable_parameters`. Supporting (not authoritative) figure: `hpc_results/checkpoints/best_miflu_L24.pth` is 328,585,240 bytes, consistent with a full fp32 state dict of ≈82.06M parameters. Reported as **UNRECOVERED** rather than asserted.

## 5. Role in the comparison

- **Wave-1 Validation (clean-v3, 1025-row):** `gpt2_miflu` ranked **1st of 8** with `average_MSE_4L = 0.7708721…` and was frozen as the best LLM / overall champion (`results/v3_clean/analysis/model_ranking.csv`, `selection_outcome.json`).
- **Final one-time Test/Holdout:** it **lost** to `nlinear` (3.0505 vs 2.7389) — the documented "generalization reversal" (`results/v3_clean/final/final_test_metrics.json`).
- **A2 / author-966 (post-clone):** the same `scripts/miflu_model.py` was re-fit on the author's 966-row data; labelled "**miflu (corrected reconstruction — text path live, validation-selected)**" (`recovery/stage6/results_report_zh.md` §4.1), `average_MSE_4L = 2.041519`, statistically indistinguishable from `nlinear` (2.049550, paired t = −0.11).
- The **author's released code** was separately diagnosed as defective ("LoRA never applied, freeze is a no-op, 100% trainable, Test used for checkpoint selection" — `recovery/stage6/results_report_zh.md` §5) and must **not** be conflated with this implementation.

## 6. Reproducibility of this file

`scripts/miflu_model.py` is byte-identical to the frozen B-track snapshot (`results/innovation/source_snapshot/scripts/miflu_model.py`, both SHA-256 `0e6bdb61…`). However, `results/v2_legacy_archive`-era migration notes and `REPOSITORY_PROVENANCE.md` §4 warn that the repository has a single git commit, so the *exact* version used for the earliest (Aug-2026) runs cannot be recovered from git; the 2026-09-19 `source_snapshot/` is the authoritative as-run copy for Wave-1.