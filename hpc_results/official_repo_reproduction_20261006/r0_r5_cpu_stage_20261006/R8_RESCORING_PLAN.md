# R8 — RESCORING PLAN

## Can the seven historical models be rescored?

| Question | Answer |
|---|---|
| do prediction artefacts exist locally? | **YES** — the final Test has **84 run directories** of `test_predictions.csv` under `results/v3_clean/test_eval/results/` |
| are they re-scorable? | **YES** — CSV predictions plus the frozen evaluator |
| do they need re-scoring? | **NO** for their own metrics. The **ranking** is re-aggregated with one new row |
| do any need retraining? | **NO** |
| what about Stage C (Wave-1 validation)? | 580 accepted rows; re-aggregated the same way |

## The one-scorer rule

Both sides must be scored by the **same** evaluator. The historical evaluator is
`clean_metrics.py`; the F1/R1-B evaluator is `scorer_f1.py`. Two options:

| Option | Assessment |
|---|---|
| **A (recommended)** re-score the seven historical prediction CSVs with `scorer_f1.py` | puts both sides on one implementation, at **zero GPU cost**; requires converting CSV -> the NPZ schema |
| B keep the historical evaluator for the seven and use `scorer_f1` for MIFlu | **rejected** — two metric implementations in one ranking is exactly the class of error this project has already been burned by |

## Verification steps before any aggregation

1. the seven historical prediction files load and carry `(origin, lead, variable)`;
2. the new MIFlu artefact carries **the same** `var_cols`;
3. **origin sets are identical** across all eight models at each horizon;
4. no duplicate `(model, horizon, seed)` keys;
5. the partition invariant `wins_A + wins_B + ties == n_cells` holds for every pairwise test;
6. the seasonal-naive reference used by the historical track is the **safe** formula
   (`clean_metrics.py` clamps) — **it is**, so no correction is needed there.

## Cost

Pure CPU. **Zero GPU-hours.**
