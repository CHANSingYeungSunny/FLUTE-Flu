# Stage 3 — exact commands (prepared, NOT executed)

Statuses: `READY` = runnable now on GPU; `BLOCKED_PENDING_PATCH` = requires the
unapplied `author_data_adapter.patch` (or a new runner) first; `BLOCKED` =
awaiting supervisor/environment decision. **No command below has been run.**
Generation scripts must not auto-submit to the scheduler.

Entry points verified against the workspace:

| Entry point | Supported args | 966-row capable? |
| --- | --- | --- |
| `scripts/train_miflu.py` | `--horizon --reps --epochs --batch --seed --export-dir --ckpt-dir` | **NO** (assert_full_window + derive_split refuse 966) |
| `scripts/train_ablation.py` | `--variant --recipe --early-stop --patience` | **NO** (same guards) |
| `scripts/train_baseline.py` | GPT4TS unimodal (NOT NLinear) | no 1025 guard, but wrong model + own DATA_PATH |
| `main_ILI_lora.py` (author repo) | author defaults | YES (own 966-row data) — but is A0, not A2 |

---

## A0 — released-code diagnostic (1 fit)

```
# on a GPU compute node, from recovery/author_repo/:
python main_ILI_lora.py \
    --pred_len 24 --seq_len 104 --patch_size 24 --stride 2 \
    --gpt_layers 6 --d_model 768 \
    --itr 1 --train_epochs 20 --batch_size 16 \
    --learning_rate 0.0001 \
    # --multimodal 0 --PEFT 0 --freeze 1 --pretrain 1   (released DEFAULTS)
```

Status: **BLOCKED** (`D-a0-env`). Requires: (a) a GPU node, (b) confirm gpt2
base weights are present in the author repo's expected cache, (c) confirm the
author data path `dataset/illness/national_illness.csv`. The `--multimodal 0`
default means the missing text-embedding file (`text_emb_label_*.txt`) is NOT
touched. Expected output: feature-0 (weighted ILI) Test MSE, Test-in-loop.

Note: A0's metric is a single-variable weighted-ILI number, NOT a seven-variable
benchmark. Do not compare it numerically to A2.

---

## A2 — controlled author-data comparison (36 learned + 8 naive fits)

All A2 commands require `author_data_adapter.patch` applied (adds
`--profile author_966`). They are `BLOCKED_PENDING_PATCH` until then.

### A2-MIFlu (corrected MIFlu, full text, LoRA r=4) — 12 fits

```
for L in 24 36 48 60; do
  for S in 42 43 44; do
    python scripts/train_miflu.py --horizon $L --seed $S --reps 1 \
      --epochs 20 --batch 16 \
      --profile author_966 \
      --export-dir results/stage3_a2/author_966/miflu/ \
      --ckpt-dir results/stage3_a2/ckpt/author_966/miflu/      # BLOCKED_PENDING_PATCH
  done
done
```

### A2-NOTEXT (no_multi: no text, LoRA kept) — 12 fits

```
for L in 24 36 48 60; do
  for S in 42 43 44; do
    python scripts/train_ablation.py --variant no_multi \
      --horizon $L --seed $S --epochs 20 --batch 16 \
      --profile author_966 \
      --export-dir results/stage3_a2/author_966/notext/ \
      --ckpt-dir results/stage3_a2/ckpt/author_966/notext/    # BLOCKED_PENDING_PATCH
  done
done
```

`no_text` definition: `use_text=False`, `prompt_cache=None` -> single zero token.
Sequence length and patch positions differ from `full`; this measures the whole
text pathway, not a matched-length content control.

### A2-NLIN (NLinear) — 12 fits

```
# requires NEW runner scripts/train_nlinear_966.py (see author_data_adapter.patch
# and configs/a2_new_runners.json). No such entry point exists today.
python scripts/train_nlinear_966.py --horizon $L --seed $S \
  --profile author_966 \
  --export-dir results/stage3_a2/author_966/nlinear/            # BLOCKED_PENDING_PATCH
```

### A2 naive (Last Value + Seasonal Naive) — 8 deterministic evals

```
# requires NEW runner scripts/train_naive_966.py (see patch). Deterministic.
python scripts/train_naive_966.py --name last_value_naive --horizon $L \
  --profile author_966                                            # BLOCKED_PENDING_PATCH
python scripts/train_naive_966.py --name seasonal_naive --horizon $L \
  --profile author_966                                            # BLOCKED_PENDING_PATCH
```

---

## B — refreshed snapshot (already run) — no new fits proposed

`scripts/train_miflu.py --reps 10 --epochs 20 --batch 16 --seed 42` (1025 rows)
was already run (8-17); v3_clean froze the selection. No B rerun is proposed
unless the supervisor orders a gap-repair rerun (see spec §B).

## C — holdout (exposed) — no new Test evaluation

No C command is proposed. The original holdout is `EXPOSED`; no untouched
interval has been identified.

---

## Verification commands that are permitted NOW (CPU-only, no training)

```
# profile isolation: author 966 vs project 1025 hash + calendar
python recovery/stage3/gap_consequence_check.py

# calendar canonicalisation self-check
python -c "import sys; sys.path.insert(0,'scripts'); import cdc_calendar as c; c._self_check(); print('cdc_calendar OK')"

# frozen seed list + selection metric
python -c "import json; d=json.load(open('results/v3_clean/analysis/frozen_analysis_protocol.json')); print(d['seeds'], d['selection_rule']['ranking_metric'])"
```
