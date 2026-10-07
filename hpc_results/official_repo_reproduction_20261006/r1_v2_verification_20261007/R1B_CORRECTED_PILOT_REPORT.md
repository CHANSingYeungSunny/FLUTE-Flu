# R1-B CORRECTED PILOT — REPORT

Generated 2026-10-07. Namespace `r1_v2_20261007`. Authorisation: continuous
execution (supersedes the 0.30 GPU-h cap).

# VERDICT: `PARTIAL_REPRODUCTION`

On the predeclared scale of `R1_REPRODUCTION_SUCCESS_GATES.md` (fixed before
execution, tolerances not tunable): all four horizons run, the contract is
matched, the results are directionally right, and **every horizon lies outside
the predeclared tolerance**. Gate C15 independently caps a one-repetition pilot
at `PARTIAL_REPRODUCTION`.

On the pilot scale: **`PILOT_DIRECTIONALLY_ALIGNED`** — right trend, wrong
magnitude, consistently.

---

## 1. Jobs and cost

| # | job | horizon | state | elapsed | GPU-h |
|---:|---|---|---|---:|---:|
| 1 | 608045_0 | L=24 | COMPLETED (rc 0) | 00:08:01 | 0.1336 |
| 2 | 608061_1 | L=36 | COMPLETED (rc 0) | 00:07:45 | 0.1292 |
| 3 | 608087_2 | L=48 | COMPLETED (rc 0) | 00:07:31 | 0.1253 |
| 4 | 608105_3 | L=60 | COMPLETED (rc 0) | 00:07:17 | 0.1214 |
| | | | | **00:30:34** | **0.5094** |

One GPU (A100) per job, `stingy` partition, `MaxJobsPU=1` respected, nothing run
on a login node. Measured cost per fit **0.127 GPU-h** — close to the 0.157
measured from the failed run 607969, so the corrected plan's cost model was sound.

## 2. Per-horizon result

| | L=24 | L=36 | L=48 | L=60 | mean |
|---|---:|---:|---:|---:|---:|
| **reproduced MSE** | **2.133497** | **2.022708** | **1.841337** | **1.793311** | **1.947713** |
| **reproduced MAE** | **0.929781** | **0.997668** | **0.895716** | **0.911584** | **0.933687** |
| paper MSE | 1.542 | 1.422 | 1.414 | 1.364 | 1.4355 |
| paper MAE | 0.726 | 0.779 | 0.757 | 0.719 | 0.74525 |
| Δ MSE | +0.5915 | +0.6007 | +0.4273 | +0.4293 | **+0.5122** |
| rel. MSE | **+38.4 %** | **+42.2 %** | **+30.2 %** | **+31.5 %** | **+35.7 %** |
| Δ MAE | +0.2038 | +0.2187 | +0.1387 | +0.1926 | +0.1884 |
| reproduced SD | n/a | n/a | n/a | n/a | n/a |
| inside MSE tol (±0.10)? | no | no | no | no | **0 / 4** |
| inside MAE tol (±0.05)? | no | no | no | no | **0 / 4** |

**SD is `n/a`, not 0** — one repetition. Mean tolerance is ±0.08; the mean is
+0.5122 outside it.

Selected epochs were **5, 6, 10, 11** of 20; validation MSE ≈ 0.20–0.23 at each
horizon.

## 3. Contract gates C1–C15

| # | Gate | Result |
|---|---|---|
| C1 | author 966-row dataset, SHA-256 pinned | ✅ `2a96dfed…ebfe5` |
| C2 | split 676 / 97 / 193 chronological | ✅ |
| C3 | scaler fitted on train rows only | ✅ (also confirmed in the author's own `Dataset_Custom`) |
| C4 | seven channels evaluated | ✅ prediction arrays are `(n, L, 7)` |
| C5 | origins match the containment rule | ✅ **549/74/170 · 537/62/158 · 525/50/146 · 513/38/134** |
| C6 | text pathway functional | ✅ per-checkpoint probe (job 608153, CPU-only): **`text_active` on all four**; max\|Δ\| 0.4606 / 0.7675 / 1.9188 / 3.7375; text-grad 0.0155 / 0.0105 / 0.0351 / 0.0179 |
| C7 | LoRA actually applied | ✅ 12 LoRA tensors every fit |
| C8 | freeze effective | ✅ trainable 1.67 M / 82.78 M = **2.02 %** (L24) … 3.38 % (L60) |
| C9 | checkpoint selection validation-only | ✅ `test_access_during_fit = False` |
| C10 | Test evaluated once | ✅ |
| C11 | predictions **and** targets persisted | ✅ 4 NPZs |
| C12 | independent scoring reproduces the numbers | ✅ max disagreement **1.9e-07** |
| C13 | no Track-B artefact used | ✅ |
| C14 | deviations declared | ✅ B-1…B-7 |
| C15 | repetition count stated honestly | ✅ **1** ⇒ verdict capped at `PARTIAL_REPRODUCTION` |

Structural checks on all four NPZs pass: shapes `(n, L, 7)`, origins unique and
ascending, every target block inside the Test split. Locked checkpoints written
(6.7–11.4 MB, atomic) with `checkpoint_reload_max_abs_diff = 0.0` on all four.

**All 15 contract gates are closed.** The C6 probe additionally re-verified the
locked-checkpoint path on the persisted artefacts: loading the 43 stored tensors
leaves exactly the **49 frozen backbone tensors** absent (the sidecar's
`n_frozen_tensors = 49`, reconstructed from the pinned `gpt2` snapshot), with
`unexpected_keys = []`, and the reloaded checkpoint reproduces the persisted
NPZ to **max |Δ| = 1.4e-06**. Evidence: `R1B_CHECKPOINT_TEXT_PROBE.json`.

## 4. The lead diagnosis — the released selection rule

**The released code selects the checkpoint on the Test set.** From
`main_ILI_lora.py` (lines 210–264, verbatim):

```python
vali_loss = vali(model, vali_data, vali_loader, criterion, args, device, ii)
mse_temp, mae_temp = test(model, test_data, test_loader, args, device, ii)   # Test EVERY epoch
...
if mse_temp < min_mse:
    min_mse = mse_temp
    best_epoch_result = {'mse': mse_temp, ..., 'model_state': model.state_dict()}
...
model.load_state_dict(best_epoch_result['model_state'])   # <- this state is saved
torch.save(best_epoch_result['model_state'], best_model_path)
```

`min_mse` is driven by the **test** metric, so the network the paper reports is
the one that minimised Test MSE over 20 epochs — an optimistic selection on the
evaluation set. Early stopping is commented out.

R1-B deliberately **does not** do this: correction B-5 selects on validation and
reads Test once. That is the scientifically correct choice, and it is the single
largest known divergence between the R1-B contract and the behaviour that
produced the paper's numbers.

**This is a released-code defect, and it is a plausible explanation of the sign
and rough size of the gap** — but it is *not yet measured*. It is recorded here
as the leading hypothesis, not as an established cause.

Two mechanisms could contribute:
1. **selection bias** — best-of-20 on Test is optimistically biased;
2. **effective training length** — validation windows sit almost entirely inside
   the training range (the author's `border1s[1] = num_train - seq_len` places
   them there), so validation MSE is a near-train quantity and stops improving
   early; best-validation selection therefore picks epoch 5–11 of 20, while the
   released rule effectively reports a converged epoch.

## 5. What the fixed window contract now rests on

The corrected origin counts reproduce the author's **own loader arithmetic**
exactly, not merely an earlier project record:

```
border1s/test = 966 - 193 - 104 = 669 ; border2s/test = 966  ->  297 rows
tot_len = 297 - 104 - L + 1  ->  170 / 158 / 146 / 134   (L = 24/36/48/60)
```

identical to the four reproduced counts. The strict-containment contract is thus
the author's rule, independently derived.

## 6. Declared unresolved settings

| Setting | Status |
|---|---|
| pooling axes | mean over (origins × leads × 7 variables), z-space — **chosen, not recovered** |
| optimizer | Adam (released default); paper states none |
| scheduler | none (released applies a hard-coded 0.9 decay) |
| **selection rule** | **see §4 — the released rule selects on Test; R1-B selects on validation** |
| seed identity | repetition index → seed 1000+rep; 1 repetition |

## 7. Not done

The ten-repetition expansion (not justified while the result is outside
tolerance) · R1-C · Tier-2/Tier-3 · the historical 1025-row replacement ·
the 4-vs-4 re-score · the DOCX. The per-checkpoint text-path re-probe (C6) **was**
run and is closed — see §3.

**No number in this report is estimated or carried over from another run.**
Every reproduced value is from the persisted NPZ, re-scored independently.