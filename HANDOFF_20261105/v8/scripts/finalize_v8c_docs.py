# -*- coding: utf-8 -*-
"""Final v8c documentation sync (no HPC work, no model work)."""
import csv
from pathlib import Path

R = Path(r"C:\Users\Asus\Desktop\FYP code\MLFlu\HANDOFF_20261105\v8")

# ---------------------------------------------------------------- T2 verdict
p = R / "foundation" / "T2_VERDICT.md"
with p.open("a", encoding="utf-8") as f:
    f.write("""

---

## FINAL UPDATE 2026-11-06 — FULL 80-CELL MATRIX COMPLETED

`status: COMPLETED (80/80 valid cells; documented rolling-origin protocol)`.
The earlier `COMPLETED_WITH_DOCUMENTED_SCOPE` (8 cells) and the original `BLOCKED`
verdicts are SUPERSEDED.

- Job **744886** `t2_fm_full80` on `stingy` / A100-SXM4-80GB produced
  `FOUNDATION_80_CELLS.csv`: **80/80 `ok`, all finite, 80 real prediction NPZ**
  under `v8/foundation/t2_hpc_evidence/full80_out/`.
- Matrix = 2 models x 4 L (24/36/48/60) x 10 replicates. Both checkpoints are
  FROZEN ZERO-SHOT with no training seed dimension, so 10 seeds would give 10
  identical predictions. The 10 replicates are therefore **10 DISTINCT FORECAST
  ORIGINS** (rows 773-782), each with its own context and target.
  `seed_semantics=NOT_APPLICABLE`, `replicate_kind=rolling_origin`.
  The literal 10-seed expansion remains `NOT_EXECUTED_BY_PROTOCOL` with that exact
  reason — this is a documented protocol deviation, NOT a fabricated seed dimension.
- Measured resources: peak VRAM 2608 MiB (51 nvidia-smi samples), `/usr/bin/time -v`
  wall 50.71 s, Chronos latency 10.229 +/- 1.074 ms (warm-up 1 / repeat 10),
  TimesFM 50.906 +/- 4.459 ms (warm-up 1 / repeat 5).
- Labels `foundation_chronos` / `foundation_timesfm` remain a SEPARATE ROSTER.
  Both checkpoints are UNIVARIATE; the per-channel adapter DISCARDS cross-channel
  dependence and is NOT information-set matched to the multivariate arms. No
  training/fine-tuning, no full-1120 comparison.
- Full record: `v8/foundation/T2_FULL80.md`; per-NPZ hashes:
  `v8/foundation/T2_EVIDENCE_HASHES_FULL80.txt`.
""")
print("T2_VERDICT_APPENDED")

# ---------------------------------------------------------------- T2 roster
p = R / "foundation" / "FOUNDATION_ROSTER.csv"
rows = list(csv.DictReader(p.open(encoding="utf-8", newline="")))
cols = list(rows[0].keys())
for c in ("cells_executed", "executed_job_ids", "replicate_kind", "peak_vram_mib"):
    if c not in cols:
        cols.append(c)
for r in rows:
    rid = r.get("repo_id", "")
    if "chronos-bolt-tiny" in rid:
        r.update({"status": "PILOT_AND_80CELL_MATRIX_COMPLETED", "cells_executed": "40",
                  "executed_job_ids": "744589;744607;744886;744897",
                  "replicate_kind": "rolling_origin (10 distinct origins)",
                  "peak_vram_mib": "596",
                  "separate_roster": "yes"})
    elif "timesfm-2.0-500m-pytorch" in rid:
        r.update({"status": "PILOT_AND_80CELL_MATRIX_COMPLETED", "cells_executed": "40",
                  "executed_job_ids": "744607;744886;744897",
                  "replicate_kind": "rolling_origin (10 distinct origins)",
                  "peak_vram_mib": "2594",
                  "separate_roster": "yes"})
    for c in cols:
        r.setdefault(c, "")
with p.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print("FOUNDATION_ROSTER_UPDATED", len(rows), "rows")

# ---------------------------------------------------------------- TASK_LOG
p = R / "TASK_LOG.md"
s = p.read_text(encoding="utf-8")
s = s.replace(
    "status: COMPLETED_WITH_DOCUMENTED_SCOPE (finalised 2026-11-06T15:58:04Z; the earlier BLOCKED verdict is SUPERSEDED — see T2 FINAL UPDATE below)",
    "status: COMPLETED (80/80 valid cells; documented rolling-origin protocol; finalised 2026-11-06T17:39:16Z — see T2 FULL80 UPDATE)")
s = s.replace(
    "status: COMPLETED (real output table; with a documented 2-cell quarantine caveat)",
    "status: COMPLETED (388/388 NPZ readable; the 2 quarantined cells were RESTORED — see T3 RESTORE UPDATE)")
s = s.replace(
    "status: PARTIAL (IMPROVED) — MIFlu peak VRAM now MEASURED (4816 MiB); five model rows still\n        NOT_MEASURED and foundation rows still BLOCKED (see T6 UPDATE below)",
    "status: COMPLETED (all 6 representative models have measured peak VRAM; see T6 FINAL SWEEP UPDATE)\n        Three models still lack an isolated single-forward latency (explicitly NOT_MEASURED).")

APP = """

---

## FINAL v8c UPDATES — 2026-11-06 (supersedes the interim records above)

### T2 FULL80 UPDATE
status: COMPLETED
commands: `sbatch t2_full80.sbatch` -> job **744886** `t2_fm_full80`, `stingy` /
  A100-SXM4-80GB; `/usr/bin/time -v ... t2_full80.py`; nvidia-smi 1 s sampling.
exit_codes: 0:0 COMPLETED; wall 50.71 s; Max RSS 5,088,224 KB.
outputs: `v8/foundation/T2_FULL80.md`,
  `v8/foundation/t2_hpc_evidence/full80_out/FOUNDATION_80_CELLS.csv`,
  `FOUNDATION_80_REPORT.json`, 80 `pred_*.npz`,
  `v8/foundation/T2_EVIDENCE_HASHES_FULL80.txt`.
evidence: **80/80 cells `ok`, all finite, 80 real NPZ**; 2 models x 4 L x
  10 DISTINCT FORECAST ORIGINS (rows 773-782). peak VRAM 2608 MiB (51 samples);
  Chronos 10.229 +/- 1.074 ms (warm-up 1 / repeat 10), TimesFM 50.906 +/- 4.459 ms
  (warm-up 1 / repeat 5). `seed_semantics=NOT_APPLICABLE`.
remaining: the literal `2 x 4 L x 10 seeds` expansion is `NOT_EXECUTED_BY_PROTOCOL`
  (frozen zero-shot models have no training seed dimension); no multivariate-native
  checkpoint, no full-1120 comparison; per-channel univariate adapter limits remain.

### T3 RESTORE UPDATE
status: COMPLETED
commands: `sbatch t3_restore_final.sbatch` -> job **744884** `t3_restore_final`,
  `tiny` / cpunode-034. COPY-restored the 2 corrupt NPZ from their existing valid
  7-channel copies, validated all 388 NPZ with numpy inside sbatch, then re-ran the
  exact `final_llm_import` task with `QUEUE_FORCE_FINALISE=1`.
exit_codes: 0:0 COMPLETED; all 3 analysis scripts rc=0, `ok=true`.
outputs: `v8/T3_RESTORE.md`, `v8/evidence/t3_restore/restore_20261106T173725Z/*`.
evidence: **388/388 NPZ readable, 0 unreadable**, `(W,7,L)`, all finite.
  `BENCH_MSE_BY_MODEL_L.csv` hash `2e03b510...` -> **`a7d98ad84a72c5b82610e076f64cabecdda8ebe64099ef7e8a078161a4541e46`**
  (69 lines). The 2 original corrupt files remain archived, not deleted.
remaining: this is still a LEGACY analysis-tree table, a different scoring
  population from the 1120 national panel and the LEGACY WF panel.

### T5 PROVENANCE UPDATE
status: COMPLETED (step 4)
commands: created `v8/PAPER_TO_CODE.md` (v7 content + the dated JBHI guidance
  verification block); patched `v8/packaging/build_v8_return.py` so
  `RETURN_V8/PAPER_TO_CODE.md` prefers the v8 copy over the frozen v7 skeleton.
exit_codes: 0 (Python file writes).
evidence: the v7 original at `HANDOFF_20261105/v7/RETURN_V7/PAPER_TO_CODE.md`
  remains byte-identical; `v8/JBHI_PROVENANCE_PATCH.md` is now applied.
remaining: the official template class file itself stays UNVERIFIED
  (404 / WAF 418 / API 302->502).

### T6 FINAL SWEEP UPDATE
status: COMPLETED (all 6 representative models measured)
commands: `sbatch t6_sweep.sbatch` -> job **744897** `t6_final_sweep`;
  `sbatch t6_miflu_fix.sbatch` -> job **744899** `t6_miflu_fix`
  (fixes the rc=126 `Permission denied` of the sweep's MIFlu step).
exit_codes: 744897 = 0:0 COMPLETED; 744899 = 0:0 COMPLETED.
outputs: `v8/T6_FINAL_SWEEP.md`, `v8/RESOURCE_MEASUREMENTS.csv` sha256
  `9574eeff6f0e39ddba6488b2e8fe8ef09b763c90fdd27223d7960b8f886b1117`,
  `v8/resource_logs/final_sweep/*`, `v8/resource_logs/t6sweep_744897.out`.
evidence: peak VRAM (A100-SXM4-80GB) MIFlu **4816 MiB** (46+63 samples),
  NLinear **558** (36), PatchTST **720** (7), GPT-2 frozen encoder **1070** (11),
  Chronos **596** (6), TimesFM **2594** (11). Warm-up+repeated REAL forward
  latencies: GPT-2 6.98 +/- 0.097 ms, Chronos 9.854 +/- 0.337 ms,
  TimesFM 48.273 +/- 3.531 ms. Cross-checked by 744886 and 744532.
remaining: MIFlu / NLinear / PatchTST isolated single-forward latency is
  explicitly NOT_MEASURED (their measured quantity was a real full cell export or
  training job); all rows `scope=subset_only_not_full_1120`; no full-1120 Pareto.

### T7 v8c REBUILD and T8 FINAL PACKAGE
T7: the 3 v8 DOCX/PDF pairs were rebuilt again (v8c) so their BODIES carry the
  final 80-cell T2, 388-cell T3, T5 provenance and 6-model T6 results; old
  claims are marked SUPERSEDED. See `v8/docs/V8C_REBUILD_LOG.md`.
T8: the final package was rebuilt AFTER all v8c outputs landed. See
  `v8/T8_VERDICT.md` and `v8/packaging/FINAL_HASHES.txt` for the authoritative
  file count, ZIP sizes and SHA-256 (kept outside RETURN_V8 because the package
  mirrors its own documentation and ZIP hashes therefore change on each rebuild).
"""
if "### T2 FULL80 UPDATE" not in s:
    s = s.rstrip() + APP
p.write_text(s, encoding="utf-8")
print("TASK_LOG_UPDATED")

# ------------------------------------------------- addendum / changelog
p = R / "docs" / "V8_SCIENTIFIC_ADDENDUM.md"
with p.open("a", encoding="utf-8") as f:
    f.write("""

---

## V8C FINAL UPDATE (2026-11-06 UTC) — supersedes the v8b sections above

The v8b text above recorded the *interim* state. All four items below are now
final; the earlier statements are SUPERSEDED, not silently overwritten.

1. **T2 — 80 valid cells, not 8.** Job `744886` produced
   `FOUNDATION_80_CELLS.csv` with **80/80 `ok`, all finite, 80 real NPZ**
   (`v8/foundation/t2_hpc_evidence/full80_out/`). Because both checkpoints are
   frozen zero-shot with no training seed dimension, the 10 replicates are
   **10 distinct forecast origins** (rows 773-782), not 10 seeds;
   `seed_semantics=NOT_APPLICABLE`. The literal 10-seed expansion remains
   `NOT_EXECUTED_BY_PROTOCOL`. Peak VRAM 2608 MiB; Chronos 10.229 +/- 1.074 ms
   and TimesFM 50.906 +/- 4.459 ms (warm-up + repeated). See `v8/foundation/T2_FULL80.md`.
2. **T3 — 388/388 NPZ readable.** Job `744884` COPY-restored the two corrupt
   files from existing valid 7-channel copies and re-ran `final_llm_import`;
   `BENCH_MSE_BY_MODEL_L.csv` is now `a7d98ad8...e46`. The quarantine caveat is
   resolved. See `v8/T3_RESTORE.md`.
3. **T5 — provenance applied.** `v8/PAPER_TO_CODE.md` carries the dated JBHI
   guidance verification and the builder now prefers it. The official template
   class file is still UNVERIFIED.
4. **T6 — all 6 representative models measured.** Jobs `744897` / `744899`:
   peak VRAM MIFlu 4816, NLinear 558, PatchTST 720, GPT-2 1070, Chronos 596,
   TimesFM 2594 MiB. Warm-up+repeated real forward latencies for GPT-2
   6.98 +/- 0.097, Chronos 9.854 +/- 0.337, TimesFM 48.273 +/- 3.531 ms.
   Isolated single-forward latency for MIFlu/NLinear/PatchTST remains explicitly
   NOT_MEASURED. See `v8/T6_FINAL_SWEEP.md`.

Still blocked / unverified: the literal 10-seed expansion; multivariate-native
foundation checkpoints; full-1120 comparisons; the univariate adapter's
information-set mismatch; official JBHI template class file; confirmatory
dependence-aware statistics; retrospective model-panel peak metrics.
No full-1120 Pareto claim. The manuscript is NOT submission-ready; a structural
validator PASS means `scientific_readiness: NOT_ASSESSED`.
""")
print("ADDENDUM_UPDATED")

p = R / "docs" / "V8_CHANGELOG.md"
with p.open("a", encoding="utf-8") as f:
    f.write("""

---

## 6. V8C final sync (2026-11-06 UTC) — supersedes §5's interim statuses

§5 recorded `T2 -> COMPLETED_WITH_DOCUMENTED_SCOPE (8 cells)` and
`T6 -> PARTIAL (IMPROVED)`; both are now SUPERSEDED by these final states:

| Task | Final status | Evidence |
|---|---|---|
| T2 | **COMPLETED — 80/80 valid cells** | job `744886`; `v8/foundation/T2_FULL80.md`; 80 NPZ; 10 rolling origins; peak VRAM 2608 MiB |
| T3 | **COMPLETED — 388/388 NPZ** | job `744884`; `v8/T3_RESTORE.md`; table `a7d98ad8...e46` |
| T5 | **COMPLETED — provenance applied** | `v8/PAPER_TO_CODE.md`; builder prefers v8 copy; template class file UNVERIFIED |
| T6 | **COMPLETED — 6 models measured** | jobs `744897`/`744899`; `v8/T6_FINAL_SWEEP.md`; CSV sha256 `9574eeff...1117` |
| T7 | **COMPLETED — v8c rebuild** | `v8/docs/V8C_REBUILD_LOG.md` |
| T8 | **COMPLETED — final package** | `v8/packaging/FINAL_HASHES.txt`, `v8/T8_VERDICT.md` |

T1 (1020/1020 WF), T4 (frozen CDC vintage + as-of peaks) and T5's dated
verification record are unchanged. Old 28-arm snapshot, the 1120 national panel
and the LEGACY 5-fold N=3 WF panel remain three separately labelled populations.
Still NOT EXECUTED / UNVERIFIED / NOT_MEASURED: the literal 10-seed expansion,
the official JBHI template class file, isolated single-forward latency for three
models, confirmatory dependence-aware statistics, and any full-1120 Pareto claim.
""")
print("CHANGELOG_UPDATED")
