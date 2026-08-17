# ChatTime Variant (Phase 2 — ISOLATED, NON-DEFAULT)

This directory isolates the **ChatTime-style L=52 walk-forward** pipeline
(`generate_walkforward.py`). It is **NOT** part of the MIFlu (IEEE JBHI 2025)
reproduction deliverable.

## Why it exists
The Fix Brief requires the MIFlu reproduction to use the **paper protocol**
(`scripts/train_miflu.py`): `T=104`, `L ∈ {24,36,48,60}` evaluated as four
independent runs, static `70:10:20` split, `shuffle=False`. The L=52
walk-forward protocol is a *different* evaluation scheme (used by ChatTime) and
was the source of the earlier non-comparable numbers. We keep it only for the
Phase 2 ChatTime-backbone comparison, so the two protocols can never be the
default/active path for the MIFlu paper.

## Contents
- `generate_walkforward.py` — produces
  `results/ili/miflu_fulltest_walkforward.csv` (date, ground_truth, prediction)
  using the N=7 L=52 checkpoint (`checkpoints/best_miflu_L52.pth`).
- Indicator / figure scripts for the walk-forward CSV are likewise kept here
  (add them as Phase 2 proceeds) and must NOT overwrite the paper-protocol
  tables under `data/results_miflu_paper_protocol_*.csv`.

## Usage
```bash
python scripts/chattime_variant/generate_walkforward.py \
    --ckpt checkpoints/best_miflu_L52.pth
```

## Naming convention (avoid confusion)
| Artifact | Protocol |
|----------|----------|
| `data/results_miflu_paper_protocol_*.csv` | MIFlu paper protocol (DEFAULT) |
| `results/ili/miflu_fulltest_walkforward.csv` | ChatTime L=52 walk-forward (ISOLATED) |
