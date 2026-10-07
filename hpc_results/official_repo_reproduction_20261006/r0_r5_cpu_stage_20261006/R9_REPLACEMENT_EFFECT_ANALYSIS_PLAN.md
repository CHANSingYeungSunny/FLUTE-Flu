# R9 — REPLACEMENT EFFECT ANALYSIS PLAN

## The question

> Does replacing the historical self-built MIFlu with an official-repository-based MIFlu
> change the metrics, the ranking, or the conclusions?

## Eight things to measure, per the objective

| # | Quantity | Method |
|---|---|---|
| 1 | **MSE** | old vs new MIFlu `average_MSE_4L`, per horizon and aggregate |
| 2 | **MAE** | same |
| 3 | **per-horizon ranking** | rank of all eight at each L, old vs new |
| 4 | **overall ranking** | the 8-model rank table, old vs new, with rank deltas |
| 5 | **LLM-side average** | mean over the four LLM entries, old vs new |
| 6 | **non-LLM-side average** | mean over the four non-LLM entries (unchanged by construction) |
| 7 | **statistical conclusions** | paired cell tests with the **corrected** win direction (`A wins iff diff < 0`), plus the partition invariant |
| 8 | **computational cost** | training GPU-hours, inference time, **checkpoint storage** (this is where the reduction techniques matter) |
| 9 | **report conclusions** | which statements in the DOCX change, and how |

## The two results that must both be reported

| Stage | Old | Expected effect |
|---|---|---|
| C — Wave-1 validation | `gpt2_miflu` **1st** (0.771) | does the official MIFlu still win validation? |
| D — one-time Test/Holdout | `gpt2_miflu` **lost** to `nlinear` (3.0505 vs 2.7389) | does it still lose? |

**Reporting only one of these is selective reporting.** They already disagree, so the
replacement's effect on their disagreement is itself the finding.

## Group summaries are secondary

The four LLM and four non-LLM entries are a **fixed, deliberately chosen selection, not a
random sample**. Group means may be **described**; they may **not** be used to infer anything
about "LLMs" or "non-LLMs" as categories. And the group mean and the best-in-group already
point in opposite directions in the historical data, so **both must be shown**.

## Required uncertainty treatment

- per-seed values retained, not only aggregate means;
- paired differences computed at **common forecast origins**;
- block resampling over **consecutive origins**, not independent cell resampling;
- the historical Test is **exposed and retrospective** — it cannot become fresh evidence.
