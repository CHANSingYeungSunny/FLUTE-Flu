# STATUS CORRECTION ADDENDUM

Generated 2026-10-06. **Append-only — no original file was modified.**

This addendum corrects five statements in the earlier deliverables. Each correction
names the file and value it supersedes, so a reader can still see the original.

---

## C-1 — `mse_mean` was mislabelled in the four-horizon table

**Supersedes**: the `mse_mean` column in `../REPORT_ZH.md` §D and `../REPORT_EN.md` §D,
and the `mse_mean_over_epochs` column in `../a1_results_aggregate.csv` /
`../a1_results_per_run.csv`.

**What the author's `mse_mean` actually is** (traced in `main_ILI_lora.py`'s `test()`
and the epoch loop): the mean over the `itr` repetitions of the **final-epoch Test
MSE**. With `itr=1` it is simply the **last epoch's** Test MSE. It is *not* a mean
across epochs. The A0 log corroborates this (`mse_mean = 0.9685, mse_std = 0.0000`
for a single iteration).

**What the earlier table printed** was a *different quantity* — the mean of the 20
per-epoch Test MSE values — under the label `mse_mean`.

| L | value printed as `mse_mean` (mean over 20 epochs) | **author's actual `mse_mean`** (final-epoch, itr=1) | best-epoch |
|---:|---:|---:|---:|
| 24 | 0.6044 | **0.5793** | 0.5344 @ ep8 |
| 36 | 0.6028 | **0.5920** | 0.5387 @ ep10 |
| 48 | 0.6571 | **0.6088** | 0.6069 @ ep16 |
| 60 | 0.6545 | **0.6361** | 0.5933 @ ep5 |

The values 0.5793 / 0.5920 / 0.6088 / 0.6361 are exactly the last rows of the four
per-epoch CSVs, confirming the semantics.

**Corrected statement**: *the author's `mse_mean` for the four runs is 0.5793 / 0.5920 /
0.6088 / 0.6361 (final-epoch Test MSE, one repetition each).* The mean-over-epochs
values may still be quoted, but only under the distinct name
`mean_of_per_epoch_test_mse`, never as `mse_mean`.

---

## C-2 — the A2 text-influence magnitude was a probe defect

**Supersedes**: `max|Δpred| = 59.6875` and `|grad_text| = 7.13e+08` in
`../TEXT_PATH_RESOLUTION.md` §6, `../REPORT_ZH.md` §E.2 and `../REPORT_EN.md` §E.2.

**Cause**: the v1 A2 probe fed the model **raw** CSV values (`OT ≈ 176 569`) where the
model contract requires input **already in StandardScaler space**. The forward pass ends
in `y_hat_rev = y_hat_norm * stdevs + means`, so the input scale propagated into the
output and inflated every measured difference and gradient.

**Corrected** (`probe_a2_text_path_v2.py`, train-fit scaler applied first):

| Quantity | superseded (v1) | **corrected (v2)** |
|---|---:|---:|
| `max\|Δpred\|`, different prompt, same length | 59.6875 | **6.518e-04** |
| `max\|Δpred\|`, row-permuted text | 6308.3 | **6.525e-02** |
| `\|grad_text\|` | 7.13e+08 | **0.025178** |
| prediction range | scale-driven by raw input | **[-0.828, +1.717]** (z-space) |

**The conclusion does not change**: A2's text path **is** active (`text_active`) under
both probes. Only the magnitude was wrong.

---

## C-3 — `decay_fac=0.75` is not the decay actually applied

**Supersedes**: `DEVIATION_LEDGER.md` D-13 and the `lr_schedule` column in
`../a1_results_per_run.csv`, which say the schedule is
`"type1 exponential decay, decay_fac=0.75 (released default, MEASURED active)"`.

**Corrected**: with `cos=0` (the default), `adjust_learning_rate` **is** called — so a
schedule is real and the D-13 headline stands. But on the `lradj='type1'` path the
implementation uses a **hard-coded 0.9 factor applied from epoch 4**
(`utils/tools.py:26-27`); **`decay_fac=0.75` is not used on that path**.

Arithmetic check confirming which constant was used:

```
observed LR at the logged epoch = 0.00019371024450000004
5e-4 * 0.9^9  = 1.9371024450e-4   ✅ exact match
5e-4 * 0.75^9 = 3.7523e-5         ✗ three orders away
```

**Corrected statement**: *the released code applies a hard-coded 0.9 exponential decay
from epoch 4; `--decay_fac 0.75` is inert on the default path.*

---

## C-4 — `feat_id=[0]` is broader than "the Test split is broken"

**Supersedes** (strengthens): the repeated phrase "Test covers feature 0 only", e.g.
`../STATUS_AFTER_CONTINUATION.md` §4 and `IMPLEMENTATION_IDENTITY`-adjacent notes.

**Independently re-verified in the loader** this session:

```python
data_loader.py:305   seq_x = self.data_x[s_begin:s_end, feat_id:feat_id+1]   # ONE channel
data_loader.py:312   if self.set_type == 2:  length = ...                    # no * enc_in
                     else:                   length = ... * self.enc_in
data_loader.py:299   feat_id = index // self.tot_len
```

Two coupled facts:

1. **`__getitem__` slices a single channel** (`feat_id:feat_id+1`), so *every* sample in
   *every* split is a **univariate `(T,1)` window**. The released model never forms a
   seven-variable window at all. The A0 log confirms the tensor shape: `test shape:
   (160, 24, 1)`.
2. Because `__len__` omits the `× enc_in` factor for `set_type == 2`, `index // tot_len`
   is identically 0 for the Test split, so **only channel 0 (`% WEIGHTED ILI`) is ever
   evaluated**.

**Corrected statement**: *the released code trains univariate per-channel windows that
share one set of weights, and evaluates only channel 0 — `% WEIGHTED ILI`. This is not a
"multivariate model with a Test bug"; it is a univariate formulation end to end.*

**Consequence**: the paper describes a multivariate multimodal model. The released code
does not implement one. This is a **paper-vs-code contract difference**, recorded in
`PAPER_CODE_CONTRACT_DIFFERENCES.csv`, and it is the single largest obstacle to a
defensible Table V reconstruction.

---

## C-5 — the four completed runs are A0-R, not A1-P

**Supersedes**: any wording that could place the four horizon runs inside A1-P, e.g. the
`track` value `A1_reconstructed_paper_config` in `../a1_results_per_run.csv` and
`../a1_results_aggregate.csv`.

**Corrected classification**:
`Released-code feature-0 replay, single run per horizon` — i.e. **A0-R**.

They must not be described as: successful Table V reproduction / A1-P completed / paper
reproduction completed / clean Test results / seven-variable benchmark results /
10-repetition results.

---

## Summary of corrections

| # | Superseded | Corrected |
|---|---|---|
| C-1 | `mse_mean` = mean over 20 epochs (0.6044/0.6028/0.6571/0.6545) | author's `mse_mean` = final-epoch, itr-mean = **0.5793/0.5920/0.6088/0.6361** |
| C-2 | A2 `max\|Δ\|`=59.7, `grad`=7.13e8 | **6.518e-04 / 6.525e-02, grad 0.0252** (verdict unchanged: `text_active`) |
| C-3 | lr decay by `decay_fac=0.75` | **hard-coded 0.9 from epoch 4**; `decay_fac` inert |
| C-4 | "Test covers feature 0 only" | **all splits are univariate; only channel 0 evaluated** |
| C-5 | four runs tagged `A1_reconstructed_paper_config` | **A0-R released-code replay** |

**None of the original files were edited.** Each remains exactly as written; this
addendum is the correction channel.
---

## C-6 — "the 10 repetitions would be deterministic duplicates" is REFUTED

A claim raised during this audit — that because `main_ILI_lora.py` fixes the seed once
(lines 27-30, `fix_seed = 2021`) the `--itr` repetitions would be identical — was
**tested and refuted**.

**What is verified**: the seed is set **once**, at module level, outside the
`for ii in range(args.itr)` loop, and there is no `set_seed` helper and no reseeding
inside it.

**What was measured** (local CPU, the author's own `GPT4TS` constructor, replicating
lines 27-30 exactly and consuming RNG between constructions to emulate training):

```
itr0 == itr1 : False
itr1 == itr2 : False
```

The global RNG advances across iterations, so each repetition receives a **different**
random initialisation. Repetitions are therefore **not** duplicates.

**The real limitation is different, and still matters**: the repetitions are **not
addressable by seed**. There is no declared seed list, so an individual repetition
cannot be re-run in isolation; the set is reproducible only by replaying the whole job
deterministically. The paper says "the mean of 10 repetitions" but discloses no seeds,
and the released harness does not provide them either.

**Consequence for budget**: `--itr 10` would produce ten genuinely different runs, so
the ~11 GPU-h estimate is not wasted effort — but for a *seed-controlled* replication
the project's own declared seed list (42-51) remains the better instrument.

---

## C-7 — A0-R runs saved no predictions, so independent re-scoring is impossible

**Verified**: in `utils/tools.py` `test()`, the two `np.save` calls that would persist
predictions and targets are **commented out** (lines 300 and 302). `test()` returns only
the scalar `mse, mae`. Nothing in the four runs wrote a `.npy`.

**Consequence**: the four A0-R horizon scores **cannot be independently re-scored** —
only re-run. This is a hard limitation of the released code, not of this project's
harness, and it is one reason the runs are A0-R rather than A1-P.

It also explains the recorded `author_exit_code=1`: the training loop completes and
writes its metrics CSV and checkpoint, then `test_vis` crashes on
`setting + 'results.csv'` where `setting` carries a `torch.device`. The metrics are
therefore valid; the non-zero exit is a post-hoc crash.

---

## C-8 — "100 % of parameters are trainable" is unverified for the four runs

The measured 82,705,944 / 82,705,944 = 100 % trainable figure was obtained with the
released **default `PEFT=0`**. The four runs set **`PEFT=1`**, which routes through
`get_peft_model` and *does* freeze the base model. **No artefact records the PEFT=1
trainable count.**

**Corrected statement**: the released `freeze` flag is a no-op (it only ever sets
`requires_grad = True`), but the effective trainable set for the four runs is
**UNRECOVERED** and must not be quoted as "all 82.7 M parameters".
