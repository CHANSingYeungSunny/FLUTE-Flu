# MIFlu — Paper Evaluation Contract Audit

**Scope.** Audit of the evaluation contract of the MIFlu paper (IEEE JBHI 2025, DOI
10.1109/JBHI.2025.3561214) as disclosed in the paper versus as implemented in the authors'
released code at commit `6ed2101`. Fifteen questions (Q1–Q15) plus one additional finding on
Section V-C. This file is new and read-only with respect to every pre-existing artifact.

**Primary sources read directly**
- `MIFlu_paper.md` (the paper, line-numbered) — cited as `[paper-md L…]`.
- `audit_20260930/paper_text.txt` (raw PDF text extraction) — cited as `[paper-txt L…]`.
- `recovery/author_repo/` @ `6ed2101`: `main_ILI_lora.py`, `models/GPT4TS_lora.py`,
  `data_provider/data_loader.py`, `data_provider/data_factory.py`, `utils/tools.py`,
  `utils/metrics.py` — cited as `[code file L…]`.
- Runtime evidence: `hpc_results/stage6/a0_gpu/a0_587091.out` (A0 released-code replay);
  A1 author-harness runs `hpc_results/official_repo_reproduction_20261006/hpc_a1*/…`.

**Prior work used only as leads, re-derived here**
- `recovery/a1/a1_evidence_table_zh.md`, `recovery/implementation_audit.md`,
  `hpc_results/official_repo_reproduction_20261006/HYPERPARAMETER_PROVENANCE.md`,
  `…/DEVIATION_LEDGER.md`. Every load-bearing claim below is re-derived from the primary
  source and the primary line is quoted; the prior-work path is named where a measurement is
  *reused* rather than re-derived.

**Classification legend (exactly one per question).**
`PAPER_EXPLICIT` · `CODE_EXPLICIT` · `README_EXPLICIT` · `CONFIG_EXPLICIT` ·
`LOG_INFERRED` · `USER_CONFIRMED` · `RECONSTRUCTED_ASSUMPTION` · `CONFLICTING_EVIDENCE` ·
`UNRECOVERED`.

There is **no README, no LICENSE, no requirements file and no config file in the authors'
released tree** (`recovery/author_repo/` contains only `main_ILI_lora.py`, `models/`,
`data_provider/`, `utils/`, `dataset/`, `text_emb.ipynb`, `.vscode/`). `README_EXPLICIT`
therefore cannot be a source for the *author* contract; it is used only once, for the
project's own README (Q8 corroboration only).

---

## Q1. Does Table V forecast one influenza target or all seven variables?

**Finding.** The paper *defines* the national task over **seven variables** (the national ILI
plus six sub-indicator variables). It never states which variable(s) the single Table V
scalar is computed over, and Eq. (1) carries only the lead-time dimension, so the *evaluated*
variable set for Table V is not pinned by the paper.

**Evidence.**
- `[paper-md L78]` (Section III-A, National ILI Forecasting): *"Predicts not only the ILI for
  the entire country, but also several sub-indicator variables (national ILI, ILI by age
  group, ILI adjusted for population size or number of reporting providers; see Table II)."*
- `[paper-txt L260-262]` verbatim: *"National ILI forecasting predicts not only the ILI for
  the entire country (i.e., national ILI), but also several variables that represent
  sub-indicators of national ILI."*
- `[paper-md L238]` (datasets): *"Seven variables for national ILIs occurring in the US
  between 2002 and 2021…"*
- `[paper-md L464-510]` (Table X prompt) enumerates all seven features `(1)…(7)`.
- Counter-signal inside the paper: `[paper-txt L266-270]` Eq. (1) writes the output as
  `Ŷ = Ŷ^{t+L} … Ŷ^{t+1}` — a vector over lead time only, with no variable index; and
  `[paper-md L502]` labels feature (7) *"'OT' feature for long-term forecasting task"* (a
  single named forecasting target). The paper therefore does not settle whether the Table V
  number is a seven-variable aggregate or a single-target (OT / weighted-ILI) score.
- The released code evaluates a single feature (see Q3, Q10).

**Classification: PAPER_EXPLICIT** — the paper explicitly defines the national task over
seven variables (Section III-A, Table II, Table X). *Residual gap:* the aggregation set of the
Table V scalar itself is UNRECOVERED (see Q12).

---

## Q2. What are the roles of the seven variables?

**Finding.** Seven national variables, all ILI-related sub-indicators of the US CDC ILINet
national series. Roles are given by the Table X prompt and by the descriptive-statistics
narrative (`Fig. 2(a)`).

**Evidence.**
- `[paper-md L464-505]` (Table X, verbatim excerpts):
  - (1) *"Percentage of patient visits in the healthcare system attributed to influenza,
    adjusted for the proportion of each reporting center's total patient visits."*
  - (2) *"Percentage of unweighted influenza, not adjusted for the proportion of each
    reporting total patient visits."*
  - (3) *"Total number of influenza patients between age 0 and 4."*
  - (4) *"Total number of influenza patients between age 5 and 24."*
  - (5) *"Total number of influenza patients."*
  - (6) *"A number of influenza providers." … "The overall trend is upward."*
  - (7) *"'OT' feature for long-term forecasting task. … This variable peaks 2 times for 1
    year. The overall trend is upward."*
- `[paper-md L251]` (Fig. 2(a) description): Variables 1–2 are *"Percentage of ILI
  patient"* (0–8%); 3–5 *"ILI patient count"*; 6 *"# of healthcare providers"*; 7 *"ILI
  patient count"* at ~1.8e6 scale.
- Column names in the released data confirm the roles:
  `recovery/author_repo/dataset/illness/national_illness_orig.csv` header =
  `date,% WEIGHTED ILI,%UNWEIGHTED ILI,AGE 0-4,AGE 5-24,ILITOTAL,NUM. OF PROVIDERS,OT`;
  the code's copy `national_illness.csv` header = `date,1,2,3,4,5,6,OT` (numeric names,
  semantic labels dropped). The released loader reorders to `['date','1'…'6','OT']`
  (`[code data_loader.py L252-255]`), so **feature 0 = column "1" = % WEIGHTED ILI**.

**Classification: PAPER_EXPLICIT.**

---

## Q3. Is `feat_id=[0]` intentional / paper-required / a single-target design / a shortcut / an evaluation defect / unrecoverable?

**Finding.** It is an **evaluation defect of the released code**, not required by the paper
and not documented anywhere as a design choice. On the Test split the loader emits only
feature 0 (`% WEIGHTED ILI`) because (a) the standard "target-only at test" branch is dead
under the default `features='M'`, and (b) `__len__` for the Test split omits the `×enc_in`
factor, so `feat_id = index // tot_len` is identically 0.

**Evidence (re-derived from code, not taken on trust).**
- `[code data_loader.py L268-273]` (`Dataset_Custom.__read_data__`):
  ```python
  if self.features == 'M' or self.features == 'MS':
      cols_data = df_raw.columns[1:]
      df_data = df_raw[cols_data]
  elif self.set_type == 2:
      df_data = df_raw[[self.target]]
  ```
  With the default `--features M` (`[code main_ILI_lora.py L41]`), the first branch always
  matches, so the `elif self.set_type == 2` (target-only at test) branch is **dead code**.
- `[code data_loader.py L312-317]` (`__len__`):
  ```python
  if self.set_type == 2:
      length = (len(self.data_x) - self.seq_len - self.pred_len + 1)
  else:
      length = (len(self.data_x) - self.seq_len - self.pred_len + 1) * self.enc_in
  ```
  Test length is **not** multiplied by `enc_in`. Train/val are.
- `[code data_loader.py L299-306]` (`__getitem__`): `feat_id = index // self.tot_len`; for
  Test, `index ∈ [0, tot_len)` ⇒ `feat_id ≡ 0`.
- Consequence in a real run: `[A0 log a0_587091.out]` prints
  `test shape: (10, 16, 24, 1)` then `test shape: (160, 24, 1)` — a **single-channel**
  (M = 1) test tensor, consistent with feature 0 only.
- Train/val nevertheless cycle `feat_id = 0…6`; because `seq_x` is sliced as
  `data_x[s_begin:s_end, feat_id:feat_id+1]` (`[code data_loader.py L305-306]`), every sample
  is a **univariate** `(T,1)` window — the model never receives the seven variables jointly
  in either split, so neither input nor output is multivariate in the released code.

**Classification: CONFLICTING_EVIDENCE** — the paper's contract is a seven-variable national
task (Q1); the released code scores one feature and never forms a multivariate window. The
`elif self.set_type == 2` branch and the missing `×enc_in` are code-level facts; they conflict
with the paper, and no documentary evidence (paper, comment, commit message) declares
single-target scoring as intended.

---

## Q4. Does Table V use final epoch / validation-selected checkpoint / best Test epoch / Test-selected checkpoint / mean across epochs / another rule?

**Finding.** **The paper states no checkpoint or model-selection rule at all.** The paper's
only sentence on training duration is that epochs and learning rate were set empirically.
Therefore the paper's rule is unrecoverable.

Separately, the released code (not the paper) nominally selects by **Test MSE per epoch**, but
the selection is inert: the restore is commented out and the live-reference state dict means
the reported number is the **last epoch**.

**Evidence.**
- Paper: `[paper-md L298]` / `[paper-txt L601-603]`: *"We set the number of training epochs and
  the learning rate for MIFlu empirically because the hyperparameters vary depending on the
  base model."* A full-text search of `paper_text.txt` finds **no** occurrence of
  "checkpoint", "early stop", "best epoch", "best model", or "validation" in the results
  sections.
- Code: `[code main_ILI_lora.py L211]` `mse_temp, mae_temp = test(...)` every epoch;
  `[L225-227]` `if mse_temp < min_mse: … best_epoch_result = {… 'model_state':
  model.state_dict()}` (a **live reference**, not `deepcopy`);
  `[L235-238]` early-stopping call commented out;
  `[L242-243]` the restore `# model.load_state_dict(best_epoch_result['model_state'])` is
  **commented out**;
  `[L245]` after the loop, `mse, mae = test(...)` runs on the **current (= last-epoch)**
  model, and `mses.append(mse)` feeds the reported mean.
- Net: the printed "Best performance… MSE" is the min-Test-MSE bookkeeping value, but the
  model that is evaluated and saved (`[L263-264]`) is the **last-epoch** model.

**Classification: UNRECOVERED** (the paper's rule is unstated; the code's effective rule —
last epoch — is documented here but is not evidence of the paper's rule).

---

## Q5. How are the 10 repetitions aggregated?

**Finding.** By **arithmetic mean** across the ten repetitions, per the paper. The paper does
not specify whether the mean is taken over per-repetition scalar metrics or by pooling
repetition predictions; only "the mean of 10 repetitions" is stated.

**Evidence.**
- `[paper-md L306]`: *"Forecasting performance is assessed as the mean of **10
  repetitions**."*
- `[paper-txt L618]` verbatim: *"We assess the forecasting performance by calculating the
  mean of 10 repetitions of the forecasting results."*
- No per-repetition values, standard deviations, or confidence intervals are reported anywhere
  (`Table V` gives one scalar per L and metric; `Table VIII` gives one average per scheme).
- Code analogue (for contrast): the released harness means over `itr`, not over epochs —
  `[code main_ILI_lora.py L246,255-258]` `mses.append(mse) … print("mse_mean = {:.4f}…"
  .format(np.mean(mses)))`, with `--itr 1` by default (`[L84]`).

**Classification: PAPER_EXPLICIT** (arithmetic mean over 10 repetitions). The *unit* of
averaging (scalar-per-repetition vs pooled predictions) is not stated and is therefore a
sub-gap.

---

## Q6. Are the 10 seeds specified anywhere?

**Finding.** **No.** Neither the paper nor the released code specifies any seed list for the
ten repetitions.

**Evidence.**
- `[paper-txt]`: a full-text search finds **no** occurrence of "seed" or "random" in the
  paper (the only near-hit is the unrelated word "knowledge").
- `[code main_ILI_lora.py L27-30]`: the released entry point hard-codes a single fixed seed
  `fix_seed = 2021` at import (`random.seed(2021); torch.manual_seed(2021);
  np.random.seed(2021)`), and `[L84]` `--itr default=1` — there is no seed vector and no
  per-repetition reseeding.
- The project's own 42…51 list (`scripts/configs.py L212` `"seed": 42`;
  `scripts/innovation/paths.py L308` `SEEDS_FULL = tuple(range(42, 52))`;
  `REPRODUCIBILITY.md L126-127` *"base seed 42 (repetition r uses seed `42 + r - 1`)"*) is a
  **project declaration**, not the authors'.

**Classification: UNRECOVERED.**

---

## Q7. Direct sources for: epochs, initial learning rate, optimizer, scheduler, decay factor, batch size, early stopping, checkpoint-selection rule.

**Finding.** The paper discloses **none** of these values for MIFlu (it says only "set
empirically"). Every concrete value that exists is either an argparse **default** in the
released entry point or a **code** construct. There is therefore no paper-level source for
any of the eight items.

**Per-item evidence.**

| Item | Paper | Released code / config (direct source) |
|---|---|---|
| Epochs | **UNRECOVERED** — `[paper-md L298]` "set empirically" | `[main_ILI_lora.py L58]` `--train_epochs default=1` (CONFIG) |
| Initial LR | **UNRECOVERED** — same sentence | `[main_ILI_lora.py L55]` `--learning_rate default=0.0001` (CONFIG); applied at `[L159]` `torch.optim.Adam(params, lr=args.learning_rate)` |
| Optimizer | **UNRECOVERED** | `[main_ILI_lora.py L159]` `torch.optim.Adam(params, lr=args.learning_rate)` (CODE) |
| Scheduler | **UNRECOVERED** | `[main_ILI_lora.py L172]` `CosineAnnealingLR(model_optim, T_max=args.tmax, eta_min=1e-8)` is *constructed unconditionally*, but stepped **only if `--cos`** (`[L230-232]`), and `--cos default=0` (`[L85]`). Default path ⇒ `[L234] adjust_learning_rate(model_optim, epoch+1, args)` (CODE) |
| Decay factor | **UNRECOVERED** | `[main_ILI_lora.py L54]` `--decay_fac default=0.75`, but see Q8/Q9: `decay_fac` is **unused** on the default `lradj='type1'` path; only `type2`/`type4` read it (`[tools.py L29,31]`). The decay that actually runs is the hard-coded `0.9` exponent (`[tools.py L27]`) |
| Batch size | **UNRECOVERED** | `[main_ILI_lora.py L56]` `--batch_size default=16` (CONFIG); used for train/val/test in `[data_factory.py L21,32,37]` |
| Early stopping | **UNRECOVERED** (not mentioned) | `[main_ILI_lora.py L161]` `EarlyStopping(patience=3,…)` is instantiated, but the call is **commented out** (`[L235-238]`), so it never fires (CODE) |
| Checkpoint-selection rule | **UNRECOVERED** | `[main_ILI_lora.py L225-227]` selects by **Test MSE** per epoch; restore commented out (`[L242-243]`); final evaluated/saved model = **last epoch** (`[L245,263-264]`) (CODE) |

**Classification: CONFIG_EXPLICIT** — the only direct sources that exist for these eight items
are the released entry point's argparse defaults and its code logic. The paper contributes
**no** value (UNRECOVERED for all eight on the paper side).

---

## Q8. Origin of "20 epochs", "learning rate 5e-4", "lradj=type1", "decay_fac=0.75". Paper values, code defaults, or project inventions?

**Finding.** Split verdict:
- **20 epochs** and **learning rate 5e-4** — **project inventions** (reconstructed
  assumptions). They appear in **neither** the paper **nor** the released code.
- **`lradj=type1`** and **`decay_fac=0.75`** — **released-code argparse defaults**
  (`[main_ILI_lora.py L59]` `--lradj default='type1'`; `[L54]` `--decay_fac default=0.75`).
  Neither is a paper value.

The two project documents the task named label 20 epochs / 5e-4 as **"Paper:"**, which is a
**provenance mislabel**, since `[MIFlu_paper.md L298]` discloses no value.

**Evidence.**
- `[EE4080_MIFlu_Research_Recovery_Plan.md L161]` verbatim: *"| Optimization | **Paper: 20
  epochs, batch size 16, learning rate 0.0005**; recover scheduler, dropout, optimizer
  details, checkpoint rule and seeds |"* — the token `Paper:` is attached to values that do
  not appear in the paper.
- `[CodeBuddy_MIFlu_Recovery_Prompt.md L63]` verbatim: *"Recover the national paper contract:
  T=104; L=24/36/48/60; seven declared variables; … **20 epochs; batch 16; learning rate
  0.0005**; ten repetitions."* — the assumption is folded into the phrase "paper contract".
- Paper refutation: `[paper-md L298]` / `[paper-txt L601-603]` — the only sentence, no
  numbers.
- Code refutation of 20/5e-4: `[main_ILI_lora.py L58]` `--train_epochs default=1`;
  `[L55]` `--learning_rate default=0.0001`.
- Project origin of the numbers: `[scripts/configs.py L209-212]` `"learning_rate": 0.0005,
  "epochs": 20, "num_repetitions": 10, "seed": 42`; the project README itself concedes the
  paper's silence — `[README.md L40-42]`: *"**Learning rate / epoch counts were not
  disclosed** by the paper ("set empirically", Section V-C)."* (README_EXPLICIT, project).
- The A1 runs label them honestly: `[hpc_a1_runs/L36/provenance.txt]`
  `epochs=20 epochs_provenance=RECONSTRUCTED_paper_discloses_no_value` and
  `learning_rate=5e-4 lr_provenance=RECONSTRUCTED_paper_discloses_no_value`.
- `decay_fac=0.75` is furthermore inert on the default path — see Q9.

**Classification: CONFLICTING_EVIDENCE** — the project documents assert these are "Paper:"
values, while the paper and the released code both contradict that. The correct statuses are
`RECONSTRUCTED_ASSUMPTION` (20 / 5e-4) and `CONFIG_EXPLICIT` (`lradj=type1`, `decay_fac=0.75`).

---

## Q9. Is learning-rate decay visible in existing logs? Is `adjust_learning_rate` called when `cos=0`?

**Finding.** **Yes** to both.

**Evidence.**
- The call is unconditional on the `cos=0` path: `[main_ILI_lora.py L230-234]`
  ```python
  if args.cos:
      scheduler.step()
      print("lr = {:.10f}".format(model_optim.param_groups[0]['lr']))
  else:
      adjust_learning_rate(model_optim, epoch + 1, args)
  ```
  with `--cos default=0` (`[L85]`). So by default the cosine scheduler is never stepped and
  `adjust_learning_rate` **is** called every epoch.
- `adjust_learning_rate` for the default `lradj='type1'` (`[tools.py L26-27]`):
  ```python
  if args.lradj =='type1':
      lr_adjust = {epoch: args.learning_rate if epoch < 3 else args.learning_rate * (0.9 ** ((epoch - 3) // 1))}
  ```
  This yields an exponential decay with a **hard-coded factor 0.9 beginning at epoch 4**.
  `decay_fac` is read only by `type2`/`type4` (`[tools.py L29,31]`) and is therefore **not
  used** on this path — so the label "decay_fac=0.75 … MEASURED active" in
  `hpc_results/official_repo_reproduction_20261006/a1_results_per_run.csv` is imprecise: the
  active decay constant is **0.9**, not 0.75.
- Visible in a real A0 log (released defaults, 1 epoch): `[a0_587091.out]`
  `lr_adjust = {1: 0.0001}` / `Updating learning rate to 0.0001`. With one epoch the schedule
  has not yet decayed (epoch 1 < 3 ⇒ lr = base).
- Visible decay requires > 3 epochs, which the A1 reconstruction has (20 epochs). A1 train
  logs are not present in this working tree; the recorded observation is
  `[DEVIATION_LEDGER.md D-13]`: *"A1 运行日志出现 `Updating learning rate to
  0.00019371024450000004`（作业 606378）"*. That value equals `5e-4 × 0.9^9 = 1.9371e-4`, i.e.
  epoch 12 of the type-1 schedule — internally consistent with the `0.9` factor (a `0.75`
  factor at epoch 12 would give `5e-4 × 0.75^9 = 3.76e-5`). The underlying A1 `train.log`
  files were not copied into this repository; this figure is therefore a **recorded
  measurement**, not one re-derived here.

**Classification: LOG_INFERRED** — decay is demonstrated by log output (`lr_adjust`,
`Updating learning rate to 0.0001` in A0; `Updating learning rate to 0.0001937…` recorded for
A1 job 606378) together with the code path. The `cos=0` call site itself is `CODE_EXPLICIT`
(`[main_ILI_lora.py L234]`).

---

## Q10. Does the released code's metric aggregation correspond exactly to Table V?

**Finding.** **No.** Three independent mismatches.

**Evidence.**
1. **Variable coverage.** Table V reports "national ILI forecasting" over the seven-variable
   contract (Q1); the released `test()` scores **feature 0 only** (Q3).
2. **Input modality.** Every sample is a univariate `(T,1)` window (`[code data_loader.py
   L305-306]`), so the model is a single-channel GPT4TS-style forecaster; a seven-variable
   national contract is not reproduced by this path.
3. **Baselines.** Table V's comparative columns are quoted from prior literature, not re-run
   (see the Section V-C finding below), so no released-code aggregation can correspond to
   them.
   - The code's aggregation itself: `[tools.py L290-331]` `test()` pools all Test batches,
     reshapes to `(-1, pred_len, 1)`, and returns `metric(preds, trues)`; `[metrics.py L18-19,
     40-49]` `MSE = np.mean((pred - true) ** 2)`. So the number is a mean over all Test
     origins × lead steps × the one feature — expressed in standardized space (Q11).

**Classification: CONFLICTING_EVIDENCE** — the released aggregation (one feature, per-sample
univariate, quoted baselines) does not correspond to Table V's seven-variable national
contract.

---

## Q11. Are MSE and MAE computed in standardized space, inverse-transformed space, or different spaces in different paths?

**Finding.** In the **only national path that exists in the released repo**, MSE/MAE are
computed in the **StandardScaler (standardized) space**. There is exactly one space; no
inverse-transform is applied on any training or evaluation path in this repository.

**Evidence.**
- Loader standardizes per column and keeps the standardized values in `data_x`/`data_y`:
  `[code data_loader.py L275-278]` `self.scaler.fit(train_data.values); data =
  self.scaler.transform(df_data.values)`; `[L294-295]` `self.data_x = data[border1:border2];
  self.data_y = data[border1:border2]`.
- The model does window-wise instance normalization and then **de-normalizes back to the
  StandardScaler space** (not to raw ILI): `[code GPT4TS_lora.py L109-112]` `means =
  x.mean(1,keepdim=True); x = x - means; … x /= stdev`; `[L152-153]` `outputs = outputs *
  stdev; outputs = outputs + means`. `stdev`/`means` are the same **standardized-window**
  statistics, so the residual is in StandardScaler units.
- `test()` never de-normalizes: `[tools.py L290-331]`; `test_vis()` likewise
  (`[tools.py L333-378]`). `Dataset_Custom.inverse_transform` exists
  (`[code data_loader.py L319-320]`) but is **never called** anywhere in `main_ILI_lora.py` or
  `utils/tools.py`.
- Paper agreement for national: `[paper-md L258]` *"Each input variable is first normalized to
  a normal distribution using StandardScaler"*; `[paper-txt L511-513]` *"We first normalize
  each input variable to a normal distribution using StandardScaler. The mean square error
  (MSE) and mean absolute error (MAE) are then calculated using (3) and (4)."* For regional
  only, the paper says the opposite — `[paper-txt L526-527]` *"Unlike national ILI
  forecasting, these metrics have been used after de-normalizing the values to reproduce the
  original range."* — but the regional dataset/model are not in the released repo.

**Classification: CODE_EXPLICIT** (standardized space in the sole released path), corroborated
by `PAPER_EXPLICIT` for the national task. The paper's regional path is de-normalized, but no
released code implements it, so there is no "different space in different code paths" within
the repo.

---

## Q12. Does Table V pool across forecast origins / leads / variables / horizons / seeds?

**Finding.** Per axis:

| Axis | Paper | Released code (`test()` + reporting) |
|---|---|---|
| Forecast origins | **Not stated** — UNRECOVERED | **Yes** — mean over all Test origins (`[tools.py L319-327]`, `[metrics.py L18-19]`) |
| Lead steps (within horizon) | **Not stated** — UNRECOVERED | **Yes** — mean over `pred_len` steps (`[tools.py L323]` reshape then global mean) |
| Variables | Paper's task = 7 (Q1); the metric's variable set is **Not stated** — UNRECOVERED | **No** — single feature (feature 0); see Q3 |
| Horizons | **No** pooling in Table V (each L is its own row, `[paper-md L318-325]`); Table VIII **does** average over L=24/36/48/60 (`[paper-md L410]`) | **No** — one run per L; no cross-L pooling in `main_ILI_lora.py` |
| Seeds / repetitions | **Yes** — `[paper-md L306]` "mean of 10 repetitions" | Mean over `itr` (`[main_ILI_lora.py L255-258]`), default `itr=1` |

The paper never defines the "M data points" of Eq. (3)/`[paper-txt L513-524]` — i.e. whether M
runs over origins, leads, variables, or a product of them — so the pooling unit for the
reported number is not determined by the paper.

**Classification: UNRECOVERED** — the paper does not specify the origins/leads/variables
pooling (the crux of the question). The repetition-mean and the per-L table structure are
`PAPER_EXPLICIT`; the code's behaviour is `CODE_EXPLICIT`. The overall status of the paper's
pooling contract is UNRECOVERED.

---

## Q13. Is the paper's reported average an equal-weight average of the four horizon-level scores? (1.542/1.422/1.414/1.364 → 1.436)

**Finding.** **Yes** — equal-weight arithmetic mean of the four horizon values.

**Evidence.**
- Per-horizon MIFlu scores: `[paper-md L318,320,322,324]` (MSE) = 1.542, 1.422, 1.414, 1.364;
  `[paper-md L319,321,323,325]` (MAE) = 0.726, 0.779, 0.757, 0.719.
- The averaged table is Table VIII, whose scope is explicit: `[paper-md L410]` caption —
  *"(average MSE/MAE for L = 24, 36, 48, 60)"*; `[paper-txt L799]` *"average MSE and MAE for
  L = 24, 36, 48, and 60."*; and its MIFlu row is `[paper-md L414]` `| MIFlu | 1.436 | 0.745 |`.
- Arithmetic confirms equal weighting:
  - MSE: (1.542 + 1.422 + 1.414 + 1.364) / 4 = 5.742 / 4 = **1.4355** → rounds to **1.436**.
  - MAE: (0.726 + 0.779 + 0.757 + 0.719) / 4 = 2.981 / 4 = **0.74525** → rounds to **0.745**.

**Classification: PAPER_EXPLICIT** — the caption states the averaging set (L = 24, 36, 48, 60)
and the arithmetic reproduces Table VIII exactly, confirming equal weights.

---

## Q14. What does the code's `mse_mean` actually mean?

**Finding.** `mse_mean` = the **arithmetic mean, over the `--itr` harness repetitions, of the
final-epoch Test MSE**. It is **not** a mean over epochs. With the default `--itr 1` it is just
the single last-epoch Test MSE.

**Trace.**
1. `[main_ILI_lora.py L111]` `mses = []`; loop `for ii in range(args.itr):` (`[L122]`).
2. After the epoch loop, the model is at **last-epoch** weights (restore commented,
   `[L242-243]`): `[L245]` `mse, mae = test(model, test_data, test_loader, args, device, ii)`;
   `[L246]` `mses.append(mse)`.
3. `[L255-258]`:
   ```python
   mses = np.array(mses)
   ...
   print("mse_mean = {:.4f}, mse_std = {:.4f}".format(np.mean(mses), np.std(mses)))
   ```
   So `mse_mean` is the mean over the `itr` repetitions only.
4. Inside a single repetition, `test()` (`[tools.py L290-331]`) pools **all** Test batches,
   reshapes to `(-1, pred_len, 1)` (`[L323-324]`), and calls `metric()` (`[L327]`), whose
   `MSE = np.mean((pred - true) ** 2)` (`[metrics.py L18-19]`). So one `mse` = mean over
   (Test origins × lead steps × the single feature), in standardized space.
5. Direct runtime confirmation: `[a0_587091.out]` (released defaults, `itr=1`, 1 epoch) prints
   `mse_mean = 0.9685, mse_std = 0.0000` — `std = 0` because `mses` has exactly one element.

**What it is NOT.** It is **not** "mean across epochs". The project deliverable column named
`mse_mean_over_epochs` in `hpc_results/official_repo_reproduction_20261006/a1_results_per_run.csv`
(e.g. L24 = 0.604363) is a *different* quantity — the mean of the 20 per-epoch Test MSEs in
`a1_results_per_epoch.csv` (verified: the 20 L24 values average to 0.60436). The released
code's `mse_mean` for that same run equals the **final-epoch** value
`mse_final_epoch = 0.57927334` (`a1_results_per_run.csv`, L24 row; equals the last row of
`hpc_a1/…L24…csv`), because `itr=1`. The two names must not be conflated.

**Classification: CODE_EXPLICIT** — fully determined by the trace in `main_ILI_lora.py`
`train()`/`test()` above, and confirmed by `LOG_INFERRED` evidence (`mse_std = 0.0000`).

---

## Q15. Can the paper and code contracts be matched without undocumented assumptions?

**Finding.** **No.** A match would require undocumented assumptions on at least four axes, and
the paper leaves several contract parameters unrecovered.

**Blocking gaps.**
1. **Variable/evaluation coverage.** Paper: seven-variable national task (Q1). Code: feature 0
   only, per-sample univariate (Q3) — needs an assumption about which variable(s) Table V
   scores.
2. **Training schedule.** Paper: epochs and LR undisclosed, `[paper-md L298]`. Code default:
   1 epoch / 1e-4 (`[L58,55]`). Any 20/5e-4 choice is `RECONSTRUCTED_ASSUMPTION` (Q7, Q8).
3. **Repetition seeds.** Paper gives none (Q6); code gives none (fixed `2021`, `itr=1`).
4. **Checkpoint / selection rule.** Paper states none (Q4); code's nominal Test-MSE selection
   is inert and yields the last-epoch model.
5. **Metric pooling unit.** Paper never defines the "M data points" over which Eq. (3)/(4)
   average (Q12).
6. **Baseline columns.** Quoted from [9]/[14], not re-run (Section V-C), so they cannot be
   regenerated from any code.

**Classification: CONFLICTING_EVIDENCE** — the paper contract and the released-code contract
differ on variable coverage, modality, selection rule, and training schedule, and the paper
additionally leaves schedule, seeds, checkpoint rule and pooling unit unspecified. A match
requires assumptions that are not documented in either source.

---

## Additional finding — Section V-C: are the baseline and MIFlu columns quoted rather than re-run?

**Exact sentence** (`[paper-txt L582-583]`, verbatim):
> *"The results for the national and regional ILI forecasting models are taken from [9] and
> [14], respectively."*

Same sentence in `[paper-md L290]`: *"Results for the national and regional ILI forecasting
models are taken from [9] and [14], respectively."*

**Context** (`[paper-txt L578-584]`): *"To compare the forecasting performance of our proposed
model, we consider SOTA models proposed for ILI forecasting. Table IV presents the list of
models we compare for national/regional ILI forecasting and their hyperparameters. These
settings are the same as those reported in previous studies [9], [14]. The results for the
national and regional ILI forecasting models are taken from [9] and [14], respectively."*

**Determination.**
- **Baseline columns = quoted, not re-run.** The sentence's subject ("the … ILI forecasting
  models") is the set of comparative models enumerated in Table IV (GPT4TS, DLinear, PatchTST,
  TimesNet, FEDformer, Autoformer, Stationary, ETSformer, LightTS, Informer, Reformer for
  national; GPT4TS, ReILIF, TFT, SAIFlu-Net, Cola-GNN, STNN, CNNRNN for regional), whose
  "settings are the same as those reported in previous studies". Reading the sentence in its
  immediate context, the comparative columns are **quoted from [9] and [14]**, i.e. **not
  re-run**. Reference [9] = GPT4TS/OneFitsAll (Zhou et al. 2023); [14] = ReILIF
  (Papagiannopoulou et al. 2024).
- **MIFlu's own column = NOT explicitly stated → UNRECOVERED.** The paper never says whether
  the MIFlu numbers in Table V are quoted from somewhere or run by the authors. The strongest
  available signal is the immediately following paragraph, `[paper-txt L601-603]`: *"We set the
  number of training epochs and the learning rate for MIFlu empirically because the
  hyperparameters vary depending on the base model."* — "we set … for MIFlu" implies the
  authors trained MIFlu themselves, but this is an **inference, not a statement**. No sentence
  in the paper states the provenance of the MIFlu column.

**Classification: PAPER_EXPLICIT** for the finding that the **baseline** results are quoted
from [9]/[14] rather than re-run; **UNRECOVERED** for the sub-question of whether MIFlu's own
column is quoted (the paper states nothing; a "they trained it" reading is only implied by
§V-C).

---

## Summary

| Q | Topic | Classification |
|---|---|---|
| Q1 | Table V: one target vs seven variables | PAPER_EXPLICIT (seven variables defined; aggregation set sub-gap) |
| Q2 | Roles of the seven variables | PAPER_EXPLICIT |
| Q3 | `feat_id=[0]` | CONFLICTING_EVIDENCE (code-level evaluation defect vs paper's 7-variable task) |
| Q4 | Table V checkpoint/selection rule | UNRECOVERED |
| Q5 | Aggregation of 10 repetitions | PAPER_EXPLICIT (arithmetic mean) |
| Q6 | The 10 seeds | UNRECOVERED |
| Q7 | Sources for 8 training settings | CONFIG_EXPLICIT (paper gives none) |
| Q8 | Origin of 20 ep / 5e-4 / type1 / 0.75 | CONFLICTING_EVIDENCE (mislabeled as "Paper:") |
| Q9 | LR decay visible; `cos=0` call | LOG_INFERRED |
| Q10 | Code aggregation vs Table V | CONFLICTING_EVIDENCE |
| Q11 | Metric space (standardized vs inverse) | CODE_EXPLICIT (standardized; paper agrees for national) |
| Q12 | Pooling axes of Table V | UNRECOVERED |
| Q13 | Equal-weight average of 4 horizons | PAPER_EXPLICIT |
| Q14 | Meaning of `mse_mean` | CODE_EXPLICIT |
| Q15 | Paper/code contract matchable w/o assumptions | CONFLICTING_EVIDENCE (No) |
| — | §V-C baseline vs MIFlu column provenance | PAPER_EXPLICIT (baselines quoted) / UNRECOVERED (MIFlu column) |

**Corrective notes recorded by this audit.**
1. `hpc_results/official_repo_reproduction_20261006/a1_results_per_run.csv` labels the A1 LR
   schedule *"type1 exponential decay, decay_fac=0.75 (released default, MEASURED active)"*.
   The active decay constant on the `type1` path is the hard-coded **0.9** (`[tools.py L27]`);
   `decay_fac=0.75` is not read by `type1`. The recorded log value `0.00019371…` equals
   `5e-4 × 0.9^9`, not any `0.75`-based value.
2. `EE4080_MIFlu_Research_Recovery_Plan.md L161` and `CodeBuddy_MIFlu_Recovery_Prompt.md L63`
   attach the label "Paper:" to "20 epochs" and "learning rate 0.0005", which the paper does
   not disclose. The correct statuses are `RECONSTRUCTED_ASSUMPTION`.
3. The project deliverable column `mse_mean_over_epochs` is the mean over epochs, whereas the
   released code's `mse_mean` is the mean over `itr` repetitions of the final-epoch Test
   score. The names are not interchangeable (Q14).