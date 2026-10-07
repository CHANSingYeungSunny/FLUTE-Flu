# Implementation audit — Stage 2 (author code path)

Date: 2026-09-24. Scope: read-only inspection of the pinned author repo
(`recovery/author_repo/` @ `6ed2101`) entry point → loader → model → evaluator, plus one
deterministic CPU smoke check. Method: static code reading + minimal self-contained causal
attention test. No GPU, no training, no result overwrite.

Audited files:
`main_ILI_lora.py`, `models/GPT4TS_lora.py`, `data_provider/data_loader.py`,
`data_provider/data_factory.py`, `utils/tools.py`, `utils/metrics.py`, `text_emb.ipynb`.

---

## Headline

The released MIFlu entry point, run with its **own defaults**, does **not** execute the
pipeline the paper describes. Four defaults combine to make the run materially different from
the paper's framing:

| Default | Value | Effect |
| --- | --- | --- |
| `--multimodal` | 0 | text branch never runs (dead) |
| `--PEFT` | 0 | no LoRA — full fine-tune, despite the "lora" filename |
| `--freeze` + `--pretrain` | 1 / 1 | "freeze" is a no-op (see §5) |
| `--train_epochs` | 1 | one epoch by default |

Separately, the Test split enumerates **only feature 0 (weighted ILI)**, and the Test set is
evaluated every epoch and used to pick the "best" model — so the Test set is not held out.

---

## 1. Text path is dead AND structurally inert (two independent reasons)

**(a) Dead by default.** `main_ILI_lora.py:36` sets `--multimodal default=0`. The text
branch in `GPT4TS_lora.py:130` is guarded by `if self.multimodal == 1:` and never runs.

**(b) Structurally inert even if enabled.** In `GPT4TS_lora.py` `forward`:

- line 139: `outputs = torch.cat((outputs, text_emb_tensor), axis = 1)` — text appended
  **after** the time-series patches (positions `patch_num .. patch_num+K-1`).
- line 143: `outputs = self.llmmodel(inputs_embeds=outputs).last_hidden_state` — GPT-2
  **causal** attention.
- line 145: `outputs = outputs[:, :self.patch_num, :]` — only the **prefix** (time-series
  positions `0 .. patch_num-1`) is retained.

Under causal attention, position `i` attends only to positions `≤ i`. Every text token sits at
a position strictly greater than every retained patch position, so the retained prefix cannot
depend on the text. **Deterministic smoke check confirms this:** `recovery/smoke_text_visibility.py`
reproduces the exact mechanism (tiny single-head causal attention, fixed weights, identical
patches, two wildly different text embeddings) and the retained prefix is **bit-identical**
(max diff `0.0e+00`).

**(c) The `itr` parameter is unused.** `forward(self, x, itr)` (`GPT4TS_lora.py:106`) never
reads `itr`; `main_ILI_lora.py:189` calls `model(batch_x, ii)` where `ii` is the epoch index.
No text is ever passed through this route.

**(d) Prompt is a placeholder.** `text_emb.ipynb` cell-5: `template1 = 'Text from users'`.
The text embeddings are generated from the literal string `"Text from users"`, not influenza
narrative. Further, the cache filenames mismatch: the notebook saves
`gpt2text_emb_label_{pre_len}.txt` (cell-9) while the model loads `text_emb_label_0507_{pred_len}.txt`
(gpt2 branch) or `{textmodel}text_emb_label_0527_{pred_len}.txt` (else branch) — no matching
file exists, so `multimodal=1` would raise `FileNotFoundError`.

**Conclusion:** the paper's "multimodal" text contribution is not exercised by the released
code. Any reported MIFlu result is a time-series-only GPT-2 backbone (a GPT4TS-style model),
not a text-conditioned model.

---

## 2. Test split evaluates only feature 0 (weighted ILI)

`data_provider/data_loader.py`, class `Dataset_Custom`:

- `__read_data__` reorders columns to `['date', '1','2','3','4','5','6','OT']` and, for
  `features='M'`, sets `df_data = df_raw[columns[1:]]` = **7 columns** for every split
  (train / val / test). The `elif self.set_type == 2:` branch that loads only `df_raw[[target]]`
  is **dead** — the `features=='M'` branch matches first.
- `__len__`: for `set_type in (0, 1)` (train/val) it returns `tot_len * enc_in` (×7); for
  `set_type == 2` (test) it returns `tot_len` **without** the ×`enc_in` factor.
- `__getitem__`: `feat_id = index // tot_len`. On test, `index ∈ [0, tot_len)`, so
  `feat_id ≡ 0` — only feature 0 is ever emitted.

Feature 0 after reordering is column `"1"` = `% WEIGHTED ILI`. **The Test metric therefore
covers only weighted ILI, not the seven variables.** This is directly relevant to the paper's
reported MSE/MAE: a seven-variable average cannot be produced by this code path as written.

Consequence for reproduction: reproducing the paper's *numbers* requires pinning the exact
feature/aggregation the paper used; the released code's `test()` output is a single-variable
(weighted-ILI) metric.

---

## 3. Test is evaluated every epoch and used for model selection

`main_ILI_lora.py`:

- line 211: `mse_temp, mae_temp = test(model, test_data, test_loader, args, device, ii)` —
  full Test-set evaluation **inside the epoch loop**; results appended to `results` (lines
  219–224) and `mses_temp`/`maes_temp` (217–218).
- lines 225–227: `if mse_temp < min_mse: … best_epoch_result = {'model_state': model.state_dict()}` —
  the "best" epoch is chosen by **Test MSE**, not validation loss.
- line 227: `model.state_dict()` returns a **live reference** (not `deepcopy`), and it is
  never consumed — the restore at lines 242–243 is commented out, so the final evaluation
  (line 245) uses the **last-epoch** model.
- lines 235–238: early stopping is commented out.

Net effect: the Test set is fully observed during training, drives epoch selection, and yet the
final reported number comes from the last epoch — not a validation-selected checkpoint. This
invalidates the Test set's "unseen" status for any prospective reproduction that reuses this
loop verbatim.

---

## 4. Split geometry and loader mechanics (no leakage, but must be pinned)

`Dataset_Custom.__read_data__` (`data_loader.py`):

- `num_train = int(966 * 0.7) = 676`; `num_test = int(966 * 0.2) = 193`; `num_vali = 966-676-193 = 97`.
- `border1s = [0, 676-104, 966-193-104] = [0, 572, 669]`;
  `border2s = [676, 773, 966]` → train rows `0..675`, val target block `676..772`,
  test target block `773..965`.
- StandardScaler is fit on **train rows only** (`df_data[0:676]`), per-column — correct, no
  leakage from the scaler.
- `data_factory.py`: `drop_last_test=True` default, `shuffle_flag=True` for val, `False` for
  test. The last incomplete batch is dropped (a ~1–15-sample boundary effect on test).
- `shuffle` for train/val uses `seed=0` (`data_factory`), so ordering is deterministic.

The split is a fixed 70/10/20 contiguous cut, identical on every run, with the test tail
(rows 773–965) exposed as described in §3.

---

## 5. "Freeze" is a no-op; PEFT defaults off → full fine-tune

`GPT4TS_lora.py:58-61` (gpt2 branch):

```python
if configs.freeze and configs.pretrain:
    for i, (name, param) in enumerate(self.llmmodel.named_parameters()):
        if 'ln' in name or 'wpe' in name:
            param.requires_grad = True
```

It sets LayerNorm / position-embedding params to trainable but **never sets any other param to
`False`**. `GPT2Model.from_pretrained` leaves parameters `requires_grad=True`, so the entire
6-layer GPT-2 backbone remains trainable. (Contrast the llama2 branch at lines 68–73, which
correctly sets `else: requires_grad = False`.) With `--freeze 1 --pretrain 1` defaults, the
intended "freeze the pretrained backbone, train adapters" behavior does **not** occur.

`--PEFT default=0` (`main_ILI_lora.py:48`): despite the filename and LoRA imports, no LoRA
adapters are applied. The run is a **full fine-tune** of 6 GPT-2 layers + `in_layer` +
`out_layer`. This has large implications for compute cost and for any equivalence comparison
with a "LoRA" variant the paper may describe.

---

## 6. Scaling path: per-variable StandardScaler + per-window instance norm

Two scaling operations compose:

- Loader: `StandardScaler` (per-column, fit on train) transforms the input before windowing.
- Model (`GPT4TS_lora.py:109-112` and `152-153`): each input window is additionally
  instance-normalized (`x -= mean(x); x /= std(x)`) and de-normalized at the output.

Both are legitimate (the instance norm uses only the input window), but the effective
optimization target is the instance-normalized series, and the reported MSE is returned in the
instance-normalized space. Reproduction must preserve both layers exactly to match the paper's
reported scale.

---

## 7. Benign / vestigial artifacts (documented, not blocking)

- `--enc_in 862`, `--c_out 862` (`main_ILI_lora.py:70-71`) are stale defaults; the model never
  reads them (`in_layer` uses `patch_size=24`, `out_layer` uses `d_model * patch_num`).
- `--embed timeF` with **synthetic** dates (`2002-01-01 … 2020-06-30`) produces time features,
  but `GPT4TS.forward` ignores `x_mark`, so time features are computed and discarded.
- `--itr 1` default: single seed per invocation; multi-seed averages require external loops.
- `--train_epochs 1` default: one epoch. The paper's epoch count is not recorded in the repo,
  so reproduction must treat epoch count as an external parameter to be reconstructed.

---

## Consolidated risk register (verified)

| # | Risk | Verdict | Evidence |
| --- | --- | --- | --- |
| 1 | Text has no route to output | CONFIRMED (dead by default + inert by construction) | `GPT4TS_lora.py:130,139,143,145`; smoke test `0.0e+00` |
| 2 | Test covers feature 0 only (weighted ILI) | CONFIRMED | `data_loader.py __len__/__getitem__` |
| 3 | Test-in-loop + best-by-Test-MSE + no clean restore | CONFIRMED | `main_ILI_lora.py:211,225-227,242-243` |
| 4 | drop_last / val shuffle / fixed 70/10/20 cut | CONFIRMED (benign, pin required) | `data_factory.py`, `data_loader.py` |
| 5 | freeze no-op + PEFT off → full fine-tune | CONFIRMED | `GPT4TS_lora.py:58-61`, `main_ILI_lora.py:48` |
| 6 | double scaling (per-variable + instance norm) | CONFIRMED (benign, pin required) | `data_loader.py`, `GPT4TS_lora.py:109-112` |
| 7 | synthetic dates → unused time features | CONFIRMED (benign) | `main_ILI_lora.py:44`, `GPT4TS_lora.py:106` |
| 8 | enc_in/c_out vestigial | CONFIRMED (benign) | `main_ILI_lora.py:70-71` |
| 9 | prompt placeholder + cache filename mismatch | CONFIRMED (dead path) | `text_emb.ipynb` cell-5/cell-9 |

## Implication for reproduction variants

- **A0 (released-code replay)** — must be run *as-is* (its own defaults or the paper's stated
  overrides), which yields a single-variable weighted-ILI Test metric with the Test set
  in-loop. This is a faithful *replay*, not a scientific reproduction.
- **A1 (paper reconstruction)** — requires external specification of: feature aggregation
  (7-variable vs weighted-ILI), epoch count, seed count, and whether text/multimodal was
  actually enabled in the paper's runs (the released code cannot have used it).
- **A2 (corrected variant)** — requires: a proper held-out Test split (never seen during
  training/selection), a validation-selected checkpoint, and (if "multimodal" is claimed) a
  text path that actually reaches the prediction head. These are the minimal corrections.

These three must not be conflated (see `STATE.md` three-track identities).

---

## 8. Project implementation (FLUTE-Flu repo) is a corrected reconstruction, not a replay

The project's own MIFlu (`scripts/miflu_model.py`, `scripts/textual_embedder.py`,
`scripts/train_miflu.py`, `scripts/configs.py`) fixes every defect found in the released
author code. **Correction (2026-09-24):** contrary to an earlier claim, the project *has* run
the 966-row author data with its corrected model — `hpc_results/paper_exact/training_miflu_log_514859.txt`
(TSLib official 966 rows, L24 MSE_All 2.238) and a `control966` head-truncated snapshot (L24
1.379) — and the 1025-row paper-window run (8-17, MSE_All 2.593/3.341/3.237/3.559). What the
project has **not** done is A0: replay the released author code verbatim
(`main_ILI_lora.py`). See `hpc_results/paper_exact/REPLICATION_VERDICT.md`.

| Aspect | Author released code | Project implementation | Verdict |
| --- | --- | --- | --- |
| Text path | `[htime \|\| htext]` + prefix retained → text inert | `[htext \|\| htime]` (text first) → time attends to text | corrected |
| Text content | placeholder `"Text from users"` | real CDC ILINet prompt w/ per-variable min/max (`textual_embedder.py:35-68`) | corrected |
| Output | single variable (M=1) | joint 7-channel `(batch, 7, L)` via `Linear(D, 7L)` | corrected |
| Backbone training | freeze no-op + PEFT=0 → full fine-tune | freeze all + LoRA(r=4) on MHA only | corrected |
| Model selection | Test MSE every epoch (in-loop) | best **validation** MSE per rep; Test evaluated once, after training | corrected |
| Reps / seeds | `--itr 1` (single seed) | 10 repetitions, best-val rep kept (`configs.py` `num_repetitions=10`) | corrected |
| Epochs / LR | 1 epoch default / lr 1e-4 | 20 epochs / lr 5e-4 | different |
| Data window | 966 rows (author vintage) | 1025 rows, **refuses** 966 (`assert_full_window`) | different |
| Split | 676/97/193 | 717/102/206 (70/10/20 on 1025) | different |
| Scaling | per-var StandardScaler + per-window RevIN | same two-layer scheme, canonical metric space = StandardScaler space | aligned |

Consequence: the project's existing v3_clean MIFlu results are **track B + a corrected (A1/A2-style)
implementation**. They are *not* a reproduction of the paper's Table V under the released code
(A0). The project has already partially closed track A with the corrected model (966-row job
514859 and the 1025-row paper-protocol run), but the two genuinely-remaining provenance legs are:
**(i) A0** — replay the released author code verbatim (never run), and **(ii) A2** — a coherent
controlled 966-row comparison of corrected MIFlu vs no-text vs NLinear under one protocol
(never run as a matrix). These two, not a blanket "reproduce the paper", are the central gap the
rerun scope must close.
