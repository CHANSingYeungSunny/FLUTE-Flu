# REPORT_EN — V2 (revised timestamped copy)

Generated 2026-10-06. **This is a new file. `../REPORT_EN.md` is unchanged.**

It carries only what must be corrected plus the current conclusions; the full narrative is in
`FINAL_EXECUTION_REPORT_EN.md` and the itemised corrections are in
`STATUS_CORRECTION_ADDENDUM.md`.

## Differences from the original report (six required replacements)

| Location | Original | **Corrected** |
|---|---|---|
| §D table | `mse_mean` = 0.6044 / 0.6028 / 0.6571 / 0.6545 | those are **means over 20 epochs**; the author's `mse_mean` is the **final-epoch** Test MSE = **0.5793 / 0.5920 / 0.6088 / 0.6361** |
| §D table | the four runs tagged A1-P | they are **A0-R released-code feature-0 replays** |
| §E.2 | A2 `max\|Δ\|` = 59.6875, grad 7.13e8 | **6.518e-04 / 6.525e-02, grad 0.025178** (the old values came from feeding unstandardized input) |
| §E / §H | "Test covers feature 0 only" | **every split is univariate `(T,1)`**; the released code never builds a seven-variable window |
| §D note | "LR decays by decay_fac=0.75" | **hard-coded 0.9 from epoch 4**; `decay_fac` is inert |
| §H | "Track A extension needs ≈1.84 GPU-h" | the author configuration costs a measured **0.2769 GPU-h/fit**; 40 fits ≈ **11.08 GPU-h** |

## Conclusions that still hold

- ✅ the released code's text path is **inert** (CPU and A100 agree; positive control proves the probe has power)
- ✅ the A2 implementation's text path is **active** → the benchmark's full-vs-no-text contrast is a genuine text contrast
- ✅ **0 paper numbers reproduced**; Tables V–IX and Figures 3–7 all unreproduced
- ✅ A0-R four horizons: 0.5793 / 0.5920 / 0.6088 / 0.6361 (final epoch, 1 repetition, single channel)
- ✅ MIFlu vs NLinear indistinguishable across 12 cells (t = −0.11; MIFlu better in **7/12**), sign flips with horizon
- ✅ paired-statistics win direction corrected; four unit tests pass
- ✅ GPU ledger 2.24361 / 2.3 confirmed; 0.05639 remaining

## New facts

- **Storage**: 204.6 GiB across 19 historical directories, of which only **66.7 MiB is byte-identical** (0.032 %) — deduplication cannot relieve the quota
- **Seeds**: `--itr 10` would not produce duplicate runs (the RNG advances, giving different inits)
- **Not re-scorable**: the released code saves no predictions (`np.save` commented out) → A0-R scores cannot be independently recomputed
- **Historical family**: 0 symlinks, 0 hard links → apparent size == actual usage

## Still not claimable

❌ paper reproduced ❌ A0-R numbers beat the paper ❌ 20/5e-4 are paper settings ❌ cross-track MSE comparison ❌ historical Qwen was quantized
