# Protocol deviations — 2026-11-05T16:30:00Z / 2026-11-06 00:30 HKT

1. **Original `PROTOCOL_LOCK.json` had `frozen: false` when the 1120 matrix was submitted.**
   Preserved unchanged; nothing back-dated. All comparisons are retrospective/exploratory,
   not prospective confirmation. (`do_not_backdate_freeze: true`)
2. **New scoring spec created after execution** — `PANEL_DEFINITION.json` v1, timestamped
   2026-11-05T16:30:00Z. Historical test outcomes were already inspected; disclosure is explicit.
3. **Profile split**: MIFlu cells use `author_repo_966`, all others `author_966`.
   Byte hashes differ; numeric identity measured 0.0 over 7 aligned channels. This is a
   cross-model comparability caveat, not a resolved equality of metadata/calendar.
4. **MIFlu exports are ILITOTAL-only** (40 CSV), incompatible with the 7-channel NPZ of
   other models. No harmonised leaderboard is claimed. A recovery job (739549) and a
   measured CPU pilot (740296) exist.
5. **40 blocked encoder cells** (`ds_r1_distill_qwen1_5b`) caused by HF cache layout
   mismatch; root cause patched, one distinctly-labelled rerun (740183) queued.
6. **`legacy_done.tsv` 189/189 is not validated completion** — the lane writes DONE on
   any attempt; last 50 tasks logged `rc=3 / skip.impossible / bad table6 task id`.
7. **Login-node incident 2026-11-05** — see `INCIDENT_20261105_LOGIN_NODE_DSTATE.md`.
   No Slurm job was killed by the recovery `pkill` (verified via `sacct`).
8. **Two conflicting legacy TODO files**: `code/queue/legacy_todo.tsv` = 189 rows
   (139/189 earlier) and `trackB_20261104/all/LEGACY_TODO.tsv` = 191 rows
   (19 Table VI + 170 WF + 2 other). Reconciliation requires configuration matching,
   not row counts.
