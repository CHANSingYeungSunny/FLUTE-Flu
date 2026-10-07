# Original reproduction repository — incident integrity report

Innovation implementation source **`innov-v2.2`** · scientific protocol `innov-v2.0`
Audited root: `/home/sychan552/scratch/CHATTIME/Chattime` (→ `/gpfs1/scratch/sychan552/CHATTIME/Chattime`)
Audit was **strictly read-only**: nothing was written, touched, chmod'd, copied over or removed, no Git operation, no source-snapshot rebuild.
Tool: `scripts/audit_original_repo_integrity.py` (outside the frozen scope, so no cascade), run on HPC with `python -B`.

## Gate

```
original_reproduction_repository_integrity_verified = false
blocker = ORIGINAL_REPRO_REPOSITORY_INTEGRITY_NOT_FULLY_VERIFIED
```

Reason: **one** in-scope pre-existing file (`scripts/compute_miflu_indicators.py`) is **UNRESOLVED** — no trusted
pre-incident content reference survives. No Slurm job may be submitted while this blocker is open.

## 1. Affected-path inventory

27 paths inventoried; **22 inside the incident blast radius**, 5 out-of-scope probes.
Blast radius = the 95 members of `innovation_hpc_bundle.tar.gz` **plus** the paths removed during recovery.
Machine-readable: `affected_path_inventory.json`; per-path hashes: `content_hash_comparison.csv`.

| class | count | status |
|---|---|---|
| reused dependency source (could be overwritten) | 7 | 5 `VERIFIED_IDENTICAL`, 1 `PREEXISTING_LOCAL_MODIFICATION_VERIFIED`, 1 `UNRESOLVED` |
| created by the extraction then removed | 15 | 15 `EXPECTED_NEW_AND_REMOVED` |
| residual probes | 18 globs | 0 residual (`residual_unexpected = 0`) |
| non-source probes (out of blast radius) | 5 | 3 `VERIFIED_IDENTICAL`, 2 `HASH_MISMATCH` (pre-existing, see §4) |

## 2. Method — what counts as content evidence

Size, mtime, pyc-header size, `git status` and "it imports" are **not** accepted as proof.

The strongest surviving content reference for a pre-incident file is the compiled artifact HPC produced
**from that pre-incident source**: `scripts/__pycache__/<mod>.cpython-39.pyc`. The audit compiles the current
source **in memory** (`compile(...)`, no pyc is written) and compares a canonical bytecode digest
(name / argcount / firstlineno / `co_code` / names / varnames / consts, recursing into nested code objects;
`co_filename` and `co_flags` excluded). Equal digests ⇒ the two sources are content-equivalent.
*Stated limitation:* bytecode does not encode comments or pure whitespace, so this proves semantic content
identity, not byte identity.

## 3. Per-file content evidence (the 7 reused dependency sources)

| file | status | current SHA-256 | pyc-recorded src size | bytecode cur / pre-incident pyc | Git |
|---|---|---|---|---|---|
| `scripts/configs.py` | VERIFIED_IDENTICAL | `5b64ad545a621b6b…` | 11206 = 11206 | `cfc139bb6f` = `cfc139bb6f` | untracked (no blob ref) |
| `scripts/scaler_utils.py` | VERIFIED_IDENTICAL | `efac4e58ca855630…` | 10915 = 10915 | `092284111d` = `092284111d` | untracked |
| `scripts/miflu_model.py` | PREEXISTING_LOCAL_MODIFICATION_VERIFIED | `0e6bdb61213bfdcc…` | 27160 = 27160 | `f2637df7cc` = `f2637df7cc` | tracked, working copy ≠ HEAD (documented refactor) |
| `scripts/textual_embedder.py` | VERIFIED_IDENTICAL | `71fb44abd97f056f…` | 11203 = 11203 | `9021c5972a` = `9021c5972a` | tracked, **clean** (HEAD blob = working copy) |
| `scripts/cdc_calendar.py` | VERIFIED_IDENTICAL | `963751eec162a8ee…` | 10991 = 10991 | `2cbffc945b` = `2cbffc945b` | untracked |
| `scripts/early_stopping.py` | VERIFIED_IDENTICAL | `be75264643f24c7d…` | 7202 = 7202 | `3a5b7e0b7d` = `3a5b7e0b7d` | untracked |
| `scripts/compute_miflu_indicators.py` | **UNRESOLVED** | `bf72d37ce9eaa21c…` | **24236 ≠ 24398** | `1c30218a46` ≠ `ad50ad3c8b` | tracked, working copy ≠ HEAD |

For the six verified files the current source compiles to **exactly** the bytecode of the surviving
pre-incident `.pyc`, so the extraction did not change their content. All seven also equal the frozen
innovation copy (`matches_frozen_copy = true`), i.e. their content is fully determined and known.

## 4. The one unresolved file — `scripts/compute_miflu_indicators.py`

* Current content: 24398 B, sha256 `bf72d37ce9eaa21c…` (identical to the local working copy and to the
  frozen v2.2 copy).
* The surviving pre-incident `.pyc` was compiled (2026-09-02) from a **24236 B** source, i.e. from an older
  revision; its bytecode differs from the current source's (`1c30218a46` vs `ad50ad3c8b`). Because the pyc is
  **stale**, it cannot certify the pre-incident content.
* Local Git HEAD blob is a different, earlier revision (~13.4 kB), so HEAD is **not** a usable reference
  either; the file had documented pre-incident working-tree edits.
* Searched for any pre-incident copy of the 24398 B revision on HPC: the only copies are the two deployment
  roots (`innov-v2.1_dc7ee964`, `innov-v2.2_06b83e18`, both tar-extracted, mtime epoch 0) and the audited file
  itself. No dated pre-incident copy exists.
* Searched for post-2026-09-03 outputs of that script on HPC that would reveal which revision was in use:
  none (latest indicator output is 2026-09-02 21:54).
* **Consequence:** it cannot be proven whether the extraction replaced the 24236 B revision with the local
  24398 B revision, or whether the 24398 B revision had already been uploaded before the incident. Status
  stays `UNRESOLVED`. Repair requires a decision: accept the current (local/frozen) content, or restore a
  specific older revision — **no action taken, nothing modified**.

## 5. Out-of-blast-radius divergence (informational, NOT incident damage)

| path | HPC mtime | HPC size | vs local |
|---|---|---|---|
| `data/scaler_miflu_national.json` | 2026-08-31T19:29:22Z | 527 | differs |
| `data/predictions_miflu_L24_paper_protocol.csv` | 2026-08-29T17:03:08Z | 1 491 171 | differs (local is newer/larger) |

Neither path is a bundle member, and both mtimes predate the incident by ~two weeks, so the extraction
**could not** have written them. They are pre-existing local↔remote divergences (each side regenerated at a
different time). They are reported for awareness and are deliberately **excluded from the incident gate**.
`data/raw/national_illness_raw.csv` and the `full__earlystop` `summary.csv` / `metrics.csv` are
`VERIFIED_IDENTICAL` against their untouched local copies.

## 6. Residual check (cleanup verification)

`scripts/innovation/`, `tests/innovation/`, `results/innovation/`, `MIFlu_innovation_plan_v2.md`,
`hpc_scripts/{innovation_worker.sh, hpc_env_check.sh, pilot_specs.json, pilot_*.sh(4), submit_innovation_*.sh(4)}`,
`results/innovation/source_snapshot_manifest.json` and the bundle/sidecar files are all **absent**
(`residual_unexpected = 0`). `hpc_scripts/` holds only the 14 original reproduction submit scripts, and
`results/` holds only `chattime_cgtsf_*` / `chattime_zeroshot_*` JSON plus the `ili/` and `local_dry_run/` trees.

## 7. Conclusion

The original reproduction repository is **not** declared unaffected: 6 of 7 affected sources are content-verified,
no residual remains, and every non-source probe outside the blast radius is explained — but one file is
`UNRESOLVED`, so the gate stays `false` and the blocker stays open.
