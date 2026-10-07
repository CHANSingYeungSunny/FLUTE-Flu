# R1-B IMPLEMENTATION CHANGE LEDGER

Generated 2026-10-06. Records **every** deviation of the R1-B implementation from the
author's released code, with its evidence and classification.

**Implementation base**: the author's released tree at commit
`6ed210150b8819313947cf607eb1821c87b1bee3`, **imported, never modified**. The R1-B code
lives in `r1b/r1b_model.py` and `r1b/r1b_train.py` and reaches the author's code by
subclassing `models.GPT4TS_lora.GPT4TS`.

**Author tree integrity**: `git status` on `recovery/author_repo` shows only regenerated
`.pyc` files and an output directory; `git diff --stat` reports 9 files, **0 insertions,
0 deletions**. The author's sources are byte-identical to the release.

---

## 1. The seven corrections

| # | Correction | Class | Paper / code evidence | Effect measured |
|---|---|---|---|---|
| **B-1** | **multivariate windows over all seven channels** | required by the paper | paper L238 lists seven variables; Table X enumerates them. The released `Dataset_Custom.__getitem__` slices `feat_id:feat_id+1`, and its `__len__` omits `× enc_in` for Test so `feat_id` is identically 0 | output shape becomes `(B, L, 7)`; verified on synthetic data |
| **B-2** | **functional text pathway**: text prefixed, then the patch positions that follow it are read | repairs a released-code defect | the paper's method *is* the text contribution. The released order concatenates text **after** the patches and then keeps `outputs[:, :patch_num]`, which under causal attention cannot see the text | `max\|Δpred\|` 0.000e+00 → **5.88e-02**; `\|grad_text\|` 0.0 → **1.04e-03**; verdict `text_inert` → **`text_active`** |
| **B-3** | **`PEFT=1`** so the author's LoRA branch executes | required by the paper | paper L300 (r=4) and L214 (multi-head attention). The released `--PEFT` defaults to **0**, so `get_peft_model` never runs | not testable locally (no `peft`); must be verified on HPC. **`--target_modules` must NOT be passed**: the author's argparse declares it `type=str` with a LIST default, so an override arrives as a bare string and peft raises `Target modules c_attn not found` (observed on job 606361) |
| **B-4** | **effective freeze** of the pretrained backbone except LoRA, `ln*` and `wpe` | repairs a released-code defect | paper L214 says only PE and layer-normalization are tuned. The released loop only ever sets `requires_grad = True` and never `False` | trainable **82,705,944 / 82,705,944 = 100 %** → **1,599,768 / 82,705,944 = 1.93 %** (49 backbone tensors frozen, 27 kept) |
| **B-5** | **validation-only checkpoint selection** | needed for clean evaluation | the released code computes Test MSE every epoch and keeps the best (`min_mse` L225, saved L264); early stopping is instantiated but its call is commented out (L235-236). The paper states no rule | Test is never read during the fit in `r1b_train.py` |
| **B-6** | **persist predictions and targets** | needed for clean evaluation | the released `utils/tools.py` has its two `np.save` calls **commented out** (L300, L302), so released-code scores cannot be independently re-scored | `pred_<tag>.npz` written with `pred`, `target`, `target_start_row`, `L`, `seed`, `var_cols`, `profile`, `containment`, `space`, `checkpoint_selection`, `track` |
| **B-7** | **declared training configuration** | **`PAPER_EXPLICIT`** — see §2 | **Table IV** (national block) gives epochs **20**, batch **16**, lr **0.0005**, T **104** | epochs 20 / lr 5e-4 / batch 16 |

---

## 2. ⚠️ B-7 corrects an earlier conclusion

Earlier rounds classified epochs and learning rate as **`UNRECOVERED`** and called the
project's 20 / 5e-4 a **`RECONSTRUCTED_ASSUMPTION`** with no source. **That was wrong.**

Reading **PDF page 7 as an image** yields Table IV's settings block:

| Setting | National ILI |
|---|---|
| L | 24, 36, 48, 60 |
| **Epochs** | **20** |
| **Batch size** | **16** |
| **Learning rate** | **0.0005** |
| T | 104 |

**Neither Markdown contains these values.** The new
`reference_papers/…Scheme.md` explicitly states the table was not extractable and lists
only the comparison-model names; the older `MIFlu_paper.md` omits Table IV entirely. So
this is a **single-source** finding, labelled `PDF_VISUALLY_VERIFIED`.

**Corrected classification**: epochs, batch size, learning rate and T are
**`PAPER_EXPLICIT` via Table IV**. What remains genuinely `UNRECOVERED` is: **optimizer,
scheduler, seed list, checkpoint-selection rule, pooling axes**.

---

## 3. What R1-B does NOT change

| Kept exactly as released |
|---|
| the patch embedding (`nn.Linear(patch_size, d_model)`), replication padding, patch/stride (24/2) |
| the GPT-2 backbone truncation to `gpt_layers = 6` |
| the output head `nn.Linear(d_model * patch_num, pred_len)` |
| the instance normalization inside `forward` and its reversal at the end |
| the author's LoRA branch code (only the `PEFT` flag differs) |
| the author's `models/GPT4TS_lora.py` on disk — **unmodified** |

---

## 4. Deviation classification summary

| Class | Count | Items |
|---|---:|---|
| required by the paper | 2 | B-1, B-3 |
| repairs a released-code defect | 2 | B-2, B-4 |
| needed for clean evaluation | 2 | B-5, B-6 |
| declared reconstruction / paper-explicit config | 1 | B-7 |
| technical compatibility | 0 | — |

**Every one is a DECLARED deviation.** None may be described as "the released behaviour",
and none may be described as "the paper's own run".

---

## 5. Provenance of the correction set

| Correction | Would need author confirmation? |
|---|---|
| B-1 | no — the paper's task scope is explicit |
| **B-2** | **yes** — the paper's own token order is self-contradictory (L205 vs L219), so the repair is a *declared algorithm change* |
| B-3 | no — LoRA is stated; only the flag was off |
| B-4 | partly — the paper describes the policy in prose |
| B-5 | yes — the paper states no selection rule |
| B-6 | no — persisting predictions is an engineering requirement |
| B-7 | no — Table IV states the values |