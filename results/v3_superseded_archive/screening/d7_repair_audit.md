# D7 repair audit

Generated 2026-09-16T21:31:17Z.

## Defect

`screening_artifacts.py` executed `int(encoder.context_dim())`. With `--text-encoder none` that value is `None`, so Gate `566029` failed with `ExitCode 1:0`, 1/8 models (only `gpt2_miflu`, whose GPT-2 encoder reports 768).

## Repair

- added `_null_safe_context_dim(encoder)`; `context_dim()` called **at most once**
- `None` -> JSON `null`; `int` -> `int`; integral `float` -> `int`
- `bool` / `str` / other -> **TypeError** (fail closed)
- **no** substitution of `0`/`-1`/fabricated dimensions
- no change to encoder selection, model construction, forward pass, losses, training, predictions, metrics, checkpoints or the dataset

Classification: **BEHAVIOR_NEUTRAL_OPTIONAL_METADATA_SERIALIZATION_FIX**

## Version cascade

- version: `innov-v3.4-screening-artifact-contract` -> `innov-v3.5-context-dim-null-safe`
- files: 90 -> 90
- aggregate before: `8597d08e603048d4f86642ba4b1fb56689c54c64a630f72e2db313aec7603c91`
- aggregate after: `1856817016d84f75fce90073da51fe38414f1f59be98698490c5b52ba2bd39e3`
- v3.4 snapshot, bundles and deployment root preserved

## Model-free tests

- unexpected v3-relevant failures: **1**
- known stale legacy failures (not D7): 2
