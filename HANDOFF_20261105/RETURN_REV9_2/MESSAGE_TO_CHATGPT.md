# MESSAGE TO CHATGPT — rev9.2 return, 2026-11-05T16:30:00Z / 2026-11-06 00:30 HKT

**Status: IN-PROGRESS — but O1 is now unblocked and running. Do not treat this as a completed scientific result.**

NEW: a measured CPU export path produces full 7-channel MIFlu tensors from the
40 existing checkpoints (pilot 740312 validated: `(170,7,24)`, finite, 345 s/cell,
CSV↔NPZ test target equality 1.776e-15). Full array 740344 is running on `tiny`
compute nodes. This bypasses the gpu_a100 queue prediction of 11-07. Do NOT
claim a leaderboard or new statistics until all 40 tensors land and both panels
are recomputed from identical target populations.

Read first: `RETURN_STATUS.json`, `SCIENTIFIC_AUDIT.md`, `PROTOCOL_DEVIATIONS.md`,
`COMMANDS_EXECUTED.csv`, `PANEL_DEFINITION.json`, `VALIDATION_RESULT.json`.
Extract `RETURN_TO_CHATGPT.zip` and `RAW_EVIDENCE.zip` into the SAME root.

## What changed since the last return

- Live counts: core **160/160**, national **1080/1120** (not 117/139/141).
- 40 cells blocked by an HF cache **layout** mismatch; root cause fixed and one
  distinctly-labelled rerun submitted (740183), still PENDING.
- 7-channel MIFlu recovery: 0/40 tensors; job 739549 PENDING to 2026-11-07;
  a measured 1-cell CPU pilot (740296) is running on a compute node to find a
  faster path. **This follows the new hard rule: no model work on the login node.**
- `legacy_done.tsv` 189/189 is a DONE-label artifact, not completion — last 50
  tasks `rc=3 / skip.impossible`. Do not use it in the rewrite.
- A new versioned scoring spec `PANEL_DEFINITION.json` was created AFTER execution
  and is explicitly disclosed as retrospective. Original `PROTOCOL_LOCK.json`
  (frozen:false) preserved unchanged.
- All project deliverables were replaced with the supplied rev9.2 full-project
  artefacts (hash-verified); the Chinese main report and `report_internal_qa_zh`
  companion remain separate, Q01–Q25 preserved.

## What is still missing (do not write as findings)

Harmonised leaderboard, both accuracy panels, event-level peaks, paired statistics
and a new Holm family, ablation predictive trend, regional/rolling-origin validity,
CDC calendar/vintage, numerical-foundation controls, resource measurements, O2.
Each has an explicit blocker in `RETURN_STATUS.json` and an exact command in
`COMMANDS_EXECUTED.csv`.

## Instructions for the rewrite

Do not force the historical 28-arm/136-pair numbers onto new panels; keep them
labelled as an earlier snapshot. Do not infer equivalence from non-rejection,
text/training causality from fixed-weight CPU checks, or seasonal probability from
4/16 screens. Do not turn scheduler status into journal findings. Do not claim
JBHI readiness from formatting, completion or a validator PASS.
Preserve FYP metadata (BEng Computer and Data Engineering, EE4080, 2026/27 A) and
the required blank meetings / weekly-hours fields.
