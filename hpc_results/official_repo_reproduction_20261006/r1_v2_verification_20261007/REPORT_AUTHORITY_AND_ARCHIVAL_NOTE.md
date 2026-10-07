# REPORT AUTHORITY AND ARCHIVAL NOTE

Generated 2026-10-07. Records which report is authoritative, which is
historical, and why.

---

## Current authoritative report

```
results/v3_clean/analysis/reports/
MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版.docx
```

- sha256 `f41652ff3d108575a9e93d789810f2fd0d345bb3b8536f14a5367922691f57ef`
- 44,675 bytes
- describes **Track C** — the author-966 strict-containment eight-model
  one-time-Test championship — and **Track R** (R1-B, `PARTIAL_REPRODUCTION`)
- this is the report that states the current conclusion

## Historical report (archived, not deleted)

```
results/v3_clean/analysis/reports/archive/
MIFlu_非LLM与LLM流感预测最终报告_中文版_旧版_历史1025行实验.docx
```

- sha256 `9c573f48fb65e590c7973223d6cb5e0ab74e2dfa4f6df11ec936f980a6b50ead`
- 1,372,896 bytes — **byte-identical to the original**, verified after copying
- the original remains in place at
  `results/v3_clean/analysis/reports/MIFlu_非LLM与LLM流感预测最终报告_中文版.docx`
  with the same sha256; it was **copied, not moved, and not altered**

## Classification

The archived report is:

```
SUPERSEDED_HISTORICAL_REPORT
```

**Not** "false". Its statements were accurate for the experiment it described.
It is superseded because its conclusions apply to a **different**:

| axis | archived report | current report |
|---|---|---|
| dataset | 1025-row July-2026 snapshot | 966-row author file (Table II 7/7) |
| MIFlu implementation | project self-built reconstruction | official repository, corrected R1-B |
| split / window contract | 717/102/206, target-start rule (boundary-contaminated) | 676/97/193, strict containment |
| final Test scope | three frozen models (gpt2_miflu, nlinear, seasonal_naive) | all eight models |
| champion basis | Validation ranking + a three-model Test | one-time Test over eight models |

## Why it is preserved

- it is the only record of the pre-official-repository project
- it documents the 1025-row historical dataset, the self-built MIFlu, the old
  Wave-1 validation ranking and the earlier NLinear Test conclusion
- it is the baseline against which the historical Track H work is described

## Why it is superseded

Because the dataset, the model implementation, the split/window contract and the
Test scope all changed. Absolute MSE values are **not** comparable across the
two reports, and the archived report must not be cited for the current
championship or for the current paper-reproduction verdict.

## Track mapping

| report | tracks described |
|---|---|
| archived (`…中文版.docx`) | Track H — 1025-row historical experiment |
| current (`…官方仓库966行严格测试冠军版.docx`) | Track C (championship) + Track R (R1-B, `PARTIAL_REPRODUCTION`) |

## Handling rules

- the archived copy is **read-only** in practice; do not edit it
- do not present the archived report as the current conclusion
- when citing its numbers, label them **Track H / historical 1025-row**
- do not delete it