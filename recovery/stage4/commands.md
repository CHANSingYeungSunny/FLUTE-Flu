# Stage 4 — executable commands (reduced matrix)

Status: **READY_FOR_AUTHORIZED_LAUNCH**. Commands below are checked against the
implemented runners and the frozen A2 protocol; **none have been run**. They must
be submitted from a GPU compute node only (never the login node), and only after
the launch decisions in `launch_decisions.md` are recorded as authorized.

Reduced matrix: **44 launchable records** (36 learned + 8 deterministic) + 1
BLOCKED (A0). Seeds = `[42, 43, 44]` (first three of the frozen 10-seed list).
Selection metric = `average_MSE_4L` = mean of `mse_all` (7-var, z-space) over
L ∈ {24,36,48,60}; Test scored once after selection.

## A2-MIFlu (corrected MIFlu, full text, LoRA r=4) — 12 fits

```bash
for L in 24 36 48 60; do
  for S in 42 43 44; do
    python scripts/train_miflu.py --horizon $L --seed $S --reps 1 \
      --epochs 20 --batch 16 --profile author_966 \
      --export-dir results/stage3_a2/author_966/miflu/ \
      --ckpt-dir   results/stage3_a2/ckpt/author_966/miflu/
  done
done
```

## A2-NOTEXT (`no_multi`: no text, LoRA kept) — 12 fits

```bash
for L in 24 36 48 60; do
  for S in 42 43 44; do
    python scripts/train_ablation.py --variant no_multi \
      --horizon $L --seed $S --reps 1 --epochs 20 --batch 16 \
      --profile author_966 \
      --export-dir results/stage3_a2/author_966/notext/
  done
done
```

## A2-NLIN (NLinear) — 12 fits

```bash
for L in 24 36 48 60; do
  for S in 42 43 44; do
    python scripts/train_nlinear_966.py --horizon $L --seed $S \
      --profile author_966 \
      --export-dir results/stage3_a2/author_966/nlinear/
  done
done
```

## A2 naive (Last Value + Seasonal Naive) — 8 deterministic evals

```bash
for L in 24 36 48 60; do
  python scripts/train_naive_966.py --name last_value_naive --horizon $L \
    --profile author_966 --export-dir results/stage3_a2/author_966/naive/
  python scripts/train_naive_966.py --name seasonal_naive --horizon $L \
    --profile author_966 --export-dir results/stage3_a2/author_966/naive/
done
```

## A0 — released-code diagnostic (1 fit) — BLOCKED

```bash
# from recovery/author_repo/, on a GPU node, after D-a0-env is resolved:
python main_ILI_lora.py --pred_len 24 --seq_len 104 --patch_size 24 --stride 2 \
  --gpt_layers 6 --d_model 768 --itr 1 --train_epochs 20 --batch_size 16 \
  --learning_rate 0.0001
# released defaults: --multimodal 0 --PEFT 0 --freeze 1 --pretrain 1
```

## Aggregation (after the matrix completes; CPU)

The frozen selection metric `average_MSE_4L` is the mean of each run's
`mse_all` (7-var z-space) over the four horizons. Each runner already writes a
`metrics.csv` with per-(L, seed) `mse_all`; a small aggregation step computes the
per-model `average_MSE_4L`. Naive rows report a single deterministic value per
horizon (mapped to the seed-42 cell; `stochastic_seed_applicable=false`).
