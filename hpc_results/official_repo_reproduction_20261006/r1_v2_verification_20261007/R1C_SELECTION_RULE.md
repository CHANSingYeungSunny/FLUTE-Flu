# R1-C — FROZEN SELECTION AND EVALUATION RULE

Frozen 2026-10-07 **before any R1-C fit was submitted**. Not modifiable after
results are seen.

---

## 1. Candidate set

Frozen to **two entries**: `C0_R1B_REFERENCE` (the existing R1-B result, no new
compute) and **`C1_released_type1_scheduler`** (the only evidence-supported
change; see `R1C_DOCUMENTARY_EVIDENCE.md` §2).

No candidate may be added after execution begins.

> **Documented inconsistency (2026-10-07, post-execution).** The frozen matrix
> `R1C_FROZEN_CANDIDATE_MATRIX.csv` describes C0 as a **12-fit run** at seeds
> 1000/1001/1002, not as "no new compute". The two frozen documents therefore
> disagree on the C0 row. **Execution followed the matrix**, because re-running
> the reference at matched seeds is the more conservative choice: it replaces a
> single-repetition reference with a 3-seed mean, which is what makes the C1-vs-C0
> comparison statistically meaningful (see `PAPER_GAP_COMPARABILITY_AUDIT.csv`,
> blocking violation `same_seed_policy`).
>
> This text is **not** amended to match reality. It is recorded here so that the
> divergence is visible. Neither document has been edited to remove the
> discrepancy, and no candidate was added, removed or re-parameterised after any
> result was seen.

## 2. What C1 changes — and only this

```
lr(epoch) = 5e-4                      if epoch <  3
          = 5e-4 * 0.9 ** (epoch-3)   if epoch >= 3
```

`epoch` is 1-based, matching the released `adjust_learning_rate` call
`adjust_learning_rate(model_optim, epoch + 1, args)` where the loop variable is
0-based — i.e. the released code passes `epoch+1`, so its `epoch` argument is the
**1-based** epoch number.

Everything else is byte-identical to the frozen R1-B configuration:
`T=104, epochs=20, batch=16, lr0=5e-4, Adam, LoRA r=4 on c_attn, PEFT=1,
effective freeze, 7-channel target, author text asset, strict containment,
validation-only checkpoint selection, Test read once`.

## 3. Selection rule (how a candidate is judged)

1. **Validation** selects the checkpoint within each fit. Test is **not** read.
2. Test is read **once per fit**, after the checkpoint is frozen.
3. A candidate is summarised by its **mean `average_MSE_4L` over the three
   seeds**, exactly as the reference.
4. Comparison is **C1 vs C0** on the same three seeds and four horizons.

## 4. Success criterion (predeclared, not movable)

```
relative error vs paper = (mean_MSE_4L - 1.4355) / 1.4355 * 100

WITHIN_5_PERCENT_EVIDENCE_SUPPORTED   if relative error <= 5.00 %
IMPROVED_BUT_ABOVE_5_PERCENT          if 5 % < relative error < 35.68 %
NO_EVIDENCE_SUPPORTED_IMPROVEMENT     if relative error >= 35.68 %
CONTRACT_NOT_IDENTIFIABLE             if the contract cannot be matched to the paper
NOT_REPRODUCIBLE_WITHIN_5_PERCENT_FROM_RELEASED_ARTIFACTS
                                      if no evidence-supported candidate can reach 5 %
```

A `WITHIN_5_PERCENT` claim additionally requires, at that point:
**all four horizons** inside ±0.10 of the paper value, **both MSE and MAE**,
**three repetitions**, independent scoring, `text_active`, valid LoRA, valid
freezing, and a valid key contract. A single horizon or a single lucky seed
**does not count**.

## 5. Prohibitions

- no tuning of T, epochs, batch, lr, LoRA rank or targets
- no modification of Track C
- no use of Track C Test results to choose R1-C settings
- no candidate invented without documentary support
- no discarding of a poor-performing candidate from the report
- no selection of "the result closest to the paper" as the finding

## 6. Reporting

**All** candidates are reported, including C1 if it is worse than C0.

## 7. Effect on the championship

**None.** The Track C champion is frozen and is not revisited regardless of the
R1-C outcome. R1-C concerns Track R only.