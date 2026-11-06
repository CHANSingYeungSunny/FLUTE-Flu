# Scientific audit — 2026-11-06

## Supported

| Claim | Evidence |
|---|---|
| National common panel is complete at the cell level | `cellok.py count all/export all/cells_all.tsv` = 1120/1120 |
| MIFlu seven-channel recovery is coherent | all 40 7ch NPZ `target` arrays equal the NLinear targets exactly (shape, values, `target_start_row`, max diff 0.0) |
| New leading MSE order | all-valid: MIFlu 1.7944 < PatchTST 1.9521 < NLinear 2.0782; crop: 1.4994 / 1.6352 / 1.9027 |
| Crop panel reproduces the old mean | MIFlu crop 1.4994 vs historical 1.4995 |
| MIFlu and PatchTST lead step-level peak passes | MIFlu 252/1680 (15.0%), PatchTST 215/1680 (12.8%), NLinear 57/1680 (3.4%) |
| Event detection separates from timing/height | iTransformer 99.1% detection but PIE 71.2%; MIFlu 98.8% detection, PIE 30.4% |
| No monotonic depth trend | K4 1.4989, K6 1.5457 (n=10), K2 1.5813, K8 1.6124, no_lora 1.6330, K12 1.7604 |
| Regional Table VI has valid aggregate rows | 53/53 `mse_z` rows after rerunning L13/s2030 and L15/s2026 |

## Contradicted / not reproduced

1. **Historical “NLinear is the peak champion”.** On the harmonised 1120 panel, NLinear has
   57/1680 step passes (3.4%), far below MIFlu (252) and PatchTST (215). The historical 16-unit
   table is a different scoring population and must not be silently replaced.
2. **Historical “monotonic depth trend”.** The 60-cell ladder is non-monotonic; K4 is best,
   K12 worst.
3. **Legacy DONE = valid (partly corrected).** Direct seven-channel recomputation from the raw
   NPZ validates **802 / 1,020** walk-forward rows; **218** have no NPZ. The stored `metrics.csv`
   had 329 non-finite values, but those rows are recovered by recomputation. 218 missing cells
   remain and must not be called complete.

## Partial / exploratory

- Paired Wilcoxon + Holm on 28 models (378 pairs): 349 rejections, min adjusted p ≈ 6.9e-10.
  Cells share the national series and overlapping targets; this is **exploratory**, not
  independent-sample confirmation.
- Seed-cluster bootstrap (1,000 resamples over the 10 seeds) for all 378 pairs:
  **359 / 378 95% CIs exclude zero**. This addresses seed-level dependence but **not** the
  overlapping lengths/targets within a seed; still not a confirmatory inference.
- Walk-forward means are partial (n varies; MIFlu n=22 only).
- Regional means are 10-variable `mse_z`, not comparable to the 7-channel national means.

## Blocked / not executed

| Item | Reason |
|---|---|
| `final_llm_import` | legacy lane returns `idle-no-work`; 1 TODO remains, no output |
| Full Table VI | 2 of 53 regional cells missing |
| Full walk-forward | 547 cells non-finite or missing |
| Numerical foundation models (Chronos/TimesFM) | not implemented/pinned in this run |
| CDC calendar/vintage | not reconstructed; peaks are retrospective |
| JBHI template/fees/AI disclosure | not re-verified against live selector |
| Resource measurements | no new measured wall/VRAM/latency table |
| v7 reports and return ZIP | not rebuilt |

## Bottom line

The **new 1120-cell national panel is real and scores differently from the historical snapshot**,
especially on peak skill. Table VI is largely valid; walk-forward is not. No new manuscript
result should be written until the v7 documents and return package are rebuilt and the
exploratory statistics are labelled as such.
