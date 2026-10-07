# R3 FEW-SHOT AND REGIONAL — BLOCKED STATUS

Both Tier-3 families are blocked. **They must not block the controlled MIFlu replacement.**
Each gets its own verdict and is recorded, not deleted from the denominator.

## Regional (Table III, Table VI, Table IX, Figs 5, 6)

| Item | Status |
|---|---|
| **verdict** | **`BLOCKED_BY_MISSING_DATA`** |
| dataset | US-Region — "ILI in 10 HHS regions, week 40 1997 to week 18 2020" per the paper |
| released? | **NO** — the author repository ships only the national file |
| split | the paper states **50:10:40** for regional (distinct from the national 70:10:20) |
| models | ReILIF (three variants), SAIFlu-Net, Cola-GNN, CNNRNN, STNN, TFT, GPT4TS |
| horizon set | **2, 3, 5, 10, 13, 15, 20** — and L=1 is explicitly excluded because monitoring data lag at least a week |
| Table VI values | MIFlu RMSE/PCC are transcribed for all seven horizons (image-verified) |
| what would unblock it | obtaining the US-Region ILI series and the regional preprocessing |

## Few-shot (Fig. 7)

| Item | Status |
|---|---|
| **verdict** | **`BLOCKED_BY_MISSING_CONFIGURATION`** |
| training fractions | `UNRECOVERED` |
| chronological or random subsampling | `UNRECOVERED` |
| validation/Test definition | `UNRECOVERED` |
| repetition count and plotted uncertainty | `UNRECOVERED` |
| the paper's claim | MIFlu "can effectively enhance the forecasting performance of the unimodal model in the few-shot setting" |
| what would unblock it | the sampling recipe; a declared reconstruction could substitute only if labelled as such |

## Why neither blocks the primary objective

The primary question is *whether replacing MIFlu changes the historical 4-vs-4 ranking*.
That comparison is **national**. Neither the regional nor the few-shot study participates in
it. Blocking the replacement on an unreleased dataset would be a category error — and the
recovery plan already anticipated this: *"a partially reproduced result with precisely
localized blockers"* is a legitimate FYP outcome.
