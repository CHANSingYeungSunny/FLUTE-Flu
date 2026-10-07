# A0-R METRIC SEMANTICS — what `mse_mean` actually is

Generated 2026-10-06. Append-only; nothing existing was modified.

**Question.** The released entry point prints, for L=24,
`mse_mean = 0.5793, mse_std = 0.0000`, and a separate line
`Best performance in iteration 0: Epoch 8 with MSE = 0.5344 and MAE = 0.4503`.
This file determines, from the code, exactly what those two numbers are and why they differ.

**Sources.** `recovery/author_repo/main_ILI_lora.py` (`train()` L91-267); its `test()` in
`recovery/author_repo/utils/tools.py` L290-331; `utils/metrics.py` L4-49;
`models/GPT4TS_lora.py` `forward()` L106-155; `data_provider/data_loader.py`
`Dataset_Custom` L244-317; the archived per-epoch CSVs
(`hpc_a1/…pl24….csv`, `hpc_a1_runs/L{36,48,60}/…csv`).

---

## 1. `test()` traced line by line (`utils/tools.py` L290-331)

| Line | Statement | What it means |
|---|---|---|
| L291-292 | `preds = []; trues = []` | two Python lists, in memory only |
| L295 | `model.eval()` | batch-norm/dropout inference mode |
| L296 | `with torch.no_grad():` | no gradients |
| L297 | `for i,(batch_x, batch_y, …) in enumerate(test_loader)` | iterate the test loader; `batch_size=16`, `drop_last=True` |
| L304 | `batch_x = batch_x.float().to(device)` | `(16, 104, 1)` — **one variable per sample** |
| L305 | `batch_y = batch_y.float()` | `(16, label_len+pred_len, 1)` = `(16, 18+L, 1)`, kept on CPU |
| L307 | `outputs = model(batch_x[:, -args.seq_len:, :], itr)` | `(16, L, 1)` — the model returns `[b, pred_len, M]` with `M=1` |
| L310 | `outputs = outputs[:, -args.pred_len:, :]` | keep the L forecast steps |
| L311 | `batch_y = batch_y[:, -args.pred_len:, :].to(device)` | keep the matching L ground-truth steps |
| L313-314 | `pred = outputs.detach().cpu().numpy(); true = batch_y.detach().cpu().numpy()` | `(16, L, 1)` each |
| L316-317 | `preds.append(pred); trues.append(true)` | one array per batch |
| L319-320 | `preds = np.array(preds); trues = np.array(trues)` | `(n_batches, 16, L, 1)` |
| L323-324 | `preds = preds.reshape(-1, L, 1)` | `(n_batches*16, L, 1)` — flatten batch and origin |
| L327 | `mae,mse,rmse,mape,mspe,smape,nd = metric(preds, trues)` | `metrics.MSE` = `np.mean((pred-true)**2)` over **all** elements |
| L331 | `return mse, mae` | **only two scalars leave the function** — the arrays are discarded |

### 1.1 Which feature(s) are scored

**Feature 0 only.** `Dataset_Custom.__len__` returns, for the test split (`set_type == 2`),
`(len(data_x) - seq_len - pred_len + 1)` **without** multiplying by `enc_in` (L312-316). The
loader therefore yields `tot_len` windows, and `__getitem__` computes
`feat_id = index // tot_len` — so for every test index `index < tot_len` ⇒ `feat_id = 0`.
Feature 0 is the first numeric column **`"1"`** (weighted ILI) in
`national_illness.csv` (`date,1,2,3,4,5,6,OT`). The other 6 variables are never evaluated
by `test()`.

### 1.2 What is averaged over what

`metrics.MSE(pred, true) = np.mean((pred - true) ** 2)` is a **single global mean** over the
full `(n_batches × batch_size × pred_len × 1)` array, i.e. over:

* **origins** — every test window that survives `drop_last` (160 / 144 / 144 / 128 for
  L = 24 / 36 / 48 / 60), and
* **leads** — every horizon step `1..L` inside each window, and
* the **single** channel `M = 1` (feature 0).

There is no per-origin or per-lead aggregation and no averaging over the 7 variables — the
7-variable dimension is never entered. MAE is the same reduction applied to `|pred-true|`.

### 1.3 Standardized or original space?

**Standardized (z-scored), not raw ILI counts.** `Dataset_Custom.__read_data__` fits a
`sklearn.StandardScaler` on the **training slice** (`df_data[0:676]`, the scaler's
`border1s[0]:border2s[0]`) and transforms the whole frame (L275-278), so `data_x`/`data_y`
are z-scored with the train mean/std of feature 0. `GPT4TS.forward` additionally does a
per-window *instance* normalization internally (subtract the lookback mean, divide by the
lookback std, L109-111) but restores it before returning (`outputs = outputs*stdev + means`,
L152-153), so the returned tensor is back in the loader's z-space. `pred` and `true` are
therefore both z-scores of feature 0 — the ANOVA-style "MSE" is a normalized quantity, not an
error in ILI counts, and is not on the same scale as the paper's Table V numbers.

---

## 2. How the per-iteration values become `mse_mean`

Inside `train()`:

* **In-loop, every epoch** (L211-224): `mse_temp, mae_temp = test(...)`; the pair is appended
  to `results` (which becomes `./results/<setting>.csv`) and to `mses_temp`.
* **In-loop running minimum** (L225-227): `if mse_temp < min_mse:` → store
  `best_epoch_result = {mse, mae, epoch, model_state}`. This is the *best-epoch* tracker.
* **After the epoch loop** (L245-247): `mse, mae = test(...)` is called **once more** on the
  current weights (nothing has trained since the last epoch — only `adjust_learning_rate`
  ran), and this single value is appended to **`mses`**.
* **After the `itr` loop** (L255-257): `mses = np.array(mses); print("mse_mean = {:.4f}".
  format(np.mean(mses)))`.

**Therefore `mse_mean = mean over repetitions (`itr`) of each repetition's post-loop test
MSE.** With `--itr 1` (all four A0-R runs) there is exactly one element, so

> **`mse_mean` = the Test MSE at the final epoch's weights. It is NOT a mean across epochs.**

### 2.1 Exactly how `0.5793` (L=24) was produced

1. Epoch index 19 is the last training epoch. Its in-loop `test()` (L211) returned
   `mse_temp = 0.57927334`; `results.append({... epoch:19, mse:0.57927334 ...})` wrote it as
   the **last row** of `a1_reconstructed_L24_…_itr0.csv`.
2. The post-loop `test()` (L245) ran on the **same** final weights and returned the same
   `0.57927334`, so `mses = [0.57927334]`.
3. L257 computed `np.mean([0.57927334]) = 0.57927334` and printed `mse_mean = 0.5793`.

The identical construction gives `mse_mean = 0.5920` (L36), `0.6088` (L48), `0.6361` (L60) —
each equals its run's final-epoch row (0.592006, 0.608798, 0.636060) to 4 d.p. **`mse_mean` is
the final-epoch value, not any kind of average over epochs.** If `itr > 1` it would become the
mean of several such final-epoch values (one per repetition), still never an epoch average.

---

## 3. Relationship to `Best performance … with MSE =` — different code paths

The line `Best performance in iteration {ii}: Epoch {…} with MSE = {…}` (L259) prints
`best_epoch_result`, which is maintained **inside** the epoch loop by the running minimum at
L225-227. Both numbers are produced by `test()`, but they are reduced in different places and
in opposite directions:

| | `mse_mean` (L257) | `Best performance … MSE` (L259) |
|---|---|---|
| Source call | post-loop `test()` (L245) | in-loop `test()` (L211) |
| Weight state | final epoch's weights | the epoch that minimised Test MSE |
| Reduction | `np.mean(mses)` over repetitions | `min` over epochs (strict `<`) |
| L24 value | 0.5793 (epoch 19) | **0.5344** (epoch 8) |
| L36 value | 0.5920 (epoch 19) | 0.5387 (epoch 10) |
| L48 value | 0.6088 (epoch 19) | 0.6069 (epoch 16) |
| L60 value | 0.6361 (epoch 19) | 0.5933 (epoch 5) |

Because the final epoch is not the best epoch, `mse_mean > best-epoch MSE` on every horizon.
**They are not two views of one number; they answer different questions.** `mse_mean` answers
"how well does the network do when training stops?"; the `Best performance` line answers "how
well did any checkpoint do?" — and it is that best checkpoint (not the final one) that is saved
to `checkpoint.pth` (L260-264) and used for `test_vis`.

---

## 4. Naming collision — three different quantities called "mean"

The four-horizon deliverable tables add a **third** quantity, so any bare use of "mse_mean"
is ambiguous:

| Name / where | Definition | L24 | L36 | L48 | L60 |
|---|---|---:|---:|---:|---:|
| `mse_mean` (entry point stdout, L257) | mean over repetitions of the post-loop Test MSE (= final-epoch value at itr=1) | 0.5793 | 0.5920 | 0.6088 | 0.6361 |
| `mse_mean_over_epochs` (`a1_results_per_run.csv`, `build_a1_results.py` L103) | arithmetic mean of the 20 per-epoch Test MSEs | 0.604363 | 0.602817 | 0.657133 | 0.654465 |
| `mse_best_epoch` (`a1_results_per_run.csv`) | minimum per-epoch Test MSE | 0.534386 | 0.538689 | 0.606936 | 0.593349 |

`REPORT_EN.md` §C labels its column "mse_mean" but fills it with the **middle** row
(`mse_mean_over_epochs`, 0.6044/0.6028/0.6571/0.6545) — i.e. a mean over epochs, **not** the
entry point's `mse_mean`. The two must not be interchanged.

---

## 5. Bottom line

* `mse_mean` = **feature-0-only, standardized-space** MSE, averaged over surviving test
  origins × forecast leads (not over variables), reduced as the **mean over repetitions of the
  final-epoch test score**. At `itr=1` it is simply **the last epoch's Test MSE**.
* `0.5793` (L24) = `np.mean([0.57927334])` = the epoch-19 Test MSE the entry point itself
  printed; it equals the last row of the run's per-epoch CSV.
* `Best performance … MSE = 0.5344` is a **different** number from a **different** reduction
  (running minimum across epochs), computed inside the epoch loop.
* Neither value is comparable to Table V: different variable coverage (feature 0 vs all 7),
  different space (z-scores vs the paper's scale), different checkpoint rule (Test-selected),
  and a single repetition.