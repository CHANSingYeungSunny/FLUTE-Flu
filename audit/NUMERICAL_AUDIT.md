# Verification of the corrected snapshot

The corrected data.py uses proper forward cumulative-max Holm. All source CSVs are preserved. The separate audit recomputes from p_raw without trusting the exported adjusted column. Full inputs are hashed in INPUT_SHA256.json.

| Claim | Recomputed value | Source | Status |
|---|---|---|---|
| Retained roster | 13 conventional + 4 LLM-based + 11 frozen encoders = 28 | BENCH_MSE_BY_MODEL_L.csv, family/model groups | Match |
| Leading MSE means | MIFlu 1.557389, PatchTST 1.662078, NLinear 1.871583 | Same file, keyed model × L | Match at requested precision |
| Spread | 3.605692× | Same file, max/min model means | Match, 3.6× |
| Peak passes | NLinear 4/16; MIFlu 4/16; PatchTST 0/16 | BENCH_PTE_PIE_BY_STEP.csv, recomputed conjunction | Match |
| Peak summary | NLinear PTE 1.677083, PIE 9.476573%; MIFlu 1.128472, 26.846017%; PatchTST 1.239583, 32.755029% | Same file, all 16 cells per arm | Match; MIFlu has best mean timing of these three |
| Rank associations | ρ(MSE,PIE)=+0.735632; ρ(MSE,passes)=−0.429189, p=0.022662 | Joined MSE/peak tables | Match; both signs have expected accuracy direction |
| Parameter regression | slope +0.1171442, R² 0.0222656 | BENCH_EFFICIENCY.csv, 11 rows with parameters | Match |
| Parameter trade-off | 211.0627× for 11.1940% lower observed MSE | NLinear/PatchTST rows | Match |
| Unadjusted pair count | 128/136 below 0.05 | BENCH_PAIRED_TESTS.csv p_raw | Match |
| Corrected pair count | 0/136 below 0.05 | Forward cumulative-max Holm | Match |
| Minimum adjusted p | Rounded-export calculation 0.066368; exact-grid recovery 0.06640625 | Same p_raw, 1/4096 grid documented by exact test code | Match, about 0.0664 |
| NLinear–PatchTST | 0.117180 from rounded exports; 0.1171875 after documented-grid recovery | Same file, model_a=nlinear/model_b=patchtst | Both round to 0.1172 |
| Paired family | 17 models, MIFlu included, DLinear excluded; 16 rows involve MIFlu | Unique model_a/model_b and membership checks | Residual prose mismatch in corrected handoff; repaired |
| Reproduction MSE | 1.3045 / 1.3561 / 1.6543 / 1.6829; mean 1.4995 | ESSAY_VS_REPRODUCTION_TABLE_V.csv lines 2–6 | Match; paper mean 1.4355 |
| Reproduction MAE | 0.7482 / 0.7712 / 0.8381 / 0.8596; mean 0.8043 | Same table lines 2–6 | Match; MAE signs are one lower/three higher |
| Encoder result | 4.737409–5.204929; every one exceeds decision tree 4.319765 | Benchmark CSV, encoder family | Match |
| Evaluation windows | 160/144/144/128 for L24/36/48/60 | Benchmark metadata and eval_windows.py | Match |
| Ablation | 27/60 at the supplied snapshot | Owner prompt §2.9 and constants | Owner-reported; live HPC not executed |
| Local data identity | Maximum numeric difference zero across 966×7 matching columns | Supplied author-format and paper-exact files | Match locally; independent upstream byte identity not verified |
| Hardware coverage | 204 provenance rows include excluded DLinear and omit MIFlu/encoders; overlap is 192 retained cells | BENCH_GPU_PROVENANCE.csv model names | Complete 336-cell hardware coverage not established |
| No-text invariant | Three named tests assert text invariance/default masking/full-no-text CPU equality | tests_archive/test_miflu_ablations.py | Assertions statically verified; runtime not executed |

The exported adjusted column is deliberately retained for provenance but is not consumed by the revised reporting path. Recovering the exact-test grid is labelled as recovery, not a fresh raw-prediction rescore. Minimum p resolution alone blocks rejection for this declared family at n=12. Overlapping horizons/targets make independence or exchangeability an additional concern.

ORIGINAL_NUMERICAL_INVENTORY.csv inventories every numeric token in the corrected upload’s six DOCX files with its sentence/table location. NON_SUPPORTED_SENTENCES.csv lists semantic claims needing repair or qualification. The complete document diffs record the revisions. Incidental token matches are not semantic proof.

Scope: headline export arithmetic and one raw NLinear prediction cell were rerun. Entire GPU training, all raw prediction cells, upstream source identity, ten-seed raw run provenance and live HPC were not executed. Their exact follow-up commands and required artefacts are listed separately. No complete independent raw-training verification is claimed.
