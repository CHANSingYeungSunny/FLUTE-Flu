# PAPER GAP — REDUCTION CALCULATION

Generated 2026-10-07. All values recomputed from persisted prediction artefacts;
none are copied from a summary.

---

## 1. The paper target

| horizon | paper MSE | paper MAE |
|---|---:|---:|
| L24 | 1.542 | 0.726 |
| L36 | 1.422 | 0.779 |
| L48 | 1.414 | 0.757 |
| L60 | 1.364 | 0.719 |
| **average** | **1.4355** | **0.74525** |

## 2. The two author-966 MIFlu results

Both are author-966, strict containment, seeds 42/43/44, 7-variable z-space,
one-time Test. They differ **only** in implementation and text asset.

### (a) Old — project self-built MIFlu (A2)

Recomputed from `pred_miflu_L{L}_s{seed}.npz` (12 artefacts):

| horizon | per-seed mean MSE |
|---|---:|
| L24 | 2.443924 |
| L36 | 1.936020 |
| L48 | 1.767731 |
| L60 | 2.018403 |
| **average_MSE_4L** | **2.041519** |

**Cross-check:** A2's own recorded figure was **2.042**. The recomputation
reproduces it, which validates the arithmetic used for both sides.

### (b) New — official-repository-based corrected MIFlu (R1-B)

`average_MSE_4L` = **1.9477** (four-horizon pilot report).

## 3. The calculation

```
paper                       = 1.4355

old absolute gap  = 2.041519 - 1.4355 = 0.606019
new absolute gap  = 1.9477   - 1.4355 = 0.512200

old relative gap  = 0.606019 / 1.4355 * 100 = 42.22 %
new relative gap  = 0.512200 / 1.4355 * 100 = 35.68 %

percentage-point reduction = 42.22 - 35.68 = 6.54 pp

relative reduction in gap = (0.606019 - 0.512200) / 0.606019 * 100 = 15.5 %
```

| quantity | value |
|---|---:|
| old relative error vs paper | **+42.22 %** |
| new relative error vs paper | **+35.68 %** |
| percentage-point reduction | **6.54 pp** |
| relative reduction of the gap | **15.5 %** |
| remaining gap | **35.68 %** |

## 4. What this does and does not mean

**It does mean:** replacing the project's self-built reconstruction with the
official repository's corrected MIFlu moved the author-966 result closer to the
paper — the gap shrank from 42.2 % to 35.7 %, i.e. 15.5 % of the original gap
was removed.

**It does not mean** the paper is reproduced. The result remains **35.7 % above**
the paper's four-horizon average MSE, and **zero of four horizons** entered the
predeclared ±0.10 MSE band. The paper-level verdict stays `PARTIAL_REPRODUCTION`.

**Two honest qualifications.**

1. **This is not "the same model improved."** The two results are different
   implementations — a self-built reconstruction versus the author's
   architecture. The comparison measures which implementation sits closer to the
   paper, not a tuning gain within one model.
2. **The text asset differs too** (declared deviation D2: the project's prompt
   encoder versus the author's `text_emb_label_0507_<L>.txt`). So the 15.5 %
   gap reduction is attributable to the *combined* change of implementation and
   text asset, not to the architecture alone. Separating the two would require a
   further controlled run and has not been done.

## 5. Wording used in the report

> The current evidence-based official-repository reconstruction remains
> approximately **35.7 %** above the paper's reported four-horizon average MSE.

**MSE is not accuracy.** "35.7 %" is a relative error in a squared-error metric
against a reported value. It is **not** a model accuracy percentage, and a
"35.7 % less accurate" reading would be wrong.

## 6. Comparability

See `PAPER_GAP_COMPARABILITY_AUDIT.csv`. The two runs are comparable on dataset
(identical sha256), split, variables, metric space, horizons, pooling, seeds,
window rule, containment flag, checkpoint policy and Test scope. They differ in
implementation and text asset — the difference the comparison exists to measure.