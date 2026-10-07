# Limitations, incidents and disclosures

## 1. Historic original-repository integrity uncertainty
- The pre-incident byte identity of `scripts/compute_miflu_indicators.py` could not be
  established; `historical_original_repository_integrity_verified=false` is retained
  permanently. The current script was adopted prospectively as canonical with a
  regression check against a trusted pre-incident prediction file.

## 2. Source-version repair history
- `innov-v2.1` -> `v2.2` (pilot-spec metadata) -> `v2.3` (governance + 5-layer metadata
  chain) -> `v2.4` (pilot script safety) -> `v2.5` (autonomous controller) -> `v2.6`
  (`{{`/`}}` literal in generated worker) -> `v2.7` (missing `import os`; stage-aware
  startup check) -> `v2.8` (run-dir stage disambiguation) -> `v2.9` (model-key slug and
  Test-path regex fixes) -> `v2.10` (Stage-F cohort provenance).
- None of these changed the scientific protocol (`innov-v2.0`), splits, scaler,
  prompt statistics, metrics, thresholds or early stopping.

## 3. Controller and stage-provenance defects
- Stages F/J/G/H/I/J all recorded `experiment_stage="full"`, producing 36 cross-stage
  duplicate specs. The champion cohort was therefore reconstructed **by provenance**
  (Stage-F only), never by performance values.
- Local gate stages (A/C/E/K) were initially skipped because they produce no Slurm job;
  fixed by giving them one synthetic step.

## 4. Selector normalisation and Test-path regex fixes
- `select_best_model.py` compared an un-slugged `gpt2_miflu` against a slugged
  `gpt2-miflu`, so the baseline cohort was always empty. Fixed in v2.9.
- The Test-isolation regex `test(evaluations)?` never matched `test_evaluations`;
  corrected to `test(_evaluations)?`.

## 5. Single-use Test receipt
- Exactly one receipt exists: `results/innovation/test_evaluations/
ONE_TIME_TEST_ACCESS_RECEIPT.json`, bound to `test_eval_id =
final_nlinear_20260915T145710Z`.
- The authorization was consumed on first access; the evaluation reported here is a
  **resume of that same evaluation**, not a second Test.

## 6. Test resume incident (2026-09-16) — login-node misuse
- The Test was originally launched with `nohup` **on the login node** instead of via
  `sbatch`. It entered **D state (uninterruptible I/O wait)** for >1 h 14 min at 41/52
  cells, which blocked `ps` and prevented sshd from forking new SSH sessions.
- Remedy: `kill -9 3032070` from an already-open shell (new sessions could not be
  created), then `pkill -9 -f run_one_time_test` / `-f controller.sh` for orphans.
- The remaining 11 cells were then run as **sbatch job 560659** on `stingy`.
- **Standing rule adopted:** no compute on the login node; everything via `sbatch`.

## 7. Statistical limitations
- The baseline arm has only 3 seeds (42-44) versus 10 for the champion; paired tests
  use only the 3 matched seeds and are severely underpowered.
- After Holm correction only one comparison (MAE at L=36) reaches p<0.05.
- No claim of statistical superiority is made; `observed best` is reported.

## 8. Incomplete items
- **EvoForecast (stage N)**: optional, beyond the authorization ceiling, not attempted.
- Pre-COVID/COVID split analysis was not pre-registered and is therefore **not**
  reported as a result.

## 9. Champion immutability
- The champion `nlinear` was frozen on validation before any Test access and was
  **never** reselected, retuned or retrained after Test results were seen.
