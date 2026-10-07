# R1-C — DOCUMENTARY EVIDENCE FOR THE UNRESOLVED SETTINGS

Generated 2026-10-07. Every claim below is quoted from the released author code
or the paper, with file and line. Nothing is inferred from a summary.

Source tree: `/scratch/sychan552/a0_replay` (author repository, unmodified).

---

## 1. The unresolved settings, one by one

### 1.1 Optimizer — **RECOVERED, already matched**

```python
# main_ILI_lora.py:159
model_optim = torch.optim.Adam(params, lr=args.learning_rate)
```

Adam is the released default. **R1-B also uses Adam.** This setting is *not* a
source of the gap.

### 1.2 Scheduler — **RECOVERED, and MISMATCHED** ⚠

```python
# utils/tools.py:26-27
if args.lradj =='type1':
    lr_adjust = {epoch: args.learning_rate if epoch < 3
                 else args.learning_rate * (0.9 ** ((epoch - 3) // 1))}
```

The released code decays the learning rate by **0.9× per epoch from epoch 3
onwards**. Over 20 epochs that is `5e-4 → 5e-4 × 0.9^17 ≈ 8.3e-6`.

**R1-B never calls `adjust_learning_rate` or `scheduler.step()`.** It declares
`lradj="type1"` in its config but trains all 20 epochs at a **constant 5e-4**.

This is a genuine, documentary-supported omission — the only setting found where
R1-B silently differs from a *recovered* released default rather than making a
declared repair.

### 1.3 Checkpoint-selection rule — recovered; R1-B differs **deliberately**

```python
# main_ILI_lora.py:211, 225-227, 260-264
mse_temp, mae_temp = test(model, test_data, test_loader, args, device, ii)
...
if mse_temp < min_mse:
    min_mse = mse_temp
    best_epoch_result = {..., 'model_state': model.state_dict()}
...
model.load_state_dict(best_epoch_result['model_state'])
```

The released rule selects the checkpoint on **Test MSE**, reading Test every
epoch; early stopping is commented out.

R1-B selects on **Validation** (correction B-5). This is a **declared repair**,
not an omission: reproducing it would mean reintroducing test-set selection.
It is therefore **not** a legitimate R1-C candidate.

### 1.4 Pooling axes / evaluation scope — recovered; R1-B differs **deliberately**

```python
# utils/tools.py:304-311
batch_x = batch_x.float().to(device)   # torch.Size([16, 104, 1])   <-- ONE channel
outputs = model(batch_x[:, -args.seq_len:, :], itr)
outputs = outputs[:, -args.pred_len:, :]
```

The released evaluation runs **single-channel** (`[16, 104, 1]`), consistent with
the released loader's `feat_id` bug. It therefore cannot produce the paper's
**7-variable** Table V.

R1-B evaluates all seven channels (correction B-1) — again a **declared repair**,
not an omission, and not a candidate.

### 1.5 Repetition aggregation — documented in the released output

```python
# main_ILI_lora.py:252-257
print("mse_mean = {:.4f}, mse_std = {:.4f}".format(np.mean(mses), np.std(mses)))
```

The released script reports a **mean and standard deviation over iterations**.
The paper's Table V is a single number per cell; whether it is a mean over ten
repetitions is **not stated in the released code**. The paper reports ten
repetitions; the aggregation rule is **unrecovered**.

### 1.6 Seed mechanism — **NOT PRESENT**

No seed list, no `torch.manual_seed` call tied to a repetition index, and no
seed recorded in the released script. **Unrecovered.**

### 1.7 Other recovered settings — all already matched

| setting | released | R1-B | match |
|---|---|---|---|
| T | 104 | 104 | ✅ |
| epochs | 20 (Table IV) | 20 | ✅ |
| batch | 16 (Table IV) | 16 | ✅ |
| lr | 5e-4 | 5e-4 | ✅ |
| LoRA r | 4 | 4 | ✅ |
| LoRA targets | `["c_attn"]` | `["c_attn"]` | ✅ |
| gpt_layers | 6 | 6 | ✅ |

---

## 2. What this leaves as a legitimate candidate

Sorting the unresolved settings by whether a candidate is **evidence-supported
and non-defect-reintroducing**:

| setting | status | candidate? |
|---|---|---|
| optimizer | recovered, matched | no — nothing to change |
| **scheduler** | **recovered, R1-B omits it** | **YES — C1** |
| checkpoint rule | recovered; R1-B repairs it | no — would reintroduce Test selection |
| pooling axes | recovered; R1-B repairs it | no — would reintroduce single-channel eval |
| repetition aggregation | unrecovered | no — no evidence to instantiate |
| seed mechanism | unrecovered | no — no evidence to instantiate |
| T/epochs/batch/lr/LoRA | recovered, matched | no — nothing to change |

**Exactly one legitimate candidate exists: C1 — apply the released `type1`
learning-rate schedule.**

This is the outcome the brief's "bounded, evidence-supported" constraint asks
for: the search space is not narrowed by preference, it is narrowed by evidence,
and it happens to contain a single item.

## 3. Why the other settings cannot be candidates

- **Checkpoint rule and pooling axes** are *repairs* of released defects. A
  candidate that reverts them would reproduce the defect, not the paper. Testing
  them would also require reading Test during selection, which the brief forbids
  and which would make the resulting number non-comparable.
- **Repetition aggregation and seed mechanism** have no documentary
  instantiation. Inventing values would be accuracy hunting with extra steps.

## 4. Expectation stated in advance

Applying C1 differs from R1-B only in the learning-rate trajectory. R1-B's
selected epochs were 5, 6, 10 and 11 of 20 — *early*. A decaying schedule
typically helps *later* epochs, which R1-B's validation rule was already
rejecting. So C1 may plausibly change little.

**This expectation is recorded before running anything**, so that a null result
cannot be spun as a surprise and a positive result cannot be over-claimed.