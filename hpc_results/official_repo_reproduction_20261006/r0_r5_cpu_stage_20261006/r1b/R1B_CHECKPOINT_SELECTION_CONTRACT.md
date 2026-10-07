# R1B CHECKPOINT SELECTION CONTRACT

## The rule R1-B uses

> **Best validation MSE (`mse_all`, seven variables, z-space), evaluated after every
> epoch. Test is not read during the fit, and not read during selection.**

## Why it is a declared deviation

| | Paper | Released code |
|---|---|---|
| rule | **NOT STATED** | Test MSE selects the best epoch, **every epoch**: `min_mse` at L225, saved at L264. Early stopping is instantiated but its call is **commented out** (L235-236) |

The released rule reads Test during training and uses it to choose the weights, so its
scores are **Test-selected** and not a clean held-out result. R1-B therefore selects on
validation. This is **declared deviation B-5**.

## What is enforced

| Guarantee | How |
|---|---|
| Test not read during training | `dl_te` is unused inside the epoch loop |
| Test not read during selection | the best is tracked from `dl_va` only |
| selection recorded | the artefact carries `checkpoint_selection = "best_validation_mse"` |
| a Test-selected artefact is refused | `scorer_f1` rejects any artefact whose metadata mentions Test |

## Measured behaviour

Job 607887 confirmed save → reload → predict is **exactly** reproducible:
`max|Δ| = 0.000e+00` across a full forward pass, checkpoint 331,158,882 B.

## The unresolved item

**The paper's own rule is `UNRECOVERED`.** If direct evidence later shows the authors
selected on Test, R1-B's rule must be re-labelled accordingly — but until then
validation-only is the defensible choice, and the deviation is on the record.
