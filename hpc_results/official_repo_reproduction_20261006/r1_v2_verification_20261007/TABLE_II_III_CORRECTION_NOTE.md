# CORRECTION NOTE — TABLES II AND III WERE NEVER MISSING

Issued 2026-10-07, after the user challenged the `UNREADABLE` classification.

---

## What I claimed, and why it was wrong

I stated repeatedly — in `PAPER_WIDE_RESULT_INVENTORY.csv`,
`PAPER_LEVEL_REPRODUCTION_VERDICT.md`, `CPU_STAGE_FINAL_STATUS_EN.md`, the R1-B
report and the Track C report — that **Tables II and III were unreadable**,
because "PDF page 5 was never rendered" and "all cell values are images absent
from the text layer".

**That was wrong.** Both tables are present, with complete numeric values, in:

```
reference_papers/MIFlu_Large_Language_Model-Based_Multimodal_Influenza_Forecasting_Scheme.md
  TABLE II   line 158
  TABLE III  line 169
```

## Root cause — a search error, not a source limitation

My evidence for "unreadable" was a search I ran as:

```bash
grep -rln "Table III\|TABLE III" --include="*.md" . | head -8
```

**There are 12 matching files.** `head -8` truncated the list, and
`reference_papers/…Scheme.md` was **#12**. I then treated a truncated list as a
complete one and asserted a negative conclusion from it.

The upstream `PAPER_TABLE_CELL_MASTER.csv` also carries `UNREADABLE` for all of
Table III — so the error was inherited from an earlier stage as well, but I
repeated and amplified it without re-checking, and I filled in a confident
blocker string ("Must not be guessed") that made a search failure look like a
documentary fact.

**The generalisable lesson:** a truncated result is not evidence of absence, and
a grep whose output was cut short must never be used to assert that something
does not exist. This is the same class of error as the two key bugs found
earlier in the project — a check that silently returned a smaller answer than
the truth.

## What is actually true

### Table II — national descriptive statistics

Re-verified **against the printed values** (previously the 7/7 claim rested on
values of unstated provenance):

| var | Avg (paper) | Avg (966-row) | dev | Max (paper) | Max (data) | SD (paper) | SD (data) | dev |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 1.851 | 1.851 | 0.02 % | 7.715 | 8 | 1.342 | 1.342 | 0.03 % |
| 2 | 1.845 | 1.845 | 0.01 % | 7.780 | 8 | 1.308 | 1.308 | 0.03 % |
| 3 | 3434.814 | 3434.814 | 0.00 % | 24097 | 24097 | 3152.330 | 3152.330 | 0.00 % |
| 4 | 4981.128 | 4981.128 | 0.00 % | 45513 | 45513 | 5950.799 | 5950.799 | 0.00 % |
| 5 | 13540.720 | 13540.716 | 0.00 % | 111361 | 111361 | 15003.120 | 15003.122 | 0.00 % |
| 6 | 1608.262 | 1608.262 | 0.00 % | 3453 | 3453 | 681.227 | 681.227 | 0.00 % |
| OT | 651497.500 | 651497.460 | 0.00 % | 1640587 | 1640587 | 348838.200 | 348838.190 | 0.00 % |

**7/7 match, maximum deviation 0.03 %** (population SD). This is now a direct,
independent confirmation that **the 966-row author file is the paper's dataset** —
which is the load-bearing premise of both R1-B and Track C. The premise was
always correct; what was missing was the verification, and it now exists.

### Table III — US-Region descriptive statistics

Fully available: 10 regions × (Average, Max, SD) plus a Total row
(Total: 1,072.780 / 30,282 / 1,949.170). Status changed from `UNREADABLE` to
**`VERIFIED_AVAILABLE`**.

**What this does not change:** Table III is *descriptive statistics*. The
underlying **US-Region data is still unreleased**, so the statistics cannot be
recomputed, and **Table VI (regional forecasting results) remains
`BLOCKED_BY_MISSING_DATA`**. Availability of Table III does not unblock Table VI.

## Records corrected

- `paper/PAPER_WIDE_RESULT_INVENTORY.csv` — TBL-II and TBL-III rows
- `PAPER_LEVEL_REPRODUCTION_VERDICT.md` — §2 rows and the "unread" sentence
- `CPU_STAGE_FINAL_STATUS_EN.md` — the Tables II/III row

## Records still to correct

- the Track C report's blocked-items sentence and the v2 report (both still
  in progress; the v2 report will carry the corrected status)
- `paper/PAPER_TABLE_CELL_MASTER.csv` — its `UNREADABLE` rows for Table III are
  superseded by the transcription and should be relabelled