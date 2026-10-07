# F1 SHARED EVALUATION CONTRACT

Generated 2026-10-06. Every clause is **enforced or asserted**, not merely stated.

Legend: ✅ enforced in code · ⚙️ set by an operator flag · 🔒 asserted by a preflight gate

| # | Clause | How it is enforced | Where |
|---|---|---|---|
| **S1** | same author 966-row dataset | `sha256sum` of the data file is compared against the pinned digest and the job **exits 4** on mismatch | `f1_gpu_fit.sbatch` ✅ |
| **S1b** | same dataset SHA-256 | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` pinned in the script | ✅ |
| **S2** | same chronological train/validation/Test boundaries | `data_loader`/`configs.derive_split` integer rule → 676/97/193; `A2_REQUIRE_STRICT=1` | ⚙️ |
| **S3** | scaler fitted on training rows only | `ScalerBundle` fitted on `data[:train_end]`; `assert dd["scaler"].train_end == dd["train_end"]` in `preflight()` | ✅ |
| **S4** | same target-variable contract | all 7 channels; `f1_score_all.py` compares `var_cols` against the declared list | ✅ gate G4 |
| **S5** | input length 104 | `CONFIG["T"] = 104` | ✅ |
| **S6** | horizons 24/36/48/60, independent runs | one job per (arm, horizon); `L_list = [24,36,48,60]` | ✅ |
| **S7** | identical legal forecast origins | `--containment strict`: the whole target block `[o+1, o+L]` must lie inside its split; `A2_REQUIRE_STRICT=1` makes a non-strict run **exit** | ✅ |
| **S8** | identical forecast leads | leads `1..L` for every model, by construction of the window builder | ✅ |
| **S9** | identical evaluated feature keys | see S4 | ✅ gate G4 |
| **S10** | same pilot seed | `SEED=42` in both sbatch scripts; `f1_score_all.py` flags any model whose seed set differs | ✅ gate G5 |
| **S11** | validation-only checkpoint selection | the trainers select on best **validation** `mse_all`; no Test quantity is computed during the fit | ✅ |
| **S12** | Test evaluated once, after selection | `DEFER_TEST=1` — the trainer logs *"Test NOT evaluated (validation-only fit)"* and writes the locked checkpoint instead | ✅ |
| **S13** | validation/Test shuffle disabled | `DataLoader(..., shuffle=False)` for the val and Test loaders in every trainer | ✅ |
| **S14** | evaluation `drop_last=False` | the F1 trainers construct their own `DataLoader`s **without** `drop_last`, so it defaults to `False`. (The released `data_factory` sets `drop_last=drop_last_test`; F1 does not use that path.) | ✅ |
| **S15** | predictions saved | `score_test_stage5.py::dump_predictions` writes `np.savez_compressed(pred, target, target_start_row, L, seed, var_cols, train_mean, train_std, ...)`; the naive runner writes the same schema | ✅ |
| **S16** | targets saved | same call, `target=` array | ✅ |
| **S17** | origin/lead/feature/horizon/seed metadata saved | the NPZ carries `target_start_row`, `L`, `seed`, `var_cols`; `score_test_stage5.py` also writes an origin manifest with epiweek labels | ✅ |
| **S18** | independent scoring | `f1_score_all.py` + `scorer_f1.py`; the arithmetic is delegated to `scripts/score_predictions_independent.py`, which the **training code never calls** | ✅ |
| **S19** | no Test-assisted selection | `DEFER_TEST=1` (S12) **and** an explicit rejection gate: an artefact whose `checkpoint_selection` metadata mentions Test is refused | ✅ gate + test A13 |
| **S20** | no Historical Track B checkpoint reuse | `scorer_f1` **rejects** any artefact with `profile` in `{historical_track_b, historical, track_b, july2026}`; F1 writes only to `$HOME/.../f1/` and never reads a v3 deployment root | ✅ test A10 |

---

## 1. The preflight assertion the brief requires

The brief asks for *"a preflight assertion that refuses to run if any required condition
is missing"*. Three layers implement it:

1. **At job start** (`f1_gpu_fit.sbatch`): the dataset SHA-256 is compared and the job
   exits `4` on mismatch; `A2_REQUIRE_STRICT=1` makes any non-strict containment exit.
2. **Inside the trainers**: `preflight()` asserts the scaler was fitted on the training
   rows and that Test targets lie inside the Test split.
3. **At scoring time** (`f1_score_all.py`): gates G1–G7. An artefact that is malformed,
   off-contract, Track-B-derived, or Test-selected is **rejected**, and F1 reports
   `FAILED_INTEGRITY` rather than producing a ranking.

Layer 3 is the last line of defence and is deliberately the strictest: it refuses to
score, rather than scoring something it cannot vouch for.

---

## 2. What "refuses" means in each failure mode

| Failure | Behaviour |
|---|---|
| wrong dataset | job exits 4 before training |
| non-strict containment | trainer exits (via `A2_REQUIRE_STRICT`) |
| NaN / Inf in predictions | artefact **rejected**, not scored |
| wrong number of variables | artefact rejected |
| pred/target shape mismatch | artefact rejected |
| missing `var_cols` | artefact rejected |
| non-standardized space | artefact rejected |
| Historical Track B profile | artefact rejected |
| Test-selected checkpoint metadata | artefact rejected |
| a model or horizon missing | gate G1/G2/G6 FAIL → status ≠ COMPLETE |
| forecast keys differ across models | gate G4 FAIL |
| more than one seed present | gate G5 FAIL |
| scoring not run | no ranking produced at all |

---

## 3. Deviations from the *released* implementation

F1 is **not** the released code path. Every deviation is declared in
`F1_TARGET_CONTRACT.md` §4 and is a deliberate correction, not an accident:

- 7 channels rather than 1;
- multivariate windows rather than univariate;
- validation selection rather than Test selection;
- predictions persisted;
- leakage-safe seasonal naive;
- 20 epochs / 5e-4 (a declared `RECONSTRUCTED_ASSUMPTION`).

Calling F1 a reproduction of the paper, or of the released code, would be false. It is a
**corrected fair comparison under a declared contract**.