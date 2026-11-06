# SCIENTIFIC AUDIT — 2026-11-05T16:30:00Z / 2026-11-06 00:30 HKT

Status: **IN-PROGRESS**. Every claim below is tied to an exact source. A structural
validator PASS is structure/hash consistency only; `scientific_readiness: NOT_ASSESSED`.

## SUPPORTED

| Claim | Source | Population |
|---|---|---|
| Core 160/160 cells have valid artefacts | `cellok.py count core/export core/cells.tsv` | core panel, 4 arms x 4 L x 10 seeds |
| National 1080/1120 valid | `cellok.py count all/export all/cells_all.tsv` | 28-arm national roster |
| 40 blocked cells are all `ds_r1_distill_qwen1_5b` | `all/BLOCKED_CELLS.tsv`, `all/failed/*` (=2 attempts) | national roster |
| Cause of those 40 = HF cache LAYOUT mismatch | lane0_v2.log `LocalEntryNotFoundError`; offline `try_to_load_from_cache` with legacy layout resolves config/model/tokenizer | those 40 cells |
| 40 MIFlu checkpoints exist | `find core/ckpt/miflu -name best_miflu_L*.pth | wc -l` = 40 | core MIFlu |
| 0 seven-channel MIFlu tensors exist | `find core/export7ch -name '*.npz'` = 0; local RAW_EVIDENCE 237 non-MIFlu NPZ + 40 MIFlu ILITOTAL-only CSV | O1 |
| No Slurm job was killed by the 15:22 UTC recovery pkill | `sacct -u sychan552 --starttime=2026-11-05T15:00` — no CANCELLED; 735298/299/300/301 COMPLETED 0:0 | all jobs |
| The two data profiles differ in bytes but match numerically | measured aligned 7-channel comparison, max abs diff 0.0 | both profiles |

## PARTIAL

| Claim | Gap |
|---|---|
| 60/60 ablation cells DONE | per-run values, matched default reference, paired differences, variability not aggregated; no depth/LoRA trend |
| Three no-text CPU assertions 3 passed / 0 skipped | from an earlier run; test file, imported modules, pinned env, JUnit/stdout not bundled in this return |
| `legacy_done.tsv` 189/189 | counts attempts, not valid cells; final 50 tasks `rc=3` |
| 1080 national cells | not independently rescored here; raw tensors remain on HPC |

## CONTRADICTED

| Claim | Evidence |
|---|---|
| "189/189 legacy completion" | `legacy_lane.log` final 50: `SKIP_REASON=bad table6 task id`, `rc=3` |
| "MIFlu can join a 7-channel leaderboard" | MIFlu exports have only `ground_truth_ili / prediction_ili` columns |
| "117 / 139 / 141 are current counts" | fresh capture shows 1080/1120 |

## BLOCKED

| Output | Exact blocker |
|---|---|
| Harmonised leaderboard / both accuracy panels | 0/40 7-channel MIFlu tensors; 739549 PENDING to 11-07, CPU pilot 740296 running |
| Event-level peak matches | requires harmonised tensors + pre-frozen detector parameters |
| Paired statistics / new Holm | no common target population; dependence units undefined |
| 40 encoder cells | 740183 PENDING to 11-07 (root cause fixed) |
| Regional / rolling-origin validity | no eligible origins/regions frozen; synthetic calendar labels |
| Chronos/TimesFM controls | not executed; source-pinned config + measured pilot cost required |
| O2 calibration | optional; not executed; must not replace O1 |

## DO NOT INFER

Non-rejection is not equivalence. Fixed-weight CPU text checks do not establish
gradient reachability or independent training trajectories. 4/16 aggregate unit
passes are not seasonal probabilities. 211x parameters is not 211x latency.
Ten seeds are not ten independent epidemics. Formatting or a validator PASS is
not JBHI publishability.

## Historical snapshot (unchanged, separate)

28 = 13 conventional + 4 LLM-based + 11 frozen encoders; paired family 17 models
INCLUDING MIFlu, excluding DLinear/encoders = 136 pairs; proper Holm from `p_raw`
with forward cumulative maximum = 0/136 rejections, 128/136 raw p<0.05,
min adjusted p ~= 0.0664, NLinear–PatchTST 0.1172. MSE order MIFlu < PatchTST <
NLinear; PIE order NLinear < MIFlu < PatchTST ("inverted at both ends").
MIFlu and NLinear each 4/16 aggregate units, PatchTST 0/16. Never overwrite
`02_数字表格/*.csv` with new panels.


---

## O1 UPDATE 2026-11-05T16:41:46Z / 2026-11-06 00:41 HKT — common scoring UNBLOCKED (in progress)

A measured, validated **CPU export path** now bypasses the `gpu_a100` queue:

| Evidence | Value |
|---|---|
| Pilot job 740312 | COMPLETED 00:05:48, exit 0:0, `tiny` `cpunode-058`, **345 s/cell** |
| Tensor | `pred`/`target` `(170, 7, 24)`, all finite, panel `all_valid_strict` |
| `target_start_row` | 773..942, 170 test windows |
| `mse_all_z` (L24 s2021) | 1.7439234256744385 |
| CSV↔NPZ relation | CSV 19,032 rows over train/val/test; `abs_week − step` gives 793 starts (104..942); **test-only** NPZ starts 773..942 are a subset. 4080 `(start, step)` pairs on channel 4 (ILITOTAL) match to **1.776e-15**. |
| GPT-2 cache | MIFlu needs the DEFAULT `~/.cache/huggingface/hub`; overriding `HF_HOME` to `hf_cache` broke pilot 740296. |
| Full recovery | array **740344** (8 tasks, 4 concurrent, 5 cells each, 4h wall) on `tiny` CPU compute nodes, distinctly labelled `trackB_v2_7ch_cpu_array`; GPU job 739549 left intact. |

The relation "absolute CSV week minus forecast step reconstructs target start" is
**verified, not assumed**, and must be restricted to the TEST split. The CSV also
contains train/val rows, which is why its reconstructed start set is larger.
Channel order is recorded as `wili, unwili, age_0_4, age_5_24, ilitotal,
num_providers, ot` with ILITOTAL at index 4 — this is the assumed order and is
subject to the per-cell provenance check before any cross-model score.

**Still not claimed:** no harmonised leaderboard, no new Holm, no event-level
peaks, no ranking change. Those require all 40 tensors plus the 40 unblocked
encoder cells (`740183`, gpu_a100, 11-07) and the frozen panel spec.


---

## LIVE UPDATE 2026-11-05T16:49:21Z / 2026-11-06 00:49 HKT — first real 7-channel results

Array 740344 produced **4 of 40** validated tensors, 0 failures:

| Cell | Shape | target_start_row | mse_all_z | valid |
|---|---|---|---|---|
| L24_s2021 | (170,7,24) | 773..942 | 1.743923 | True |
| L24_s2022 | (170,7,24) | 773..942 | 1.686578 | True |
| L24_s2023 | (170,7,24) | 773..942 | 1.804358 | True |
| L24_s2024 | (170,7,24) | 773..942 | 1.816547 | True |

All pass `shape`, `finite`, `axis`/`channel` and `target_start_row` checks. These are
**all-valid-panel** values only; the historical-crop panel and any cross-model
comparison are NOT yet computed. Four numbers are not a leaderboard and must not be
used to revise the manuscript ranking. Per-cell provenance JSONs contain axis order,
channel names, target row indices, lead indices, scaler mean/std, profile hash,
checkpoint hash, seed, hardware and wall time.
