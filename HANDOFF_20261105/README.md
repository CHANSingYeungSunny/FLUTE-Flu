# HANDOFF 2026-11-05 — where everything is

This folder is the **submission/handoff package** for ChatGPT. It was previously only in
`C:\Users\Asus\Desktop\FYP code\_review_20261104\`; it is now copied inside the project so it
is visible here.

## Send these two files

| File | Purpose |
|---|---|
| `RETURN_TO_CHATGPT.zip` | Human-readable return package: run ledger, metrics, v6 reports, scheduler fix, evidence index |
| `RAW_EVIDENCE.zip` | Real per-cell evidence (predictions/npz/metrics/manifests/logs) |

Unzip both into the **same** directory to restore the full tree.

- `RETURN_TO_CHATGPT.zip` — 7,299,432 B — SHA-256 `40391F43D712BB98CF4F6E97131FEAADA95FBCF4D9E29786F3DB3A6BB0152841`
- `RAW_EVIDENCE.zip` — 65,761,420 B — SHA-256 `3B7F116BD591BC7AC81DFDF79659DF500A1A8B4C4196E6E4DFCF2F254DF7F0EE`

## The prompt

Copy the English block inside `MESSAGE_TO_CHATGPT.md` and send it with the two zips.
It tells ChatGPT:

- core 160/160 is complete;
- the common 1120 is **in progress at 141/1120** (not finished);
- the package ledger is a 117/1003 snapshot; see `LIVE_STATUS_DRIFT.md`;
- keep old scientific numbers, only update execution status/limitations;
- do not claim a full Track B panel or new peak numbers.

## Also in this folder

- `VALIDATION_RESULT.json` — validator PASS (structure/hash/status only, NOT scientific validation)
- `LIVE_STATUS_DRIFT.md` — why the ledger says 117 while live is 141+
- `SCHEDULER_FIX.md` — the v2 scheduler defects fixed
- `RETURN_SUMMARY.md` — package summary

## Current live state at handoff (00:15 HKT)

- Core: **160 / 160 complete**
- Common 1120: **141 / 1120**, one lane running, two `gpu_a100` lanes pending
- 13 empty `decision_tree` partial dirs; 28 quarantined partials
- Scratch **306 / 300 GB soft** (grace 10 days), hard 1024 GB
- Table VI / WF: not started; post-all adapter waits for `all/phase.done`
