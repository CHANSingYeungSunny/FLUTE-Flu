# REPRODUCE

All commands are relative to the consolidated return tree root unless stated.
Use a Python with numpy/pandas/scipy and a POSIX shell.

## Local checks (already executed; logs are in `logs/`)
```
python scripts/verify_snapshot.py --raw-smoke
python -m pytest tests/test_snapshot_audit.py -q
python -m pytest tests_archive --collect-only -q
PYTHONPATH=05_程序代码 HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  python -m pytest -q -rs --junitxml=tests/no_text_runtime.xml \
  tests_archive/test_miflu_ablations.py -k 'no_text_makes_the_forward_pass_ignore_the_text_tensor or default_text_pathway_is_masked_out_documented_state or no_text_and_full_arms_agree_bitwise_on_cpu'
```
The archived collection reports import errors (exit 2); they were not deleted or
replaced with always-true assertions.

## Validate THIS return package (structure/hashes only)
```
python tools/make_return_manifest.py . --exclude VALIDATION_RESULT.json
python tools/validate_return.py . --out VALIDATION_RESULT.json
python tools/make_return_manifest.py . --exclude VALIDATION_RESULT.json
python tools/validate_return.py . --out VALIDATION_RESULT.json
```
`tools/` is copied from the DeepSeek_Burgundy_Handoff package. Extract BOTH
`RETURN_TO_CHATGPT.zip` and `RAW_EVIDENCE.zip` into one directory first, or raw
integrity validation cannot pass.

## One raw cell -> CSV -> conclusion (minimal executable example)
```
python code/trackB_v2/cellok.py check \
  RAW_EVIDENCE/cells/all/export/calf_llm/L24_s2021 backbone
python code/trackB_v2/cellok.py count \
  RAW_EVIDENCE/cells/all/export RAW_EVIDENCE/cells/all/cells_all.tsv
head RAW_EVIDENCE/cells/all/export/calf_llm/L24_s2021/metrics.csv
grep '^trackB|all|calf_llm|L24|s2021' RUN_METRICS.csv
```
`cellok.py` is the same validator the HPC controller uses; it checks artefact
presence, finite values and valid npz, not scientific correctness.

## On Burgundy (monitor / resume, NOT a fresh submission)
```
ssh sychan552@burgundy.hpc.cityu.edu.hk 'squeue -u sychan552; \
  python /gpfs1/scratch/sychan552/trackB_20261104/cellok.py count \
  /gpfs1/scratch/sychan552/trackB_20261104/all/export \
  /gpfs1/scratch/sychan552/trackB_20261104/all/cells_all.tsv'
```
To resume a dead controller only:
```
sbatch /gpfs1/scratch/sychan552/trackB_20261104/all/controller_v2.sbatch
```
Do NOT resubmit lanes manually while a controller is alive; its name-based
check prevents duplicates. Signed source of every patched script is under
`code/trackB_v2/`; the original files are preserved on HPC under
`trackB_20261104/v2_backup/`.
