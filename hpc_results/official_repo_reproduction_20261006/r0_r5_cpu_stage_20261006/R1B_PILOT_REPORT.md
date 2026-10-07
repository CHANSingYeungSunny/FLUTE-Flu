# R1-B PAPER-REPRODUCTION PILOT — REPORT

Generated 2026-10-06. Authorization: **0.30 GPU-h, new and independent.**

# PILOT VERDICT: `PILOT_ENGINEERING_FAILURE`

**The pilot did not complete, and it was stopped deliberately.** One fit failed on a real
code defect; the budget arithmetic then prohibited a retry. The defect is **diagnosed and
fixed and verified**, and the corrected implementation is ready — but it cannot be run
under the remaining allowance.

---

## 1. Slurm jobs and states

| # | Job | Horizon | State | Elapsed | GPU | GPU-h |
|---:|---|---|---|---|---:|---:|
| 1 | **607969_0** | L=24 | **FAILED** (exit 1) | 00:09:24 | 1 | **0.156667** |
| 2 | **607984_1** | L=36 | **CANCELLED** (by me) | 00:06:36 | 1 | **0.110000** |
| | | | | | | **0.266667** |

**Queue is empty. The submission loop has been killed.** No further job will be submitted.

---

## 2. GPU budget

| | GPU-h |
|---|---:|
| authorization | **0.300000** |
| consumed | **0.266667** |
| **remaining** | **0.033333** |
| measured cost of one R1-B fit | **≈0.157** (from job 607969: 564 s) |
| **cost of the remaining 4 fits** | **≈0.627** |

**0.033 ≤ 0.157.** The remaining allowance cannot fund **even one** corrected fit, let alone
four. The authorization's own rule therefore applies:

> *"A retry is permitted only after diagnosing the failure, estimating retry cost, and
> confirming total projected use remains below 0.30 GPU-hours."*
> *"Stop immediately if projected cumulative use may exceed 0.30 GPU-hours."*

`0.266667 + 0.157 = 0.4237 > 0.30` → **retry NOT permitted. Stopped.**

### Why job 607984 was cancelled rather than left to finish

It was running the **same defective code**, so it was certain to fail again — and letting it
reach its own failure would have put cumulative use at **0.2667 + 0.157 = 0.4237 GPU-h**,
**breaching the cap**. Cancelling at 6:36 was the lowest-cost action available.

---

## 3. Why the fit cost 0.157 GPU-h, not the projected 0.0533

The launcher's per-fit estimate came from **F1**, where the corrected MIFlu trains only
LoRA + head over a batch of **16** sequences. R1-B is **7× more expensive** because the
seven-channel contract expands the batch to `B*M = 2×7 = 14` sequences **per sample**:
the author's forward produces `(B*M, patch_num, D)` and R1-B then prefixes 317 text tokens,
so the LLM sees **14 x 359** positions instead of the author's **16-sample, 1-channel** view.

**The 0.0533 h/fit figure does not transfer to the seven-channel contract.** That is a
forecast error in the plan, not in the run — and it is now a measured number.

---

## 4. The engineering defect — diagnosed, fixed, verified

### Symptom
```
RuntimeError: stack expects each tensor to be equal size,
              but got [24, 7] at entry 0 and [23, 7] at entry 2
```
This occurred during **Test evaluation**, after all 20 epochs had trained successfully
(train loss 0.19 → 0.094, val 1.35 → 0.764).

### Root cause
`R1BDataset` computed its origins as `[lo, hi-L-1]` with `x = data[o : o+T]`. That formula
**ignores T entirely**, so the target slice `data[o+T : o+T+L]` ran past the end of the
966-row array — the final window came back **23 rows instead of 24**.

### The fix
`o` is redefined as the **last input index**:
```
input  = data[o-T+1 : o+1]
target = data[o+1  : o+1+L]
origins= [max(lo-1, T-1), hi-L-1]
```
This is the standard rolling-origin convention, and it matches the recovery plan's rule:
*"historical input context crossing an earlier split boundary is permitted; future targets
crossing a boundary are not."*

### Independent verification of the fix
The corrected formula reproduces the **recorded A2/R1-B origin counts exactly**:

| L | expected (train/val/Test) | corrected formula | match |
|---:|---|---|---|
| 24 | 549 / 74 / 170 | 549 / 74 / 170 | ✅ |
| 36 | 537 / 62 / 158 | 537 / 62 / 158 | ✅ |
| 48 | 525 / 50 / 146 | 525 / 50 / 146 | ✅ |
| 60 | 513 / 38 / 134 | 513 / 38 / 134 | ✅ |

**All four horizon counts match the contract that the project recorded before this pilot
existed.** That is independent confirmation that the corrected windows are the intended
ones — not a formula chosen to make a number look right.

An in-class assertion was added so an out-of-range window can never silently produce a
short tensor again.

---

## 5. What the failed run DID establish

| Evidence | Value |
|---|---|
| the R1-B trainer **runs on GPU** and trains | 20/20 epochs, train 0.19 → 0.094 |
| the model **converges** | validation 1.349 → **0.764** at epoch 20 |
| validation selection is live | per-epoch validation MSE logged, best tracked |
| the paper configuration was applied | T=104, 20 epochs, batch 16, lr 5e-4, PEFT=1, 7 channels |
| storage preflight passed on the HPC | `STORAGE_PREFLIGHT_PASS`, quota free 20.36 GiB vs a 16.58 MiB projection |
| storage postflight passed | `STORAGE_POSTFLIGHT_PASS`, no `.part` residue |
| provenance recorded | dataset SHA verified, config and declared-unexplained settings written |

**What it did not establish**: any Test metric, prediction artefact, or checkpoint — the
crash occurred before the save.

---

## 6. Required per-horizon report

| Field | L=24 | L=36 | L=48 | L=60 |
|---|---|---|---|---|
| reproduced MSE | **n/a** | n/a | n/a | n/a |
| reproduced MAE | **n/a** | n/a | n/a | n/a |
| paper MSE / MAE | 1.542 / 0.726 | 1.422 / 0.779 | 1.414 / 0.757 | 1.364 / 0.719 |
| absolute / relative difference | **not computable** | — | — | — |
| selected epoch | **not reached** | — | — | — |
| validation metric | best val **0.764** (epoch 20) — informational only, from a run that later crashed | — | — | — |
| Test metric | **not reached** | — | — | — |
| GPU-hours | 0.156667 | 0.110000 (cancelled) | 0 | 0 |
| checkpoint size | none written | none | — | — |
| trainable parameters | **1,673,496** (from the Tier-1 CPU gate) | same | same | same |
| text-path verdict | **`text_active`** (Tier-1 CPU gate, PEFT=1: `max\|Δ\|=4.63e-02`, grad `1.16e-03`) | same | same | same |

**No MSE or MAE can be reported, and none is invented.** The paper targets above are the
verified Table V MIFlu column: **1.542/0.726 · 1.422/0.779 · 1.414/0.757 · 1.364/0.719**,
four-horizon mean **1.4355 / 0.74525**.

---

## 7. Gate status at the time of submission

**All 12 pre-submission gates passed**, and none has since failed:

| Gate | Result |
|---|---|
| 1 squeue empty | ✅ |
| 2 repo `1f6563f`, git status unchanged | ✅ |
| 3 scripts match the manifest (4/4 hashes) | ✅ |
| 4 the 30 engineering gates remain valid | ✅ `T19_T20_T29_ALL_PASS = True` |
| 5 LoRA present | ✅ 12 tensors / 73,728 params, all `c_attn` |
| 6 frozen/trainable counts match the CPU gate | ✅ 49 frozen, 1,673,496 trainable (2.02 %) |
| 7 output under `$HOME` | ✅ enforced in-script |
| 8 scratch not written | ✅ read-only code root only |
| 9 quota and inode guard | ✅ free 20.36 GiB |
| 10 projected peak storage fits | ✅ 16.58 MiB vs 20.36 GiB |
| 11 four configurations immutable | ✅ array index → horizon |
| 12 independent scorer ready; text active | ✅ |

**The failure was a defect the gates could not see** — a window-construction bug in the
data loader that only manifests at the Test split. No static gate would have caught it;
running it did.

---

## 8. Storage verification

| Check | Result |
|---|---|
| preflight (quota-aware, on the HPC) | `STORAGE_PREFLIGHT_PASS` — quota free **20.36 GiB** vs a **16.58 MiB** projection |
| postflight (job 607969) | `STORAGE_POSTFLIGHT_PASS` — 2 files, **0 partial files** |
| locked-checkpoint path | enforced; the 331 MB full path is not used |
| output location | `/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/preds/` |
| scratch | never written |

---

## 9. Output directory

```
/gpfs1/home/sychan552/official_repo_reproduction_20261006/r1/
  preds/r1b__L24__rep0/{provenance.txt, train.log}
  logs/r1b_pilot_607969_0.{out,err}, r1b_pilot_607984_1.{out,err}
  manifests/PILOT_LOG.tsv, GPU_LEDGER_R1B.tsv
```

---

## 10. Recommended next action

> **Request a corrective authorization that funds a corrected re-run.**

| Item | Value |
|---|---|
| fits needed | **4** (L=24/36/48/60, one repetition) |
| **measured** cost per fit | **0.157 GPU-h** |
| base | **0.628 GPU-h** |
| +20 % retry buffer | **0.754** |
| **recommended request** | **0.80 GPU-h** |
| storage | 16.6 MiB (locked path) |
| wall clock @ `MaxJobsPU=1` | ~12 min |

The previous 0.30 request was sized from the **F1 LoRA cost**, which does not transfer to the
seven-channel contract. **The corrected request is sized from this pilot's own measurement.**

**Alternative if 0.80 is not available**: four fits cannot be run, but **one** corrected fit
(≈0.157 GPU-h) would validate the fix end to end and produce a first Table V comparison at
a single horizon. That would be a `PARTIAL` pilot, and it must be reported as one.

---

## 11. Confirmations

| Confirmation | Evidence |
|---|---|
| **no GPU job beyond the two reported** | `squeue` empty; the loop was killed |
| **the 0.30 cap was not exceeded** | 0.266667 ≤ 0.30 — the second job was cancelled specifically to keep it so |
| sealed remainders untouched | F1's 0.35 and the older 0.05639 were **not** used |
| **no Historical Track B artifact modified** | 19 `innovation_deploy_root_v3_*` directories intact; `results/v3_clean` 1,485 files unchanged |
| **F1 unmodified** | 29/29 artefacts byte-identical |
| **the original DOCX unmodified** | SHA-256 `9c573f48fb65e590c7973223d6cb5e0ab74e2dfa4f6df11ec936f980a6b50ead` |
| pre-audit deliverables | 66/66 byte-identical |
| author source tree | 0 insertions, 0 deletions |
| **no fabricated numbers** | every "reproduced" cell above says **n/a**; nothing was invented |

## 12. Not begun, as instructed

Ten-repetition expansion · R1-C sensitivity · Tier-2 experiments · the historical 1025-row
MIFlu retraining · the 4-vs-4 replacement · DOCX generation. **None was started.**