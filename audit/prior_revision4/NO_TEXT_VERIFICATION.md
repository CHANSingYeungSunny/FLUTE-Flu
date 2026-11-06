# What is needed to verify the no-text invariant

A citation to a path is not enough to verify a file’s content or its runtime behaviour. The corrected upload already supplies the files needed for static verification. No additional upload is needed for that level of review.

## Static evidence now inspected

- `tests_archive/test_miflu_ablations.py`: the test assertions and matched-initialisation contract.
- `05_程序代码/miflu_model.py`: time-then-text concatenation, lower-triangular attention mask, selection of the first time-patch positions, and use_text flag.
- `05_程序代码/train_miflu.py`: resolve_variant and _text_batch, for the CLI contract.
- `05_程序代码/configs.py`: the default model configuration.

The archived file explicitly contains these model-level checks:

1. `test_no_text_makes_the_forward_pass_ignore_the_text_tensor`
2. `test_default_text_pathway_is_masked_out_documented_state`
3. `test_no_text_and_full_arms_agree_bitwise_on_cpu`

Their assertions are statically verified. Their outcomes here are **not executed**. Inference on fixed weights in eval mode is a narrower claim than equality of entire independently trained runs, where dropout/RNG paths can differ.

## Files needed for actual execution of the archived test

The four files above plus these current imported modules, all already present in this upload:

- `05_程序代码/textual_embedder.py`
- `05_程序代码/scaler_utils.py`
- `05_程序代码/cdc_calendar.py`
- `05_程序代码/walk_forward.py`

Runtime dependencies: pytest, torch, transformers, NumPy and pandas, in the owner’s known working versions. `GPT2Model.from_pretrained("gpt2")` also needs a locally cached, pinned GPT-2 config and weight file, with the revision and SHA-256 recorded. Tokenizer files are not needed for the three random-text-tensor checks unless other code constructs the textual embedder. Do not upload credentials or a private cache wholesale. A dependency/version record and the three test results with skip reasons are sufficient to review a local execution; weights need not be uploaded merely to cite that execution.

POSIX command from the project root:

```bash
PYTHONPATH="$PWD/05_程序代码" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python -m pytest -q -rs tests_archive/test_miflu_ablations.py -k 'no_text_makes_the_forward_pass_ignore_the_text_tensor or default_text_pathway_is_masked_out_documented_state or no_text_and_full_arms_agree_bitwise_on_cpu'
```

PowerShell equivalent:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) '05_程序代码')
$env:HF_HUB_OFFLINE = '1'
$env:TRANSFORMERS_OFFLINE = '1'
python -m pytest -q -rs tests_archive/test_miflu_ablations.py -k 'no_text_makes_the_forward_pass_ignore_the_text_tensor or default_text_pathway_is_masked_out_documented_state or no_text_and_full_arms_agree_bitwise_on_cpu'
```

These commands were **not executed here**. The archived _build helper catches model-loading errors and marks tests skipped, so a clean exit alone is not evidence of bitwise equality. Inspect `-rs` output and require the three named assertions to run, with no skipped model checks. The whole archive collection command was executed and failed, as recorded in ARCHIVE_COLLECTION_LOG.txt.
