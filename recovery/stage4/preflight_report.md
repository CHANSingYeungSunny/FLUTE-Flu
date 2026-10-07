# Stage 4 — CPU preflight report

Date: 2026-09-24. Environment: local Windows CPU (no GPU). No full training, no
new Test scoring, no model download.

Per Stage 4 §3, these are focused CPU checks on permitted development inputs.
Each check maps to a concrete failure risk in §3.

| # | Check | Result | Evidence |
| --- | --- | --- | --- |
| 1 | `configs` self-check (split + profiles) | PASS | `python scripts/configs.py` → `[configs] self-check OK` |
| 2 | Author & project profiles distinct; hashes + splits correct | PASS | both `verify_profile_hash` pass; `676/773` vs `717/819` |
| 3 | Target windows stay inside their assigned split | PASS | `train_nlinear_966 --preflight` split-boundary invariant |
| 4 | Training scaler uses train rows only | PASS | `ScalerBundle.fit_from_train(train_end=…)`; scaler train_end == split train_end |
| 5 | All 7 variables present & evaluated | PASS | windows are (N=7, T); `mse_all` is 7-var (mirrors `train_ablation.evaluate`) |
| 6 | NLinear == original implementation (identical weights/inputs) | PASS | `--self-check`: extracted class reproduces reference NLinear maths, max abs err `0.0e+00` |
| 7 | Different text tensors reach the corrected model | BLOCKED (needs GPT-2 cache) | prompt `date_range_string` threading is verified at build level; token-level tensor check deferred to compute node |
| 8 | Full vs no-text differ only as specified | PASS (code-level) | `no_multi` = `use_text=False`, `prompt_cache=None`; only pathway differs |
| 9 | Last Value / Seasonal Naive never read future (incl. leads 53–60) | PASS | `train_naive_966 --preflight` future-leak guard over every lead 0..59 |
| 10 | Seasonal-naive lag-52 == calendar weeks on author 966 | PASS | 966-row data is dense; `clamped references=0` |

## Command log (all CPU, all PASS)

```
python scripts/configs.py                          -> [configs] self-check OK
python scripts/train_nlinear_966.py --self-check   -> forward matches reference (err 0.0e+00)
python scripts/train_nlinear_966.py --preflight --horizon 24 --profile author_966
   profile=author_966 n=966 train_end=676 val_end=773 windows train=572 val=98 test=169
python scripts/train_nlinear_966.py --preflight --horizon 60 --profile project_1025
   profile=project_1025 n=1025 train_end=717 val_end=819 windows train=613 val=103 test=146
python scripts/train_naive_966.py --self-check
python scripts/train_naive_966.py --preflight --name seasonal_naive --horizon 60 --profile author_966
   val_windows=98, future-leak guard OK, clamped=0
python scripts/train_naive_966.py --preflight --name last_value_naive --horizon 24 --profile author_966
```

Profile threading was also verified by importing `train_miflu` /
`train_ablation`, setting `ACTIVE_PROFILE=author_966`, and calling
`load_and_normalize()` — both returned `train_end=676, val_end=773` with a
(966,7) array, and `project_1025` returned the unchanged `717/819`.

## NLinear window counts (author 966, per horizon)

| L | train | val | test |
| --- | ---: | ---: | ---: |
| 24 | 572 | 98 | 169 |
| 36 | 560 | 98 | 169 |
| 48 | 548 | 98 | 169 |
| 60 | 536 | 98 | 169 |

(window counts differ from split row counts 676/97/193; row counts are the
boundary, window counts are stride-1 windows whose target start is inside each
split.)

## Deferred to compute node (not runnable / not authorized here)

- **Check #7 (text-tensor sensitivity)** — requires the local GPT-2 cache and an
  actual forward pass; a toy substitute would be reported as a pass, which §3
  forbids. Marked BLOCKED, prepared for the authorized compute-node preflight.
- Any **Test split scoring** (naive `mse_all` on Test, NLinear test metrics) —
  this is new Test evaluation and is part of the launch, not the preflight. The
  preflight used the **validation** split only for naive shape/leak checks.
