# NEXT DEEPSEEK PROMPT — finish every remaining MIFlu task

You are the research engineer for CHAN Sing Yeung's MIFlu / FLUTE-Flu FYP on CityU Burgundy.
Work from the Windows project root:

`C:\Users\Asus\Desktop\FYP code\MLFlu`

Read these first, in order:

1. `HANDOFF_20261105/MASTER_PLAN.md`
2. `HANDOFF_20261105/final/FINAL_RESULTS.md`
3. `HANDOFF_20261105/final/SCIENTIFIC_AUDIT.md`
4. `HANDOFF_20261105/v7/V7_SCIENTIFIC_ADDENDUM.md`
5. `HANDOFF_20261105/v7/BLOCKED_AND_UNVERIFIED.md`
6. `HANDOFF_20261105/v7/MESSAGE_TO_CHATGPT.md`
7. `04_详细说明文档/OUTAGE_RECOVERY.md` and `HANDOFF_20261105/INCIDENT_20261105_LOGIN_NODE_DSTATE.md`

Current verified state (do not redo):

- National panel **1120/1120 complete**; 7-channel MIFlu **40/40**, targets exactly equal NLinear.
- Table VI regional **53/53 valid** after rerunning L13/s2030 and L15/s2026.
- Walk-forward **802/1020 valid** after seven-channel recomputation from raw NPZ; **218 have no NPZ**.
- v7 package exists:
  - `HANDOFF_20261105/v7/RETURN_TO_CHATGPT.zip` — 195,052,119 B — SHA-256 `8A471572FAFEC109B49A39B9C0A7C033F8046B0DA4C57B354BD856F8EAF3A99D`
  - `HANDOFF_20261105/v7/RAW_EVIDENCE.zip` — 183,829,699 B — SHA-256 `798C0D7F9F64E7DA93510479CC7647F2717D4BBD8024F1AE3B0064F8A53EB82B`

Everything below is unfinished. Finish each task **one at a time**, or in parallel only when the
tasks touch disjoint files/partitions. For every task write: start/end UTC, exact command, exit code,
stdout/stderr path, output hashes, and status `COMPLETED` or `BLOCKED` with evidence.

---

## HARD RULES

1. **Never run model work, `torch.load`, `import torch`, `from_pretrained`, or recursive `du` on the
   login node.** Use `sbatch` on a compute node. CPU inference is still model work.
2. **Download weights locally on Windows first**, then transfer a single tar with `scp`; extract and
   load on a compute node. Do not run `hf download` on the login node.
3. Pin every model revision/sha256 and licence. Record the exact repo id + revision.
4. Never fabricate a DONE cell. A job label, a directory, or `legacy_done.tsv` is not evidence.
5. Never delete frozen CSVs, raw predictions, checkpoints, or owner-edited PPTX.
6. `RETURN_TO_CHATGPT.zip` validator PASS is structural only (`scientific_readiness: NOT_ASSESSED`).
7. If a task is genuinely impossible (missing data/weights/licence, no compute), mark `BLOCKED`
   with the exact missing input and the smallest next action. Do not substitute a smaller model
   under the same name.

---

## TASK 1 — Walk-forward missing 218 cells

Evidence: `HANDOFF_20261105/final/WF_RECOMPUTED.csv` shows 802 `ok`, 218 `no_npz`.

Steps:

1. List the 218 `no_npz` rows; group by fold/model/L/seed.
2. Check the legacy queue rows for those configurations: are they `SKIPPED`, never queued, or
   missing because of the old N=3 protocol? Use `code/queue/master_queue.tsv` and `queue_state.tsv`.
3. For configurations that are valid under the current protocol, create a distinctly-labelled
   rerun job `wf_fix218` on `stingy` or `gpu_a100` (A100 only), with `--fold <F>` and the correct
   model/L/seed. Run a 1-cell pilot first; then batch.
4. For configurations that are not valid under the current protocol (e.g. old seeds 42/43/44 that
   are not in 2021–2030), **do not invent them**; mark them `BLOCKED: protocol-mismatch` with the
   queue row.
5. Re-aggregate with `wf_recompute.py`; update `WF_RECOMPUTED.csv` and `WF_RECOMPUTED_MEANS.csv`.

Acceptance: every one of the 218 is either `COMPLETED` with a valid NPZ/MSE or `BLOCKED` with a
protocol reason. No silent `DONE`.

---

## TASK 2 — Numerical foundation models (Chronos, TimesFM)

Goal: two faithful, source-pinned numerical foundation-model controls, separate from the 11 frozen
language encoders.

Steps:

1. **Local download on Windows** (not on the HPC login node):
   - Chronos: official `amazon-science/chronos-forecasting`, Apache-2.0; pick a pinned release/tag
     and revision.
   - TimesFM: official Google Research package (`timesfm` on PyPI) and its weight repo; pin the
     version and revision.
   - `huggingface-cli download ... --revision <sha> --local-dir C:\models\<name>`
   - tar each model, compute SHA-256, then `scp` the tar to
     `/gpfs1/scratch/sychan552/models/`.
2. **On HPC**: create an isolated env (do not modify `mlflu_hpc`), e.g.
   `/home/sychan552/.venvs/mlflu_fm`. Extract the tar **inside an sbatch job** on `tiny`, verify
   SHA-256, and record the licence.
3. Check context length, prediction length, channel handling, and pretraining overlap. If the model
   cannot accept T=104 / L=24–60 or seven channels without a documented adapter, record the adapter
   and its limits.
4. **Pilot one cell** (`1 model × L24 × seed 2021`) on `stingy` A100. Measure wall time, peak VRAM,
   and finite predictions. Do **not** run the full matrix if the pilot fails.
5. If the pilot passes, run `2 models × 4 L × 10 seeds = 80` cells (or the smallest faithful subset
   the model supports), labelled `foundation_chronos` / `foundation_timesfm`. Do not merge them into
   the 28-arm family; create a separate roster/version.
6. If weights/licence/context cannot be resolved, mark `BLOCKED` with the exact URL/revision,
   error, and the smallest missing input.

Acceptance: either 80 valid cells with predictions + measured resources, or a BLOCKED record with
evidence. No claim that frozen language encoders are these models.

---

## TASK 3 — Legacy `final_llm_import`

1. Inspect `master_queue.tsv` row `final_llm_import` (`f5_llm_import`).
2. Read `code/queue/master_task_v2.py` handler for `f5_llm_import` (runs `analysis_expanded.py`,
   `plot_bench.py`, `plot_pareto.py`).
3. Run it once on a compute node (tiny is enough) with the exact task id/kind; capture logs and
   output table hashes. If it rewrites old `paper_tables`, save a backup first and compare.
4. If it fails, record the exact error and mark `BLOCKED`; do not fake a table.

Acceptance: a real output table or a precise error.

---

## TASK 4 — CDC calendar / vintage

1. Search for archived CDC ILINet releases (e.g. archived CSV snapshots, CDC FluView archives,
   Software Heritage copies).
2. Decide whether the actual **release date / revision** can be reconstructed. Archived final CSVs
   alone are not a vintage.
3. If yes, build a `cdc_vintage.csv` with release date + revision id + affected weeks; re-run the
   peak assignment with the correct as-of data.
4. If no, keep `BLOCKED: no release-calendar/vintage source found` with the URLs checked and the
   exact limitation.

Acceptance: either a vintage table and re-scored peaks, or a documented BLOCKED.

---

## TASK 5 — JBHI verification

1. Retrieve the official IEEE JBHI author page and the current template selector.
2. Verify: page limit (14 pages including supplementary), abstract ≤250 words, double-column
   single-spaced, embedded figures/tables, AI-use disclosure, fees/open-access.
3. If the selector returns HTTP 418 or the exact class cannot be downloaded, record the exact URL,
   status code and date; keep `UNVERIFIED`.
4. Update `PAPER_TO_CODE.md`/manuscript provenance accordingly; do not call it submission-ready.

Acceptance: a dated verification record or a precise UNVERIFIED note.

---

## TASK 6 — Resource measurements

1. For a representative subset (MIFlu, NLinear, PatchTST, one frozen encoder, Chronos, TimesFM):
   measure training wall time, peak VRAM, inference latency (warm-up + repeated), batch/precision,
   GPU model and software versions.
2. Use `sbatch` with `/usr/bin/time -v` and `nvidia-smi` sampling; save raw logs.
3. Do not claim full-1120 Pareto from a subset. Report the subset and the missing cells explicitly.

Acceptance: a `RESOURCE_MEASUREMENTS.csv` with measured rows and a scope column.

---

## TASK 7 — v8 documents

After T1–T6:

1. Update the English manuscript body (not only an addendum) and Chinese internal report/Q&A with
   the new WF, foundation, resource and provenance results.
2. Keep the old 28-arm snapshot labelled separately; add the foundation models as a separate roster.
3. Update `DOCUMENT_UPDATE_MAP.csv`, `SCIENTIFIC_AUDIT.md`, `BLOCKED_AND_UNVERIFIED.md`.
4. Rebuild DOCX/PDF with `build_v7_manuscript.py` / `build_v7_internal_zh.py` patterns, or the
   project builder; verify page counts and that no old claim is silently overwritten.

Acceptance: v8 DOCX/PDF with the new results and explicit old/new separation.

---

## TASK 8 — Final package

1. Rebuild `RETURN_TO_CHATGPT.zip` and `RAW_EVIDENCE.zip` with the new cells/predictions.
2. Run:
   ```bash
   python tools/make_return_manifest.py RETURN_V8 --exclude VALIDATION_RESULT.json
   python tools/validate_return.py RETURN_V8 --out RETURN_V8/VALIDATION_RESULT.json
   ```
3. Report exit code, file count, sizes and SHA-256. PASS must still say
   `scientific_readiness: NOT_ASSESSED`.
4. Include a `MESSAGE_TO_CHATGPT.md` listing exactly what changed and what remains BLOCKED.

Acceptance: validator PASS, hashes reported, no unlisted files.

---

## DELIVERABLE FORMAT

For each task, append to `HANDOFF_20261105/v8/TASK_LOG.md`:

```
## T<n> — <title>
status: COMPLETED | BLOCKED
start_utc:
end_utc:
commands:
exit_codes:
outputs: <paths + sha256>
evidence:
remaining:
```

Final answer must state: completed vs blocked counts, exact HPC job IDs, new file hashes, and the
next command for the user. Do not claim “all done” unless every task is `COMPLETED` or explicitly
`BLOCKED` with accepted evidence.
