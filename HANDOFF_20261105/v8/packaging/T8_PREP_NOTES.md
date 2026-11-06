# T8_PREP_NOTES.md — why this is a PRELIMINARY packaging pass, and how to re-run

## Why this pass is preliminary

TASK 8 assembled `v8/RETURN_V8/` and rebuilt the two ZIPs using **only the files
that existed at build time (2026-11-06T14:18:14Z)**. Two expected inputs had NOT
landed yet:

1. **T7 v8 DOCX/PDF** — `01_最终报告/v8/` did NOT exist at build time. The builder's
   conditional COPY step correctly skipped it, so `RETURN_V8/DOCUMENTS/v8/` is
   absent from this pass. TASK 7 may still produce the English manuscript body,
   Chinese internal report / Q&A, and DOCX/PDF afterwards.
2. **The T1-updated walk-forward CSV** — `final/WF_RECOMPUTED.csv` currently shows
   1020 rows / **802 `ok` / 218 `no_npz`** (the seven-channel recomputation baseline),
   and `v8/TASK_LOG.md` T1 is still **IN PROGRESS** (job 743850 RUNNING, 744271
   `wf_recompute` PENDING). The final updated `WF_RECOMPUTED.csv` /
   `WF_RECOMPUTED_MEANS.csv` may land AFTER this package. The frozen v7 baselines
   are preserved in `v8/evidence/WF_RECOMPUTED_v7_baseline.csv` and
   `WF_RECOMPUTED_MEANS_v7_baseline.csv`; do NOT fabricate 218 COMPLETED cells.

Also note: `v8/T8_VERDICT.md` and this `T8_PREP_NOTES.md` were written AFTER the
builder ran, so they are NOT inside `RETURN_V8/` on this pass. They are v8 text
files, so a re-run folds them in automatically.

A validator `integrity_status: PASS` is STRUCTURAL ONLY
(`scientific_readiness: NOT_ASSESSED`). Nothing here is "all done".

## The exact single re-run command

Once T7 DOCX/PDF and/or the final WF CSV exist, run this **one** command from the
project root `C:\Users\Asus\Desktop\FYP code\MLFlu`:

```
python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/build_v8_return.py"
```

This single builder call performs, in order, exactly:

1. **builder** — wipes and re-assembles `v8/RETURN_V8/` (it is a staging dir of
   COPIES only; `shutil.rmtree` is used ONLY here). It re-scans every v8 text file,
   re-copies the updated `HANDOFF_20261105/final/`, the v7 addendum/audit docs, the
   frozen `v7/RETURN_V7/` key files (separately labelled under `v7_snapshot/`), and
   any `01_最终报告/v8/` DOCX/PDF that now exist (COPY only).
2. **manifest** — invokes the official `v8/packaging/tools/make_return_manifest.py`
   on `RETURN_V8` with `--exclude VALIDATION_RESULT.json` (writes
   `RETURN_MANIFEST.json`; never hand-written).
3. **validator** — invokes the official `v8/packaging/tools/validate_return.py`
   on `RETURN_V8` with `--out RETURN_V8/VALIDATION_RESULT.json`, and reports the
   real `integrity_status` / `scientific_readiness` (it does NOT force a PASS).
4. **ZIPs** — rebuilds `v8/RETURN_TO_CHATGPT.zip` (contents of `RETURN_V8/`) and
   `v8/RAW_EVIDENCE.zip`, and recomputes byte sizes + SHA-256.
5. Writes refreshed logs (`build_v8_return.stdout.txt`, `*.command.txt`,
   `*.stdout.txt`, `*.stderr.txt`, `*.exit_code.txt`) and
   `v8/packaging/v8_package_report.json` with the exact included-path list.

The exact argv the builder uses for steps 2–3 (identical to the explicitly-run
step-2 commands in `T8_VERDICT.md`):

```
python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/tools/make_return_manifest.py" "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/RETURN_V8" --exclude VALIDATION_RESULT.json
python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/tools/validate_return.py" "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/RETURN_V8" --out "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/RETURN_V8/VALIDATION_RESULT.json"
```

If you prefer to also re-capture the explicit step-2 stdout/stderr logs under
`v8/packaging/step2_*.txt`, run those two commands again afterwards (they are
deterministic and idempotent, producing byte-identical
`RETURN_MANIFEST.json` / `VALIDATION_RESULT.json`).

## After any re-run

- The file set changes (new DOCX/PDF / WF CSV / `T8_VERDICT.md` /
  `T8_PREP_NOTES.md` are now v8 text files), so the builder reports **NEW** file
  counts, **NEW** ZIP byte sizes and **NEW** SHA-256. The authoritative numbers
  after a re-run are those in `v8/packaging/v8_package_report.json` and the
  builder's `build_v8_return.stdout.txt` — **not** the numbers frozen in
  `T8_VERDICT.md` from the earlier pass.
- Re-check `integrity_status: PASS` AND `scientific_readiness: NOT_ASSESSED` in
  the regenerated `RETURN_V8/VALIDATION_RESULT.json`. If either is wrong, report
  it; never edit `validate_return.py` to force a PASS.
- Update `v8/MESSAGE_TO_CHATGPT.md` and `v8/T8_VERDICT.md` to reflect the newly
  landed files and hashes (they describe the package that contains them, so they
  are inherently self-referential).
- Do NOT delete frozen CSVs, raw predictions, checkpoints or owner-edited PPTX;
  do NOT overwrite `HANDOFF_20261105/v7/*` or `RETURN_REV9_2/*`; do NOT call the
  manuscript submission-ready.
