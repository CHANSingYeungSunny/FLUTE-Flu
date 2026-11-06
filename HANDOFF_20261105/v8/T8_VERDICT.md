# T8_VERDICT.md — TASK 8 (v8 final package), 2026-11-06

```
status: COMPLETED (PRELIMINARY PACKAGING PASS)
        The v8 return package was assembled and structurally validated with the
        files available on 2026-11-06. This is NOT a scientific completion and
        NOT "all done": T7 DOCX/PDF and the T1-updated final WF CSV have NOT
        landed. validator PASS is structural only -> scientific_readiness:
        NOT_ASSESSED.
start_utc: 2026-11-06T14:18:14Z   # first timestamped packaging command (builder);
                                    # file read/inspection phase immediately precedes
end_utc:   2026-11-06T14:21:37Z   # last `date -u` after verification; this verdict written immediately after
builder_window_utc: 2026-11-06T14:18:14Z -> 2026-11-06T14:20:05Z
project_root: C:\Users\Asus\Desktop\FYP code\MLFlu
python: 3.13.14 (Windows, Git Bash)
```

## 1. Scope honoured

- Wrote ONLY into `HANDOFF_20261105/v8/packaging/`, `v8/RETURN_V8/`,
  `v8/MESSAGE_TO_CHATGPT.md`, `v8/T8_VERDICT.md`, `v8/RETURN_TO_CHATGPT.zip`,
  `v8/RAW_EVIDENCE.zip`.
- Did NOT modify `v8/TASK_LOG.md`, `HANDOFF_20261105/final/*`,
  `HANDOFF_20261105/v7/*`, `HANDOFF_20261105/RETURN_REV9_2/*`, or any frozen CSV,
  raw prediction, checkpoint, or owner-edited PPTX. All sources were COPY only.
- `shutil.rmtree` was used ONLY on `v8/RETURN_V8/` (own staging dir of copies).
- `RETURN_MANIFEST.json` was written ONLY by the official tool; never hand-written.
- The validator was NOT edited to force a PASS.

## 2. Exact commands and exit codes (all run from the project root)

The two official tools were first inspected (`argparse`): `make_return_manifest.py`
takes a positional `root: Path` + `--exclude` (append); `validate_return.py` takes
a positional `root: Path` + `--out` (Path). The prompt's invocation therefore
worked as-is; only the paths were adapted to absolute Windows paths and the tool
copies in `v8/packaging/tools/`. No different invocation was required.

| # | exact command (as run) | exit code |
|---|---|---|
| C0 | `cp "handoffs/20261105_return/tools/make_return_manifest.py" "HANDOFF_20261105/v8/packaging/tools/make_return_manifest.py"` and the same for `validate_return.py` (byte-identical copies verified by SHA-256) | 0 |
| C1 | `python "HANDOFF_20261105/v8/packaging/build_v8_return.py" > "HANDOFF_20261105/v8/packaging/build_run.stdout.txt" 2>&1` | **0** |
| C2 | `python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/tools/make_return_manifest.py" "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/RETURN_V8" --exclude VALIDATION_RESULT.json > ".../step2_make_return_manifest.stdout.txt" 2> ".../step2_make_return_manifest.stderr.txt"` | **0** |
| C3 | `python "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/packaging/tools/validate_return.py" "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/RETURN_V8" --out "C:/Users/Asus/Desktop/FYP code/MLFlu/HANDOFF_20261105/v8/RETURN_V8/VALIDATION_RESULT.json" > ".../step2_validate_return.stdout.txt" 2> ".../step2_validate_return.stderr.txt"` | **0** |
| C4 | `python -c "<verification: PASS/NOT_ASSESSED assert, manifest coverage, ZIP internal consistency, ZIP sizes + SHA-256>"` | **0** |
| C5 | `date -u +%Y-%m-%dT%H:%M:%SZ` (twice) | 0 |

C1 (`build_v8_return.py`) ALSO invokes the two official tool copies internally
with the identical argv (logged in `v8/packaging/make_return_manifest.command.txt`
and `validate_return.command.txt`, both exit_code=0). C2/C3 are the explicit
step-2 runs from the project root; they are deterministic and idempotent, and
reproduced byte-identical `RETURN_MANIFEST.json` / `VALIDATION_RESULT.json`
(verified: ZIP-internal copies == on-disk copies).

### stdout / stderr / exit-code paths (all under `v8/packaging/`)

- `build_run.stdout.txt` (= `build_v8_return.stdout.txt`, 98,513 B): full builder
  stdout incl. the exact list of 1304 included relative paths.
- `make_return_manifest.{command,stdout,stderr,exit_code}.txt`,
  `validate_return.{command,stdout,stderr,exit_code}.txt` (builder-internal runs).
- `step2_make_return_manifest.stdout.txt` / `.stderr.txt`,
  `step2_validate_return.stdout.txt` / `.stderr.txt` (explicit C2/C3 runs;
  stderr empty for both).
- `v8_package_report.json`: machine-readable report (UTC, file count, validator,
  ZIP sizes/hashes, full included-path list).

## 3. File counts

- v8 text files mirrored (`.md .csv .json .tsv .py .sbatch .sh .txt .log`): **100**
- `final/` files copied (HANDOFF_20261105/final/): **19**
- v7 addendum/audit docs into `audit/v7/`: **4**
- `v7_snapshot/` root files + `DOCUMENTS/v7/` docs: **20 + 18**
- REQUIRED root skeleton files copied: **18**
- `RAW_EVIDENCE/` 1120-panel NPZ copied: **1120**
- **`RETURN_V8/` files assembled by builder: 1304**
- **`files hashed: 1304`** (`make_return_manifest.py` stdout, both runs)
- **`RETURN_V8/` total files on disk: 1306** (= 1304 manifest members +
  `RETURN_MANIFEST.json` + `VALIDATION_RESULT.json`)
- `RETURN_TO_CHATGPT.zip` members: **1306** (1120 NPZ)
- `RAW_EVIDENCE.zip` members: **2232** (2068 NPZ + `RAW_EVIDENCE_README.md` +
  full `v8/evidence/`, `resource_logs/`, `cdc_vintage/`, `foundation/`,
  `scripts/`, `final/` directories)
- Manifest coverage diff: **[]** (no unlisted files; `listed-but-missing: []`).

## 4. ZIP sizes + SHA-256

| ZIP | bytes | SHA-256 |
|---|---:|---|
| `HANDOFF_20261105/v8/RETURN_TO_CHATGPT.zip` | **197,801,169** | `571e589b168180eed42ab0ee590d9f9e438f316667e0bb14cbb09e923a6f7fcd` |
| `HANDOFF_20261105/v8/RAW_EVIDENCE.zip` | **344,228,221** | `1ab7fc0b5b9c2205aa85af2bf1422a9499afec1a6869f12622e59b93593bdfc0` |

Both ZIPs pass `zipfile.testzip()` (returns `None`). Nothing was downloaded; all
NPZ were already present in the project.

## 5. Validator result (`RETURN_V8/VALIDATION_RESULT.json`)

```json
{
  "integrity_status": "PASS",
  "scope": "structure, file hashes and limited status consistency only; NOT scientific validation",
  "run_status_counts": {"completed": 1120},
  "check_status_counts": {"passed": 5},
  "scientific_readiness": "NOT_ASSESSED",
  "errors": []
}
```

Verified explicitly: `integrity_status == PASS` AND
`scientific_readiness == NOT_ASSESSED` (asserted, exit 0). The validator was
NOT modified. PASS is structural only; it is NOT scientific certification and
must not be read as submission-readiness.

## 6. Evidence

- `v8/packaging/build_v8_return.py` — reproducible builder (assembly + official
  tools + ZIPs + hashes). Single re-run command in `v8/packaging/T8_PREP_NOTES.md`.
- `v8/packaging/tools/` — byte-identical COPIES of the official tools (originals
  at `handoffs/20261105_return/tools/` untouched).
- `v8/RETURN_V8/RETURN_MANIFEST.json` (official tool), `VALIDATION_RESULT.json`
  (official validator), `RETURN_LAYOUT.md` (structure + old/new separation).
- `v8/MESSAGE_TO_CHATGPT.md` — exact v8-vs-v7 changes and BLOCKED / NOT_EXECUTED /
  UNVERIFIED list citing `v8/TASK_LOG.md`, `v8/foundation/T2_VERDICT.md`,
  `v8/cdc_vintage/T4_VERDICT.md`, `v8/T5_VERDICT.md`, `v8/T6_VERDICT.md`.
- Old/new separation: frozen 28-arm snapshot (`02_数字表格/*.csv`) NOT bundled;
  new 1120-panel tables under `final/`; foundation models on the separate
  `foundation/FOUNDATION_ROSTER.csv`; v7 return separately labelled under
  `v7_snapshot/`. Verified: zero `02_数字表格` files leaked into `RETURN_V8/`.
- `01_最终报告/v8/` did NOT exist at build time → `DOCUMENTS/v8/` absent (COPY-only
  conditional worked as specified).
- `v8/packaging/v8_package_report.json` + all stdout/stderr logs in §2.

## 7. Remaining (explicitly NOT claimed as done)

- **PRELIMINARY pass**: T7 DOCX/PDF (`01_最终报告/v8/`) and the T1-updated
  `final/WF_RECOMPUTED.csv` / means may land AFTER this package. Re-run the single
  command in `v8/packaging/T8_PREP_NOTES.md` once they exist; the builder is
  idempotent and re-hashes/re-zips/re-validates everything.
- `T8_VERDICT.md` and `T8_PREP_NOTES.md` are written AFTER the builder ran, so on
  THIS pass they are NOT inside `RETURN_V8/` / `RETURN_TO_CHATGPT.zip`. A re-run
  folds them in (they are v8 text files).
- T1: 218 `no_npz` walk-forward cells still IN PROGRESS (743850 RUNNING,
  744271 PENDING at `TASK_LOG.md`); **802 ok / 218 no_npz** in the current
  `final/WF_RECOMPUTED.csv`. No DONE claim.
- T2: Chronos/TimesFM pilot + 80 cells **BLOCKED / NOT_EXECUTED** (no full weights,
  no isolated env, no pilot).
- T4: actual CDC release date/revision id **BLOCKED**; peak re-scoring **BLOCKED**.
- T5: official template class file **UNVERIFIED**; `submission-ready: NO`.
- T6: peak VRAM + true model-forward latency **NOT_MEASURED**; full-1120 Pareto
  **NOT claimed**.
- T7: manuscript body / internal report / Q&A / `DOCUMENT_UPDATE_MAP.csv` /
  `SCIENTIFIC_AUDIT.md` / `BLOCKED_AND_UNVERIFIED.md` updates **NOT EXECUTED** in
  this pass (out of T8 write scope).
- Paired statistics remain EXPLORATORY; the two quarantined corrupt legacy MIFlu
  NPZ from T3 remain unresolved.

**Bottom line:** the structural v8 package is built and validated (PASS /
NOT_ASSESSED) with honest hashes, but this is a preliminary snapshot, not "all
done", and no scientific readiness is asserted.
